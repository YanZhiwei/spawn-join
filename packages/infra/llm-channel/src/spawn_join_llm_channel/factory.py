"""Create a concrete channel transport from explicit protocol configuration."""

from collections.abc import Mapping
from typing import TypeAlias

from spawn_join_llm_provider import ChannelConfig, ConfigurationError, ProtocolKind

from ._anthropic import AnthropicChannel
from ._openai import OpenAIChannel

ChatChannel: TypeAlias = OpenAIChannel | AnthropicChannel


def create_channel(
    config: ChannelConfig,
    *,
    api_key: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> ChatChannel:
    """Create the channel implementation selected by the explicit protocol."""
    match config.protocol:
        case ProtocolKind.CHAT_COMPLETIONS | ProtocolKind.RESPONSES:
            return OpenAIChannel(config, api_key=api_key, environ=environ)
        case ProtocolKind.ANTHROPIC_MESSAGES:
            return AnthropicChannel(config, api_key=api_key, environ=environ)
        case _:
            raise ConfigurationError(f"Unsupported protocol: {config.protocol}")
