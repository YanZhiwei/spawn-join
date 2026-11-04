"""Pinned contract checks for the supported DeepAgents minor line."""

from __future__ import annotations

import inspect
from collections.abc import Callable, Mapping
from importlib.metadata import version
from typing import Any, cast

import deepagents
from deepagents import CompiledSubAgent, SubAgent
from deepagents.backends import StateBackend
from deepagents.middleware.subagents import (
    GENERAL_PURPOSE_SUBAGENT,
    TaskToolSchema,
)
from deepagents.middleware.summarization import create_summarization_middleware
from langchain_core.language_models import BaseChatModel
from langgraph.errors import GraphInterrupt


def test_deepagents_version_is_in_the_supported_line() -> None:
    raw = version("deepagents")
    major, minor, patch = (int(part) for part in raw.split(".")[:3])

    assert (major, minor) == (0, 7)
    assert patch >= 32


def test_native_subagent_types_are_importable() -> None:
    assert SubAgent is not None
    assert CompiledSubAgent is not None
    assert issubclass(GraphInterrupt, BaseException)


def test_summarization_middleware_name_is_replaceable(
    make_fake_model: Callable[[str], BaseChatModel],
) -> None:
    middleware = create_summarization_middleware(
        make_fake_model("summary"),
        StateBackend(),
    )

    assert middleware.name == "SummarizationMiddleware"


def test_general_purpose_default_is_available() -> None:
    raw = cast(Mapping[str, object], GENERAL_PURPOSE_SUBAGENT)
    description = raw.get("description")
    system_prompt = raw.get("system_prompt")

    assert raw.get("name") == "general-purpose"
    assert isinstance(description, str) and description
    assert isinstance(system_prompt, str) and system_prompt


def test_task_schema_uses_the_native_delegation_arguments() -> None:
    assert {"description", "subagent_type"} <= set(TaskToolSchema.model_fields)


def test_create_deep_agent_accepts_the_assembly_parameters() -> None:
    create_agent: Any = cast(Any, deepagents).create_deep_agent
    parameters = set(inspect.signature(create_agent).parameters)
    expected = {
        "model",
        "tools",
        "system_prompt",
        "middleware",
        "subagents",
        "backend",
        "checkpointer",
        "store",
        "interrupt_on",
        "state_schema",
        "context_schema",
        "response_format",
        "permissions",
        "skills",
        "memory",
        "cache",
        "name",
        "debug",
    }

    assert expected <= parameters
