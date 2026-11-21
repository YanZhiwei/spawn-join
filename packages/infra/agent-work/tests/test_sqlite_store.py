"""SQLite store tests for spawn-join-agent-work (schema, claim, fencing)."""

from __future__ import annotations

import asyncio
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from spawn_join_agent_work import (
    SqliteWorkStore,
    WorkConfigurationError,
    WorkConflictError,
    WorkSpec,
    WorkState,
)


class FrozenClock:
    def __init__(self, now: datetime) -> None:
        self.value = now

    def now(self) -> datetime:
        return self.value


def _spec(
    key: str,
    *,
    priority: int = 0,
    queue: str = "default",
    namespace: str = "default",
    available_at: datetime | None = None,
) -> WorkSpec:
    return WorkSpec(
        kind="report",
        payload=b"{}",
        idempotency_key=key,
        priority=priority,
        queue=queue,
        namespace=namespace,
        available_at=available_at,
    )


def _store(tmp_path: Path, now: datetime) -> tuple[SqliteWorkStore, FrozenClock]:
    clock = FrozenClock(now)
    return SqliteWorkStore(tmp_path / "work.db", clock=clock), clock


def test_schema_is_created_and_wal_enabled(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    _store(tmp_path, now)
    with sqlite3.connect(tmp_path / "work.db") as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        version = connection.execute("SELECT version FROM schema_version").fetchone()[0]
    assert {"work_items", "schema_version"} <= tables
    assert mode == "wal"
    assert version == 1


def test_enqueue_get_and_duplicate_key(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _ = _store(tmp_path, now)

    item = asyncio.run(store.enqueue(_spec("k1", priority=5)))
    fetched = asyncio.run(store.get(item.id))

    assert fetched is not None
    assert fetched.id == item.id
    assert fetched.state is WorkState.QUEUED
    assert fetched.spec.priority == 5
    assert fetched.spec.payload == b"{}"
    assert fetched.attempts == 0

    with pytest.raises(WorkConflictError):
        asyncio.run(store.enqueue(_spec("k1")))

    assert asyncio.run(store.get("missing")) is None


def test_claim_filters_and_orders_by_priority(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _ = _store(tmp_path, now)

    low = asyncio.run(store.enqueue(_spec("low", priority=1)))
    high = asyncio.run(store.enqueue(_spec("high", priority=9)))
    other_queue = asyncio.run(store.enqueue(_spec("q", queue="other")))
    other_ns = asyncio.run(store.enqueue(_spec("n", namespace="other")))
    future = asyncio.run(
        store.enqueue(_spec("future", available_at=now + timedelta(hours=1)))
    )

    claimed = asyncio.run(
        store.claim(
            owner="worker-1",
            queues=["default"],
            namespace="default",
            limit=10,
            lease_seconds=60,
            now=now,
        )
    )
    assert [item.id for item in claimed] == [high.id, low.id]
    assert all(item.state is WorkState.RUNNING for item in claimed)
    assert all(item.attempts == 1 for item in claimed)
    assert all(item.lease is not None for item in claimed)

    remaining = {
        item.id
        for item in (
            asyncio.run(store.get(other_queue.id)),
            asyncio.run(store.get(other_ns.id)),
            asyncio.run(store.get(future.id)),
        )
        if item is not None
    }
    assert remaining == {other_queue.id, other_ns.id, future.id}
    assert (
        asyncio.run(
            store.claim(
                owner="worker-1",
                queues=[],
                namespace="default",
                limit=1,
                lease_seconds=60,
                now=now,
            )
        )
        == []
    )


def test_concurrent_claims_do_not_double_claim(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _ = _store(tmp_path, now)
    ids = {asyncio.run(store.enqueue(_spec(f"k{i}"))).id for i in range(3)}

    async def claim_two() -> list[str]:
        first, second = await asyncio.gather(
            store.claim(
                owner="worker-1",
                queues=["default"],
                namespace="default",
                limit=3,
                lease_seconds=60,
                now=now,
            ),
            store.claim(
                owner="worker-2",
                queues=["default"],
                namespace="default",
                limit=3,
                lease_seconds=60,
                now=now,
            ),
        )
        return [item.id for item in first + second]

    claimed = asyncio.run(claim_two())
    assert sorted(claimed) == sorted(ids)
    assert len(claimed) == len(set(claimed)) == 3


def test_single_item_claim_has_exactly_one_winner(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _ = _store(tmp_path, now)
    item = asyncio.run(store.enqueue(_spec("only")))

    async def claim_both() -> tuple[list[str], list[str]]:
        first, second = await asyncio.gather(
            store.claim(
                owner="worker-1",
                queues=["default"],
                namespace="default",
                limit=1,
                lease_seconds=60,
                now=now,
            ),
            store.claim(
                owner="worker-2",
                queues=["default"],
                namespace="default",
                limit=1,
                lease_seconds=60,
                now=now,
            ),
        )
        return [entry.id for entry in first], [entry.id for entry in second]

    first, second = asyncio.run(claim_both())
    assert sorted(first + second) == [item.id]
    assert (first == [] and second == [item.id]) or (
        first == [item.id] and second == []
    )


def test_expired_lease_is_reclaimed_once(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, clock = _store(tmp_path, now)
    item = asyncio.run(store.enqueue(_spec("k1")))

    first = asyncio.run(
        store.claim(
            owner="worker-1",
            queues=["default"],
            namespace="default",
            limit=1,
            lease_seconds=10,
            now=now,
        )
    )
    assert [claimed.id for claimed in first] == [item.id]

    clock.value = now + timedelta(seconds=11)
    reclaimed = asyncio.run(
        store.claim(
            owner="worker-2",
            queues=["default"],
            namespace="default",
            limit=1,
            lease_seconds=10,
            now=clock.value,
        )
    )
    assert [claimed.id for claimed in reclaimed] == [item.id]
    assert reclaimed[0].attempts == 2
    assert reclaimed[0].lease is not None
    assert reclaimed[0].lease.owner == "worker-2"

    again = asyncio.run(
        store.claim(
            owner="worker-3",
            queues=["default"],
            namespace="default",
            limit=1,
            lease_seconds=10,
            now=clock.value,
        )
    )
    assert again == []


def test_claim_argument_validation(tmp_path: Path) -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store, _ = _store(tmp_path, now)

    with pytest.raises(WorkConfigurationError):
        asyncio.run(
            store.claim(
                owner="",
                queues=["default"],
                namespace="default",
                limit=1,
                lease_seconds=1,
                now=now,
            )
        )
    with pytest.raises(WorkConfigurationError):
        asyncio.run(
            store.claim(
                owner="w",
                queues=["default"],
                namespace="default",
                limit=0,
                lease_seconds=1,
                now=now,
            )
        )
    with pytest.raises(WorkConfigurationError):
        asyncio.run(
            store.claim(
                owner="w",
                queues=["default"],
                namespace="default",
                limit=1,
                lease_seconds=0,
                now=now,
            )
        )
    with pytest.raises(WorkConfigurationError):
        asyncio.run(
            store.claim(
                owner="w",
                queues=["default"],
                namespace="default",
                limit=1,
                lease_seconds=1,
                now=datetime(2026, 11, 22),
            )
        )
