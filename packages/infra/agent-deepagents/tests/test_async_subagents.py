"""Async subagent declaration, gating, and report contracts."""

from __future__ import annotations

from collections.abc import Callable
from types import MappingProxyType
from typing import Any, cast

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from spawn_join_agent_deepagents.errors import SubagentConfigurationError
from spawn_join_agent_deepagents.models import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
)
from spawn_join_agent_deepagents.subagents import (
    AsyncSubAgentDefinition,
    SubAgentDefinition,
    SubAgentKind,
    SubAgentMode,
)
from spawn_join_agent_deepagents.supervisor import SupervisorSpec, build_supervisor


def _bindings(supervisor: BaseChatModel, worker: BaseChatModel) -> ModelBindings:
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


def _async_definition(**overrides: Any) -> AsyncSubAgentDefinition:
    values: dict[str, Any] = {
        "name": "remote-researcher",
        "description": "Research on a remote Agent Protocol deployment.",
        "graph_id": "research_agent",
        "url": "https://example.invalid",
        "headers": {"Authorization": "Bearer secret-token"},
        "update_strategy": "enqueue",
    }
    values.update(overrides)
    return AsyncSubAgentDefinition(**values)


def test_async_definition_normalizes_headers() -> None:
    definition = _async_definition()

    assert isinstance(definition.headers, MappingProxyType)
    assert definition.mode == SubAgentMode.ISOLATED


def test_blank_graph_id_is_rejected() -> None:
    with pytest.raises(SubagentConfigurationError, match="graph_id"):
        _async_definition(graph_id="  ")


def test_async_subagent_requires_the_experimental_gate(
    monkeypatch: pytest.MonkeyPatch,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_create(**kwargs: Any) -> object:
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(
        "spawn_join_agent_deepagents.supervisor._create_deep_agent",
        fake_create,
    )
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])

    with pytest.raises(SubagentConfigurationError, match="async subagents"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor, worker),
                subagents=(_async_definition(),),
            )
        )

    assert calls == []


def test_async_subagent_is_forwarded_without_package_injection(
    monkeypatch: pytest.MonkeyPatch,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_create(**kwargs: Any) -> object:
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(
        "spawn_join_agent_deepagents.supervisor._create_deep_agent",
        fake_create,
    )
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])

    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            subagents=(_async_definition(),),
            allow_experimental_async_subagents=True,
        )
    )

    native = calls[0]["subagents"][-1]
    assert native["name"] == "remote-researcher"
    assert native["graph_id"] == "research_agent"
    assert native["update_strategy"] == "enqueue"
    assert native["headers"]["Authorization"] == "Bearer secret-token"
    assert "model" not in native
    assert "middleware" not in native

    async_report = assembly.report.subagents[-1]
    assert async_report.kind == SubAgentKind.ASYNC
    assert async_report.model_source == "remote:research_agent"
    assert async_report.availability == "experimental"
    assert "async_subagents" in assembly.report.experimental_features
    rendered = repr(assembly.report)
    assert "secret-token" not in rendered
    assert "example.invalid" not in rendered


def test_async_name_must_be_unique_across_forms(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])
    declarative = SubAgentDefinition(
        name="remote-researcher",
        description="Local worker.",
    )

    with pytest.raises(SubagentConfigurationError, match="duplicate"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor, worker),
                subagents=(declarative, _async_definition()),
                allow_experimental_async_subagents=True,
            )
        )


def test_unsupported_subagent_form_is_a_stable_configuration_error(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])
    unsupported = cast(Any, {"name": "raw-dict"})

    with pytest.raises(SubagentConfigurationError, match="unsupported"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor, worker),
                subagents=(unsupported,),
            )
        )


def test_async_override_is_rejected(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    from langchain.agents.middleware.types import AgentMiddleware
    from spawn_join_agent_deepagents.errors import MiddlewareConfigurationError
    from spawn_join_agent_deepagents.middleware import MiddlewareConfiguration

    class Marker(AgentMiddleware[Any, Any, Any]):
        @property
        def name(self) -> str:
            return "marker"

    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])

    with pytest.raises(MiddlewareConfigurationError, match="compiled/async"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor, worker),
                subagents=(_async_definition(),),
                allow_experimental_async_subagents=True,
                middleware=MiddlewareConfiguration(
                    worker_overrides={"remote-researcher": (Marker(),)}
                ),
            )
        )


def test_async_defaults_match_the_upstream_update_strategy() -> None:
    definition = AsyncSubAgentDefinition(
        name="remote-researcher",
        description="Remote worker.",
        graph_id="research_agent",
    )

    assert definition.update_strategy == "interrupt"


def test_async_cannot_use_the_reserved_default_name() -> None:
    with pytest.raises(SubagentConfigurationError, match="reserved default"):
        AsyncSubAgentDefinition(
            name="general-purpose",
            description="Remote worker.",
            graph_id="research_agent",
        )


def test_async_fork_requires_both_experimental_gates(
    monkeypatch: pytest.MonkeyPatch,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_create(**kwargs: Any) -> object:
        calls.append(kwargs)
        return object()

    monkeypatch.setattr(
        "spawn_join_agent_deepagents.supervisor._create_deep_agent",
        fake_create,
    )
    supervisor = make_sequence_model([AIMessage(content="unused")])
    worker = make_sequence_model([AIMessage(content="worker")])
    forked = _async_definition(mode=SubAgentMode.FORK)

    with pytest.raises(SubagentConfigurationError, match="fork"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor, worker),
                subagents=(forked,),
                allow_experimental_async_subagents=True,
            )
        )

    build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor, worker),
            subagents=(forked,),
            allow_experimental_async_subagents=True,
            allow_experimental_fork=True,
        )
    )
    assert calls
