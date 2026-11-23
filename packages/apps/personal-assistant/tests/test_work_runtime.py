"""Agent-work backed goal runtime tests."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from spawn_join_personal_assistant import GoalRuntime, HostConfigError, goal_text

from spawn_join_agent_work import (
    WorkConflictError,
    WorkItem,
    WorkOutcome,
    WorkResult,
    WorkState,
)

NOW = datetime(2026, 11, 22, tzinfo=UTC)


class FrozenClock:
    def __init__(self, now: datetime) -> None:
        self.value = now

    def now(self) -> datetime:
        return self.value


def test_enqueue_and_run_goal(tmp_path: Path) -> None:
    clock = FrozenClock(NOW)
    runtime = GoalRuntime(tmp_path / "goals.db", clock=clock)
    item = asyncio.run(runtime.enqueue("say hi", idempotency_key="k1"))
    assert item.state is WorkState.QUEUED

    async def executor(item: WorkItem) -> WorkResult:
        assert goal_text(item) == "say hi"
        return WorkResult(outcome=WorkOutcome.SUCCESS, summary="ok")

    assert asyncio.run(runtime.run_once(executor)) == 1
    finished = asyncio.run(runtime.store.get(item.id))
    assert finished is not None
    assert finished.state is WorkState.COMPLETED
    assert finished.result == "ok"


def test_deadline_and_due_are_mapped(tmp_path: Path) -> None:
    clock = FrozenClock(NOW)
    runtime = GoalRuntime(tmp_path / "goals.db", clock=clock)
    due = NOW + timedelta(minutes=5)
    item = asyncio.run(
        runtime.enqueue(
            "bounded", idempotency_key="k1", due_at=due, deadline_seconds=2.5
        )
    )
    assert item.spec.available_at == due
    assert item.spec.deadline_seconds == 2.5


def test_invalid_goal_inputs_raise_host_config_error(tmp_path: Path) -> None:
    runtime = GoalRuntime(tmp_path / "goals.db", clock=FrozenClock(NOW))
    with pytest.raises(HostConfigError):
        asyncio.run(runtime.enqueue("   ", idempotency_key="k1"))
    with pytest.raises(HostConfigError):
        asyncio.run(
            runtime.enqueue(
                "naive", idempotency_key="k2", due_at=datetime(2026, 11, 22)
            )
        )
    with pytest.raises(HostConfigError):
        GoalRuntime("not-a-path")  # type: ignore[arg-type]


def test_duplicate_goal_is_rejected(tmp_path: Path) -> None:
    runtime = GoalRuntime(tmp_path / "goals.db", clock=FrozenClock(NOW))
    asyncio.run(runtime.enqueue("first", idempotency_key="k1"))
    with pytest.raises(WorkConflictError):
        asyncio.run(runtime.enqueue("second", idempotency_key="k1"))


def test_future_goal_is_not_claimed(tmp_path: Path) -> None:
    clock = FrozenClock(NOW)
    runtime = GoalRuntime(tmp_path / "goals.db", clock=clock)
    asyncio.run(
        runtime.enqueue("later", idempotency_key="k1", due_at=NOW + timedelta(hours=1))
    )

    async def executor(item: WorkItem) -> WorkResult:
        raise AssertionError("future goal must not run")

    assert asyncio.run(runtime.run_once(executor)) == 0


def test_serve_processes_goal_and_stops(tmp_path: Path) -> None:
    clock = FrozenClock(NOW)
    runtime = GoalRuntime(tmp_path / "goals.db", clock=clock)
    item = asyncio.run(runtime.enqueue("serve me", idempotency_key="k1"))

    async def executor(item: WorkItem) -> WorkResult:
        return WorkResult(outcome=WorkOutcome.SUCCESS, summary="served")

    async def scenario() -> WorkState:
        stop = asyncio.Event()
        finished: WorkItem | None = None
        runner_task = asyncio.create_task(runtime.serve(executor, stop=stop))
        for _ in range(200):
            finished = await runtime.store.get(item.id)
            if finished is not None and finished.state is WorkState.COMPLETED:
                break
            await asyncio.sleep(0.01)
        stop.set()
        await asyncio.wait_for(runner_task, timeout=2)
        assert finished is not None
        return finished.state

    assert asyncio.run(scenario()) is WorkState.COMPLETED
