"""Memory and skills configuration contracts."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from spawn_join_agent_deepagents.context_sources import (
    MemoryConfiguration,
    SkillsConfiguration,
)
from spawn_join_agent_deepagents.errors import (
    ContextConfigurationError,
    MiddlewareConfigurationError,
)
from spawn_join_agent_deepagents.middleware import MiddlewareConfiguration
from spawn_join_agent_deepagents.models import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
)
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


@pytest.mark.parametrize(
    "sources",
    [(), ("  ",), ("a", "a")],
)
def test_memory_rejects_empty_blank_and_duplicate_sources(
    sources: tuple[str, ...],
) -> None:
    with pytest.raises(ContextConfigurationError):
        MemoryConfiguration(sources=sources)


@pytest.mark.parametrize(
    "sources",
    [(), ("  ",), ("a", "a")],
)
def test_skills_reject_empty_blank_and_duplicate_sources(
    sources: tuple[str, ...],
) -> None:
    with pytest.raises(ContextConfigurationError):
        SkillsConfiguration(sources=sources)


def test_string_source_is_not_treated_as_a_sequence() -> None:
    with pytest.raises(ContextConfigurationError, match="not a string"):
        MemoryConfiguration(sources="AGENTS.md")  # type: ignore[arg-type]


def test_default_context_is_forwarded_upstream(
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

    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor),
            control_default_subagent=False,
            memory=MemoryConfiguration(sources=("AGENTS.md",)),
            skills=SkillsConfiguration(sources=("skills",)),
        )
    )

    assert calls[0]["memory"] == ["AGENTS.md"]
    assert calls[0]["skills"] == ["skills"]
    assert assembly.report.context.memory_source_count == 1
    assert assembly.report.context.memory_managed_by == "upstream"
    assert assembly.report.context.skills_source_count == 1
    assert assembly.report.context.skills_managed_by == "upstream"


def test_legacy_sequence_sources_keep_working(
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

    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor),
            control_default_subagent=False,
            memory=("AGENTS.md",),
            skills=("skills",),
        )
    )

    assert calls[0]["memory"] == ["AGENTS.md"]
    assert calls[0]["skills"] == ["skills"]
    assert assembly.report.context.memory_source_count == 1


def test_cache_control_false_is_managed_by_the_package(
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

    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor),
            control_default_subagent=False,
            memory=MemoryConfiguration(
                sources=("AGENTS.md",),
                cache_memory_prefix=False,
            ),
        )
    )

    assert calls[0]["memory"] is None
    names = [item.name for item in calls[0]["middleware"]]
    assert "MemoryMiddleware" in names
    assert assembly.report.context.memory_managed_by == "package"
    assert assembly.report.context.memory_cache_prefix is False


def test_package_managed_memory_rejects_a_user_memory_middleware(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    class MemoryMiddleware(AgentMiddleware[Any, Any, Any]):
        @property
        def name(self) -> str:
            return "MemoryMiddleware"

    supervisor = make_sequence_model([AIMessage(content="unused")])

    with pytest.raises(MiddlewareConfigurationError, match="MemoryMiddleware"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor),
                control_default_subagent=False,
                memory=MemoryConfiguration(
                    sources=("AGENTS.md",),
                    cache_memory_prefix=False,
                ),
                middleware=MiddlewareConfiguration(supervisor=(MemoryMiddleware(),)),
            )
        )
