"""Agent-work backed goal runtime for the personal assistant host.

This is the migration seam to ``spawn-join-agent-work``; CLI wiring lands in
T015. The legacy ``work.store.WorkStore`` and ``scheduler.Scheduler`` remain as
a compatibility layer for HITL approvals.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import cast

from spawn_join_agent_work import (
    Clock,
    SqliteWorkStore,
    WorkConfigurationError,
    WorkExecutor,
    WorkItem,
    WorkRunner,
    WorkSpec,
)

from ..errors import HostConfigError

_GOAL_KIND = "personal-assistant.goal"


class GoalRuntime:
    """Durable goal queue backed by the agent-work SQLite store."""

    def __init__(self, database: Path, *, clock: Clock | None = None) -> None:
        raw = cast(object, database)
        if not isinstance(raw, Path):
            raise HostConfigError("database: must be a pathlib.Path")
        try:
            database.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise HostConfigError(f"database: cannot create parent: {exc}") from exc
        self._store = SqliteWorkStore(database, clock=clock)
        self._clock = clock

    @property
    def store(self) -> SqliteWorkStore:
        return self._store

    async def enqueue(
        self,
        goal: str,
        *,
        idempotency_key: str,
        due_at: datetime | None = None,
        deadline_seconds: float | None = None,
        max_attempts: int = 3,
    ) -> WorkItem:
        """Persist a goal and return its queued work item."""

        raw_goal = cast(object, goal)
        if not isinstance(raw_goal, str) or not raw_goal.strip():
            raise HostConfigError("goal: must be a non-empty string")
        try:
            spec = WorkSpec(
                kind=_GOAL_KIND,
                payload=goal.encode("utf-8"),
                idempotency_key=idempotency_key,
                available_at=due_at,
                deadline_seconds=deadline_seconds,
                max_attempts=max_attempts,
            )
        except WorkConfigurationError as exc:
            raise HostConfigError(f"goal: {exc}") from exc
        return await self._store.enqueue(spec)

    async def run_once(self, executor: WorkExecutor) -> int:
        """Claim and execute one batch of due goals."""

        runner = WorkRunner(self._store, executor, clock=self._clock)
        return await runner.run_once()

    async def serve(
        self,
        executor: WorkExecutor,
        *,
        stop: asyncio.Event | None = None,
    ) -> None:
        """Run the continuous claim/execute loop until stopped."""

        runner = WorkRunner(self._store, executor, clock=self._clock)
        await runner.serve(stop)


def goal_text(item: WorkItem) -> str:
    """Decode the human-readable goal stored in a work item's payload."""

    return item.spec.payload.decode("utf-8")
