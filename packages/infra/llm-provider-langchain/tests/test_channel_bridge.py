"""Channel-to-model configuration bridge tests."""

from spawn_join_llm_provider import ChannelConfig, ProtocolKind
from spawn_join_llm_provider_langchain import ChatModelConfig


def test_from_channel_preserves_connection_fields() -> None:
    channel = ChannelConfig(
        name="primary",
        protocol=ProtocolKind.ANTHROPIC_MESSAGES,
        endpoint="https://api.example.com",
        credential_ref="ANTHROPIC_API_KEY",
        timeout_seconds=42.0,
    )

    config = ChatModelConfig.from_channel(
        channel,
        model="claude-test",
        max_retries=2,
    )

    assert config.protocol is ProtocolKind.ANTHROPIC_MESSAGES
    assert config.endpoint == "https://api.example.com"
    assert config.timeout_seconds == 42.0
    assert config.model == "claude-test"
    assert config.max_retries == 2


def test_from_channel_uses_safe_defaults() -> None:
    channel = ChannelConfig(
        name="primary",
        protocol=ProtocolKind.CHAT_COMPLETIONS,
        endpoint="https://api.example.com/v1",
        credential_ref="OPENAI_API_KEY",
    )

    config = ChatModelConfig.from_channel(channel, model="gpt-test")

    assert config.max_retries == 0
    assert config.timeout_seconds == 30.0
