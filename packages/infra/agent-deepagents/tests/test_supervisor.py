"""Supervisor assembly contracts and offline delegation tests."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, cast

import pytest
from deepagents.backends import StateBackend
from deepagents.middleware.filesystem import FilesystemPermission
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command
from spawn_join_agent_deepagents.errors import (
    MiddlewareConfigurationError,
    ModelBindingError,
    RecoveryConfigurationError,
    SubagentConfigurationError,
    UnsupportedSyncDelegationError,
)
from spawn_join_agent_deepagents.execution import (
    DelegationConfiguration,
    DelegationController,
    DelegationPolicy,
)
from spawn_join_agent_deepagents.middleware import MiddlewareConfiguration
from spawn_join_agent_deepagents.models import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
)
from spawn_join_agent_deepagents.recovery import RecoveryContext
from spawn_join_agent_deepagents.subagents import (
    CompiledSubAgentDefinition,
    SubAgentDefinition,
    SubAgentKind,
)
from spawn_join_agent_deepagents.supervisor import (
    SupervisorSpec,
    build_supervisor,
)


class RecordingMiddleware(AgentMiddleware[Any, Any, Any]):
    """Record before_model calls to prove which worker stack ran."""

    def __init__(self, name: str, events: list[str]) -> None:
        super().__init__()
        self._name = name
        self._events = events

    @property
    def name(self) -> str:
        return self._name

    def before_model(
        self,
        state: Any,
        runtime: Any,
    ) -> dict[str, Any] | None:
        del state, runtime
        self._events.append(self.name)
        return None


def _bindings(
    supervisor: BaseChatModel,
    worker: BaseChatModel | None = None,
    *,
    include_summarization: bool = True,
    require_summarization: bool = True,
) -> ModelBindings:
    bindings = [ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor)]
    if worker is not None:
        bindings.append(ModelBinding(ModelPurpose.WORKER, model=worker))
    if include_summarization:
        bindings.append(
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            )
        )
    return ModelBindings(
        catalog=None,
        bindings=tuple(bindings),
        require_summarization=require_summarization,
    )


def _task_call(subagent: str, description: str, call_id: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "task",
                "args": {
                    "description": description,
                    "subagent_type": subagent,
                },
                "id": call_id,
                "type": "tool_call",
            }
        ],
    )


def _compiled_worker(state: dict[str, Any]) -> dict[str, Any]:
    del state
    return {"messages": [AIMessage(content="compiled result")]}


def _compiled_definition() -> CompiledSubAgentDefinition:
    return CompiledSubAgentDefinition(
        name="compiled",
        description="Runs a compiled graph.",
        runnable=RunnableLambda(_compiled_worker),
    )


def _researcher_definition() -> SubAgentDefinition:
    return SubAgentDefinition(
        name="researcher",
        description="Research a topic.",
        model_purpose=ModelPurpose.WORKER,
    )


def test_build_supervisor_returns_native_graph_and_report(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker result")])
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            subagents=(_researcher_definition(), _compiled_definition()),
            name="coordinator",
        )
    )

    assert assembly.graph is not None
    assert assembly.report.supervisor_name == "coordinator"
    assert {item.name for item in assembly.report.subagents} == {
        "general-purpose",
        "researcher",
        "compiled",
    }
    general_purpose = next(
        item for item in assembly.report.subagents if item.name == "general-purpose"
    )
    assert general_purpose.model_source == "purpose:worker"
    assert general_purpose.kind is SubAgentKind.DECLARATIVE
    assert "SummarizationMiddleware" in assembly.report.middleware.replaced_defaults


def test_offline_declarative_and_compiled_delegation(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model(
        [
            _task_call("researcher", "Research the topic", "call-researcher"),
            _task_call("compiled", "Run the compiled worker", "call-compiled"),
            AIMessage(content="final answer"),
        ]
    )
    worker = make_sequence_model([AIMessage(content="researcher result")])
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            subagents=(_researcher_definition(), _compiled_definition()),
            name="coordinator",
        )
    )

    result = cast(
        dict[str, Any],
        asyncio.run(
            assembly.graph.ainvoke(
                {"messages": [HumanMessage(content="Start the task")]}
            )
        ),
    )
    messages = cast(list[Any], result["messages"])
    contents = [str(getattr(message, "content", "")) for message in messages]

    assert any("researcher result" in content for content in contents)
    assert any("compiled result" in content for content in contents)
    assert any("final answer" in content for content in contents)


def test_duplicate_subagent_names_are_rejected(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])
    researcher = _researcher_definition()
    duplicate = SubAgentDefinition(
        name="researcher",
        description="Another researcher.",
    )

    with pytest.raises(SubagentConfigurationError, match="duplicate"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor, worker),
                subagents=(researcher, duplicate),
            )
        )


def test_missing_worker_binding_is_rejected(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])

    with pytest.raises(ModelBindingError, match="worker"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor, worker=None),
                subagents=(_researcher_definition(),),
            )
        )


def test_missing_summarization_binding_is_rejected(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])

    with pytest.raises(ModelBindingError, match="summarization"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(
                    supervisor,
                    worker,
                    include_summarization=False,
                    require_summarization=True,
                ),
                subagents=(_researcher_definition(),),
            )
        )


def test_unknown_worker_override_is_rejected(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])

    with pytest.raises(MiddlewareConfigurationError, match="unknown"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor, worker),
                subagents=(_researcher_definition(),),
                middleware=MiddlewareConfiguration(worker_overrides={"missing": ()}),
            )
        )


def test_interrupt_without_checkpointer_is_rejected(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])

    with pytest.raises(RecoveryConfigurationError, match="checkpointer"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor, worker),
                subagents=(_researcher_definition(),),
                interrupt_on={"task": True},
            )
        )


def test_compiled_subagent_has_no_injected_middleware(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            subagents=(_compiled_definition(),),
        )
    )

    compiled = next(
        item for item in assembly.report.subagents if item.name == "compiled"
    )
    assert compiled.middleware_names == ()
    assert assembly.report.middleware.per_subagent["compiled"] == ()


def test_governed_delegation_report_and_controller_reuse(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])
    controller = DelegationController(DelegationPolicy(max_concurrency=1, max_queue=0))
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            subagents=(_researcher_definition(),),
            delegation=DelegationConfiguration(
                policy=controller.policy,
                controller=controller,
            ),
            name="coordinator",
        )
    )

    assert assembly.delegation_controller is controller
    assert assembly.report.delegation is not None
    assert assembly.report.delegation.max_concurrency == 1
    assert assembly.report.delegation.max_queue == 0
    assert assembly.report.delegation.controller_reused is True
    assert assembly.report.delegation.execution_mode == "async"


def test_offline_governed_delegation_uses_the_controller(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model(
        [
            _task_call("researcher", "Research", "call-researcher"),
            AIMessage(content="final answer"),
        ]
    )
    worker = make_sequence_model([AIMessage(content="researcher result")])
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            subagents=(_researcher_definition(),),
            delegation=DelegationConfiguration(
                policy=DelegationPolicy(max_concurrency=1, max_queue=0)
            ),
            name="coordinator",
        )
    )

    result = cast(
        dict[str, Any],
        asyncio.run(
            assembly.graph.ainvoke({"messages": [HumanMessage(content="Start")]})
        ),
    )
    contents = [
        str(getattr(message, "content", ""))
        for message in cast(list[Any], result["messages"])
    ]
    assert any("researcher result" in content for content in contents)
    assert assembly.delegation_controller is not None
    assert assembly.delegation_controller.active_count == 0


def test_subagent_interrupt_requires_a_checkpointer(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])
    researcher = SubAgentDefinition(
        name="researcher",
        description="Research.",
        interrupt_on={"some_tool": True},
    )

    with pytest.raises(RecoveryConfigurationError, match="checkpointer"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor, worker),
                subagents=(researcher,),
            )
        )


def test_false_checkpointer_is_treated_as_absent(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])

    with pytest.raises(RecoveryConfigurationError, match="checkpointer"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor, worker),
                subagents=(_researcher_definition(),),
                interrupt_on={"task": True},
                checkpointer=False,
            )
        )

    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            subagents=(_researcher_definition(),),
            checkpointer=False,
        )
    )
    assert assembly.report.resources.checkpointer == "absent"


def test_true_checkpointer_is_rejected(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])

    with pytest.raises(RecoveryConfigurationError, match="root graph"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor, worker),
                checkpointer=True,
            )
        )


def test_explicit_require_worker_is_honored(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    models = ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
        require_worker=True,
    )

    with pytest.raises(ModelBindingError, match="worker"):
        build_supervisor(
            SupervisorSpec(
                models=models,
                control_default_subagent=False,
            )
        )


def test_build_calls_create_deep_agent_once_and_preserves_resources(
    monkeypatch: pytest.MonkeyPatch,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])
    checkpointer = InMemorySaver()
    store = InMemoryStore()
    backend = StateBackend()
    calls: list[dict[str, Any]] = []

    def fake_create(**kwargs: Any) -> object:
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(
        "spawn_join_agent_deepagents.supervisor._create_deep_agent",
        fake_create,
    )
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            subagents=(_researcher_definition(),),
            checkpointer=checkpointer,
            store=store,
            backend=backend,
            name="coordinator",
        )
    )

    assert assembly.graph is not None
    assert len(calls) == 1
    assert calls[0]["model"] is supervisor
    assert calls[0]["checkpointer"] is checkpointer
    assert calls[0]["store"] is store
    assert calls[0]["backend"] is backend
    native_subagents = calls[0]["subagents"]
    assert [item["name"] for item in native_subagents] == [
        "general-purpose",
        "researcher",
    ]
    general_purpose, researcher = native_subagents
    assert general_purpose["model"] is worker
    assert general_purpose["mode"] == "isolated"
    assert general_purpose["middleware"]
    assert researcher["model"] is worker
    assert researcher["mode"] == "isolated"
    assert researcher["middleware"]


def test_sync_invocation_with_policy_is_rejected(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model(
        [_task_call("researcher", "Research", "call-researcher")]
    )
    worker = make_sequence_model([AIMessage(content="researcher result")])
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            subagents=(_researcher_definition(),),
            delegation=DelegationConfiguration(
                policy=DelegationPolicy(max_concurrency=1, max_queue=0)
            ),
            name="coordinator",
        )
    )

    with pytest.raises(UnsupportedSyncDelegationError, match="ainvoke"):
        assembly.graph.invoke({"messages": [HumanMessage(content="Start")]})


def test_controlled_general_purpose_uses_worker_model_and_middleware(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    events: list[str] = []
    supervisor = make_sequence_model(
        [
            _task_call(
                "general-purpose",
                "Handle the general task",
                "call-general-purpose",
            ),
            AIMessage(content="final answer"),
        ]
    )
    worker = make_sequence_model([AIMessage(content="general-purpose result")])
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            middleware=MiddlewareConfiguration(
                workers=(RecordingMiddleware("worker-marker", events),)
            ),
            name="coordinator",
        )
    )

    result = cast(
        dict[str, Any],
        asyncio.run(
            assembly.graph.ainvoke({"messages": [HumanMessage(content="Start")]})
        ),
    )
    contents = [
        str(getattr(message, "content", ""))
        for message in cast(list[Any], result["messages"])
    ]

    assert any("general-purpose result" in content for content in contents)
    assert events.count("worker-marker") >= 1
    general_purpose = next(
        item for item in assembly.report.subagents if item.name == "general-purpose"
    )
    assert general_purpose.kind is SubAgentKind.DECLARATIVE
    assert general_purpose.model_source == "purpose:worker"
    assert "worker-marker" in general_purpose.middleware_names


def test_upstream_general_purpose_is_reported_when_control_is_disabled(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor),
            control_default_subagent=False,
            name="coordinator",
        )
    )

    general_purpose = next(
        item for item in assembly.report.subagents if item.name == "general-purpose"
    )
    assert general_purpose.kind is SubAgentKind.UPSTREAM_DEFAULT
    assert general_purpose.model_source == "upstream:supervisor"
    assert any("upstream-owned" in warning for warning in general_purpose.warnings)
    assert any(
        "upstream-owned default" in warning for warning in assembly.report.warnings
    )


def test_permission_interrupt_requires_checkpointer(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    permissions = (
        FilesystemPermission(
            operations=["write"],
            paths=["/secret/**"],
            mode="interrupt",
        ),
    )

    with pytest.raises(RecoveryConfigurationError, match="checkpointer"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor),
                permissions=permissions,
                control_default_subagent=False,
            )
        )

    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor),
            permissions=permissions,
            checkpointer=InMemorySaver(),
            control_default_subagent=False,
        )
    )
    assert assembly.report.resources.interrupt_configured is True
    assert assembly.report.resources.thread_id_required is True


def test_permission_interrupt_and_resume_with_checkpointer(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "write_file",
                        "args": {
                            "file_path": "/secret/x.txt",
                            "content": "x",
                        },
                        "id": "call-write",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="permission-approved"),
        ]
    )
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor),
            permissions=(
                FilesystemPermission(
                    operations=["write"],
                    paths=["/secret/**"],
                    mode="interrupt",
                ),
            ),
            checkpointer=InMemorySaver(),
            control_default_subagent=False,
        )
    )
    config = RecoveryContext("thread-permission").to_graph_config()

    first = cast(
        dict[str, Any],
        asyncio.run(
            assembly.graph.ainvoke(
                {"messages": [HumanMessage(content="start")]},
                config=config,
            )
        ),
    )
    assert "__interrupt__" in first

    resumed = cast(
        dict[str, Any],
        asyncio.run(
            assembly.graph.ainvoke(
                Command(resume={"decisions": [{"type": "approve"}]}),
                config=config,
            )
        ),
    )
    contents = [
        str(getattr(message, "content", ""))
        for message in cast(list[Any], resumed["messages"])
    ]
    assert any("permission-approved" in content for content in contents)


def test_subagent_permission_interrupt_requires_checkpointer(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])
    researcher = SubAgentDefinition(
        name="researcher",
        description="Research.",
        permissions=(
            FilesystemPermission(
                operations=["write"],
                paths=["/secret/**"],
                mode="interrupt",
            ),
        ),
    )

    with pytest.raises(RecoveryConfigurationError, match="checkpointer"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor, worker),
                subagents=(researcher,),
            )
        )
