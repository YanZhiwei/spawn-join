"""Work-item state machine for the personal assistant host.

A work item is a durable, resumable unit of agent work. ``WorkStatus`` plus
``transition_allowed`` are the only authority for legal transitions; the
store enforces them on every mutation so an illegal move fails loudly
instead of silently rewriting history.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WorkStatus(StrEnum):
    """Lifecycle states of a durable work item."""

    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_ALLOWED_TRANSITIONS: dict[WorkStatus, frozenset[WorkStatus]] = {
    WorkStatus.QUEUED: frozenset({WorkStatus.RUNNING, WorkStatus.CANCELLED}),
    WorkStatus.RUNNING: frozenset(
        {
            # Interrupted rerun: a hard-killed or parent-cancelled run goes
            # back to the queue so recovery executes it exactly once more.
            WorkStatus.QUEUED,
            WorkStatus.WAITING_APPROVAL,
            WorkStatus.COMPLETED,
            WorkStatus.FAILED,
            WorkStatus.CANCELLED,
        }
    ),
    WorkStatus.WAITING_APPROVAL: frozenset(
        {
            WorkStatus.RUNNING,
            WorkStatus.FAILED,
            WorkStatus.CANCELLED,
        }
    ),
    WorkStatus.COMPLETED: frozenset(),
    WorkStatus.FAILED: frozenset(),
    WorkStatus.CANCELLED: frozenset(),
}


def transition_allowed(current: WorkStatus, target: WorkStatus) -> bool:
    """Report whether the state machine permits ``current`` -> ``target``."""

    return target in _ALLOWED_TRANSITIONS[current]


@dataclass(frozen=True, slots=True)
class WorkItem:
    """A durable unit of agent work with its lifecycle fields.

    Attributes:
        id: Store-assigned unique identifier (UUID hex).
        idempotency_key: Caller-supplied key, unique across items; replaying
            the same key never creates a second item or side effect.
        goal: Non-empty natural-language goal for the agent run.
        status: Current lifecycle state.
        created_at / updated_at: ISO-8601 UTC timestamps.
        due_at: Optional ISO-8601 UTC time when the item becomes runnable.
        deadline_seconds: Optional total runtime budget for one attempt.
        attempts: Number of started runs; incremented on queued->running.
        result_summary: Optional human-readable completion summary.
        failure_category: Optional stable failure category (e.g. timeout).
        thread_id: Optional checkpointer thread associated with this item.
    """

    id: str
    idempotency_key: str
    goal: str
    status: WorkStatus
    created_at: str
    updated_at: str
    due_at: str | None = None
    deadline_seconds: float | None = None
    attempts: int = 0
    result_summary: str | None = None
    failure_category: str | None = None
    thread_id: str | None = None
