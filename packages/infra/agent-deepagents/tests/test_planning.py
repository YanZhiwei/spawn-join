"""Contracts for the opt-in planning configuration."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest
import spawn_join_agent_deepagents as package
import spawn_join_agent_deepagents.planning as planning_module
from spawn_join_agent_deepagents.errors import MiddlewareConfigurationError
from spawn_join_agent_deepagents.planning import PlanningConfiguration


def test_defaults_use_langchain_defaults() -> None:
    configuration = PlanningConfiguration()

    assert configuration.system_prompt is None
    assert configuration.tool_description is None


def test_custom_values_are_preserved() -> None:
    configuration = PlanningConfiguration(
        system_prompt="Plan before acting.",
        tool_description="Track multi-step work.",
    )

    assert configuration.system_prompt == "Plan before acting."
    assert configuration.tool_description == "Track multi-step work."


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("system_prompt", ""),
        ("system_prompt", "   "),
        ("tool_description", ""),
        ("tool_description", "\n\t"),
    ],
)
def test_blank_values_are_rejected(field: str, value: str) -> None:
    with pytest.raises(MiddlewareConfigurationError, match=rf"planning\.{field}"):
        cast(Any, PlanningConfiguration)(**{field: value})


@pytest.mark.parametrize("field", ["system_prompt", "tool_description"])
def test_non_string_values_are_rejected(field: str) -> None:
    with pytest.raises(MiddlewareConfigurationError, match=rf"planning\.{field}"):
        cast(Any, PlanningConfiguration)(**{field: cast(Any, 1)})


def test_configuration_is_frozen_and_slotted() -> None:
    configuration = PlanningConfiguration()

    with pytest.raises(FrozenInstanceError):
        cast(Any, configuration).system_prompt = "changed"
    assert not hasattr(configuration, "__dict__")


def test_package_and_module_export_the_same_type() -> None:
    assert package.PlanningConfiguration is PlanningConfiguration
    assert planning_module.PlanningConfiguration is PlanningConfiguration
