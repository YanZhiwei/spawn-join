"""Contracts for assembly reports and lifecycle diagnostics."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from types import MappingProxyType
from typing import Any, cast

import pytest
from spawn_join_agent_deepagents.diagnostics import (
    AssemblyReport,
    DelegationReport,
    DiagnosticEvent,
    DiagnosticEventType,
    DiagnosticsConfig,
    ResourceReport,
    SubagentReport,
)
from spawn_join_agent_deepagents.middleware import MiddlewareScopeReport
from spawn_join_agent_deepagents.models import ModelPurpose
from spawn_join_agent_deepagents.subagents import SubAgentKind, SubAgentMode


def test_event_type_values_are_stable() -> None:
    expected = {
        "delegation.selected",
        "delegation.queued",
        "delegation.started",
        "delegation.completed",
        "delegation.failed",
        "delegation.timed_out",
        "delegation.cancelled",
        "delegation.interrupted",
        "delegation.rejected",
    }

    assert {item.value for item in DiagnosticEventType} == expected


def test_event_is_frozen_and_detail_is_read_only() -> None:
    event = DiagnosticEvent(
        event_type=DiagnosticEventType.DELEGATION_STARTED,
        occurred_at=datetime.now(UTC),
        detail={"phase": "start"},
    )

    assert isinstance(event.detail, MappingProxyType)
    mutable = cast(dict[str, str], event.detail)
    with pytest.raises(TypeError):
        mutable["phase"] = "changed"

    with pytest.raises(FrozenInstanceError):
        cast(Any, event).outcome = "changed"


def test_assembly_report_is_safe_and_immutable() -> None:
    report = AssemblyReport(
        package_version="0.1.0",
        deepagents_version="0.7.32",
        supervisor_name="coordinator",
        models={ModelPurpose.SUPERVISOR: "injected:BaseChatModel"},
        subagents=(
            SubagentReport(
                name="researcher",
                kind=SubAgentKind.DECLARATIVE,
                mode=SubAgentMode.ISOLATED,
                model_source="catalog:worker",
                middleware_names=("audit",),
            ),
        ),
        middleware=MiddlewareScopeReport(
            supervisor_names=("audit",),
            worker_names=(),
            per_subagent={"researcher": ("audit",)},
        ),
        delegation=DelegationReport(
            max_concurrency=2,
            max_queue=1,
            deadline_seconds=5.0,
            controller_reused=True,
            execution_mode="async",
        ),
        resources=ResourceReport(
            backend="default_state",
            store="host",
            checkpointer="host",
            interrupt_configured=True,
            thread_id_required=True,
        ),
        warnings=("async-only",),
        experimental_features=("forked_subagents",),
        diagnostics_enabled=True,
    )

    assert isinstance(report.models, MappingProxyType)
    assert isinstance(report.middleware.per_subagent, MappingProxyType)
    assert report.subagents[0].middleware_names == ("audit",)
    assert report.warnings == ("async-only",)
    assert "sk-" not in repr(report)

    with pytest.raises(FrozenInstanceError):
        cast(Any, report).supervisor_name = "changed"


def test_diagnostics_config_accepts_sync_and_async_callbacks() -> None:
    events: list[DiagnosticEvent] = []

    def sync_callback(event: DiagnosticEvent) -> None:
        events.append(event)

    async def async_callback(event: DiagnosticEvent) -> None:
        events.append(event)

    config = DiagnosticsConfig(
        sync_callback=sync_callback,
        async_callback=async_callback,
        include_thread_id=True,
    )

    assert config.sync_callback is sync_callback
    assert config.async_callback is async_callback
    assert config.include_thread_id is True


def test_resource_report_defaults_are_explicit() -> None:
    report = ResourceReport()

    assert report.backend == "host"
    assert report.store == "absent"
    assert report.checkpointer == "absent"
    assert report.interrupt_configured is False
    assert report.thread_id_required is False


def test_event_defaults_have_no_sensitive_correlation() -> None:
    event = DiagnosticEvent(
        event_type=DiagnosticEventType.DELEGATION_COMPLETED,
        occurred_at=datetime.now(UTC),
    )

    assert event.thread_id is None
    assert event.run_id is None
    assert event.detail is None
