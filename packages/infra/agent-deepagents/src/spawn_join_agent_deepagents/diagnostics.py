"""Immutable assembly reports and redacted lifecycle event contracts."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.errors import GraphInterrupt
from langgraph.types import Command

from .errors import DelegationQueueFullError, DelegationTimeoutError
from .middleware import DIAGNOSTICS_MIDDLEWARE_NAME, MiddlewareScopeReport
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
class PermissionReport:
    """Counts of host-provided filesystem permission rules by effect."""

    allow: int = 0
    deny: int = 0
    interrupt: int = 0


@dataclass(frozen=True, slots=True)
class ResourceReport:
    """Safe presence/ownership summary for host-provided resources."""

    backend: str = "host"
    backend_kind: str = "default_state"
    store: str = "absent"
    checkpointer: str = "absent"
    interrupt_configured: bool = False
    thread_id_required: bool = False
    permissions: PermissionReport = field(default_factory=PermissionReport)


@dataclass(frozen=True, slots=True)
class ContextReport:
    """Safe summary of memory and skills sources; paths are not recorded."""

    memory_source_count: int = 0
    memory_cache_prefix: bool = True
    memory_managed_by: str = "absent"
    skills_source_count: int = 0
    skills_managed_by: str = "absent"


@dataclass(frozen=True, slots=True)
class ProfileReport:
    """Keys registered with the upstream beta profile registries."""

    harness_keys: tuple[str, ...] = ()
    provider_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "harness_keys", tuple(self.harness_keys))
        object.__setattr__(self, "provider_keys", tuple(self.provider_keys))


@dataclass(frozen=True, slots=True)
class RubricReport:
    """Safe description of the optional beta rubric middleware."""

    enabled: bool = False
    max_iterations: int = 0
    model_source: str = "none"
    tool_count: int = 0


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
    context: ContextReport = field(default_factory=ContextReport)
    profiles: ProfileReport = field(default_factory=ProfileReport)
    rubric: RubricReport = field(default_factory=RubricReport)
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


ToolResult = ToolMessage | Command[Any]


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Safe correlation fields extracted from one task tool request."""

    subagent_name: str
    tool_call_id: str | None
    run_id: str | None
    thread_id: str | None


def request_context(request: ToolCallRequest) -> RequestContext:
    """Extract only safe identifiers from a task tool request."""

    args = request.tool_call.get("args", {})
    subagent_name = str(args.get("subagent_type", ""))
    tool_call_id = request.tool_call.get("id")
    runtime = getattr(request, "runtime", None)
    execution_info = (
        getattr(runtime, "execution_info", None) if runtime is not None else None
    )
    run_id = (
        getattr(execution_info, "run_id", None) if execution_info is not None else None
    )
    thread_id = (
        getattr(execution_info, "thread_id", None)
        if execution_info is not None
        else None
    )
    return RequestContext(
        subagent_name=subagent_name,
        tool_call_id=str(tool_call_id) if tool_call_id is not None else None,
        run_id=str(run_id) if run_id is not None else None,
        thread_id=str(thread_id) if thread_id is not None else None,
    )


class DiagnosticEmitter:
    """Build redacted events and dispatch to the configured callbacks."""

    def __init__(
        self,
        config: DiagnosticsConfig,
        supervisor_name: str | None,
    ) -> None:
        self._config = config
        self._supervisor_name = supervisor_name

    def emit(
        self,
        event_type: DiagnosticEventType,
        *,
        context: RequestContext | None = None,
        outcome: str | None = None,
        error_category: str | None = None,
        detail: Mapping[str, str] | None = None,
    ) -> None:
        event = self._event(
            event_type,
            context=context,
            outcome=outcome,
            error_category=error_category,
            detail=detail,
        )
        if self._config.sync_callback is not None:
            self._config.sync_callback(event)

    async def aemit(
        self,
        event_type: DiagnosticEventType,
        *,
        context: RequestContext | None = None,
        outcome: str | None = None,
        error_category: str | None = None,
        detail: Mapping[str, str] | None = None,
    ) -> None:
        event = self._event(
            event_type,
            context=context,
            outcome=outcome,
            error_category=error_category,
            detail=detail,
        )
        if self._config.sync_callback is not None:
            self._config.sync_callback(event)
        if self._config.async_callback is not None:
            await self._config.async_callback(event)

    def _event(
        self,
        event_type: DiagnosticEventType,
        *,
        context: RequestContext | None,
        outcome: str | None,
        error_category: str | None,
        detail: Mapping[str, str] | None,
    ) -> DiagnosticEvent:
        return DiagnosticEvent(
            event_type=event_type,
            occurred_at=datetime.now(UTC),
            supervisor_name=self._supervisor_name,
            subagent_name=(context.subagent_name if context is not None else None),
            tool_call_id=(context.tool_call_id if context is not None else None),
            run_id=context.run_id if context is not None else None,
            thread_id=(
                context.thread_id
                if context is not None and self._config.include_thread_id
                else None
            ),
            outcome=outcome,
            error_category=error_category,
            detail=detail,
        )


class DelegationDiagnosticsMiddleware(AgentMiddleware[Any, Any, Any]):
    """Emit redacted lifecycle records around native task calls."""

    def __init__(self, emitter: DiagnosticEmitter) -> None:
        super().__init__()
        self._emitter = emitter

    @property
    def name(self) -> str:
        return DIAGNOSTICS_MIDDLEWARE_NAME

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolResult],
    ) -> ToolResult:
        if request.tool_call["name"] != "task":
            return handler(request)
        context = request_context(request)
        self._emitter.emit(
            DiagnosticEventType.DELEGATION_SELECTED,
            context=context,
        )
        try:
            result = handler(request)
        except GraphInterrupt:
            self._emitter.emit(
                DiagnosticEventType.DELEGATION_INTERRUPTED,
                context=context,
                outcome="interrupted",
                error_category="interrupted",
            )
            raise
        except Exception as exc:
            self._emitter.emit(
                DiagnosticEventType.DELEGATION_FAILED,
                context=context,
                outcome="failed",
                error_category=type(exc).__name__,
            )
            raise
        self._emitter.emit(
            DiagnosticEventType.DELEGATION_COMPLETED,
            context=context,
            outcome="completed",
        )
        return result

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolResult]],
    ) -> ToolResult:
        if request.tool_call["name"] != "task":
            return await handler(request)
        context = request_context(request)
        await self._emitter.aemit(
            DiagnosticEventType.DELEGATION_SELECTED,
            context=context,
        )
        try:
            result = await handler(request)
        except asyncio.CancelledError:
            await self._emitter.aemit(
                DiagnosticEventType.DELEGATION_CANCELLED,
                context=context,
                outcome="cancelled",
                error_category="cancelled",
            )
            raise
        except GraphInterrupt:
            await self._emitter.aemit(
                DiagnosticEventType.DELEGATION_INTERRUPTED,
                context=context,
                outcome="interrupted",
                error_category="interrupted",
            )
            raise
        except Exception as exc:
            if isinstance(exc, (DelegationQueueFullError, DelegationTimeoutError)):
                raise
            await self._emitter.aemit(
                DiagnosticEventType.DELEGATION_FAILED,
                context=context,
                outcome="failed",
                error_category=type(exc).__name__,
            )
            raise
        await self._emitter.aemit(
            DiagnosticEventType.DELEGATION_COMPLETED,
            context=context,
            outcome="completed",
        )
        return result
