"""Framework-independent LLM channel contracts, options and errors."""

from .channels import (
    Channel,
    ChannelConfig,
    ChannelStatus,
    ModelInfo,
    ModelPage,
    PingResult,
)
from .errors import (
    ChannelError,
    ChannelResponseError,
    ChannelUnavailableError,
    ConfigurationError,
    LLMProviderError,
    UnsupportedChannelOperationError,
)
from .options import (
    AnthropicMessagesOptions,
    AnthropicThinking,
    AnthropicThinkingAdaptive,
    AnthropicThinkingBudget,
    ChatCompletionsOptions,
    ProtocolKind,
    ProtocolOptions,
    ResponsesOptions,
)

__all__ = [
    "AnthropicMessagesOptions",
    "AnthropicThinking",
    "AnthropicThinkingAdaptive",
    "AnthropicThinkingBudget",
    "Channel",
    "ChannelConfig",
    "ChannelError",
    "ChannelResponseError",
    "ChannelStatus",
    "ChannelUnavailableError",
    "ChatCompletionsOptions",
    "ConfigurationError",
    "LLMProviderError",
    "ModelInfo",
    "ModelPage",
    "PingResult",
    "ProtocolKind",
    "ProtocolOptions",
    "ResponsesOptions",
    "UnsupportedChannelOperationError",
]
