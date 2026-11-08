"""Rubric configuration, beta gating, and assembly reporting."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from deepagents import RubricMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from spawn_join_agent_deepagents.errors import RubricConfigurationError
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
