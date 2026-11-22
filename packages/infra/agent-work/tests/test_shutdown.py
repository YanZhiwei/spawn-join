"""Continuous serve loop and graceful shutdown tests."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from datetime import UTC, datetime

from spawn_join_agent_work import (
    ConcurrencyPolicy,
    InMemoryWorkStore,
    WorkEvent,
    WorkItem,
    WorkOutcome,
    WorkResult,
    WorkRunner,
    WorkSpec,
    WorkState,
)

NOW = datetime(2026, 11, 22, tzinfo=UTC)


class FrozenClock:
    def __init__(self, now: datetime) -> None:
        self.value = now

    def now(self) -> datetime:
        return self.value


class IdleNotifier:
    def __init__(self) -> None:
        self.closed = False

    async def publish(self, event: WorkEvent) -> None:
        return None

    async def subscribe(self, queues: Sequence[str]) -> AsyncIterator[WorkEvent]:
        await asyncio.Event().wait()
        yield WorkEvent(
            work_id="never",
            queue="default",
            namespace="default",
            type="wakeup",
            occurred_at=NOW,
        )

    async def aclose(self) -> None:
        self.closed = True


async def _wait_for_state(
    store: InMemoryWorkStore, work_id: str, state: WorkState, timeout: float = 2
) -> WorkItem:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        item = await store.get(work_id)
        if item is not None and item.state is state:
            return item
        await asyncio.sleep(0.01)
    raise AssertionError(f"item {work_id} never reached {state}")


def test_serve_processes_items_and_stops() -> None:
    async def scenario() -> WorkState:
        clock = FrozenClock(NOW)
        store = InMemoryWorkStore(clock=clock)
        item = await store.enqueue(
            WorkSpec(kind="report", payload=b"{}", idempotency_key="k1")
        )

        async def executor(item: WorkItem) -> WorkResult:
            return WorkResult(outcome=WorkOutcome.SUCCESS, summary="ok")

        runner = WorkRunner(
            store,
            executor,
            clock=clock,
            concurrency=ConcurrencyPolicy(poll_interval_seconds=0.01),
        )
        task = asyncio.create_task(runner.serve())
        finished = await _wait_for_state(store, item.id, WorkState.COMPLETED)
        await runner.astop()
        await asyncio.wait_for(task, timeout=2)
        return finished.state

    assert asyncio.run(scenario()) is WorkState.COMPLETED


def test_astop_releases_inflight_lease_immediately() -> None:
    async def scenario() -> WorkItem:
        clock = FrozenClock(NOW)
        store = InMemoryWorkStore(clock=clock)
        item = await store.enqueue(
            WorkSpec(kind="report", payload=b"{}", idempotency_key="k1")
        )
        blocked = asyncio.Event()

        async def executor(item: WorkItem) -> WorkResult:
            await blocked.wait()
            return WorkResult(outcome=WorkOutcome.SUCCESS)

        runner = WorkRunner(
            store,
            executor,
            clock=clock,
            concurrency=ConcurrencyPolicy(poll_interval_seconds=0.01),
        )
        task = asyncio.create_task(runner.serve())
        running = await _wait_for_state(store, item.id, WorkState.RUNNING)
        await asyncio.wait_for(runner.astop(), timeout=10)
        await asyncio.wait_for(task, timeout=2)
        released = await store.get(item.id)
        assert released is not None
        assert running.lease is not None
        return released

    released = asyncio.run(scenario())
    assert released.state is WorkState.QUEUED
    assert released.lease is None


def test_astop_is_idempotent_and_stalled_serve_returns() -> None:
    async def scenario() -> None:
        clock = FrozenClock(NOW)
        store = InMemoryWorkStore(clock=clock)

        async def executor(item: WorkItem) -> WorkResult:
            return WorkResult(outcome=WorkOutcome.SUCCESS)

        runner = WorkRunner(
            store,
            executor,
            clock=clock,
            concurrency=ConcurrencyPolicy(poll_interval_seconds=0.01),
        )
        await runner.astop()
        await asyncio.wait_for(runner.serve(), timeout=1)
        await runner.astop()

        task = asyncio.create_task(runner.serve())
        await asyncio.sleep(0.02)
        await runner.astop()
        await runner.astop()
        await asyncio.wait_for(task, timeout=2)

    asyncio.run(scenario())


class BrokenNotifier(IdleNotifier):
    async def subscribe(self, queues: Sequence[str]) -> AsyncIterator[WorkEvent]:
        raise RuntimeError("notifier unavailable")
        yield WorkEvent(
            work_id="never",
            queue="default",
            namespace="default",
            type="wakeup",
            occurred_at=NOW,
        )


def test_broken_notifier_falls_back_to_polling() -> None:
    async def scenario() -> WorkState:
        clock = FrozenClock(NOW)
        store = InMemoryWorkStore(clock=clock)
        notifier = BrokenNotifier()

        async def executor(item: WorkItem) -> WorkResult:
            return WorkResult(outcome=WorkOutcome.SUCCESS)

        runner = WorkRunner(
            store,
            executor,
            clock=clock,
            notifier=notifier,
            concurrency=ConcurrencyPolicy(poll_interval_seconds=0.01),
        )
        task = asyncio.create_task(runner.serve())
        await asyncio.sleep(0.02)
        item = await store.enqueue(
            WorkSpec(kind="report", payload=b"{}", idempotency_key="poll")
        )
        finished = await _wait_for_state(store, item.id, WorkState.COMPLETED)
        await runner.astop()
        await asyncio.wait_for(task, timeout=2)
        return finished.state

    assert asyncio.run(scenario()) is WorkState.COMPLETED


def test_max_concurrency_is_enforced() -> None:
    async def scenario() -> tuple[int, int]:
        clock = FrozenClock(NOW)
        store = InMemoryWorkStore(clock=clock)
        active = 0
        peak = 0

        async def executor(item: WorkItem) -> WorkResult:
            nonlocal active, peak
            active += 1
            peak = max(peak, active)
            await asyncio.sleep(0.02)
            active -= 1
            return WorkResult(outcome=WorkOutcome.SUCCESS)

        runner = WorkRunner(
            store,
            executor,
            clock=clock,
            concurrency=ConcurrencyPolicy(
                max_concurrency=1, claim_batch=2, poll_interval_seconds=0.01
            ),
        )
        items = [
            await store.enqueue(
                WorkSpec(kind="report", payload=b"{}", idempotency_key=f"k{i}")
            )
            for i in range(3)
        ]
        task = asyncio.create_task(runner.serve())
        for item in items:
            await _wait_for_state(store, item.id, WorkState.COMPLETED)
        await runner.astop()
        await asyncio.wait_for(task, timeout=2)
        return peak, len(items)

    peak, count = asyncio.run(scenario())
    assert peak == 1
    assert count == 3


def test_polling_fallback_processes_work_enqueued_after_start() -> None:
    async def scenario() -> WorkState:
        clock = FrozenClock(NOW)
        store = InMemoryWorkStore(clock=clock)

        async def executor(item: WorkItem) -> WorkResult:
            return WorkResult(outcome=WorkOutcome.SUCCESS)

        runner = WorkRunner(
            store,
            executor,
            clock=clock,
            concurrency=ConcurrencyPolicy(poll_interval_seconds=0.01),
        )
        task = asyncio.create_task(runner.serve())
        await asyncio.sleep(0.02)
        item = await store.enqueue(
            WorkSpec(kind="report", payload=b"{}", idempotency_key="late")
        )
        finished = await _wait_for_state(store, item.id, WorkState.COMPLETED)
        await runner.astop()
        await asyncio.wait_for(task, timeout=2)
        return finished.state

    assert asyncio.run(scenario()) is WorkState.COMPLETED


def test_notifier_is_closed_on_stop() -> None:
    async def scenario() -> bool:
        clock = FrozenClock(NOW)
        store = InMemoryWorkStore(clock=clock)
        notifier = IdleNotifier()

        async def executor(item: WorkItem) -> WorkResult:
            return WorkResult(outcome=WorkOutcome.SUCCESS)

        runner = WorkRunner(
            store,
            executor,
            clock=clock,
            notifier=notifier,
            concurrency=ConcurrencyPolicy(poll_interval_seconds=0.01),
        )
        task = asyncio.create_task(runner.serve())
        await asyncio.sleep(0.02)
        await runner.astop()
        await asyncio.wait_for(task, timeout=2)
        return notifier.closed

    assert asyncio.run(scenario()) is True
