"""Tests for the exact public surface of the protocol package."""

import sys

import spawn_join_llm_provider as provider

EXPECTED_EXPORTS = [
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
    "EndpointConfig",
    "LLMProviderError",
    "ModelInfo",
    "ModelPage",
    "PingResult",
    "ProtocolKind",
    "ProtocolOptions",
    "ResponsesOptions",
    "UnsupportedChannelOperationError",
]

FORBIDDEN_NAMES = [
    "ChatRequest",
    "ChatResponse",
    "ContentBlock",
    "FinishReason",
    "LLMProvider",
    "Message",
    "ModelCapabilities",
    "NamedToolChoice",
    "OpaqueBlock",
    "ReasoningBlock",
    "ReasoningDelta",
    "Role",
    "StreamCompleted",
    "StreamEvent",
    "TextBlock",
    "TextDelta",
    "ToolCallBlock",
    "ToolCallDelta",
    "ToolChoice",
    "ToolDefinition",
    "ToolResultBlock",
    "Usage",
]


def test_exact_public_exports() -> None:
    assert provider.__all__ == EXPECTED_EXPORTS


def test_forbidden_custom_contracts_are_absent() -> None:
    for name in FORBIDDEN_NAMES:
        assert name not in provider.__all__
        assert not hasattr(provider, name)


def test_import_does_not_load_langchain() -> None:
    assert "langchain_core" not in sys.modules
