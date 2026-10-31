"""Tests for the adapter's exact public surface."""

import spawn_join_llm_provider_langchain as adapter

EXPECTED_EXPORTS = ["ChatModelConfig", "create_chat_model"]

FORBIDDEN_NAMES = [
    "ChatRequest",
    "ChatResponse",
    "ContentBlock",
    "LLMProvider",
    "Message",
    "Provider",
    "ReasoningBlock",
    "StreamEvent",
    "TextBlock",
    "ToolCallBlock",
    "ToolResultBlock",
    "bind_options",
    "map_options",
]


def test_exact_public_exports() -> None:
    assert adapter.__all__ == EXPECTED_EXPORTS


def test_forbidden_custom_contracts_are_absent() -> None:
    for name in FORBIDDEN_NAMES:
        assert name not in adapter.__all__
        assert not hasattr(adapter, name)


def test_no_message_or_conversion_public_attributes() -> None:
    for name in dir(adapter):
        lowered = name.lower()
        assert "message" not in lowered
        assert "convert" not in lowered
