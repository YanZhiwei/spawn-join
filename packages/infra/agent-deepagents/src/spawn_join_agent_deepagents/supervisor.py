"""Native supervisor assembly from explicit product contracts."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from importlib.metadata import version
from types import MappingProxyType
from typing import Any, cast

import deepagents
from deepagents import DeepAgentState, MemoryMiddleware, RubricMiddleware
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

from .backends import backend_kind, permission_report
from .context_sources import MemoryConfiguration, SkillsConfiguration
from .diagnostics import (
    AssemblyReport,
    ContextReport,
    DelegationDiagnosticsMiddleware,
    DelegationReport,
    DiagnosticEmitter,
    DiagnosticsConfig,
    ProfileReport,
    ResourceReport,
    RubricReport,
    SubagentReport,
)
from .errors import (
    AgentConfigurationError,
    MiddlewareConfigurationError,
    ModelBindingError,
    ProfileConfigurationError,
    RubricConfigurationError,
    SubagentConfigurationError,
)
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
from .profiles import ProfilesConfiguration
from .recovery import (
    checkpointer_present,
    validate_checkpointer_value,
    validate_interrupt_checkpointer,
)
from .rubric import RubricConfiguration
from .subagents import (
    DEFAULT_GENERAL_PURPOSE_NAME,
    AsyncSubAgentDefinition,
    CompiledSubAgentDefinition,
    ResponseFormatLike,
    SubAgentDefinition,
    SubAgentDefinitionLike,
    SubAgentKind,
    SubAgentMode,
    ToolLike,
    validate_experimental_async_subagents,
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
    allow_experimental_async_subagents: bool = False
    allow_experimental_profiles: bool = False
    profiles: ProfilesConfiguration | None = None
    allow_experimental_rubric: bool = False
    rubric: RubricConfiguration | None = None
    backend: BackendProtocol | None = None
    store: BaseStore | None = None
    checkpointer: CheckpointerType = None
    interrupt_on: Mapping[str, bool | InterruptOnConfig] | None = None
    state_schema: type[DeepAgentState] | None = None
    context_schema: type[Any] | None = None
    response_format: ResponseFormatLike | None = None
    permissions: Sequence[FilesystemPermission] | None = None
    skills: Sequence[str] | SkillsConfiguration | None = None
    memory: Sequence[str] | MemoryConfiguration | None = None
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
        skills = self.skills
        if skills is not None and not isinstance(skills, SkillsConfiguration):
            object.__setattr__(self, "skills", tuple(skills))
        memory = self.memory
        if memory is not None and not isinstance(memory, MemoryConfiguration):
            object.__setattr__(self, "memory", tuple(memory))


@dataclass(frozen=True, slots=True)
class SupervisorAssembly:
    """The native graph, its safe report, and the reusable execution seam."""

    graph: Any
    report: AssemblyReport
    delegation_controller: DelegationController | None = None


def build_supervisor(spec: SupervisorSpec) -> SupervisorAssembly:
    """Validate the spec and assemble exactly one native supervisor graph."""

    _validate_subagents(spec)
    _validate_rubric(spec)
    worker_requirement = spec.models.require_worker
    if worker_requirement is None:
        worker_requirement = _worker_required(spec)
    resolved = spec.models.resolve(require_worker=worker_requirement)

    backend = spec.backend if spec.backend is not None else StateBackend()
    summary = _summary_middleware(resolved, backend)
    memory_list, memory_middleware, skills_list, context = _context_plan(
        spec,
        backend,
    )
    extra_reserved: frozenset[str] = frozenset()
    if memory_middleware is not None:
        extra_reserved = frozenset({"MemoryMiddleware"})
    profiles = _apply_profiles(spec, extra_reserved)
    controller = _delegation_controller(spec)
    rubric_middleware = _rubric_middleware(spec)
    supervisor_middleware = _supervisor_middleware(
        spec,
        summary,
        controller,
        memory_middleware,
        rubric_middleware,
    )
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
        memory_list,
        skills_list,
    )
    report = _build_report(
        spec,
        resolved,
        subagent_reports,
        per_subagent,
        supervisor_middleware,
        summary,
        context,
        profiles,
    )
    return SupervisorAssembly(
        graph=graph,
        report=report,
        delegation_controller=controller,
    )


def _validate_subagents(spec: SupervisorSpec) -> None:
    raw_definitions: Sequence[object] = cast(Sequence[object], spec.subagents)
    for definition in raw_definitions:
        if not isinstance(
            definition,
            (
                SubAgentDefinition,
                CompiledSubAgentDefinition,
                AsyncSubAgentDefinition,
            ),
        ):
            raise SubagentConfigurationError(
                "subagents: unsupported subagent definition of type "
                f"{type(definition).__name__}"
            )
    validate_unique_subagent_names(spec.subagents)
    validate_experimental_async_subagents(
        spec.subagents,
        allow_experimental_async_subagents=(spec.allow_experimental_async_subagents),
    )
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
        if not isinstance(definition, SubAgentDefinition)
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


def _apply_profiles(
    spec: SupervisorSpec,
    extra_reserved: Collection[str],
) -> ProfilesConfiguration | None:
    if spec.profiles is None:
        return None
    if not spec.allow_experimental_profiles:
        raise ProfileConfigurationError(
            "profiles: harness/provider profiles require "
            "allow_experimental_profiles=True"
        )
    spec.profiles.apply(extra_reserved=extra_reserved)
    return spec.profiles


def _validate_rubric(spec: SupervisorSpec) -> None:
    if spec.rubric is None:
        return
    if not spec.allow_experimental_rubric:
        raise RubricConfigurationError(
            "rubric: rubric grading requires allow_experimental_rubric=True"
        )


def _rubric_middleware(
    spec: SupervisorSpec,
) -> MiddlewareType | None:
    if spec.rubric is None:
        return None
    rubric = spec.rubric
    return RubricMiddleware(
        model=rubric.model,
        system_prompt=rubric.system_prompt,
        tools=list(rubric.tools),
        max_iterations=rubric.max_iterations,
        on_evaluation=rubric.on_evaluation,
    )


def _context_plan(
    spec: SupervisorSpec,
    backend: BackendProtocol,
) -> tuple[
    list[str] | None,
    MiddlewareType | None,
    list[str] | None,
    ContextReport,
]:
    memory_list: list[str] | None = None
    memory_middleware: MiddlewareType | None = None
    memory_count = 0
    memory_cache_prefix = True
    memory_managed_by = "absent"

    if isinstance(spec.memory, MemoryConfiguration):
        memory_count = spec.memory.source_count
        memory_cache_prefix = spec.memory.cache_memory_prefix
        if spec.memory.cache_memory_prefix:
            memory_list = list(spec.memory.sources)
            memory_managed_by = "upstream"
        else:
            if any(
                item.name == "MemoryMiddleware" for item in spec.middleware.supervisor
            ):
                raise MiddlewareConfigurationError(
                    "middleware.supervisor: MemoryMiddleware is reserved when "
                    "memory.cache_memory_prefix=False"
                )
            memory_middleware = MemoryMiddleware(
                backend=backend,
                sources=list(spec.memory.sources),
                add_cache_control=False,
            )
            memory_managed_by = "package"
    elif spec.memory is not None:
        memory_count = len(spec.memory)
        memory_list = list(spec.memory)
        memory_managed_by = "upstream"

    skills_list: list[str] | None = None
    skills_count = 0
    skills_managed_by = "absent"
    if isinstance(spec.skills, SkillsConfiguration):
        skills_count = spec.skills.source_count
        skills_list = list(spec.skills.sources)
        skills_managed_by = "upstream"
    elif spec.skills is not None:
        skills_count = len(spec.skills)
        skills_list = list(spec.skills)
        skills_managed_by = "upstream"

    return (
        memory_list,
        memory_middleware,
        skills_list,
        ContextReport(
            memory_source_count=memory_count,
            memory_cache_prefix=memory_cache_prefix,
            memory_managed_by=memory_managed_by,
            skills_source_count=skills_count,
            skills_managed_by=skills_managed_by,
        ),
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
        definition.name == DEFAULT_GENERAL_PURPOSE_NAME
        and not isinstance(definition, AsyncSubAgentDefinition)
        for definition in subagents
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
    memory_middleware: MiddlewareType | None = None,
    rubric_middleware: MiddlewareType | None = None,
) -> list[MiddlewareType]:
    middleware: list[MiddlewareType] = list(spec.middleware.supervisor)
    if summary is not None:
        middleware.append(summary)
    if memory_middleware is not None:
        middleware.append(memory_middleware)
    if rubric_middleware is not None:
        middleware.append(rubric_middleware)
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


def _native_async(definition: AsyncSubAgentDefinition) -> dict[str, Any]:
    native: dict[str, Any] = {
        "name": definition.name,
        "description": definition.description,
        "graph_id": definition.graph_id,
        "update_strategy": definition.update_strategy,
        "mode": definition.mode.value,
    }
    if definition.url is not None:
        native["url"] = definition.url
    if definition.headers is not None:
        native["headers"] = dict(definition.headers)
    if definition.webhook is not None:
        native["webhook"] = definition.webhook
    if definition.notify_parent is not None:
        native["notify_parent"] = definition.notify_parent
    return native


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


def _async_report(definition: AsyncSubAgentDefinition) -> SubagentReport:
    return SubagentReport(
        name=definition.name,
        kind=SubAgentKind.ASYNC,
        mode=definition.mode,
        model_source=f"remote:{definition.graph_id}",
        availability="experimental",
        warnings=(
            "async subagents require a remote Agent Protocol server and the "
            "async execution path",
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
    skills: tuple[str, ...] | None = None
    if isinstance(spec.skills, SkillsConfiguration):
        skills = tuple(spec.skills.sources)
    elif spec.skills is not None:
        skills = tuple(spec.skills)
    return SubAgentDefinition(
        name=DEFAULT_GENERAL_PURPOSE_NAME,
        description=description,
        system_prompt=system_prompt,
        model_purpose=ModelPurpose.WORKER,
        skills=skills,
    )


def _native_subagents(
    spec: SupervisorSpec,
    resolved: ResolvedModelBindings,
    summary: MiddlewareType | None,
) -> tuple[
    list[Any],
    tuple[SubagentReport, ...],
    dict[str, tuple[str, ...]],
]:
    definitions: list[SubAgentDefinitionLike] = list(spec.subagents)
    controlled_default = _uses_controlled_general_purpose(spec)
    if controlled_default:
        definitions.insert(0, _default_general_purpose_definition(spec))
    native: list[Any] = []
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
        elif isinstance(definition, CompiledSubAgentDefinition):
            native.append(_native_compiled(definition))
            reports.append(_compiled_report(definition))
            per_subagent[definition.name] = ()
        else:
            native.append(_native_async(definition))
            reports.append(_async_report(definition))
            per_subagent[definition.name] = ()
    return native, tuple(reports), per_subagent


def _create_graph(
    spec: SupervisorSpec,
    resolved: ResolvedModelBindings,
    backend: BackendProtocol,
    supervisor_middleware: list[MiddlewareType],
    native_subagents: list[Any],
    memory_list: list[str] | None,
    skills_list: list[str] | None,
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
            skills=skills_list,
            memory=memory_list,
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


def _subagent_warnings(spec: SupervisorSpec) -> list[str]:
    warnings: list[str] = []
    declarative_count = sum(
        isinstance(definition, SubAgentDefinition) for definition in spec.subagents
    )
    if _uses_controlled_general_purpose(spec):
        declarative_count += 1
    compiled_count = sum(
        isinstance(definition, CompiledSubAgentDefinition)
        for definition in spec.subagents
    )
    async_count = sum(
        isinstance(definition, AsyncSubAgentDefinition) for definition in spec.subagents
    )
    if (compiled_count or async_count) and spec.middleware.workers:
        if async_count == 0:
            warnings.append(
                "middleware.workers: compiled subagents own their middleware "
                "and are not modified"
            )
        else:
            warnings.append(
                "middleware.workers: compiled/async subagents own their "
                "execution and do not receive injected worker middleware"
            )
    if spec.middleware.workers and declarative_count == 0:
        warnings.append("middleware.workers: no declarative subagents are registered")
    return warnings


def _management_warnings(spec: SupervisorSpec) -> list[str]:
    warnings: list[str] = []
    if isinstance(spec.memory, MemoryConfiguration) and (
        not spec.memory.cache_memory_prefix
    ):
        warnings.append(
            "memory: the package adds MemoryMiddleware and passes memory=None "
            "because cache_memory_prefix=False"
        )
        if any(definition.mode == SubAgentMode.FORK for definition in spec.subagents):
            warnings.append(
                "memory: package-managed memory is not inherited by fork "
                "subagents; the upstream memory= path is disabled"
            )
    if spec.profiles is not None:
        warnings.append(
            "profiles: DeepAgents harness/provider profiles are beta and are "
            "registered process-wide before assembly"
        )
    if spec.rubric is not None:
        warnings.append(
            "rubric: DeepAgents rubric grading is beta and activates only when "
            "the invocation supplies a rubric in state"
        )
    if any(
        isinstance(definition, AsyncSubAgentDefinition) for definition in spec.subagents
    ):
        warnings.append(
            "async subagents are beta remote Agent Protocol workers and require "
            "the async execution path"
        )
    return warnings


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
    warnings.extend(_subagent_warnings(spec))
    if _uses_upstream_general_purpose(spec):
        warnings.append(
            "general-purpose: upstream-owned default uses the supervisor model; "
            "the WORKER binding and workers middleware do not apply"
        )
    if spec.diagnostics is not None and spec.diagnostics.async_callback is not None:
        warnings.append(
            "diagnostics: async callback is awaited only with ainvoke/astream; "
            "sync execution uses the sync callback only"
        )
    warnings.extend(_management_warnings(spec))
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
    context: ContextReport,
    profiles: ProfilesConfiguration | None,
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
    replaced_defaults: list[str] = []
    if summary is not None:
        replaced_defaults.append("SummarizationMiddleware")
    middleware = MiddlewareScopeReport(
        supervisor_names=tuple(item.name for item in supervisor_middleware),
        worker_names=tuple(item.name for item in spec.middleware.workers),
        per_subagent=per_subagent_report,
        replaced_defaults=tuple(replaced_defaults),
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
    experimental_features: list[str] = []
    if any(definition.mode == SubAgentMode.FORK for definition in spec.subagents):
        experimental_features.append("forked_subagents")
    if any(
        isinstance(definition, AsyncSubAgentDefinition) for definition in spec.subagents
    ):
        experimental_features.append("async_subagents")
    if profiles is not None:
        experimental_features.append("harness_profiles")
    if spec.rubric is not None:
        experimental_features.append("rubric")
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
            backend_kind=backend_kind(spec.backend),
            store="host" if spec.store is not None else "absent",
            checkpointer=(
                "host" if checkpointer_present(spec.checkpointer) else "absent"
            ),
            interrupt_configured=interrupt_configured,
            thread_id_required=interrupt_configured,
            permissions=permission_report(spec.permissions),
        ),
        context=context,
        profiles=ProfileReport(
            harness_keys=profiles.harness_keys if profiles is not None else (),
            provider_keys=profiles.provider_keys if profiles is not None else (),
        ),
        rubric=RubricReport(
            enabled=spec.rubric is not None,
            max_iterations=(
                spec.rubric.max_iterations if spec.rubric is not None else 0
            ),
            model_source=(
                spec.rubric.model_source if spec.rubric is not None else "none"
            ),
            tool_count=spec.rubric.tool_count if spec.rubric is not None else 0,
        ),
        warnings=warnings,
        experimental_features=tuple(experimental_features),
        diagnostics_enabled=spec.diagnostics is not None,
    )
