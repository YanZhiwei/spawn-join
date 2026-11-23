"""Model validation tests for spawn-join-agent-work."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from spawn_join_agent_work import (
    WorkConfigurationError,
    WorkEvent,
    WorkItem,
    WorkLease,
    WorkOutcome,
    WorkResult,
    WorkSpec,
    WorkState,
)


def _now() -> datetime:
    return datetime(2026, 11, 22, tzinfo=UTC)


def test_spec_defaults_and_validation() -> None:
    spec = WorkSpec(kind="report", payload=b"{}", idempotency_key="k1")
    assert spec.queue == "default"
    assert spec.max_attempts == 3

    with pytest.raises(WorkConfigurationError):
        WorkSpec(kind="", payload=b"{}", idempotency_key="k1")
    with pytest.raises(WorkConfigurationError):
        WorkSpec(kind="report", payload="not-bytes", idempotency_key="k1")  # type: ignore[arg-type]
    with pytest.raises(WorkConfigurationError):
        WorkSpec(
            kind="report",
            payload=b"{}",
            idempotency_key="k1",
            available_at=datetime(2026, 11, 22),
        )


def test_lease_and_item_validation() -> None:
    spec = WorkSpec(kind="report", payload=b"{}", idempotency_key="k1")
    lease = WorkLease(owner="worker-1", token="t1", until=_now())
    item = WorkItem(
        id="w1",
        spec=spec,
        state=WorkState.RUNNING,
        attempts=1,
        lease=lease,
        last_error=None,
        created_at=_now(),
        updated_at=_now(),
    )
    assert item.lease is lease

    with pytest.raises(WorkConfigurationError):
        WorkItem(
            id="",
            spec=spec,
            state=WorkState.QUEUED,
            attempts=0,
            lease=None,
            last_error=None,
            created_at=_now(),
            updated_at=_now(),
        )


def test_result_outcome_requirements() -> None:
    assert WorkResult(outcome=WorkOutcome.SUCCESS).outcome is WorkOutcome.SUCCESS
    with pytest.raises(WorkConfigurationError):
        WorkResult(outcome=WorkOutcome.RETRY)
    with pytest.raises(WorkConfigurationError):
        WorkResult(outcome=WorkOutcome.DEFER)
    deferred = WorkResult(outcome=WorkOutcome.DEFER, wait_until=_now())
    assert deferred.wait_until == _now()


def test_spec_boundaries() -> None:
    for kwargs in (
        {"priority": -1},
        {"max_attempts": 0},
        {"deadline_seconds": 0},
        {"queue": ""},
        {"namespace": " "},
    ):
        with pytest.raises(WorkConfigurationError):
            WorkSpec(kind="report", payload=b"{}", idempotency_key="k1", **kwargs)  # type: ignore[arg-type]
    with pytest.raises(WorkConfigurationError):
        WorkSpec(kind="report", payload=b"{}", idempotency_key="")


def test_item_extra_validation() -> None:
    spec = WorkSpec(kind="report", payload=b"{}", idempotency_key="k1")
    with pytest.raises(WorkConfigurationError):
        WorkItem(
            id="w1",
            spec=spec,
            state=WorkState.QUEUED,
            attempts=-1,
            lease=None,
            last_error=None,
            created_at=_now(),
            updated_at=_now(),
        )
    with pytest.raises(WorkConfigurationError):
        WorkItem(
            id="w1",
            spec=spec,
            state=WorkState.QUEUED,
            attempts=0,
            lease="bad",  # type: ignore[arg-type]
            last_error=None,
            created_at=_now(),
            updated_at=_now(),
        )


def test_event_validation() -> None:
    event = WorkEvent(
        work_id="w1",
        queue="default",
        namespace="default",
        type="claimed",
        occurred_at=_now(),
    )
    assert event.type == "claimed"
    with pytest.raises(WorkConfigurationError):
        WorkEvent(
            work_id="",
            queue="default",
            namespace="default",
            type="claimed",
            occurred_at=_now(),
        )
