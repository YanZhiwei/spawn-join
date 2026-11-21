"""Asyncio due scheduler for durable work items.

The scheduler owns the work-item side of one bounded execution cycle: it
picks due queued items, marks them running under a concurrency bound, wraps
each executor call in an optional deadline, enforces the executor's
persisted outcome, and converts failures into stable ``failed`` states.
Executor exceptions are recorded as failed items (the store is the record)
instead of aborting sibling items; parent cancellation re-queues the
running item and propagates. Interrupted runs (hard kill) are re-queued
once at recovery via ``recover_interrupted``.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from .errors import HostSchedulingError
from .work.models import WorkItem, WorkStatus
from .work.store import WorkStore

WorkExecutor = Callable[[WorkItem], Awaitable[None]]
"""Runs one RUNNING work item and persists its final store state itself."""

_MIN_CONCURRENCY = 1


def _utc_now_iso() -> str:
    """Return the current UTC time as a sortable ISO-8601 string."""

    return datetime.now(UTC).isoformat()


def _require_positive_int(label: str, value: object) -> None:
    """Reject non-int, bool, or below-minimum concurrency input."""

    if not isinstance(value, int) or isinstance(value, bool):
        raise HostSchedulingError(f"{label}: must be an int")
    if value < _MIN_CONCURRENCY:
        raise HostSchedulingError(f"{label}: must be at least {_MIN_CONCURRENCY}")


def _require_positive_number_or_none(label: str, value: object) -> None:
    """Reject non-numeric (or non-positive) deadline input; None disables."""

    if value is None:
        return
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise HostSchedulingError(f"{label}: must be a number or None")
    if value <= 0:
        raise HostSchedulingError(f"{label}: must be greater than 0")


class Scheduler:
    """Bounded due scheduler over a single-writer work store."""

    def __init__(
        self,
        store: WorkStore,
        *,
        max_concurrency: int,
        deadline_seconds: float | None = None,
    ) -> None:
        _require_positive_int("max_concurrency", max_concurrency)
        _require_positive_number_or_none("deadline_seconds", deadline_seconds)
        self._store = store
        self._max_concurrency = max_concurrency
        self._deadline_seconds = deadline_seconds

    async def recover_interrupted(self) -> list[WorkItem]:
        """Requeue RUNNING items after a restart (interrupted rerun).

        Each interrupted item is re-queued exactly once here; a later
        ``run_due`` executes it once more, and the work item's idempotency
        key keeps any external side effect from duplicating.
        """

        requeued: list[WorkItem] = []
        for item in self._store.pending_recovery():
            if item.status is WorkStatus.RUNNING:
                requeued.append(self._store.mark(item.id, WorkStatus.QUEUED))
        return requeued

    async def run_due(
        self,
        executor: WorkExecutor,
        *,
        now: str | None = None,
    ) -> list[WorkItem]:
        """Run one bounded cycle over due queued items.

        Returns the persisted final state of every processed item. Items
        that are queued without a due time, or whose due time has passed,
        are eligible; parent cancellation propagates after re-queuing the
        interrupted item.
        """

        current = now if now is not None else _utc_now_iso()
        due = [
            item
            for item in self._store.pending_recovery()
            if item.status is WorkStatus.QUEUED
            and (item.due_at is None or item.due_at <= current)
        ]
        if not due:
            return []
        semaphore = asyncio.Semaphore(self._max_concurrency)
        outcomes = await asyncio.gather(
            *(self._run_one(semaphore, executor, item) for item in due)
        )
        return [outcome for outcome in outcomes if outcome is not None]

    async def _run_one(
        self,
        semaphore: asyncio.Semaphore,
        executor: WorkExecutor,
        item: WorkItem,
    ) -> WorkItem | None:
        async with semaphore:
            running = self._store.mark(
                item.id, WorkStatus.RUNNING, increment_attempt=True
            )
            try:
                if self._deadline_seconds is None:
                    await executor(running)
                else:
                    timeout = asyncio.timeout(self._deadline_seconds)
                    try:
                        async with timeout:
                            await executor(running)
                    except TimeoutError:
                        if not timeout.expired():
                            raise
                        return self._store.mark(
                            running.id,
                            WorkStatus.FAILED,
                            failure_category="deadline",
                        )
            except asyncio.CancelledError:
                self._store.mark(running.id, WorkStatus.QUEUED)
                raise
            except Exception as exc:
                current = self._store.get(running.id)
                if current is not None and current.status is WorkStatus.RUNNING:
                    return self._store.mark(
                        running.id,
                        WorkStatus.FAILED,
                        failure_category=type(exc).__name__,
                    )
                return current
            current = self._store.get(running.id)
            if current is None or current.status is WorkStatus.RUNNING:
                return self._store.mark(
                    running.id,
                    WorkStatus.FAILED,
                    failure_category="executor_incomplete",
                )
            return current
