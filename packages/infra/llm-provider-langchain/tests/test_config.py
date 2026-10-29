"""Tests for provider configuration and credential references."""

import pytest

from spawn_join_llm_provider import ConfigurationError, ProtocolKind
from spawn_join_llm_provider_langchain.config import (
    AnthropicMessagesConfig,
    ChatCompletionsConfig,
    ProviderConfig,
    ResponsesConfig,
)
from spawn_join_llm_provider_langchain.credentials import resolve_credential


def test_protocol_configs_select_explicit_protocols() -> None:
    chat = ChatCompletionsConfig(model="m", credential_ref="KEY")
    responses = ResponsesConfig(model="m", credential_ref="KEY")
    anthropic = AnthropicMessagesConfig(model="m", credential_ref="KEY")

    assert chat.protocol == ProtocolKind.CHAT_COMPLETIONS
    assert responses.protocol == ProtocolKind.RESPONSES
    assert anthropic.protocol == ProtocolKind.ANTHROPIC_MESSAGES


def test_provider_config_repr_contains_reference_not_secret() -> None:
    config = ChatCompletionsConfig(
        model="m",
        credential_ref="TEST_API_KEY",
        base_url="https://example.com/v1",
    )
    rendered = repr(config)

    assert "TEST_API_KEY" in rendered
    assert "secret-value" not in rendered


@pytest.mark.parametrize(
    "kwargs",
    [
        {"model": " ", "credential_ref": "KEY"},
        {"model": "m", "credential_ref": " "},
        {"model": "m", "credential_ref": "KEY", "timeout_seconds": 0},
        {"model": "m", "credential_ref": "KEY", "timeout_seconds": float("nan")},
        {"model": "m", "credential_ref": "KEY", "base_url": "ftp://example.com"},
        {
            "model": "m",
            "credential_ref": "KEY",
            "base_url": "https://user:pass@example.com",
        },
    ],
)
def test_invalid_provider_config_raises_domain_error(
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ConfigurationError):
        ProviderConfig(**kwargs)  # type: ignore[arg-type]


def test_resolve_credential_reads_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_API_KEY", "secret-value")
    assert resolve_credential("TEST_API_KEY") == "secret-value"


def test_resolve_credential_rejects_missing_or_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TEST_API_KEY", raising=False)
    with pytest.raises(ConfigurationError):
        resolve_credential("TEST_API_KEY")

    monkeypatch.setenv("TEST_API_KEY", "   ")
    with pytest.raises(ConfigurationError):
        resolve_credential("TEST_API_KEY")
