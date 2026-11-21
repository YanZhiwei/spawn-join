"""Runner tests for spawn-join-agent-work."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from spawn_join_agent_work import (
    ConcurrencyPolicy,
    InMemoryWorkStore,
    LeaseLostError,
    RetryPolicy,
    WorkItem,
    WorkOutcome,
    WorkResult,
    WorkRunner,
    WorkSpec,
    WorkState,
)


class FrozenClock:
    def __init__(self, now: datetime) -> None:
        self.value = now

    def now(self) -> datetime:
        return self.value


NOW = datetime(2026, 11, 22, tzinfo=UTC)


def _make_runner(
    store: InMemoryWorkStore,
    clock: FrozenClock,
    result: WorkResult | BaseException,
    *,
    retry_policy: RetryPolicy | None = None,
    concurrency: ConcurrencyPolicy | None = None,
) -> WorkRunner:
    async def executor(item: WorkItem) -> WorkResult:
        if isinstance(result, BaseException):
            raise result
        return result

    return WorkRunner(
        store,
        executor,
        clock=clock,
        retry_policy=retry_policy,
        concurrency=concurrency,
    )


def test_success_completes_item() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    processed = asyncio.run(
        _make_runner(
            store, clock, WorkResult(outcome=WorkOutcome.SUCCESS, summary="done")
        ).run_once()
    )

    assert processed == 1
    finished = asyncio.run(store.get(item.id))
    assert finished is not None
    assert finished.state is WorkState.COMPLETED
    assert finished.result == "done"


def test_retry_result_requeues_with_backoff() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    asyncio.run(
        _make_runner(
            store,
            clock,
            WorkResult(outcome=WorkOutcome.RETRY, error="transient"),
            retry_policy=RetryPolicy(base_seconds=2, multiplier=3),
        ).run_once()
    )

    queued = asyncio.run(store.get(item.id))
    assert queued is not None
    assert queued.state is WorkState.QUEUED
    assert queued.last_error == "transient"
    assert queued.spec.available_at == NOW + timedelta(seconds=2)


def test_fail_result_marks_failed() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    asyncio.run(
        _make_runner(
            store, clock, WorkResult(outcome=WorkOutcome.FAIL, error="bad input")
        ).run_once()
    )

    failed = asyncio.run(store.get(item.id))
    assert failed is not None
    assert failed.state is WorkState.FAILED
    assert failed.last_error == "bad input"


def test_defer_result_waits_for_resume() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )
    until = NOW + timedelta(minutes=5)

    asyncio.run(
        _make_runner(
            store, clock, WorkResult(outcome=WorkOutcome.DEFER, wait_until=until)
        ).run_once()
    )

    waiting = asyncio.run(store.get(item.id))
    assert waiting is not None
    assert waiting.state is WorkState.WAITING
    assert waiting.spec.available_at == until


def test_executor_exception_becomes_terminal_failure() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    asyncio.run(_make_runner(store, clock, RuntimeError("boom")).run_once())

    failed = asyncio.run(store.get(item.id))
    assert failed is not None
    assert failed.state is WorkState.FAILED
    assert failed.last_error == "RuntimeError: boom"


def test_run_once_returns_zero_when_no_work() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    runner = _make_runner(store, clock, WorkResult(outcome=WorkOutcome.SUCCESS))
    assert asyncio.run(runner.run_once()) == 0


def test_run_once_respects_claim_batch() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    items = [
        asyncio.run(
            store.enqueue(
                WorkSpec(kind="report", payload=b"{}", idempotency_key=f"k{i}")
            )
        )
        for i in range(3)
    ]
    runner = _make_runner(
        store,
        clock,
        WorkResult(outcome=WorkOutcome.SUCCESS),
        concurrency=ConcurrencyPolicy(claim_batch=2),
    )

    assert asyncio.run(runner.run_once()) == 2
    states = [
        entry.state
        for entry in (asyncio.run(store.get(item.id)) for item in items)
        if entry is not None
    ]
    assert states.count(WorkState.COMPLETED) == 2
    assert states.count(WorkState.QUEUED) == 1


def test_retry_policy_limit_stops_retries() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    asyncio.run(
        _make_runner(
            store,
            clock,
            WorkResult(outcome=WorkOutcome.RETRY, error="transient"),
            retry_policy=RetryPolicy(max_attempts=1),
        ).run_once()
    )

    stopped = asyncio.run(store.get(item.id))
    assert stopped is not None
    assert stopped.state is WorkState.FAILED


def test_executor_cancellation_propagates_without_write_back() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    async def executor(item: WorkItem) -> WorkResult:
        raise asyncio.CancelledError

    runner = WorkRunner(store, executor, clock=clock)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(runner.run_once())

    running = asyncio.run(store.get(item.id))
    assert running is not None and running.state is WorkState.RUNNING


def test_fencing_rejects_stale_fail_write() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    async def executor(item: WorkItem) -> WorkResult:
        await store.cancel(item.id)
        return WorkResult(outcome=WorkOutcome.FAIL, error="late")

    runner = WorkRunner(store, executor, clock=clock)
    with pytest.raises(LeaseLostError):
        asyncio.run(runner.run_once())


def test_queue_and_namespace_are_passed_to_claim() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(
            WorkSpec(
                kind="report",
                payload=b"{}",
                idempotency_key="k1",
                queue="other",
                namespace="team-a",
            )
        )
    )

    default_runner = _make_runner(store, clock, WorkResult(outcome=WorkOutcome.SUCCESS))
    assert asyncio.run(default_runner.run_once()) == 0

    async def executor(item: WorkItem) -> WorkResult:
        return WorkResult(outcome=WorkOutcome.SUCCESS)

    runner = WorkRunner(
        store,
        executor,
        clock=clock,
        queues=("other",),
        namespace="team-a",
    )
    assert asyncio.run(runner.run_once()) == 1
    completed = asyncio.run(store.get(item.id))
    assert completed is not None and completed.state is WorkState.COMPLETED


def test_stale_lease_raises_lease_lost() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    async def executor(item: WorkItem) -> WorkResult:
        await store.cancel(item.id)
        return WorkResult(outcome=WorkOutcome.SUCCESS)

    runner = WorkRunner(store, executor, clock=clock)
    with pytest.raises(LeaseLostError):
        asyncio.run(runner.run_once())
