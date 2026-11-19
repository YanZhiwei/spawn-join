"""Rubric configuration, beta gating, and assembly reporting."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from deepagents import RubricMiddleware
from langchain_core._api import LangChainBetaWarning
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from spawn_join_agent_deepagents.errors import RubricConfigurationError
from spawn_join_agent_deepagents.middleware import MiddlewareConfiguration
from spawn_join_agent_deepagents.models import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
)
from spawn_join_agent_deepagents.rubric import RubricConfiguration
from spawn_join_agent_deepagents.supervisor import SupervisorSpec, build_supervisor


def _bindings(supervisor: BaseChatModel) -> ModelBindings:
    return ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )


def test_rubric_rejects_invalid_max_iterations(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    model = make_sequence_model([AIMessage(content="grade")])

    with pytest.raises(RubricConfigurationError, match="max_iterations"):
        RubricConfiguration(model=model, max_iterations=0)


@pytest.mark.parametrize("value", [-1, 1.5, "3", None, True])
def test_rubric_rejects_non_integer_or_non_positive_iterations(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    value: object,
) -> None:
    model = make_sequence_model([AIMessage(content="grade")])

    with pytest.raises(RubricConfigurationError, match="max_iterations"):
        RubricConfiguration(model=model, max_iterations=value)  # type: ignore[arg-type]


def test_rubric_requires_a_chat_model() -> None:
    with pytest.raises(RubricConfigurationError, match="model"):
        RubricConfiguration(model=None)  # type: ignore[arg-type]
    with pytest.raises(RubricConfigurationError, match="model"):
        RubricConfiguration(model="grader")  # type: ignore[arg-type]


def test_rubric_requires_the_beta_gate(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model([AIMessage(content="unused")])
    grader = make_sequence_model([AIMessage(content="grade")])

    with pytest.raises(RubricConfigurationError, match="allow_experimental"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor),
                control_default_subagent=False,
                rubric=RubricConfiguration(model=grader),
            )
        )


def test_rubric_is_assembled_and_reported(
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
    grader = make_sequence_model([AIMessage(content="grade")])

    with pytest.warns(LangChainBetaWarning, match="beta"):
        assembly = build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor),
                control_default_subagent=False,
                rubric=RubricConfiguration(model=grader, max_iterations=2),
                allow_experimental_rubric=True,
            )
        )

    middleware_types = {type(item).__name__ for item in calls[0]["middleware"]}
    assert RubricMiddleware.__name__ in middleware_types
    assert assembly.report.rubric.enabled is True
    assert assembly.report.rubric.max_iterations == 2
    assert assembly.report.rubric.model_source.startswith("injected:")
    assert "rubric" in assembly.report.experimental_features
    assert any("rubric" in warning for warning in assembly.report.warnings)


def _discard_assembly(**kwargs: Any) -> object:
    return object()


def test_native_rubric_middleware_requires_the_beta_gate(
    monkeypatch: pytest.MonkeyPatch,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    monkeypatch.setattr(
        "spawn_join_agent_deepagents.supervisor._create_deep_agent",
        _discard_assembly,
    )
    supervisor = make_sequence_model([AIMessage(content="unused")])
    grader = make_sequence_model([AIMessage(content="grade")])
    native = RubricMiddleware(model=grader)

    with pytest.raises(RubricConfigurationError, match="allow_experimental"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor),
                control_default_subagent=False,
                middleware=MiddlewareConfiguration(supervisor=(native,)),
            )
        )


def test_native_rubric_middleware_is_reported(
    monkeypatch: pytest.MonkeyPatch,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    monkeypatch.setattr(
        "spawn_join_agent_deepagents.supervisor._create_deep_agent",
        _discard_assembly,
    )
    supervisor = make_sequence_model([AIMessage(content="unused")])
    grader = make_sequence_model([AIMessage(content="grade")])
    native = RubricMiddleware(model=grader)

    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor),
            control_default_subagent=False,
            middleware=MiddlewareConfiguration(supervisor=(native,)),
            allow_experimental_rubric=True,
        )
    )

    assert assembly.report.rubric.enabled is True
    assert assembly.report.rubric.model_source == "host_middleware"
    assert "rubric" in assembly.report.experimental_features


def test_native_and_configured_rubric_cannot_be_combined(
    monkeypatch: pytest.MonkeyPatch,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    monkeypatch.setattr(
        "spawn_join_agent_deepagents.supervisor._create_deep_agent",
        _discard_assembly,
    )
    supervisor = make_sequence_model([AIMessage(content="unused")])
    grader = make_sequence_model([AIMessage(content="grade")])
    native = RubricMiddleware(model=grader)

    with pytest.raises(RubricConfigurationError, match="not both"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor),
                control_default_subagent=False,
                rubric=RubricConfiguration(model=grader),
                middleware=MiddlewareConfiguration(supervisor=(native,)),
                allow_experimental_rubric=True,
            )
        )
