"""Harness and provider profile registration contracts."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from deepagents import HarnessProfile, ProviderProfile
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from spawn_join_agent_deepagents.errors import ProfileConfigurationError
from spawn_join_agent_deepagents.models import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
)
from spawn_join_agent_deepagents.profiles import (
    HarnessProfileBinding,
    ProfilesConfiguration,
    ProviderProfileBinding,
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


def _profiles() -> ProfilesConfiguration:
    return ProfilesConfiguration(
        harness=(
            HarnessProfileBinding(
                "example:model",
                HarnessProfile(system_prompt_suffix="Be concise."),
            ),
        ),
        providers=(ProviderProfileBinding("example", ProviderProfile()),),
    )


def test_blank_profile_key_is_rejected() -> None:
    with pytest.raises(ProfileConfigurationError, match="key"):
        HarnessProfileBinding("  ", HarnessProfile())


def test_duplicate_harness_keys_are_rejected() -> None:
    configuration = ProfilesConfiguration(
        harness=(
            HarnessProfileBinding("example:model", HarnessProfile()),
            HarnessProfileBinding("example:model", HarnessProfile()),
        )
    )

    with pytest.raises(ProfileConfigurationError, match="duplicate"):
        configuration.validate()


def test_reserved_middleware_cannot_be_excluded() -> None:
    configuration = ProfilesConfiguration(
        harness=(
            HarnessProfileBinding(
                "example:model",
                HarnessProfile(
                    excluded_middleware=frozenset({"spawn_join_delegation_policy"})
                ),
            ),
        )
    )

    with pytest.raises(ProfileConfigurationError, match="reserved"):
        configuration.validate()


def test_profiles_require_the_experimental_gate(
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

    with pytest.raises(ProfileConfigurationError, match="allow_experimental"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor),
                control_default_subagent=False,
                profiles=_profiles(),
            )
        )

    assert calls == []


def test_profiles_are_registered_before_assembly(
    monkeypatch: pytest.MonkeyPatch,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    harness_calls: list[tuple[str, object]] = []
    provider_calls: list[tuple[str, object]] = []
    create_calls: list[dict[str, Any]] = []
    order: list[str] = []

    def record_harness(key: str, profile: object) -> None:
        harness_calls.append((key, profile))
        order.append("harness")

    def record_provider(key: str, profile: object) -> None:
        provider_calls.append((key, profile))
        order.append("provider")

    monkeypatch.setattr(
        "spawn_join_agent_deepagents.profiles.register_harness_profile",
        record_harness,
    )
    monkeypatch.setattr(
        "spawn_join_agent_deepagents.profiles.register_provider_profile",
        record_provider,
    )

    def fake_create(**kwargs: Any) -> object:
        create_calls.append(kwargs)
        order.append("create")
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
            profiles=_profiles(),
            allow_experimental_profiles=True,
        )
    )

    assert [key for key, _ in harness_calls] == ["example:model"]
    assert [key for key, _ in provider_calls] == ["example"]
    assert order == ["harness", "provider", "create"]
    assert create_calls
    assert assembly.report.profiles.harness_keys == ("example:model",)
    assert assembly.report.profiles.provider_keys == ("example",)
    assert "harness_profiles" in assembly.report.experimental_features


def test_registration_failure_preserves_the_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(key: str, profile: object) -> None:
        raise RuntimeError("upstream failure")

    monkeypatch.setattr(
        "spawn_join_agent_deepagents.profiles.register_harness_profile",
        fail,
    )

    with pytest.raises(ProfileConfigurationError) as caught:
        ProfilesConfiguration(
            harness=(HarnessProfileBinding("example:model", HarnessProfile()),)
        ).apply()

    assert isinstance(caught.value.__cause__, RuntimeError)


def test_package_managed_memory_cannot_be_excluded_by_a_profile(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    from spawn_join_agent_deepagents.context_sources import MemoryConfiguration

    supervisor = make_sequence_model([AIMessage(content="unused")])
    profiles = ProfilesConfiguration(
        harness=(
            HarnessProfileBinding(
                "example:model",
                HarnessProfile(excluded_middleware=frozenset({"MemoryMiddleware"})),
            ),
        )
    )

    with pytest.raises(ProfileConfigurationError, match="MemoryMiddleware"):
        build_supervisor(
            SupervisorSpec(
                models=_bindings(supervisor),
                control_default_subagent=False,
                memory=MemoryConfiguration(
                    sources=("AGENTS.md",),
                    add_cache_control=False,
                ),
                profiles=profiles,
                allow_experimental_profiles=True,
            )
        )
