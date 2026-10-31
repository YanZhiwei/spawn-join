"""Tests for adapter configuration and pre-call validation."""

from typing import cast

import pytest

from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    ChannelConfig,
    ChatCompletionsOptions,
    ConfigurationError,
    ProtocolKind,
    ProtocolOptions,
    ResponsesOptions,
)
from spawn_join_llm_provider_langchain.config import (
    ChatModelConfig,
    validate_api_key,
    validate_options,
    validate_request,
)


def _channel(
    protocol: ProtocolKind = ProtocolKind.CHAT_COMPLETIONS,
) -> ChannelConfig:
    return ChannelConfig(
        name="test-channel",
        protocol=protocol,
        endpoint="https://api.example.com/v1",
        credential_ref="test-credential",
        timeout_seconds=30.0,
    )


def test_chat_model_config_accepts_valid_values() -> None:
    config = ChatModelConfig(channel=_channel(), model="example-model")
    assert config.model == "example-model"
    assert config.max_retries == 0


@pytest.mark.parametrize("model", ["", " model", "model ", "model\n"])
def test_chat_model_config_rejects_invalid_model_names(model: str) -> None:
    with pytest.raises(ConfigurationError):
        ChatModelConfig(channel=_channel(), model=model)


def test_chat_model_config_rejects_negative_retries() -> None:
    with pytest.raises(ConfigurationError):
        ChatModelConfig(
            channel=_channel(),
            model="example-model",
            max_retries=-1,
        )


@pytest.mark.parametrize("api_key", ["", " key", "key ", "key\n"])
def test_validate_api_key_rejects_empty_or_padded_values(api_key: str) -> None:
    with pytest.raises(ConfigurationError):
        validate_api_key(api_key)


def test_validate_api_key_accepts_a_normal_value() -> None:
    validate_api_key("sk-test-secret")


@pytest.mark.parametrize(
    ("protocol", "options"),
    [
        (ProtocolKind.CHAT_COMPLETIONS, ResponsesOptions()),
        (ProtocolKind.CHAT_COMPLETIONS, AnthropicMessagesOptions()),
        (ProtocolKind.RESPONSES, ChatCompletionsOptions()),
        (ProtocolKind.RESPONSES, AnthropicMessagesOptions()),
        (ProtocolKind.ANTHROPIC_MESSAGES, ChatCompletionsOptions()),
        (ProtocolKind.ANTHROPIC_MESSAGES, ResponsesOptions()),
    ],
)
def test_validate_options_rejects_protocol_mismatches(
    protocol: ProtocolKind,
    options: object,
) -> None:
    with pytest.raises(ConfigurationError):
        validate_options(protocol, cast(ProtocolOptions, options))


@pytest.mark.parametrize(
    ("protocol", "options"),
    [
        (ProtocolKind.CHAT_COMPLETIONS, ChatCompletionsOptions()),
        (ProtocolKind.RESPONSES, ResponsesOptions()),
        (ProtocolKind.ANTHROPIC_MESSAGES, AnthropicMessagesOptions()),
    ],
)
def test_validate_options_accepts_matching_options(
    protocol: ProtocolKind,
    options: object,
) -> None:
    validate_options(protocol, cast(ProtocolOptions, options))


def test_validate_options_accepts_none() -> None:
    validate_options(ProtocolKind.CHAT_COMPLETIONS, None)


def test_validate_options_handles_plain_string_protocol() -> None:
    with pytest.raises(ConfigurationError):
        validate_options(
            cast(ProtocolKind, "chat_completions"),
            ResponsesOptions(),
        )


def test_validate_request_accepts_a_valid_request() -> None:
    validate_request(
        ChatModelConfig(channel=_channel(), model="example-model"),
        api_key="sk-test-secret",
        options=ChatCompletionsOptions(temperature=0.2),
    )


def test_invalid_channel_config_propagates() -> None:
    with pytest.raises(ConfigurationError):
        ChannelConfig(
            name="test-channel",
            protocol=ProtocolKind.CHAT_COMPLETIONS,
            endpoint="not-a-url",
            credential_ref="test-credential",
        )
