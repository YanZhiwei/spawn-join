"""In-memory work store used for contract tests and embedders.

It mirrors the SQLite adapter's observable contract without touching the
filesystem, so the shared contract suite in T008 can prove both implementations.
"""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from uuid import uuid4

from ..errors import StoreError, WorkConfigurationError, WorkConflictError
from ..models import WorkItem, WorkLease, WorkSpec, WorkState
from ..protocols import Clock
from ._support import SystemClock, require_aware, require_positive_seconds


@dataclass(slots=True)
class _Record:
    id: str
    spec: WorkSpec
    state: WorkState
    attempts: int
    available_at: datetime
    owner: str | None
    token: str | None
    until: datetime | None
    last_error: str | None
    result: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class InMemoryWorkStore:
    """Process-local store with the same semantics as the SQLite adapter."""

    def __init__(self, *, clock: Clock | None = None) -> None:
        self._clock: Clock = clock or SystemClock()
        self._records: dict[str, _Record] = {}
        self._idempotency: dict[str, str] = {}
        self._lock = asyncio.Lock()

    def _now(self) -> datetime:
        now = self._clock.now()
        require_aware("clock.now()", now)
        return now

    def _expire(self, now: datetime) -> None:
        for record in self._records.values():
            if (
                record.state is WorkState.RUNNING
                and record.until is not None
                and record.until <= now
            ):
                record.owner = None
                record.token = None
                record.until = None
                record.updated_at = now
                if record.attempts >= record.spec.max_attempts:
                    record.state = WorkState.DEAD
                    record.completed_at = now
                    record.last_error = record.last_error or "lease expired"
                else:
                    record.state = WorkState.QUEUED
                    record.available_at = now

    @staticmethod
    def _to_item(record: _Record) -> WorkItem:
        lease: WorkLease | None = None
        if record.owner is not None and record.token is not None:
            if record.until is None:
                raise StoreError("stored lease is missing its expiry")
            lease = WorkLease(
                owner=record.owner, token=record.token, until=record.until
            )
        return WorkItem(
            id=record.id,
            spec=replace(record.spec, available_at=record.available_at),
            state=record.state,
            attempts=record.attempts,
            lease=lease,
            last_error=record.last_error,
            created_at=record.created_at,
            updated_at=record.updated_at,
            result=record.result,
            completed_at=record.completed_at,
        )

    async def enqueue(self, spec: WorkSpec) -> WorkItem:
        async with self._lock:
            if spec.idempotency_key in self._idempotency:
                raise WorkConflictError(
                    f"idempotency key already exists: {spec.idempotency_key}"
                )
            now = self._now()
            work_id = uuid4().hex
            record = _Record(
                id=work_id,
                spec=spec,
                state=WorkState.QUEUED,
                attempts=0,
                available_at=spec.available_at or now,
                owner=None,
                token=None,
                until=None,
                last_error=None,
                result=None,
                created_at=now,
                updated_at=now,
                completed_at=None,
            )
            self._records[work_id] = record
            self._idempotency[spec.idempotency_key] = work_id
            return self._to_item(record)

    async def claim(
        self,
        *,
        owner: str,
        queues: Sequence[str],
        namespace: str,
        limit: int,
        lease_seconds: float,
        now: datetime,
    ) -> list[WorkItem]:
        if not owner.strip():
            raise WorkConfigurationError("owner: must be non-empty")
        if not namespace.strip():
            raise WorkConfigurationError("namespace: must be non-empty")
        if limit < 1:
            raise WorkConfigurationError("limit: must be >= 1")
        require_positive_seconds("lease_seconds", lease_seconds)
        require_aware("now", now)
        selected_queues = set(queue for queue in queues if queue)
        if not selected_queues:
            return []

        async with self._lock:
            self._expire(now)
            candidates = [
                record
                for record in self._records.values()
                if record.state is WorkState.QUEUED
                and record.spec.queue in selected_queues
                and record.spec.namespace == namespace
                and record.available_at <= now
            ]
            candidates.sort(
                key=lambda record: (
                    -record.spec.priority,
                    record.created_at,
                    record.id,
                )
            )
            selected = candidates[:limit]
            if not selected:
                return []
            token = secrets.token_hex(16)
            until = now + timedelta(seconds=lease_seconds)
            for record in selected:
                record.state = WorkState.RUNNING
                record.attempts += 1
                record.owner = owner
                record.token = token
                record.until = until
                record.updated_at = now
            return [self._to_item(record) for record in selected]

    async def heartbeat(
        self, *, work_id: str, token: str, lease_until: datetime
    ) -> bool:
        require_aware("lease_until", lease_until)
        if lease_until <= self._now():
            raise WorkConfigurationError("lease_until: must be in the future")
        async with self._lock:
            record = self._records.get(work_id)
            if (
                record is None
                or record.state is not WorkState.RUNNING
                or record.token != token
                or record.until is None
                or lease_until <= record.until
            ):
                return False
            record.until = lease_until
            record.updated_at = self._now()
            return True

    async def complete(self, *, work_id: str, token: str, summary: str | None) -> bool:
        async with self._lock:
            record = self._records.get(work_id)
            if (
                record is None
                or record.state is not WorkState.RUNNING
                or record.token != token
            ):
                return False
            now = self._now()
            record.state = WorkState.COMPLETED
            record.result = summary
            record.completed_at = now
            record.updated_at = now
            record.owner = None
            record.token = None
            record.until = None
            return True

    async def fail(
        self,
        *,
        work_id: str,
        token: str,
        error: str,
        retry_at: datetime | None,
        terminal: bool,
    ) -> bool:
        if not error.strip():
            raise WorkConfigurationError("error: must be non-empty")
        if terminal and retry_at is not None:
            raise WorkConfigurationError(
                "retry_at: must be None for a terminal failure"
            )
        if not terminal and retry_at is None:
            raise WorkConfigurationError("retry_at: required for a retryable failure")
        if retry_at is not None:
            require_aware("retry_at", retry_at)

        async with self._lock:
            record = self._records.get(work_id)
            if (
                record is None
                or record.state is not WorkState.RUNNING
                or record.token != token
            ):
                return False
            now = self._now()
            exhausted = record.attempts >= record.spec.max_attempts
            if terminal or exhausted:
                record.state = WorkState.DEAD if exhausted else WorkState.FAILED
                record.completed_at = now
            else:
                record.state = WorkState.QUEUED
                record.available_at = retry_at or now
            record.last_error = error
            record.updated_at = now
            record.owner = None
            record.token = None
            record.until = None
            return True

    async def defer(self, *, work_id: str, token: str, until: datetime) -> bool:
        require_aware("until", until)
        if until <= self._now():
            raise WorkConfigurationError("until: must be in the future")
        async with self._lock:
            record = self._records.get(work_id)
            if (
                record is None
                or record.state is not WorkState.RUNNING
                or record.token != token
            ):
                return False
            now = self._now()
            record.state = WorkState.WAITING
            record.available_at = until
            record.updated_at = now
            record.owner = None
            record.token = None
            record.until = None
            return True

    async def resume(self, work_id: str) -> bool:
        async with self._lock:
            record = self._records.get(work_id)
            if record is None or record.state is not WorkState.WAITING:
                return False
            now = self._now()
            record.state = WorkState.QUEUED
            record.available_at = now
            record.updated_at = now
            return True

    async def cancel(self, work_id: str) -> bool:
        async with self._lock:
            record = self._records.get(work_id)
            if record is None or record.state in {
                WorkState.COMPLETED,
                WorkState.FAILED,
                WorkState.DEAD,
                WorkState.CANCELLED,
            }:
                return False
            now = self._now()
            record.state = WorkState.CANCELLED
            record.completed_at = now
            record.updated_at = now
            record.owner = None
            record.token = None
            record.until = None
            return True

    async def get(self, work_id: str) -> WorkItem | None:
        async with self._lock:
            record = self._records.get(work_id)
            return None if record is None else self._to_item(record)

    async def prune(self, *, before: datetime) -> int:
        require_aware("before", before)
        if before >= self._now():
            raise WorkConfigurationError("before: must be in the past")
        async with self._lock:
            terminal = {
                WorkState.COMPLETED,
                WorkState.FAILED,
                WorkState.DEAD,
                WorkState.CANCELLED,
            }
            doomed = [
                work_id
                for work_id, record in self._records.items()
                if record.state in terminal
                and record.completed_at is not None
                and record.completed_at < before
            ]
            for work_id in doomed:
                spec = self._records.pop(work_id).spec
                self._idempotency.pop(spec.idempotency_key, None)
            return len(doomed)
