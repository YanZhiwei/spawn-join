"""SQLite state-transition and fencing tests for spawn-join-agent-work."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from spawn_join_agent_work import (
    SqliteWorkStore,
    WorkConfigurationError,
    WorkItem,
    WorkSpec,
    WorkState,
)


class FrozenClock:
    def __init__(self, now: datetime) -> None:
        self.value = now

    def now(self) -> datetime:
        return self.value


def _make_store(tmp_path: Path, now: datetime) -> tuple[SqliteWorkStore, FrozenClock]:
    clock = FrozenClock(now)
    return SqliteWorkStore(tmp_path / "work.db", clock=clock), clock


def _claim_one(
    store: SqliteWorkStore, now: datetime, owner: str = "worker-1"
) -> WorkItem:
    claimed = asyncio.run(
        store.claim(
            owner=owner,
            queues=["default"],
            namespace="default",
            limit=1,
            lease_seconds=60,
            now=now,
        )
    )
    assert len(claimed) == 1
    return claimed[0]


def _running_item(
    tmp_path: Path, now: datetime, *, max_attempts: int = 3
) -> tuple[SqliteWorkStore, FrozenClock, WorkItem]:
    store, clock = _make_store(tmp_path, now)
    asyncio.run(
        store.enqueue(
            WorkSpec(
                kind="report",
                payload=b"{}",
                idempotency_key="k1",
                max_attempts=max_attempts,
            )
        )
    )
    return store, clock, _claim_one(store, now)


def test_heartbeat_extends_only_with_matching_token(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _, item = _running_item(tmp_path, now)
    assert item.lease is not None
    extended = now + timedelta(minutes=5)

    assert asyncio.run(
        store.heartbeat(work_id=item.id, token=item.lease.token, lease_until=extended)
    )
    refreshed = asyncio.run(store.get(item.id))
    assert refreshed is not None and refreshed.lease is not None
    assert refreshed.lease.until == extended

    assert not asyncio.run(
        store.heartbeat(work_id=item.id, token="wrong", lease_until=extended)
    )
    after_wrong = asyncio.run(store.get(item.id))
    assert after_wrong is not None and after_wrong.lease is not None
    assert after_wrong.lease.until == extended

    shorter = now + timedelta(minutes=1)
    assert not asyncio.run(
        store.heartbeat(work_id=item.id, token=item.lease.token, lease_until=shorter)
    )
    after_shorter = asyncio.run(store.get(item.id))
    assert after_shorter is not None and after_shorter.lease is not None
    assert after_shorter.lease.until == extended

    with pytest.raises(WorkConfigurationError):
        asyncio.run(
            store.heartbeat(
                work_id=item.id,
                token=item.lease.token,
                lease_until=datetime(2026, 1, 1),
            )
        )


def test_complete_is_fenced_and_terminal(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _, item = _running_item(tmp_path, now)
    assert item.lease is not None

    assert not asyncio.run(store.complete(work_id=item.id, token="stale", summary="x"))
    assert asyncio.run(
        store.complete(work_id=item.id, token=item.lease.token, summary="done")
    )

    finished = asyncio.run(store.get(item.id))
    assert finished is not None
    assert finished.state is WorkState.COMPLETED
    assert finished.result == "done"
    assert finished.completed_at is not None
    assert finished.lease is None
    assert not asyncio.run(
        store.complete(work_id=item.id, token=item.lease.token, summary="again")
    )
    assert not asyncio.run(
        store.heartbeat(
            work_id=item.id,
            token=item.lease.token,
            lease_until=now + timedelta(minutes=1),
        )
    )


def test_retryable_failure_requeues_at_retry_at(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _, item = _running_item(tmp_path, now)
    assert item.lease is not None
    retry_at = now + timedelta(seconds=30)

    assert asyncio.run(
        store.fail(
            work_id=item.id,
            token=item.lease.token,
            error="transient",
            retry_at=retry_at,
            terminal=False,
        )
    )
    failed = asyncio.run(store.get(item.id))
    assert failed is not None
    assert failed.state is WorkState.QUEUED
    assert failed.last_error == "transient"
    assert failed.spec.available_at == retry_at
    assert (
        asyncio.run(
            store.claim(
                owner="worker-2",
                queues=["default"],
                namespace="default",
                limit=1,
                lease_seconds=60,
                now=now,
            )
        )
        == []
    )
    reclaimed = asyncio.run(
        store.claim(
            owner="worker-2",
            queues=["default"],
            namespace="default",
            limit=1,
            lease_seconds=60,
            now=retry_at,
        )
    )
    assert [entry.id for entry in reclaimed] == [item.id]
    assert reclaimed[0].attempts == 2


def test_retryable_failure_exhausted_goes_dead(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _, item = _running_item(tmp_path, now, max_attempts=1)
    assert item.lease is not None

    assert asyncio.run(
        store.fail(
            work_id=item.id,
            token=item.lease.token,
            error="transient",
            retry_at=now + timedelta(seconds=5),
            terminal=False,
        )
    )
    dead = asyncio.run(store.get(item.id))
    assert dead is not None
    assert dead.state is WorkState.DEAD
    assert dead.completed_at is not None
    assert dead.last_error == "transient"


def test_terminal_failure_distinguishes_failed_and_dead(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _, item = _running_item(tmp_path, now)
    assert item.lease is not None

    assert asyncio.run(
        store.fail(
            work_id=item.id,
            token=item.lease.token,
            error="invalid input",
            retry_at=None,
            terminal=True,
        )
    )
    failed = asyncio.run(store.get(item.id))
    assert failed is not None and failed.state is WorkState.FAILED

    exhausted_path = tmp_path / "exhausted"
    exhausted_path.mkdir()
    store2, _, item2 = _running_item(exhausted_path, now, max_attempts=1)
    assert item2.lease is not None
    assert asyncio.run(
        store2.fail(
            work_id=item2.id,
            token=item2.lease.token,
            error="still failing",
            retry_at=None,
            terminal=True,
        )
    )
    dead = asyncio.run(store2.get(item2.id))
    assert dead is not None and dead.state is WorkState.DEAD


def test_failure_fencing_and_validation(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _, item = _running_item(tmp_path, now)
    assert item.lease is not None

    assert not asyncio.run(
        store.fail(
            work_id=item.id,
            token="stale",
            error="transient",
            retry_at=now + timedelta(seconds=1),
            terminal=False,
        )
    )
    with pytest.raises(WorkConfigurationError):
        asyncio.run(
            store.fail(
                work_id=item.id,
                token=item.lease.token,
                error="transient",
                retry_at=None,
                terminal=False,
            )
        )
    with pytest.raises(WorkConfigurationError):
        asyncio.run(
            store.fail(
                work_id=item.id,
                token=item.lease.token,
                error="",
                retry_at=None,
                terminal=True,
            )
        )
    with pytest.raises(WorkConfigurationError):
        asyncio.run(
            store.fail(
                work_id=item.id,
                token=item.lease.token,
                error="terminal with retry",
                retry_at=now + timedelta(seconds=1),
                terminal=True,
            )
        )
    still_running = asyncio.run(store.get(item.id))
    assert still_running is not None and still_running.state is WorkState.RUNNING


def test_defer_waits_and_resume_requeues(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _, item = _running_item(tmp_path, now)
    assert item.lease is not None
    until = now + timedelta(minutes=10)

    assert asyncio.run(
        store.defer(work_id=item.id, token=item.lease.token, until=until)
    )
    waiting = asyncio.run(store.get(item.id))
    assert waiting is not None and waiting.state is WorkState.WAITING
    assert (
        asyncio.run(
            store.claim(
                owner="worker-2",
                queues=["default"],
                namespace="default",
                limit=1,
                lease_seconds=60,
                now=until,
            )
        )
        == []
    )

    assert not asyncio.run(store.resume("missing"))
    assert asyncio.run(store.resume(item.id))
    assert not asyncio.run(store.resume(item.id))
    queued = asyncio.run(store.get(item.id))
    assert queued is not None and queued.state is WorkState.QUEUED
    assert [
        entry.id
        for entry in asyncio.run(
            store.claim(
                owner="worker-2",
                queues=["default"],
                namespace="default",
                limit=1,
                lease_seconds=60,
                now=until,
            )
        )
    ] == [item.id]


def test_defer_rejects_past_or_fenced_write(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _, item = _running_item(tmp_path, now)
    assert item.lease is not None

    with pytest.raises(WorkConfigurationError):
        asyncio.run(
            store.defer(
                work_id=item.id,
                token=item.lease.token,
                until=now - timedelta(seconds=1),
            )
        )
    assert not asyncio.run(
        store.defer(
            work_id=item.id,
            token="stale",
            until=now + timedelta(minutes=1),
        )
    )
    unchanged = asyncio.run(store.get(item.id))
    assert unchanged is not None and unchanged.state is WorkState.RUNNING


def test_cancel_reaches_terminal_and_blocks_write_back(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _, item = _running_item(tmp_path, now)
    assert item.lease is not None

    assert asyncio.run(store.cancel(item.id))
    cancelled = asyncio.run(store.get(item.id))
    assert cancelled is not None
    assert cancelled.state is WorkState.CANCELLED
    assert cancelled.completed_at is not None
    assert cancelled.lease is None
    assert not asyncio.run(store.cancel(item.id))
    assert not asyncio.run(
        store.complete(work_id=item.id, token=item.lease.token, summary="late")
    )

    queued_dir = tmp_path / "queued"
    queued_dir.mkdir()
    queued_store, _ = _make_store(queued_dir, now)
    queued = asyncio.run(
        queued_store.enqueue(
            WorkSpec(kind="report", payload=b"{}", idempotency_key="k2")
        )
    )
    assert asyncio.run(queued_store.cancel(queued.id))


def test_prune_only_removes_old_terminal_items(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, clock = _make_store(tmp_path, now)

    old = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="old"))
    )
    old_item = _claim_one(store, now)
    assert old_item.lease is not None
    asyncio.run(
        store.complete(work_id=old_item.id, token=old_item.lease.token, summary=None)
    )
    queued = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="queued"))
    )

    clock.value = now + timedelta(days=40)
    removed = asyncio.run(store.prune(before=now + timedelta(days=30)))
    assert removed == 1
    assert asyncio.run(store.get(old.id)) is None
    assert asyncio.run(store.get(queued.id)) is not None

    assert asyncio.run(store.cancel(queued.id))
    clock.value = now + timedelta(days=80)
    assert asyncio.run(store.prune(before=now + timedelta(days=70))) == 1

    with pytest.raises(WorkConfigurationError):
        asyncio.run(store.prune(before=clock.value + timedelta(days=1)))
    with pytest.raises(WorkConfigurationError):
        asyncio.run(store.prune(before=datetime(2026, 1, 1)))
