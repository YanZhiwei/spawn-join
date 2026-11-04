"""Contracts for assembly reports and lifecycle diagnostics."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from types import MappingProxyType, SimpleNamespace
from typing import Any, cast

import pytest
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.errors import GraphInterrupt
from spawn_join_agent_deepagents.diagnostics import (
    AssemblyReport,
    DelegationDiagnosticsMiddleware,
    DelegationReport,
    DiagnosticEmitter,
    DiagnosticEvent,
    DiagnosticEventType,
    DiagnosticsConfig,
    RequestContext,
    ResourceReport,
    SubagentReport,
    request_context,
)
from spawn_join_agent_deepagents.errors import (
    DelegationQueueFullError,
    DelegationTimeoutError,
)
from spawn_join_agent_deepagents.execution import (
    DelegationConfiguration,
    DelegationController,
    DelegationPolicy,
    DelegationPolicyMiddleware,
)
from spawn_join_agent_deepagents.middleware import MiddlewareScopeReport
from spawn_join_agent_deepagents.models import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
)
from spawn_join_agent_deepagents.subagents import (
    SubAgentDefinition,
    SubAgentKind,
    SubAgentMode,
)
from spawn_join_agent_deepagents.supervisor import (
    SupervisorSpec,
    build_supervisor,
)


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


def _runtime() -> Any:
    return SimpleNamespace(
        execution_info=SimpleNamespace(
            run_id="run-1",
            thread_id="thread-1",
        )
    )


def _task_request(
    *,
    name: str = "task",
    runtime: Any = None,
) -> ToolCallRequest:
    return cast(
        ToolCallRequest,
        SimpleNamespace(
            tool_call={
                "name": name,
                "args": {"subagent_type": "researcher"},
                "id": "call-1",
            },
            runtime=runtime,
        ),
    )


def _task_call(subagent: str, call_id: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "task",
                "args": {
                    "description": "Do the work",
                    "subagent_type": subagent,
                },
                "id": call_id,
                "type": "tool_call",
            }
        ],
    )


def _bindings(
    supervisor: BaseChatModel,
    worker: BaseChatModel | None = None,
) -> ModelBindings:
    bindings = [ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor)]
    if worker is not None:
        bindings.append(ModelBinding(ModelPurpose.WORKER, model=worker))
    bindings.append(
        ModelBinding(
            ModelPurpose.SUMMARIZATION,
            inherit_from=ModelPurpose.SUPERVISOR,
        )
    )
    return ModelBindings(catalog=None, bindings=tuple(bindings))


def test_emitter_dispatches_sync_then_async() -> None:
    events: list[tuple[str, DiagnosticEvent]] = []

    def sync_callback(event: DiagnosticEvent) -> None:
        events.append(("sync", event))

    async def async_callback(event: DiagnosticEvent) -> None:
        events.append(("async", event))

    emitter = DiagnosticEmitter(
        DiagnosticsConfig(
            sync_callback=sync_callback,
            async_callback=async_callback,
            include_thread_id=True,
        ),
        "coordinator",
    )
    context = RequestContext(
        subagent_name="researcher",
        tool_call_id="call-1",
        run_id="run-1",
        thread_id="thread-1",
    )

    emitter.emit(DiagnosticEventType.DELEGATION_SELECTED, context=context)
    asyncio.run(
        emitter.aemit(
            DiagnosticEventType.DELEGATION_COMPLETED,
            context=context,
            outcome="completed",
        )
    )

    assert [kind for kind, _ in events] == ["sync", "sync", "async"]
    assert events[0][1].subagent_name == "researcher"
    assert events[0][1].thread_id == "thread-1"


def test_async_only_callback_is_not_called_from_sync_emit() -> None:
    events: list[DiagnosticEvent] = []

    async def async_callback(event: DiagnosticEvent) -> None:
        events.append(event)

    emitter = DiagnosticEmitter(
        DiagnosticsConfig(async_callback=async_callback),
        None,
    )
    emitter.emit(DiagnosticEventType.DELEGATION_SELECTED)
    assert events == []

    asyncio.run(emitter.aemit(DiagnosticEventType.DELEGATION_SELECTED))
    assert len(events) == 1


def test_request_context_uses_runtime_execution_info() -> None:
    context = request_context(_task_request(runtime=_runtime()))

    assert context.subagent_name == "researcher"
    assert context.tool_call_id == "call-1"
    assert context.run_id == "run-1"
    assert context.thread_id == "thread-1"


def test_diagnostics_middleware_success_and_failure_are_redacted() -> None:
    events: list[DiagnosticEvent] = []
    emitter = DiagnosticEmitter(
        DiagnosticsConfig(sync_callback=events.append),
        "coordinator",
    )
    middleware = DelegationDiagnosticsMiddleware(emitter)
    request = _task_request(runtime=_runtime())

    result = middleware.wrap_tool_call(
        request,
        lambda _: ToolMessage(content="ok", tool_call_id="call-1"),
    )
    assert cast(ToolMessage, result).text == "ok"
    assert [event.event_type for event in events] == [
        DiagnosticEventType.DELEGATION_SELECTED,
        DiagnosticEventType.DELEGATION_COMPLETED,
    ]

    events.clear()

    def failure(_: ToolCallRequest) -> ToolMessage:
        raise ValueError("sk-secret-value")

    with pytest.raises(ValueError, match="sk-secret-value"):
        middleware.wrap_tool_call(request, failure)

    assert [event.event_type for event in events] == [
        DiagnosticEventType.DELEGATION_SELECTED,
        DiagnosticEventType.DELEGATION_FAILED,
    ]
    assert events[-1].error_category == "ValueError"
    assert "sk-secret-value" not in repr(events[-1])


def test_diagnostics_middleware_cancellation_and_interruption() -> None:
    events: list[DiagnosticEvent] = []
    emitter = DiagnosticEmitter(
        DiagnosticsConfig(sync_callback=events.append),
        "coordinator",
    )
    middleware = DelegationDiagnosticsMiddleware(emitter)
    request = _task_request(runtime=_runtime())

    async def scenario() -> None:
        async def cancel(_: ToolCallRequest) -> ToolMessage:
            raise asyncio.CancelledError

        with pytest.raises(asyncio.CancelledError):
            await middleware.awrap_tool_call(request, cancel)
        assert events[-1].event_type == DiagnosticEventType.DELEGATION_CANCELLED

        events.clear()

        async def interrupt(_: ToolCallRequest) -> ToolMessage:
            raise GraphInterrupt()

        with pytest.raises(GraphInterrupt):
            await middleware.awrap_tool_call(request, interrupt)
        assert events[-1].event_type == DiagnosticEventType.DELEGATION_INTERRUPTED

    asyncio.run(scenario())


def test_policy_and_diagnostics_event_sequences() -> None:
    async def scenario() -> None:
        events: list[DiagnosticEvent] = []
        emitter = DiagnosticEmitter(
            DiagnosticsConfig(sync_callback=events.append),
            "coordinator",
        )
        request = _task_request(runtime=_runtime())

        async def success(_: ToolCallRequest) -> ToolMessage:
            return ToolMessage(content="ok", tool_call_id="call-1")

        controller = DelegationController(
            DelegationPolicy(max_concurrency=1, max_queue=0)
        )
        policy = DelegationPolicyMiddleware(controller, emitter)
        diagnostics = DelegationDiagnosticsMiddleware(emitter)
        await diagnostics.awrap_tool_call(
            request,
            lambda item: policy.awrap_tool_call(item, success),
        )
        assert [event.event_type for event in events] == [
            DiagnosticEventType.DELEGATION_SELECTED,
            DiagnosticEventType.DELEGATION_STARTED,
            DiagnosticEventType.DELEGATION_COMPLETED,
        ]

        events.clear()
        controller_timeout = DelegationController(
            DelegationPolicy(
                max_concurrency=1,
                max_queue=0,
                deadline_seconds=0.01,
            )
        )
        policy_timeout = DelegationPolicyMiddleware(
            controller_timeout,
            emitter,
        )
        diagnostics_timeout = DelegationDiagnosticsMiddleware(emitter)

        async def slow(_: ToolCallRequest) -> ToolMessage:
            await asyncio.sleep(1)
            return ToolMessage(content="late", tool_call_id="call-1")

        with pytest.raises(DelegationTimeoutError):
            await diagnostics_timeout.awrap_tool_call(
                request,
                lambda item: policy_timeout.awrap_tool_call(item, slow),
            )
        assert [event.event_type for event in events] == [
            DiagnosticEventType.DELEGATION_SELECTED,
            DiagnosticEventType.DELEGATION_STARTED,
            DiagnosticEventType.DELEGATION_TIMED_OUT,
        ]

        events.clear()
        controller_reject = DelegationController(
            DelegationPolicy(max_concurrency=1, max_queue=0)
        )
        cast(Any, controller_reject)._available = 0
        policy_reject = DelegationPolicyMiddleware(
            controller_reject,
            emitter,
        )
        diagnostics_reject = DelegationDiagnosticsMiddleware(emitter)

        with pytest.raises(DelegationQueueFullError):
            await diagnostics_reject.awrap_tool_call(
                request,
                lambda item: policy_reject.awrap_tool_call(item, success),
            )
        assert [event.event_type for event in events] == [
            DiagnosticEventType.DELEGATION_SELECTED,
            DiagnosticEventType.DELEGATION_REJECTED,
        ]

        events.clear()
        controller_queue = DelegationController(
            DelegationPolicy(
                max_concurrency=1,
                max_queue=1,
                deadline_seconds=0.01,
            )
        )
        cast(Any, controller_queue)._available = 0
        policy_queue = DelegationPolicyMiddleware(
            controller_queue,
            emitter,
        )
        diagnostics_queue = DelegationDiagnosticsMiddleware(emitter)

        with pytest.raises(DelegationTimeoutError):
            await diagnostics_queue.awrap_tool_call(
                request,
                lambda item: policy_queue.awrap_tool_call(item, success),
            )
        assert [event.event_type for event in events] == [
            DiagnosticEventType.DELEGATION_SELECTED,
            DiagnosticEventType.DELEGATION_QUEUED,
            DiagnosticEventType.DELEGATION_TIMED_OUT,
        ]

    asyncio.run(scenario())


def test_callback_exception_propagates() -> None:
    def sync_callback(event: DiagnosticEvent) -> None:
        del event
        raise RuntimeError("sync callback failed")

    emitter = DiagnosticEmitter(
        DiagnosticsConfig(sync_callback=sync_callback),
        None,
    )
    with pytest.raises(RuntimeError, match="sync callback failed"):
        emitter.emit(DiagnosticEventType.DELEGATION_SELECTED)

    async def async_callback(event: DiagnosticEvent) -> None:
        del event
        raise RuntimeError("async callback failed")

    async_emitter = DiagnosticEmitter(
        DiagnosticsConfig(async_callback=async_callback),
        None,
    )
    with pytest.raises(RuntimeError, match="async callback failed"):
        asyncio.run(async_emitter.aemit(DiagnosticEventType.DELEGATION_SELECTED))


def test_offline_diagnostics_success(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    events: list[DiagnosticEvent] = []
    supervisor = make_sequence_model(
        [
            _task_call("researcher", "call-researcher"),
            AIMessage(content="final answer"),
        ]
    )
    worker = make_sequence_model([AIMessage(content="researcher result")])
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            subagents=(
                SubAgentDefinition(
                    name="researcher",
                    description="Research a topic.",
                ),
            ),
            delegation=DelegationConfiguration(
                policy=DelegationPolicy(max_concurrency=1, max_queue=0)
            ),
            diagnostics=DiagnosticsConfig(sync_callback=events.append),
            name="coordinator",
        )
    )

    asyncio.run(assembly.graph.ainvoke({"messages": [HumanMessage(content="Start")]}))

    event_types = [event.event_type for event in events]
    assert DiagnosticEventType.DELEGATION_SELECTED in event_types
    assert DiagnosticEventType.DELEGATION_STARTED in event_types
    assert DiagnosticEventType.DELEGATION_COMPLETED in event_types
    assert any(event.tool_call_id == "call-researcher" for event in events)
    assert assembly.report.diagnostics_enabled is True


def test_async_callback_receives_events_from_offline_graph(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    events: list[DiagnosticEvent] = []

    async def async_callback(event: DiagnosticEvent) -> None:
        events.append(event)

    supervisor = make_sequence_model(
        [
            _task_call("researcher", "call-async"),
            AIMessage(content="final answer"),
        ]
    )
    worker = make_sequence_model([AIMessage(content="researcher result")])
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            subagents=(
                SubAgentDefinition(
                    name="researcher",
                    description="Research a topic.",
                ),
            ),
            diagnostics=DiagnosticsConfig(async_callback=async_callback),
            name="coordinator",
        )
    )

    asyncio.run(assembly.graph.ainvoke({"messages": [HumanMessage(content="Start")]}))

    event_types = [event.event_type for event in events]
    assert DiagnosticEventType.DELEGATION_SELECTED in event_types
    assert DiagnosticEventType.DELEGATION_COMPLETED in event_types


def test_async_callback_warning_is_reported(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])

    async def async_callback(event: DiagnosticEvent) -> None:
        del event

    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            diagnostics=DiagnosticsConfig(async_callback=async_callback),
            name="coordinator",
        )
    )

    assert any("async callback" in warning for warning in assembly.report.warnings)
