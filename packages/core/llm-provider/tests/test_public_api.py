"""Tests for the exact public surface of the protocol package."""

import sys

import spawn_join_llm_provider as provider

EXPECTED_EXPORTS = [
    "AnthropicMessagesOptions",
    "AnthropicThinking",
    "AnthropicThinkingAdaptive",
    "AnthropicThinkingBudget",
    "AnthropicThinkingDisabled",
    "Channel",
    "ChannelConfig",
    "ChannelError",
    "ChannelResponseError",
    "ChannelStatus",
    "ChannelUnavailableError",
    "ChatCompletionsOptions",
    "ConfigurationError",
    "DuplicateKeyError",
    "EndpointConfig",
    "LLMProviderError",
    "Modality",
    "ModelCapabilitiesMetadata",
    "ModelChannel",
    "ModelInfo",
    "ModelLimits",
    "ModelMetadata",
    "ModelMetadataDocument",
    "ModelMetadataOverride",
    "ModelModalities",
    "ModelPage",
    "ModelPriceRate",
    "ModelPriceTier",
    "ModelPricing",
    "ModelReasoning",
    "ModelReasoningBudget",
    "ModelSource",
    "ModelSourceRef",
    "ModelStatus",
    "ModelType",
    "PingResult",
    "PriceDirection",
    "PriceUnit",
    "ProtocolKind",
    "ProtocolOptions",
    "ResponsesOptions",
    "UnsupportedChannelOperationError",
    "apply_metadata_override",
    "decode_metadata_document",
    "parse_model_metadata_document",
    "parse_model_metadata_override",
    "reject_duplicate_keys",
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
