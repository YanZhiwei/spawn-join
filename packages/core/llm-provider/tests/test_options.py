"""Contract tests for protocol-native options."""

from dataclasses import FrozenInstanceError

import pytest

from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    AnthropicThinkingAdaptive,
    AnthropicThinkingBudget,
    ChatCompletionsOptions,
    ProtocolKind,
    ResponsesOptions,
)


def test_protocol_kind_values() -> None:
    assert ProtocolKind.CHAT_COMPLETIONS.value == "chat_completions"
    assert ProtocolKind.RESPONSES.value == "responses"
    assert ProtocolKind.ANTHROPIC_MESSAGES.value == "anthropic_messages"


def test_chat_completions_options_defaults() -> None:
    options = ChatCompletionsOptions()
    assert options.stop == ()
    assert options.reasoning_effort is None


def test_responses_options_default_store_is_false() -> None:
    options = ResponsesOptions()
    assert options.store is False
    assert options.previous_response_id is None
    assert options.truncation is None
    assert options.include == ()


def test_anthropic_thinking_variants() -> None:
    budget = AnthropicThinkingBudget(budget_tokens=2048)
    adaptive = AnthropicThinkingAdaptive(display="summarized")
    options = AnthropicMessagesOptions(thinking=budget, top_k=5)
    other = AnthropicMessagesOptions(thinking=adaptive)

    assert budget.budget_tokens == 2048
    assert adaptive.display == "summarized"
    assert options.thinking == budget
    assert other.thinking == adaptive


def test_options_are_frozen() -> None:
    options = ResponsesOptions()
    with pytest.raises(FrozenInstanceError):
        options.store = True  # type: ignore[misc]
