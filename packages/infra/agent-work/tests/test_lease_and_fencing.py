"""Lease heartbeat, expiry takeover, and fencing tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from spawn_join_agent_work import (
    InMemoryWorkStore,
    LeaseLostError,
    LeasePolicy,
    SqliteWorkStore,
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


def test_expired_lease_takeover_increments_attempts_and_fences_old_owner(
    tmp_path: Path,
) -> None:
    clock = FrozenClock(NOW)
    store = SqliteWorkStore(tmp_path / "work.db", clock=clock)
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    first = asyncio.run(
        store.claim(
            owner="worker-1",
            queues=["default"],
            namespace="default",
            limit=1,
            lease_seconds=10,
            now=NOW,
        )
    )
    assert len(first) == 1 and first[0].lease is not None

    clock.value = NOW + timedelta(seconds=11)
    second = asyncio.run(
        store.claim(
            owner="worker-2",
            queues=["default"],
            namespace="default",
            limit=1,
            lease_seconds=10,
            now=clock.value,
        )
    )
    assert [entry.id for entry in second] == [item.id]
    assert second[0].attempts == 2
    assert second[0].lease is not None and second[0].lease.owner == "worker-2"

    assert not asyncio.run(
        store.complete(work_id=item.id, token=first[0].lease.token, summary="stale")
    )
    assert asyncio.run(
        store.complete(work_id=item.id, token=second[0].lease.token, summary="takeover")
    )
    finished = asyncio.run(store.get(item.id))
    assert finished is not None
    assert finished.state is WorkState.COMPLETED
    assert finished.result == "takeover"


def test_runner_heartbeat_prevents_reclaim_while_executing() -> None:
    store = InMemoryWorkStore()
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    async def executor(item: WorkItem) -> WorkResult:
        await asyncio.sleep(0.6)
        return WorkResult(outcome=WorkOutcome.SUCCESS, summary="long")

    runner = WorkRunner(
        store,
        executor,
        lease_policy=LeasePolicy(seconds=0.3, heartbeat_seconds=0.05),
    )

    async def scenario() -> list[str]:
        task = asyncio.create_task(runner.run_once())
        await asyncio.sleep(0.45)
        intruder = await store.claim(
            owner="intruder",
            queues=["default"],
            namespace="default",
            limit=1,
            lease_seconds=0.05,
            now=datetime.now(UTC),
        )
        await task
        return [entry.id for entry in intruder]

    assert asyncio.run(scenario()) == []
    finished = asyncio.run(store.get(item.id))
    assert finished is not None
    assert finished.state is WorkState.COMPLETED
    assert finished.result == "long"


class FailingHeartbeatStore(InMemoryWorkStore):
    async def heartbeat(
        self, *, work_id: str, token: str, lease_until: datetime
    ) -> bool:
        return False


def test_failed_heartbeat_stops_write_back() -> None:
    store = FailingHeartbeatStore()
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    async def executor(item: WorkItem) -> WorkResult:
        await asyncio.sleep(0.08)
        return WorkResult(outcome=WorkOutcome.SUCCESS, summary="late")

    runner = WorkRunner(
        store,
        executor,
        lease_policy=LeasePolicy(seconds=0.1, heartbeat_seconds=0.02),
    )

    with pytest.raises(LeaseLostError):
        asyncio.run(runner.run_once())

    still_running = asyncio.run(store.get(item.id))
    assert still_running is not None
    assert still_running.state is WorkState.RUNNING
    assert still_running.result is None
