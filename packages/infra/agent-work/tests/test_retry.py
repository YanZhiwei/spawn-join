"""Retry, stop-loss, deadline, and cancellation tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from spawn_join_agent_work import (
    InMemoryWorkStore,
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


def _retry_runner(
    store: InMemoryWorkStore,
    clock: FrozenClock,
    *,
    retry: RetryPolicy,
) -> WorkRunner:
    async def executor(item: WorkItem) -> WorkResult:
        return WorkResult(outcome=WorkOutcome.RETRY, error="transient")

    return WorkRunner(store, executor, clock=clock, retry_policy=retry)


def test_retry_backoff_uses_exponential_delay_and_ends_dead() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(
            WorkSpec(
                kind="report",
                payload=b"{}",
                idempotency_key="k1",
                max_attempts=3,
            )
        )
    )
    runner = _retry_runner(
        store,
        clock,
        retry=RetryPolicy(base_seconds=2, multiplier=3, max_attempts=3),
    )

    for expected_delay in (2.0, 6.0):
        assert asyncio.run(runner.run_once()) == 1
        queued = asyncio.run(store.get(item.id))
        assert queued is not None
        assert queued.state is WorkState.QUEUED
        assert queued.spec.available_at is not None
        delay = (queued.spec.available_at - clock.value).total_seconds()
        assert delay == pytest.approx(expected_delay)
        clock.value = queued.spec.available_at

    assert asyncio.run(runner.run_once()) == 1
    dead = asyncio.run(store.get(item.id))
    assert dead is not None
    assert dead.state is WorkState.DEAD
    assert dead.attempts == 3
    assert dead.completed_at is not None
    assert dead.last_error == "transient"

    clock.value = clock.value + timedelta(hours=1)
    assert asyncio.run(runner.run_once()) == 0
    assert asyncio.run(store.get(item.id)) == dead


def test_policy_exhaustion_stops_as_failed_before_spec_limit() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(
            WorkSpec(
                kind="report",
                payload=b"{}",
                idempotency_key="k1",
                max_attempts=5,
            )
        )
    )
    runner = _retry_runner(store, clock, retry=RetryPolicy(max_attempts=1))

    assert asyncio.run(runner.run_once()) == 1
    failed = asyncio.run(store.get(item.id))
    assert failed is not None
    assert failed.state is WorkState.FAILED
    assert failed.attempts == 1
    assert failed.last_error == "transient"


def test_deadline_fails_item_with_timeout_error() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(
            WorkSpec(
                kind="report",
                payload=b"{}",
                idempotency_key="k1",
                deadline_seconds=0.05,
            )
        )
    )

    async def executor(item: WorkItem) -> WorkResult:
        await asyncio.sleep(0.2)
        return WorkResult(outcome=WorkOutcome.SUCCESS)

    runner = WorkRunner(store, executor, clock=clock)
    assert asyncio.run(runner.run_once()) == 1

    failed = asyncio.run(store.get(item.id))
    assert failed is not None
    assert failed.state is WorkState.FAILED
    assert failed.attempts == 1
    assert failed.result is None
    assert failed.last_error is not None
    assert failed.last_error.startswith("TimeoutError: deadline exceeded")


def test_executor_timeout_without_deadline_is_not_deadline_failure() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    async def executor(item: WorkItem) -> WorkResult:
        raise TimeoutError("host timeout")

    runner = WorkRunner(store, executor, clock=clock)
    assert asyncio.run(runner.run_once()) == 1

    failed = asyncio.run(store.get(item.id))
    assert failed is not None
    assert failed.state is WorkState.FAILED
    assert failed.last_error == "TimeoutError: host timeout"


def test_external_cancellation_propagates_and_keeps_item_running() -> None:
    clock = FrozenClock(NOW)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    async def executor(item: WorkItem) -> WorkResult:
        await asyncio.sleep(1)
        return WorkResult(outcome=WorkOutcome.SUCCESS)

    runner = WorkRunner(store, executor, clock=clock)

    async def scenario() -> None:
        task = asyncio.create_task(runner.run_once())
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    running = asyncio.run(store.get(item.id))
    assert running is not None
    assert running.state is WorkState.RUNNING
    assert running.result is None
