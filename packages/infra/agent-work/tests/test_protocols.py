"""Port conformance skeleton for spawn-join-agent-work.

The stub store exists only to lock the ``WorkStore`` signatures at type-check
time; real implementations arrive with the store tasks, and the behavioural
contract suite lives in ``test_contract_store.py``.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence
from datetime import UTC, datetime

from spawn_join_agent_work import (
    Clock,
    Notifier,
    WorkEvent,
    WorkExecutor,
    WorkItem,
    WorkOutcome,
    WorkResult,
    WorkSpec,
    WorkState,
    WorkStore,
)


class FakeClock(Clock):
    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now


class FakeNotifier(Notifier):
    def __init__(self) -> None:
        self.published: list[WorkEvent] = []
        self.closed = False

    async def publish(self, event: WorkEvent) -> None:
        self.published.append(event)

    async def subscribe(self, queues: Sequence[str]) -> AsyncIterator[WorkEvent]:
        for event in self.published:
            if event.queue in queues:
                yield event

    async def aclose(self) -> None:
        self.closed = True


class StubStore(WorkStore):
    """Signature-only stub; no behaviour is claimed before T005/T007."""

    async def enqueue(self, spec: WorkSpec) -> WorkItem:
        raise NotImplementedError

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
        raise NotImplementedError

    async def heartbeat(
        self, *, work_id: str, token: str, lease_until: datetime
    ) -> bool:
        raise NotImplementedError

    async def complete(self, *, work_id: str, token: str, summary: str | None) -> bool:
        raise NotImplementedError

    async def fail(
        self,
        *,
        work_id: str,
        token: str,
        error: str,
        retry_at: datetime | None,
        terminal: bool,
    ) -> bool:
        raise NotImplementedError

    async def defer(self, *, work_id: str, token: str, until: datetime) -> bool:
        raise NotImplementedError

    async def resume(self, work_id: str) -> bool:
        raise NotImplementedError

    async def cancel(self, work_id: str) -> bool:
        raise NotImplementedError

    async def get(self, work_id: str) -> WorkItem | None:
        raise NotImplementedError

    async def prune(self, *, before: datetime) -> int:
        raise NotImplementedError


def test_clock_and_notifier_satisfy_ports() -> None:
    now = datetime(2026, 11, 22, tzinfo=UTC)
    clock: Clock = FakeClock(now)
    notifier: Notifier = FakeNotifier()
    assert clock.now() == now
    assert notifier is not None


def test_store_stub_satisfies_port_signature() -> None:
    store: WorkStore = StubStore()
    assert store is not None


def test_executor_port_is_callable() -> None:
    async def executor(item: WorkItem) -> WorkResult:
        return WorkResult(outcome=WorkOutcome.SUCCESS, summary=item.id)

    port: WorkExecutor = executor
    moment = datetime(2026, 11, 22, tzinfo=UTC)
    item = WorkItem(
        id="w1",
        spec=WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"),
        state=WorkState.QUEUED,
        attempts=0,
        lease=None,
        last_error=None,
        created_at=moment,
        updated_at=moment,
    )
    result = asyncio.run(port(item))
    assert result.outcome is WorkOutcome.SUCCESS
    assert result.summary == "w1"
