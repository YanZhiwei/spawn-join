"""Smoke tests for the in-memory work store."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from spawn_join_agent_work import (
    InMemoryWorkStore,
    WorkConflictError,
    WorkSpec,
    WorkState,
)


class FrozenClock:
    def __init__(self, now: datetime) -> None:
        self.value = now

    def now(self) -> datetime:
        return self.value


def test_enqueue_claim_and_duplicate_key() -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store = InMemoryWorkStore(clock=FrozenClock(now))
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )
    assert asyncio.run(store.get(item.id)) == item
    with pytest.raises(WorkConflictError):
        asyncio.run(
            store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
        )
    assert asyncio.run(store.get("missing")) is None


def test_schedule_is_reflected_in_spec_available_at() -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store = InMemoryWorkStore(clock=FrozenClock(now))
    future = now + timedelta(hours=1)
    item = asyncio.run(
        store.enqueue(
            WorkSpec(
                kind="report",
                payload=b"{}",
                idempotency_key="k1",
                available_at=future,
            )
        )
    )
    assert item.spec.available_at == future

    immediate = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k2"))
    )
    claimed = asyncio.run(
        store.claim(
            owner="w1",
            queues=["default"],
            namespace="default",
            limit=1,
            lease_seconds=60,
            now=now,
        )
    )
    assert [entry.id for entry in claimed] == [immediate.id]
    assert claimed[0].spec.available_at == now


def test_claim_is_priority_ordered() -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store = InMemoryWorkStore(clock=FrozenClock(now))
    low = asyncio.run(
        store.enqueue(
            WorkSpec(kind="report", payload=b"{}", idempotency_key="low", priority=1)
        )
    )
    high = asyncio.run(
        store.enqueue(
            WorkSpec(kind="report", payload=b"{}", idempotency_key="high", priority=9)
        )
    )

    def claim(owner: str) -> list[str]:
        return [
            item.id
            for item in asyncio.run(
                store.claim(
                    owner=owner,
                    queues=["default"],
                    namespace="default",
                    limit=1,
                    lease_seconds=60,
                    now=now,
                )
            )
        ]

    assert claim("w1") == [high.id]
    assert claim("w2") == [low.id]


def test_single_item_claim_has_one_winner() -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    store = InMemoryWorkStore(clock=FrozenClock(now))
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="one"))
    )

    async def claim_both() -> tuple[list[str], list[str]]:
        first, second = await asyncio.gather(
            store.claim(
                owner="w1",
                queues=["default"],
                namespace="default",
                limit=1,
                lease_seconds=60,
                now=now,
            ),
            store.claim(
                owner="w2",
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


def test_expired_lease_reclaims_until_exhausted() -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    clock = FrozenClock(now)
    store = InMemoryWorkStore(clock=clock)
    item = asyncio.run(
        store.enqueue(
            WorkSpec(
                kind="report",
                payload=b"{}",
                idempotency_key="k1",
                max_attempts=1,
            )
        )
    )
    claimed = asyncio.run(
        store.claim(
            owner="w1",
            queues=["default"],
            namespace="default",
            limit=1,
            lease_seconds=5,
            now=now,
        )
    )
    assert [entry.id for entry in claimed] == [item.id]
    clock.value = now + timedelta(seconds=6)
    assert (
        asyncio.run(
            store.claim(
                owner="w2",
                queues=["default"],
                namespace="default",
                limit=1,
                lease_seconds=5,
                now=clock.value,
            )
        )
        == []
    )
    dead = asyncio.run(store.get(item.id))
    assert dead is not None and dead.state is WorkState.DEAD
