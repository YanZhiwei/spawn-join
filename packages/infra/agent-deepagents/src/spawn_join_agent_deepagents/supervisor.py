"""Native supervisor assembly from explicit product contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from importlib.metadata import version
from types import MappingProxyType
from typing import Any, cast

import deepagents
from deepagents import DeepAgentState
from deepagents.backends import StateBackend
from deepagents.backends.protocol import BackendProtocol
from deepagents.middleware.filesystem import FilesystemPermission
from deepagents.middleware.subagents import (
    GENERAL_PURPOSE_SUBAGENT,
    CompiledSubAgent,
    SubAgent,
)
from deepagents.middleware.summarization import create_summarization_middleware
from langchain.agents.middleware import InterruptOnConfig
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.messages import SystemMessage
from langgraph.cache.base import BaseCache
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.store.base import BaseStore

from .diagnostics import (
    AssemblyReport,
    DelegationDiagnosticsMiddleware,
    DelegationReport,
    DiagnosticEmitter,
    DiagnosticsConfig,
    ResourceReport,
    SubagentReport,
)
from .errors import AgentConfigurationError, ModelBindingError
from .execution import (
    DelegationConfiguration,
    DelegationController,
    DelegationPolicyMiddleware,
)
from .middleware import MiddlewareConfiguration, MiddlewareScopeReport
from .models import (
    ModelBindings,
    ModelPurpose,
    ResolvedModelBindings,
)
from .recovery import (
    checkpointer_present,
    validate_checkpointer_value,
    validate_interrupt_checkpointer,
)
from .subagents import (
    DEFAULT_GENERAL_PURPOSE_NAME,
    CompiledSubAgentDefinition,
    ResponseFormatLike,
    SubAgentDefinition,
    SubAgentDefinitionLike,
    SubAgentKind,
    SubAgentMode,
    ToolLike,
    validate_experimental_fork,
    validate_unique_subagent_names,
)

MiddlewareType = AgentMiddleware[Any, Any, Any]
CheckpointerType = BaseCheckpointSaver[Any] | bool | None

# The upstream signature is partially typed; isolate that boundary here.
_create_deep_agent: Any = cast(
    Any,
    deepagents.create_deep_agent,  # pyright: ignore[reportUnknownMemberType]
)


@dataclass(frozen=True, slots=True)
class SupervisorSpec:
    """Validated inputs for one supervisor graph construction."""

    models: ModelBindings
    tools: Sequence[ToolLike] = ()
    system_prompt: str | SystemMessage | None = None
    subagents: Sequence[SubAgentDefinitionLike] = ()
    control_default_subagent: bool = True
    middleware: MiddlewareConfiguration = field(default_factory=MiddlewareConfiguration)
    delegation: DelegationConfiguration | None = None
    diagnostics: DiagnosticsConfig | None = None
    allow_experimental_fork: bool = False
    backend: BackendProtocol | None = None
    store: BaseStore | None = None
    checkpointer: CheckpointerType = None
    interrupt_on: Mapping[str, bool | InterruptOnConfig] | None = None
    state_schema: type[DeepAgentState] | None = None
    context_schema: type[Any] | None = None
    response_format: ResponseFormatLike | None = None
    permissions: Sequence[FilesystemPermission] | None = None
    skills: Sequence[str] | None = None
    memory: Sequence[str] | None = None
    cache: BaseCache[Any] | None = None
    name: str | None = None
    debug: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "tools", tuple(self.tools))
        object.__setattr__(self, "subagents", tuple(self.subagents))
        if self.interrupt_on is not None:
            object.__setattr__(
                self,
                "interrupt_on",
                MappingProxyType(dict(self.interrupt_on)),
            )
        if self.permissions is not None:
            object.__setattr__(self, "permissions", tuple(self.permissions))
        if self.skills is not None:
            object.__setattr__(self, "skills", tuple(self.skills))
        if self.memory is not None:
            object.__setattr__(self, "memory", tuple(self.memory))


@dataclass(frozen=True, slots=True)
class SupervisorAssembly:
    """The native graph, its safe report, and the reusable execution seam."""

    graph: Any
    report: AssemblyReport
    delegation_controller: DelegationController | None = None


def build_supervisor(spec: SupervisorSpec) -> SupervisorAssembly:
    """Validate the spec and assemble exactly one native supervisor graph."""

    _validate_subagents(spec)
    worker_requirement = spec.models.require_worker
    if worker_requirement is None:
        worker_requirement = _worker_required(spec)
    resolved = spec.models.resolve(require_worker=worker_requirement)

    backend = spec.backend if spec.backend is not None else StateBackend()
    summary = _summary_middleware(resolved, backend)
    controller = _delegation_controller(spec)
    supervisor_middleware = _supervisor_middleware(spec, summary, controller)
    native_subagents, subagent_reports, per_subagent = _native_subagents(
        spec,
        resolved,
        summary,
    )
    graph = _create_graph(
        spec,
        resolved,
        backend,
        supervisor_middleware,
        native_subagents,
    )
    report = _build_report(
        spec,
        resolved,
        subagent_reports,
        per_subagent,
        supervisor_middleware,
        summary,
    )
    return SupervisorAssembly(
        graph=graph,
        report=report,
        delegation_controller=controller,
    )


def _validate_subagents(spec: SupervisorSpec) -> None:
    validate_unique_subagent_names(spec.subagents)
    validate_experimental_fork(
        spec.subagents,
        allow_experimental_fork=spec.allow_experimental_fork,
    )
    declarative_names = {
        definition.name
        for definition in spec.subagents
        if isinstance(definition, SubAgentDefinition)
    }
    if _uses_controlled_general_purpose(spec):
        declarative_names.add(DEFAULT_GENERAL_PURPOSE_NAME)
    compiled_names = {
        definition.name
        for definition in spec.subagents
        if isinstance(definition, CompiledSubAgentDefinition)
    }
    spec.middleware.validate_for_subagents(
        declarative_names=declarative_names,
        compiled_names=compiled_names,
    )
    validate_checkpointer_value(spec.checkpointer)
    validate_interrupt_checkpointer(
        spec.checkpointer,
        _interrupt_configured(spec),
    )


def _has_permission_interrupt(
    permissions: Sequence[FilesystemPermission] | None,
) -> bool:
    return permissions is not None and any(
        permission.mode == "interrupt" for permission in permissions
    )


def _interrupt_configured(spec: SupervisorSpec) -> bool:
    if spec.interrupt_on:
        return True
    if _has_permission_interrupt(spec.permissions):
        return True
    for definition in spec.subagents:
        if not isinstance(definition, SubAgentDefinition):
            continue
        if definition.interrupt_on:
            return True
        effective_permissions = (
            definition.permissions
            if definition.permissions is not None
            else spec.permissions
        )
        if _has_permission_interrupt(effective_permissions):
            return True
    return False


def _has_general_purpose(subagents: Sequence[SubAgentDefinitionLike]) -> bool:
    return any(
        definition.name == DEFAULT_GENERAL_PURPOSE_NAME for definition in subagents
    )


def _uses_controlled_general_purpose(spec: SupervisorSpec) -> bool:
    return spec.control_default_subagent and not _has_general_purpose(spec.subagents)


def _uses_upstream_general_purpose(spec: SupervisorSpec) -> bool:
    return not spec.control_default_subagent and not _has_general_purpose(
        spec.subagents
    )


def _worker_required(spec: SupervisorSpec) -> bool:
    if _uses_controlled_general_purpose(spec):
        return True
    return any(
        isinstance(definition, SubAgentDefinition)
        and definition.model is None
        and definition.model_purpose == ModelPurpose.WORKER
        for definition in spec.subagents
    )


def _summary_middleware(
    resolved: ResolvedModelBindings,
    backend: BackendProtocol,
) -> MiddlewareType | None:
    if resolved.summarization is None:
        return None
    return create_summarization_middleware(resolved.summarization, backend)


def _delegation_controller(
    spec: SupervisorSpec,
) -> DelegationController | None:
    if spec.delegation is None:
        return None
    return spec.delegation.controller or DelegationController(spec.delegation.policy)


def _supervisor_middleware(
    spec: SupervisorSpec,
    summary: MiddlewareType | None,
    controller: DelegationController | None,
) -> list[MiddlewareType]:
    middleware: list[MiddlewareType] = list(spec.middleware.supervisor)
    if summary is not None:
        middleware.append(summary)
    emitter = (
        DiagnosticEmitter(spec.diagnostics, spec.name)
        if spec.diagnostics is not None
        else None
    )
    if emitter is not None:
        middleware.append(DelegationDiagnosticsMiddleware(emitter))
    if controller is not None:
        middleware.append(DelegationPolicyMiddleware(controller, emitter))
    return middleware


def _declarative_middleware(
    definition: SubAgentDefinition,
    spec: SupervisorSpec,
    summary: MiddlewareType | None,
) -> tuple[MiddlewareType, ...]:
    middleware: list[MiddlewareType] = [
        *definition.middleware,
        *spec.middleware.workers,
        *spec.middleware.worker_overrides.get(definition.name, ()),
    ]
    if summary is not None:
        middleware.append(summary)
    return tuple(middleware)


def _model_for_purpose(
    resolved: ResolvedModelBindings,
    purpose: ModelPurpose,
) -> Any:
    model = resolved.by_purpose.get(purpose)
    if model is None:
        raise ModelBindingError(
            f"models.{purpose}: no resolved model for the subagent purpose"
        )
    return model


def _native_declarative(
    definition: SubAgentDefinition,
    resolved: ResolvedModelBindings,
    middleware: tuple[MiddlewareType, ...],
) -> SubAgent:
    model = (
        definition.model
        if definition.model is not None
        else _model_for_purpose(resolved, definition.model_purpose)
    )
    native: dict[str, Any] = {
        "name": definition.name,
        "description": definition.description,
        "model": model,
        "middleware": list(middleware),
        "mode": definition.mode.value,
    }
    if definition.system_prompt is not None:
        native["system_prompt"] = definition.system_prompt
    if definition.tools is not None:
        native["tools"] = list(definition.tools)
    if definition.interrupt_on is not None:
        native["interrupt_on"] = dict(definition.interrupt_on)
    if definition.response_format is not None:
        native["response_format"] = definition.response_format
    if definition.skills is not None:
        native["skills"] = list(definition.skills)
    if definition.permissions is not None:
        native["permissions"] = list(definition.permissions)
    return cast(SubAgent, native)


def _native_compiled(definition: CompiledSubAgentDefinition) -> CompiledSubAgent:
    native: dict[str, Any] = {
        "name": definition.name,
        "description": definition.description,
        "runnable": definition.runnable,
        "mode": definition.mode.value,
    }
    return cast(CompiledSubAgent, native)


def _declarative_report(
    definition: SubAgentDefinition,
    middleware: tuple[MiddlewareType, ...],
    *,
    warnings: tuple[str, ...] = (),
) -> SubagentReport:
    model_source = (
        f"injected:{type(definition.model).__name__}"
        if definition.model is not None
        else f"purpose:{definition.model_purpose}"
    )
    return SubagentReport(
        name=definition.name,
        kind=SubAgentKind.DECLARATIVE,
        mode=definition.mode,
        model_source=model_source,
        middleware_names=tuple(item.name for item in middleware),
        availability=(
            "experimental" if definition.mode == SubAgentMode.FORK else "available"
        ),
        warnings=warnings,
    )


def _compiled_report(definition: CompiledSubAgentDefinition) -> SubagentReport:
    return SubagentReport(
        name=definition.name,
        kind=SubAgentKind.COMPILED,
        mode=definition.mode,
        model_source="compiled",
        availability=(
            "experimental" if definition.mode == SubAgentMode.FORK else "available"
        ),
    )


def _default_general_purpose_definition(
    spec: SupervisorSpec,
) -> SubAgentDefinition:
    raw: Mapping[str, object] = cast(Mapping[str, object], GENERAL_PURPOSE_SUBAGENT)
    description = raw.get("description")
    system_prompt = raw.get("system_prompt")
    if not isinstance(description, str) or not isinstance(system_prompt, str):
        raise AgentConfigurationError(
            "supervisor: upstream general-purpose definition is incomplete"
        )
    return SubAgentDefinition(
        name=DEFAULT_GENERAL_PURPOSE_NAME,
        description=description,
        system_prompt=system_prompt,
        model_purpose=ModelPurpose.WORKER,
        skills=None if spec.skills is None else tuple(spec.skills),
    )


def _native_subagents(
    spec: SupervisorSpec,
    resolved: ResolvedModelBindings,
    summary: MiddlewareType | None,
) -> tuple[
    list[SubAgent | CompiledSubAgent],
    tuple[SubagentReport, ...],
    dict[str, tuple[str, ...]],
]:
    definitions: list[SubAgentDefinitionLike] = list(spec.subagents)
    controlled_default = _uses_controlled_general_purpose(spec)
    if controlled_default:
        definitions.insert(0, _default_general_purpose_definition(spec))
    native: list[SubAgent | CompiledSubAgent] = []
    reports: list[SubagentReport] = []
    per_subagent: dict[str, tuple[str, ...]] = {}
    for definition in definitions:
        if isinstance(definition, SubAgentDefinition):
            middleware = _declarative_middleware(definition, spec, summary)
            native.append(_native_declarative(definition, resolved, middleware))
            reports.append(
                _declarative_report(
                    definition,
                    middleware,
                    warnings=(
                        (
                            "package-controlled default subagent; "
                            "uses the WORKER purpose and worker middleware",
                        )
                        if controlled_default
                        and definition.name == DEFAULT_GENERAL_PURPOSE_NAME
                        else ()
                    ),
                )
            )
            per_subagent[definition.name] = tuple(item.name for item in middleware)
        else:
            native.append(_native_compiled(definition))
            reports.append(_compiled_report(definition))
            per_subagent[definition.name] = ()
    return native, tuple(reports), per_subagent


def _create_graph(
    spec: SupervisorSpec,
    resolved: ResolvedModelBindings,
    backend: BackendProtocol,
    supervisor_middleware: list[MiddlewareType],
    native_subagents: list[SubAgent | CompiledSubAgent],
) -> Any:
    try:
        return _create_deep_agent(
            model=resolved.supervisor,
            tools=list(spec.tools),
            system_prompt=spec.system_prompt,
            middleware=cast(Any, supervisor_middleware),
            subagents=native_subagents,
            backend=backend,
            checkpointer=(
                spec.checkpointer if checkpointer_present(spec.checkpointer) else None
            ),
            store=spec.store,
            interrupt_on=(
                None if spec.interrupt_on is None else dict(spec.interrupt_on)
            ),
            state_schema=spec.state_schema,
            context_schema=spec.context_schema,
            response_format=cast(Any, spec.response_format),
            permissions=(None if spec.permissions is None else list(spec.permissions)),
            skills=None if spec.skills is None else list(spec.skills),
            memory=None if spec.memory is None else list(spec.memory),
            cache=spec.cache,
            name=spec.name,
            debug=spec.debug,
        )
    except Exception as exc:
        raise AgentConfigurationError(
            "supervisor: upstream graph assembly failed"
        ) from exc


def _model_source_labels(
    bindings: ModelBindings,
) -> Mapping[ModelPurpose, str]:
    labels: dict[ModelPurpose, str] = {}
    for binding in bindings.bindings:
        if binding.model is not None:
            labels[binding.purpose] = f"injected:{type(binding.model).__name__}"
        elif binding.catalog is not None:
            labels[binding.purpose] = f"catalog:{binding.catalog}"
        elif binding.inherit_from is not None:
            labels[binding.purpose] = f"inherited:{binding.inherit_from}"
    return labels


def _report_warnings(
    spec: SupervisorSpec,
    summary: MiddlewareType | None,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if summary is None:
        warnings.append(
            "models.summarization: no explicit summarization binding; the "
            "upstream default may use the supervisor model"
        )
    declarative_count = sum(
        isinstance(definition, SubAgentDefinition) for definition in spec.subagents
    )
    if _uses_controlled_general_purpose(spec):
        declarative_count += 1
    compiled_count = sum(
        isinstance(definition, CompiledSubAgentDefinition)
        for definition in spec.subagents
    )
    if compiled_count and spec.middleware.workers:
        warnings.append(
            "middleware.workers: compiled subagents own their middleware and "
            "are not modified"
        )
    if _uses_upstream_general_purpose(spec):
        warnings.append(
            "general-purpose: upstream-owned default uses the supervisor model; "
            "the WORKER binding and workers middleware do not apply"
        )
    if spec.middleware.workers and declarative_count == 0:
        warnings.append("middleware.workers: no declarative subagents are registered")
    if spec.diagnostics is not None and spec.diagnostics.async_callback is not None:
        warnings.append(
            "diagnostics: async callback is awaited only with ainvoke/astream; "
            "sync execution uses the sync callback only"
        )
    return tuple(warnings)


_UPSTREAM_GENERAL_PURPOSE_MIDDLEWARE = (
    "FilesystemMiddleware",
    "SummarizationMiddleware",
    "PatchToolCallsMiddleware",
)


def _build_report(
    spec: SupervisorSpec,
    resolved: ResolvedModelBindings,
    subagent_reports: tuple[SubagentReport, ...],
    per_subagent: dict[str, tuple[str, ...]],
    supervisor_middleware: list[MiddlewareType],
    summary: MiddlewareType | None,
) -> AssemblyReport:
    warnings = _report_warnings(spec, summary)
    reports = list(subagent_reports)
    per_subagent_report = dict(per_subagent)
    if _uses_upstream_general_purpose(spec):
        reports.insert(
            0,
            SubagentReport(
                name=DEFAULT_GENERAL_PURPOSE_NAME,
                kind=SubAgentKind.UPSTREAM_DEFAULT,
                mode=SubAgentMode.ISOLATED,
                model_source="upstream:supervisor",
                middleware_names=_UPSTREAM_GENERAL_PURPOSE_MIDDLEWARE,
                availability="available",
                warnings=(
                    "upstream-owned; WORKER binding and workers middleware "
                    "do not apply",
                ),
            ),
        )
        per_subagent_report = {
            DEFAULT_GENERAL_PURPOSE_NAME: _UPSTREAM_GENERAL_PURPOSE_MIDDLEWARE,
            **per_subagent_report,
        }
    middleware = MiddlewareScopeReport(
        supervisor_names=tuple(item.name for item in supervisor_middleware),
        worker_names=tuple(item.name for item in spec.middleware.workers),
        per_subagent=per_subagent_report,
        replaced_defaults=(("SummarizationMiddleware",) if summary is not None else ()),
        warnings=warnings,
    )
    interrupt_configured = _interrupt_configured(spec)
    delegation = None
    if spec.delegation is not None:
        delegation = DelegationReport(
            max_concurrency=spec.delegation.policy.max_concurrency,
            max_queue=spec.delegation.policy.max_queue,
            deadline_seconds=spec.delegation.policy.deadline_seconds,
            controller_reused=spec.delegation.controller is not None,
            execution_mode="async",
            warnings=("governed delegation requires ainvoke/astream",),
        )
    return AssemblyReport(
        package_version=version("spawn-join-agent-deepagents"),
        deepagents_version=deepagents.__version__,
        supervisor_name=spec.name,
        models=_model_source_labels(spec.models),
        subagents=tuple(reports),
        middleware=middleware,
        delegation=delegation,
        resources=ResourceReport(
            backend="host" if spec.backend is not None else "default_state",
            store="host" if spec.store is not None else "absent",
            checkpointer=(
                "host" if checkpointer_present(spec.checkpointer) else "absent"
            ),
            interrupt_configured=interrupt_configured,
            thread_id_required=interrupt_configured,
        ),
        warnings=warnings,
        experimental_features=(
            ("forked_subagents",)
            if any(
                definition.mode == SubAgentMode.FORK for definition in spec.subagents
            )
            else ()
        ),
        diagnostics_enabled=spec.diagnostics is not None,
    )
