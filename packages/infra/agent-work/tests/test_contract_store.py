"""Shared behavioural contract for every WorkStore implementation.

The suite is parameterized over the SQLite and in-memory adapters; a new
adapter must pass it unchanged.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from spawn_join_agent_work import (
    InMemoryWorkStore,
    SqliteWorkStore,
    WorkConflictError,
    WorkItem,
    WorkSpec,
    WorkState,
    WorkStore,
)

NOW = datetime(2026, 11, 22, tzinfo=UTC)


class FrozenClock:
    def __init__(self, now: datetime) -> None:
        self.value = now

    def now(self) -> datetime:
        return self.value


@dataclass(frozen=True)
class Harness:
    store: WorkStore
    clock: FrozenClock


@pytest.fixture(params=["sqlite", "memory"])
def harness(request: pytest.FixtureRequest, tmp_path: Path) -> Harness:
    clock = FrozenClock(NOW)
    if request.param == "sqlite":
        return Harness(SqliteWorkStore(tmp_path / "work.db", clock=clock), clock)
    return Harness(InMemoryWorkStore(clock=clock), clock)


def _spec(
    key: str,
    *,
    priority: int = 0,
    queue: str = "default",
    namespace: str = "default",
    available_at: datetime | None = None,
    max_attempts: int = 3,
) -> WorkSpec:
    return WorkSpec(
        kind="report",
        payload=b"{}",
        idempotency_key=key,
        priority=priority,
        queue=queue,
        namespace=namespace,
        available_at=available_at,
        max_attempts=max_attempts,
    )


def _claim(
    harness: Harness,
    *,
    owner: str = "worker-1",
    limit: int = 1,
    queues: tuple[str, ...] = ("default",),
    namespace: str = "default",
    lease_seconds: float = 60,
    now: datetime | None = None,
) -> list[WorkItem]:
    return asyncio.run(
        harness.store.claim(
            owner=owner,
            queues=queues,
            namespace=namespace,
            limit=limit,
            lease_seconds=lease_seconds,
            now=now or harness.clock.value,
        )
    )


def _running(harness: Harness, *, max_attempts: int = 3) -> WorkItem:
    asyncio.run(harness.store.enqueue(_spec("k1", max_attempts=max_attempts)))
    claimed = _claim(harness)
    assert len(claimed) == 1
    return claimed[0]


def test_enqueue_is_durable_and_idempotent(harness: Harness) -> None:
    item = asyncio.run(harness.store.enqueue(_spec("k1")))
    fetched = asyncio.run(harness.store.get(item.id))
    assert fetched == item
    assert fetched is not None and fetched.state is WorkState.QUEUED

    with pytest.raises(WorkConflictError):
        asyncio.run(harness.store.enqueue(_spec("k1")))
    assert asyncio.run(harness.store.get("missing")) is None


def test_claim_filters_and_orders_by_priority(harness: Harness) -> None:
    low = asyncio.run(harness.store.enqueue(_spec("low", priority=1)))
    high = asyncio.run(harness.store.enqueue(_spec("high", priority=9)))
    other_queue = asyncio.run(harness.store.enqueue(_spec("q", queue="other")))
    other_ns = asyncio.run(harness.store.enqueue(_spec("n", namespace="other")))
    future = asyncio.run(
        harness.store.enqueue(_spec("future", available_at=NOW + timedelta(hours=1)))
    )

    claimed = _claim(harness, limit=10)
    assert [item.id for item in claimed] == [high.id, low.id]
    assert all(item.state is WorkState.RUNNING for item in claimed)
    assert all(item.attempts == 1 and item.lease is not None for item in claimed)

    untouched = {
        item.id
        for item in (
            asyncio.run(harness.store.get(other_queue.id)),
            asyncio.run(harness.store.get(other_ns.id)),
            asyncio.run(harness.store.get(future.id)),
        )
        if item is not None
    }
    assert untouched == {other_queue.id, other_ns.id, future.id}
    assert [entry.id for entry in _claim(harness, queues=("other",))] == [
        other_queue.id
    ]
    assert _claim(harness, queues=()) == []


def test_claim_breaks_priority_ties_by_creation_order(harness: Harness) -> None:
    first = asyncio.run(harness.store.enqueue(_spec("first", priority=5)))
    harness.clock.value = NOW + timedelta(seconds=1)
    second = asyncio.run(harness.store.enqueue(_spec("second", priority=5)))

    claimed = _claim(harness, limit=2, now=NOW + timedelta(seconds=2))
    assert [item.id for item in claimed] == [first.id, second.id]


def test_single_item_claim_has_one_winner(harness: Harness) -> None:
    item = asyncio.run(harness.store.enqueue(_spec("only")))

    async def claim_both() -> tuple[list[str], list[str]]:
        first, second = await asyncio.gather(
            harness.store.claim(
                owner="worker-1",
                queues=["default"],
                namespace="default",
                limit=1,
                lease_seconds=60,
                now=NOW,
            ),
            harness.store.claim(
                owner="worker-2",
                queues=["default"],
                namespace="default",
                limit=1,
                lease_seconds=60,
                now=NOW,
            ),
        )
        return [entry.id for entry in first], [entry.id for entry in second]

    first, second = asyncio.run(claim_both())
    assert sorted(first + second) == [item.id]
    assert (first == [] and second == [item.id]) or (
        first == [item.id] and second == []
    )


def test_expired_lease_is_reclaimed_and_old_token_is_fenced(harness: Harness) -> None:
    item = _running(harness)
    assert item.lease is not None
    harness.clock.value = NOW + timedelta(seconds=61)

    reclaimed = _claim(harness, owner="worker-2")
    assert [entry.id for entry in reclaimed] == [item.id]
    assert reclaimed[0].attempts == 2
    assert reclaimed[0].lease is not None
    assert reclaimed[0].lease.owner == "worker-2"

    assert not asyncio.run(
        harness.store.complete(work_id=item.id, token=item.lease.token, summary="stale")
    )
    after_stale = asyncio.run(harness.store.get(item.id))
    assert after_stale is not None
    assert after_stale.state is WorkState.RUNNING
    assert after_stale.lease is not None
    assert after_stale.lease.owner == "worker-2"

    assert asyncio.run(
        harness.store.complete(
            work_id=item.id, token=reclaimed[0].lease.token, summary="done"
        )
    )
    finished = asyncio.run(harness.store.get(item.id))
    assert finished is not None
    assert finished.state is WorkState.COMPLETED
    assert finished.result == "done"
    assert finished.completed_at is not None
    assert finished.lease is None
    assert _claim(harness, owner="worker-3") == []


def test_expired_lease_exhaustion_becomes_dead(harness: Harness) -> None:
    item = _running(harness, max_attempts=1)
    assert item.lease is not None
    harness.clock.value = NOW + timedelta(seconds=61)
    assert _claim(harness, owner="worker-2") == []
    dead = asyncio.run(harness.store.get(item.id))
    assert dead is not None and dead.state is WorkState.DEAD


def test_heartbeat_only_extends_and_is_fenced(harness: Harness) -> None:
    item = _running(harness)
    assert item.lease is not None
    extended = NOW + timedelta(minutes=5)

    assert asyncio.run(
        harness.store.heartbeat(
            work_id=item.id, token=item.lease.token, lease_until=extended
        )
    )
    refreshed = asyncio.run(harness.store.get(item.id))
    assert refreshed is not None and refreshed.lease is not None
    assert refreshed.lease.until == extended

    assert not asyncio.run(
        harness.store.heartbeat(work_id=item.id, token="wrong", lease_until=extended)
    )
    assert not asyncio.run(
        harness.store.heartbeat(
            work_id=item.id,
            token=item.lease.token,
            lease_until=NOW + timedelta(minutes=1),
        )
    )
    after = asyncio.run(harness.store.get(item.id))
    assert after is not None and after.lease is not None
    assert after.lease.until == extended


def test_retry_requeues_at_retry_at(harness: Harness) -> None:
    item = _running(harness)
    assert item.lease is not None
    retry_at = NOW + timedelta(seconds=30)

    assert asyncio.run(
        harness.store.fail(
            work_id=item.id,
            token=item.lease.token,
            error="transient",
            retry_at=retry_at,
            terminal=False,
        )
    )
    queued = asyncio.run(harness.store.get(item.id))
    assert queued is not None
    assert queued.state is WorkState.QUEUED
    assert queued.last_error == "transient"
    assert queued.spec.available_at == retry_at
    assert _claim(harness, owner="worker-2", now=NOW) == []

    reclaimed = _claim(harness, owner="worker-2", now=retry_at)
    assert [entry.id for entry in reclaimed] == [item.id]
    assert reclaimed[0].attempts == 2


def test_retryable_failure_exhaustion_becomes_dead(harness: Harness) -> None:
    item = _running(harness, max_attempts=1)
    assert item.lease is not None
    retry_at = NOW + timedelta(seconds=30)

    assert asyncio.run(
        harness.store.fail(
            work_id=item.id,
            token=item.lease.token,
            error="transient",
            retry_at=retry_at,
            terminal=False,
        )
    )
    dead = asyncio.run(harness.store.get(item.id))
    assert dead is not None
    assert dead.state is WorkState.DEAD
    assert dead.completed_at is not None
    assert _claim(harness, owner="worker-2", now=retry_at) == []


def test_terminal_failure_distinguishes_failed_and_dead(harness: Harness) -> None:
    item = _running(harness)
    assert item.lease is not None
    assert asyncio.run(
        harness.store.fail(
            work_id=item.id,
            token=item.lease.token,
            error="invalid",
            retry_at=None,
            terminal=True,
        )
    )
    failed = asyncio.run(harness.store.get(item.id))
    assert failed is not None and failed.state is WorkState.FAILED

    asyncio.run(harness.store.enqueue(_spec("dead", max_attempts=1)))
    claimed = _claim(harness)
    assert len(claimed) == 1 and claimed[0].lease is not None
    assert asyncio.run(
        harness.store.fail(
            work_id=claimed[0].id,
            token=claimed[0].lease.token,
            error="still failing",
            retry_at=None,
            terminal=True,
        )
    )
    dead = asyncio.run(harness.store.get(claimed[0].id))
    assert dead is not None and dead.state is WorkState.DEAD


def test_defer_waits_and_resume_requeues(harness: Harness) -> None:
    item = _running(harness)
    assert item.lease is not None
    until = NOW + timedelta(minutes=10)

    assert asyncio.run(
        harness.store.defer(work_id=item.id, token=item.lease.token, until=until)
    )
    waiting = asyncio.run(harness.store.get(item.id))
    assert waiting is not None
    assert waiting.state is WorkState.WAITING
    assert waiting.spec.available_at == until
    assert _claim(harness, owner="worker-2", now=until) == []

    assert asyncio.run(harness.store.resume(item.id))
    assert not asyncio.run(harness.store.resume(item.id))
    queued = asyncio.run(harness.store.get(item.id))
    assert queued is not None and queued.state is WorkState.QUEUED
    assert [entry.id for entry in _claim(harness, owner="worker-2", now=until)] == [
        item.id
    ]


def test_cancel_and_prune_release_idempotency_key(harness: Harness) -> None:
    item = _running(harness)
    assert item.lease is not None
    assert asyncio.run(harness.store.cancel(item.id))
    cancelled = asyncio.run(harness.store.get(item.id))
    assert cancelled is not None
    assert cancelled.state is WorkState.CANCELLED
    assert cancelled.completed_at is not None
    assert not asyncio.run(harness.store.cancel(item.id))
    assert not asyncio.run(
        harness.store.complete(work_id=item.id, token=item.lease.token, summary="late")
    )

    queued = asyncio.run(harness.store.enqueue(_spec("keep")))
    harness.clock.value = NOW + timedelta(days=40)
    assert asyncio.run(harness.store.prune(before=NOW + timedelta(days=30))) == 1
    assert asyncio.run(harness.store.get(item.id)) is None
    assert asyncio.run(harness.store.get(queued.id)) is not None

    reused = asyncio.run(harness.store.enqueue(_spec("k1")))
    assert reused.state is WorkState.QUEUED
