"""Tests for the adapter's exact public surface."""

import spawn_join_llm_channel as channel

EXPECTED_EXPORTS = [
    "AnthropicChannel",
    "ChatChannel",
    "OpenAIChannel",
    "create_channel",
]


def test_exact_public_exports() -> None:
    assert channel.__all__ == EXPECTED_EXPORTS


def test_forbidden_runtime_contracts_are_absent() -> None:
    for name in ("BaseChatModel", "ChatOpenAI", "ChatAnthropic", "LLMProvider"):
        assert not hasattr(channel, name)
