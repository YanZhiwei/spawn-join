"""Immutable assembly reports and redacted lifecycle event contracts."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType

from .middleware import MiddlewareScopeReport
from .models import ModelPurpose
from .subagents import SubAgentKind, SubAgentMode


class DiagnosticEventType(StrEnum):
    """Stable lifecycle states emitted around governed delegation."""

    DELEGATION_SELECTED = "delegation.selected"
    DELEGATION_QUEUED = "delegation.queued"
    DELEGATION_STARTED = "delegation.started"
    DELEGATION_COMPLETED = "delegation.completed"
    DELEGATION_FAILED = "delegation.failed"
    DELEGATION_TIMED_OUT = "delegation.timed_out"
    DELEGATION_CANCELLED = "delegation.cancelled"
    DELEGATION_INTERRUPTED = "delegation.interrupted"
    DELEGATION_REJECTED = "delegation.rejected"


@dataclass(frozen=True, slots=True)
class DiagnosticEvent:
    """A redacted lifecycle record with safe correlation fields."""

    event_type: DiagnosticEventType
    occurred_at: datetime
    supervisor_name: str | None = None
    subagent_name: str | None = None
    tool_call_id: str | None = None
    run_id: str | None = None
    thread_id: str | None = None
    outcome: str | None = None
    error_category: str | None = None
    detail: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if self.detail is not None:
            object.__setattr__(
                self,
                "detail",
                MappingProxyType(dict(self.detail)),
            )


DiagnosticCallback = Callable[[DiagnosticEvent], None]
AsyncDiagnosticCallback = Callable[[DiagnosticEvent], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class DiagnosticsConfig:
    """Optional callbacks for lifecycle records; the host owns transport."""

    sync_callback: DiagnosticCallback | None = None
    async_callback: AsyncDiagnosticCallback | None = None
    include_thread_id: bool = False


@dataclass(frozen=True, slots=True)
class SubagentReport:
    """Safe description of one registered subagent."""

    name: str
    kind: SubAgentKind
    mode: SubAgentMode
    model_source: str
    middleware_names: tuple[str, ...] = ()
    availability: str = "available"
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "middleware_names", tuple(self.middleware_names))
        object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True, slots=True)
class DelegationReport:
    """Safe description of the configured delegation policy."""

    max_concurrency: int
    max_queue: int
    deadline_seconds: float | None = None
    controller_reused: bool = False
    execution_mode: str = "native"
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "warnings", tuple(self.warnings))


@dataclass(frozen=True, slots=True)
class ResourceReport:
    """Safe presence/ownership summary for host-provided resources."""

    backend: str = "host"
    store: str = "absent"
    checkpointer: str = "absent"
    interrupt_configured: bool = False
    thread_id_required: bool = False


def _empty_middleware_report() -> MiddlewareScopeReport:
    return MiddlewareScopeReport(
        supervisor_names=(),
        worker_names=(),
        per_subagent={},
    )


def _empty_models() -> Mapping[ModelPurpose, str]:
    return {}


@dataclass(frozen=True, slots=True)
class AssemblyReport:
    """Immutable, loggable summary of one supervisor assembly."""

    package_version: str
    deepagents_version: str
    supervisor_name: str | None = None
    models: Mapping[ModelPurpose, str] = field(default_factory=_empty_models)
    subagents: tuple[SubagentReport, ...] = ()
    middleware: MiddlewareScopeReport = field(default_factory=_empty_middleware_report)
    delegation: DelegationReport | None = None
    resources: ResourceReport = field(default_factory=ResourceReport)
    warnings: tuple[str, ...] = ()
    experimental_features: tuple[str, ...] = ()
    diagnostics_enabled: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "models",
            MappingProxyType(dict(self.models)),
        )
        object.__setattr__(self, "subagents", tuple(self.subagents))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(
            self,
            "experimental_features",
            tuple(self.experimental_features),
        )
