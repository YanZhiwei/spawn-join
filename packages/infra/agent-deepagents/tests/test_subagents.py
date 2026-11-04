"""Contracts for declarative and compiled subagent definitions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import fields
from typing import Any

import pytest
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableLambda
from spawn_join_agent_deepagents.errors import (
    MiddlewareConfigurationError,
    SubagentConfigurationError,
)
from spawn_join_agent_deepagents.models import ModelPurpose
from spawn_join_agent_deepagents.subagents import (
    CompiledSubAgentDefinition,
    SubAgentDefinition,
    SubAgentMode,
    validate_experimental_fork,
    validate_unique_subagent_names,
)


def _identity(value: Any) -> Any:
    return value


class _MarkerMiddleware(AgentMiddleware[Any, Any, Any]):
    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        return self._name


def _compiled(
    name: str = "compiled",
    *,
    mode: SubAgentMode = SubAgentMode.ISOLATED,
) -> CompiledSubAgentDefinition:
    return CompiledSubAgentDefinition(
        name=name,
        description="A compiled worker.",
        runnable=RunnableLambda(_identity),
        mode=mode,
    )


def test_declarative_defaults_preserve_tool_inheritance() -> None:
    definition = SubAgentDefinition(name="researcher", description="Research.")

    assert definition.tools is None
    assert definition.middleware == ()
    assert definition.model_purpose == ModelPurpose.WORKER
    assert definition.mode == SubAgentMode.ISOLATED


def test_explicit_empty_tools_are_not_treated_as_inheritance() -> None:
    definition = SubAgentDefinition(
        name="researcher",
        description="Research.",
        tools=(),
    )

    assert definition.tools == ()


def test_blank_name_and_description_are_rejected() -> None:
    with pytest.raises(SubagentConfigurationError, match="name"):
        SubAgentDefinition(name="  ", description="Research.")

    with pytest.raises(SubagentConfigurationError, match="description"):
        SubAgentDefinition(name="researcher", description="  ")


def test_duplicate_names_across_forms_are_rejected() -> None:
    declarative = SubAgentDefinition(name="worker", description="Declarative.")
    compiled = _compiled("worker")

    with pytest.raises(SubagentConfigurationError, match="duplicate"):
        validate_unique_subagent_names((declarative, compiled))


def test_fork_requires_explicit_opt_in() -> None:
    definition = SubAgentDefinition(
        name="forked",
        description="Forked worker.",
        mode=SubAgentMode.FORK,
    )

    with pytest.raises(SubagentConfigurationError, match="allow_experimental_fork"):
        validate_experimental_fork(
            (definition,),
            allow_experimental_fork=False,
        )

    validate_experimental_fork((definition,), allow_experimental_fork=True)


def test_fork_rejects_skills() -> None:
    with pytest.raises(SubagentConfigurationError, match="skills"):
        SubAgentDefinition(
            name="forked",
            description="Forked worker.",
            mode=SubAgentMode.FORK,
            skills=("skill",),
        )


def test_compiled_definition_does_not_expose_injectable_fields() -> None:
    field_names = {field.name for field in fields(CompiledSubAgentDefinition)}

    assert "model" not in field_names
    assert "middleware" not in field_names
    assert "tools" not in field_names
    assert "interrupt_on" not in field_names


def test_compiled_fork_also_requires_opt_in() -> None:
    definition = _compiled("compiled-fork", mode=SubAgentMode.FORK)

    with pytest.raises(SubagentConfigurationError, match="allow_experimental_fork"):
        validate_experimental_fork(
            (definition,),
            allow_experimental_fork=False,
        )

    validate_experimental_fork((definition,), allow_experimental_fork=True)


def test_definition_middleware_reserved_name_is_rejected() -> None:
    with pytest.raises(MiddlewareConfigurationError, match="reserved"):
        SubAgentDefinition(
            name="researcher",
            description="Research.",
            middleware=(_MarkerMiddleware("SummarizationMiddleware"),),
        )


def test_definition_middleware_duplicate_names_are_rejected() -> None:
    with pytest.raises(MiddlewareConfigurationError, match="duplicate"):
        SubAgentDefinition(
            name="researcher",
            description="Research.",
            middleware=(
                _MarkerMiddleware("audit"),
                _MarkerMiddleware("audit"),
            ),
        )


def test_explicit_model_and_purpose_are_preserved(
    make_fake_model: Callable[[str], BaseChatModel],
) -> None:
    model: BaseChatModel = make_fake_model("worker")
    definition = SubAgentDefinition(
        name="researcher",
        description="Research.",
        model=model,
        model_purpose=ModelPurpose.SUPERVISOR,
        system_prompt="Be precise.",
        skills=("research",),
    )

    assert definition.model is model
    assert definition.model_purpose == ModelPurpose.SUPERVISOR
    assert definition.system_prompt == "Be precise."
    assert definition.skills == ("research",)
