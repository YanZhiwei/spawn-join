"""Validated value objects for the work runtime."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import cast

from .errors import WorkConfigurationError


class WorkState(StrEnum):
    """Durable task lifecycle states."""

    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD = "dead"
    CANCELLED = "cancelled"


class WorkOutcome(StrEnum):
    """Executor result classification."""

    SUCCESS = "success"
    RETRY = "retry"
    FAIL = "fail"
    DEFER = "defer"


def _require_aware(label: str, value: datetime) -> None:
    raw = cast(object, value)
    if not isinstance(raw, datetime):
        raise WorkConfigurationError(f"{label}: must be a datetime")
    if raw.tzinfo is None or raw.utcoffset() is None:
        raise WorkConfigurationError(f"{label}: must be timezone-aware")


def _require_non_empty(label: str, value: str) -> None:
    raw = cast(object, value)
    if not isinstance(raw, str) or not raw.strip():
        raise WorkConfigurationError(f"{label}: must be a non-empty string")


@dataclass(frozen=True, slots=True)
class WorkSpec:
    """Host-supplied, immutable work definition."""

    kind: str
    payload: bytes
    idempotency_key: str
    queue: str = "default"
    namespace: str = "default"
    priority: int = 0
    available_at: datetime | None = None
    deadline_seconds: float | None = None
    max_attempts: int = 3

    def __post_init__(self) -> None:
        _require_non_empty("kind", self.kind)
        _require_non_empty("idempotency_key", self.idempotency_key)
        _require_non_empty("queue", self.queue)
        _require_non_empty("namespace", self.namespace)
        payload = cast(object, self.payload)
        if not isinstance(payload, bytes):
            raise WorkConfigurationError("payload: must be bytes")
        priority = cast(object, self.priority)
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise WorkConfigurationError("priority: must be an int")
        if self.priority < 0:
            raise WorkConfigurationError("priority: must be >= 0")
        attempts = cast(object, self.max_attempts)
        if not isinstance(attempts, int) or isinstance(attempts, bool):
            raise WorkConfigurationError("max_attempts: must be an int")
        if self.max_attempts < 1:
            raise WorkConfigurationError("max_attempts: must be >= 1")
        if self.deadline_seconds is not None:
            deadline = cast(object, self.deadline_seconds)
            if not isinstance(deadline, (int, float)) or isinstance(deadline, bool):
                raise WorkConfigurationError(
                    "deadline_seconds: must be a number or None"
                )
            if self.deadline_seconds <= 0:
                raise WorkConfigurationError("deadline_seconds: must be > 0")
        if self.available_at is not None:
            _require_aware("available_at", self.available_at)


@dataclass(frozen=True, slots=True)
class WorkLease:
    """One execution ownership window."""

    owner: str
    token: str
    until: datetime

    def __post_init__(self) -> None:
        _require_non_empty("lease.owner", self.owner)
        _require_non_empty("lease.token", self.token)
        _require_aware("lease.until", self.until)


def _require_work_item_refs(
    spec: WorkSpec,
    state: WorkState,
    lease: WorkLease | None,
    last_error: str | None,
    result: str | None,
) -> None:
    spec_raw = cast(object, spec)
    if not isinstance(spec_raw, WorkSpec):
        raise WorkConfigurationError("spec: must be WorkSpec")
    state_raw = cast(object, state)
    if not isinstance(state_raw, WorkState):
        raise WorkConfigurationError("state: must be WorkState")
    if lease is not None:
        lease_raw = cast(object, lease)
        if not isinstance(lease_raw, WorkLease):
            raise WorkConfigurationError("lease: must be WorkLease or None")
    if last_error is not None:
        error_raw = cast(object, last_error)
        if not isinstance(error_raw, str):
            raise WorkConfigurationError("last_error: must be a string or None")
    if result is not None:
        result_raw = cast(object, result)
        if not isinstance(result_raw, str):
            raise WorkConfigurationError("result: must be a string or None")


def _require_attempts(attempts: int) -> None:
    attempts_raw = cast(object, attempts)
    if not isinstance(attempts_raw, int) or isinstance(attempts_raw, bool):
        raise WorkConfigurationError("attempts: must be an int")
    if attempts < 0:
        raise WorkConfigurationError("attempts: must be >= 0")


@dataclass(frozen=True, slots=True)
class WorkItem:
    """Persisted work item handed to an executor."""

    id: str
    spec: WorkSpec
    state: WorkState
    attempts: int
    lease: WorkLease | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
    result: str | None = None
    completed_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_non_empty("id", self.id)
        _require_work_item_refs(
            self.spec, self.state, self.lease, self.last_error, self.result
        )
        _require_attempts(self.attempts)
        _require_aware("created_at", self.created_at)
        _require_aware("updated_at", self.updated_at)
        if self.completed_at is not None:
            _require_aware("completed_at", self.completed_at)


@dataclass(frozen=True, slots=True)
class WorkResult:
    """Executor result; the runner maps it to a state transition."""

    outcome: WorkOutcome
    summary: str | None = None
    error: str | None = None
    wait_until: datetime | None = None

    def __post_init__(self) -> None:
        outcome = cast(object, self.outcome)
        if not isinstance(outcome, WorkOutcome):
            raise WorkConfigurationError("outcome: must be WorkOutcome")
        if self.outcome in {WorkOutcome.RETRY, WorkOutcome.FAIL}:
            _require_non_empty("error", self.error or "")
        if self.outcome is WorkOutcome.DEFER:
            if self.wait_until is None:
                raise WorkConfigurationError("wait_until: required for defer")
            _require_aware("wait_until", self.wait_until)


@dataclass(frozen=True, slots=True)
class WorkEvent:
    """Best-effort wake-up signal; never carries the business payload."""

    work_id: str
    queue: str
    namespace: str
    type: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        _require_non_empty("work_id", self.work_id)
        _require_non_empty("queue", self.queue)
        _require_non_empty("namespace", self.namespace)
        _require_non_empty("type", self.type)
        _require_aware("occurred_at", self.occurred_at)
