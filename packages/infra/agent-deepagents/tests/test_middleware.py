"""Contracts for product middleware scopes."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from types import MappingProxyType
from typing import Any

import pytest
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableLambda
from spawn_join_agent_deepagents.errors import MiddlewareConfigurationError
from spawn_join_agent_deepagents.middleware import (
    DELEGATION_MIDDLEWARE_NAME,
    DIAGNOSTICS_MIDDLEWARE_NAME,
    RESERVED_SUMMARIZATION_MIDDLEWARE_NAME,
    MiddlewareConfiguration,
    MiddlewareScopeReport,
)
from spawn_join_agent_deepagents.models import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
)
from spawn_join_agent_deepagents.subagents import (
    CompiledSubAgentDefinition,
    SubAgentDefinition,
)
from spawn_join_agent_deepagents.supervisor import (
    SupervisorSpec,
    build_supervisor,
)


class MarkerMiddleware(AgentMiddleware[Any, Any, Any]):
    """A minimal middleware with a stable name for scope tests."""

    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        return self._name


class RecordingMiddleware(AgentMiddleware[Any, Any, Any]):
    """Record before_model calls to prove where a middleware executes."""

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


def _bindings(
    supervisor: BaseChatModel,
    worker: BaseChatModel,
) -> ModelBindings:
    return ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor),
            ModelBinding(ModelPurpose.WORKER, model=worker),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )


def test_valid_three_scope_configuration() -> None:
    supervisor = MarkerMiddleware("audit")
    worker = MarkerMiddleware("rate-limit")
    override = MarkerMiddleware("trace")
    configuration = MiddlewareConfiguration(
        supervisor=(supervisor,),
        workers=(worker,),
        worker_overrides={"researcher": (override,)},
    )

    assert configuration.supervisor == (supervisor,)
    assert configuration.workers == (worker,)
    assert configuration.worker_overrides["researcher"] == (override,)
    configuration.validate_for_subagents(
        declarative_names={"researcher"},
        compiled_names={"compiled"},
    )


def test_duplicate_names_within_one_scope_are_rejected() -> None:
    with pytest.raises(MiddlewareConfigurationError, match="duplicate"):
        MiddlewareConfiguration(
            supervisor=(
                MarkerMiddleware("audit"),
                MarkerMiddleware("audit"),
            )
        )


@pytest.mark.parametrize(
    "reserved",
    [
        RESERVED_SUMMARIZATION_MIDDLEWARE_NAME,
        DELEGATION_MIDDLEWARE_NAME,
        DIAGNOSTICS_MIDDLEWARE_NAME,
    ],
)
def test_reserved_names_are_rejected(reserved: str) -> None:
    with pytest.raises(MiddlewareConfigurationError, match="reserved"):
        MiddlewareConfiguration(workers=(MarkerMiddleware(reserved),))


def test_same_name_in_different_scopes_is_allowed() -> None:
    configuration = MiddlewareConfiguration(
        supervisor=(MarkerMiddleware("audit"),),
        workers=(MarkerMiddleware("audit"),),
    )

    assert configuration.supervisor[0].name == "audit"
    assert configuration.workers[0].name == "audit"


def test_unknown_worker_override_is_rejected() -> None:
    configuration = MiddlewareConfiguration(
        worker_overrides={"missing": (MarkerMiddleware("trace"),)}
    )

    with pytest.raises(MiddlewareConfigurationError, match="unknown"):
        configuration.validate_for_subagents(
            declarative_names={"researcher"},
            compiled_names={"compiled"},
        )


def test_compiled_worker_override_is_rejected() -> None:
    configuration = MiddlewareConfiguration(
        worker_overrides={"compiled": (MarkerMiddleware("trace"),)}
    )

    with pytest.raises(MiddlewareConfigurationError, match="compiled"):
        configuration.validate_for_subagents(
            declarative_names={"researcher"},
            compiled_names={"compiled"},
        )


def test_blank_override_name_is_rejected() -> None:
    with pytest.raises(MiddlewareConfigurationError, match="blank"):
        MiddlewareConfiguration(worker_overrides={"  ": (MarkerMiddleware("trace"),)})


def test_duplicate_override_names_are_rejected() -> None:
    with pytest.raises(MiddlewareConfigurationError, match="duplicate"):
        MiddlewareConfiguration(
            worker_overrides={
                "researcher": (
                    MarkerMiddleware("trace"),
                    MarkerMiddleware("trace"),
                )
            }
        )


def test_scope_report_is_immutable_and_tuple_based() -> None:
    report = MiddlewareScopeReport(
        supervisor_names=("audit",),
        worker_names=("rate-limit",),
        per_subagent={"researcher": ("trace",)},
        replaced_defaults=("SummarizationMiddleware",),
        warnings=("async-diagnostics-only",),
    )

    assert report.supervisor_names == ("audit",)
    assert report.per_subagent["researcher"] == ("trace",)
    assert isinstance(report.per_subagent, MappingProxyType)


def test_middleware_scopes_execute_in_offline_delegation(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    events: list[str] = []
    supervisor_model = make_sequence_model(
        [
            _task_call("researcher", "Research", "call-researcher"),
            _task_call("compiled", "Compile", "call-compiled"),
            AIMessage(content="final answer"),
        ]
    )
    worker_model = make_sequence_model([AIMessage(content="worker result")])
    researcher = SubAgentDefinition(
        name="researcher",
        description="Research a topic.",
        middleware=(RecordingMiddleware("researcher-marker", events),),
    )
    compiled = CompiledSubAgentDefinition(
        name="compiled",
        description="Runs a compiled graph.",
        runnable=RunnableLambda(_compiled_worker),
    )
    configuration = MiddlewareConfiguration(
        supervisor=(RecordingMiddleware("supervisor-marker", events),),
        workers=(RecordingMiddleware("worker-marker", events),),
        worker_overrides={
            "researcher": (RecordingMiddleware("override-marker", events),)
        },
    )
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor_model, worker_model),
            subagents=(researcher, compiled),
            middleware=configuration,
            name="coordinator",
        )
    )

    asyncio.run(
        assembly.graph.ainvoke({"messages": [HumanMessage(content="Start the task")]})
    )

    assert events.count("supervisor-marker") >= 1
    assert events.count("researcher-marker") == 1
    assert events.count("worker-marker") == 1
    assert events.count("override-marker") == 1
    assert assembly.report.middleware.per_subagent["compiled"] == ()
    assert any(
        "compiled subagents own their middleware" in warning
        for warning in assembly.report.warnings
    )


def test_requested_worker_middleware_order_and_summarization_replacement(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    events: list[str] = []
    supervisor_model = make_sequence_model([AIMessage(content="unused")])
    worker_model = make_sequence_model([AIMessage(content="worker")])
    researcher = SubAgentDefinition(
        name="researcher",
        description="Research a topic.",
        middleware=(RecordingMiddleware("definition-marker", events),),
    )
    configuration = MiddlewareConfiguration(
        supervisor=(RecordingMiddleware("supervisor-marker", events),),
        workers=(RecordingMiddleware("worker-marker", events),),
        worker_overrides={
            "researcher": (RecordingMiddleware("override-marker", events),)
        },
    )
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor_model, worker_model),
            subagents=(researcher,),
            middleware=configuration,
            name="coordinator",
        )
    )

    names = assembly.report.middleware.per_subagent["researcher"]
    assert names == (
        "definition-marker",
        "worker-marker",
        "override-marker",
        "SummarizationMiddleware",
    )
    assert names.count("SummarizationMiddleware") == 1
    assert (
        assembly.report.middleware.supervisor_names.count("SummarizationMiddleware")
        == 1
    )
    assert assembly.report.middleware.replaced_defaults == ("SummarizationMiddleware",)
