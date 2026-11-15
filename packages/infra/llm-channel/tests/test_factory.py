"""Channel factory dispatch tests."""

import pytest
from spawn_join_llm_channel import (
    AnthropicChannel,
    ChatChannel,
    OpenAIChannel,
    create_channel,
)

from spawn_join_llm_provider import ChannelConfig, ConfigurationError, ProtocolKind


def _config(protocol: ProtocolKind) -> ChannelConfig:
    return ChannelConfig(
        name="test",
        protocol=protocol,
        endpoint="https://api.example.com/v1",
        credential_ref="TEST_KEY",
        timeout_seconds=1.0,
    )


@pytest.mark.parametrize(
    "protocol",
    [ProtocolKind.CHAT_COMPLETIONS, ProtocolKind.RESPONSES],
)
def test_create_openai_channel(protocol: ProtocolKind) -> None:
    channel = create_channel(
        _config(protocol),
        environ={"TEST_KEY": "sk-test"},
    )
    assert isinstance(channel, OpenAIChannel)
    assert isinstance(channel, ChatChannel)


def test_create_anthropic_channel() -> None:
    channel = create_channel(
        _config(ProtocolKind.ANTHROPIC_MESSAGES),
        environ={"TEST_KEY": "sk-test"},
    )
    assert isinstance(channel, AnthropicChannel)


def test_explicit_api_key_wins_over_missing_environment() -> None:
    channel = create_channel(
        _config(ProtocolKind.CHAT_COMPLETIONS),
        api_key="sk-explicit",
        environ={},
    )
    assert isinstance(channel, OpenAIChannel)


def test_missing_credential_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="is not set"):
        create_channel(_config(ProtocolKind.CHAT_COMPLETIONS), environ={})
