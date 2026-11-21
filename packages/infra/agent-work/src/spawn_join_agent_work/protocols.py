"""Port contracts for the durable work runtime.

Implementations live in ``stores``/``notify`` (and host applications); these
protocols are the only shapes shared between the runtime and its adapters.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from datetime import datetime
from typing import Protocol

from .models import WorkEvent, WorkItem, WorkResult, WorkSpec


class Clock(Protocol):
    """Source of the current time; hosts inject a fake in tests."""

    def now(self) -> datetime: ...


class Notifier(Protocol):
    """Best-effort wake-up transport; the store remains the source of truth."""

    async def publish(self, event: WorkEvent) -> None: ...

    def subscribe(self, queues: Sequence[str]) -> AsyncIterator[WorkEvent]: ...

    async def aclose(self) -> None: ...


class WorkStore(Protocol):
    """Durable work storage with atomic claim and lease fencing."""

    async def enqueue(self, spec: WorkSpec) -> WorkItem: ...

    async def claim(
        self,
        *,
        owner: str,
        queues: Sequence[str],
        namespace: str,
        limit: int,
        lease_seconds: float,
        now: datetime,
    ) -> list[WorkItem]: ...

    async def heartbeat(
        self, *, work_id: str, token: str, lease_until: datetime
    ) -> bool: ...

    async def complete(
        self, *, work_id: str, token: str, summary: str | None
    ) -> bool: ...

    async def fail(
        self,
        *,
        work_id: str,
        token: str,
        error: str,
        retry_at: datetime | None,
        terminal: bool,
    ) -> bool: ...

    async def defer(self, *, work_id: str, token: str, until: datetime) -> bool: ...

    async def resume(self, work_id: str) -> bool: ...

    async def cancel(self, work_id: str) -> bool: ...

    async def get(self, work_id: str) -> WorkItem | None: ...

    async def prune(self, *, before: datetime) -> int: ...


class WorkExecutor(Protocol):
    """Host-provided callable that executes one claimed item."""

    async def __call__(self, item: WorkItem) -> WorkResult: ...
