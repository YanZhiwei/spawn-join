"""Tests for protocol-native option contracts."""

from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    AnthropicThinkingAdaptive,
    AnthropicThinkingBudget,
    ChatCompletionsOptions,
    ConfigurationError,
    ProtocolKind,
    ResponsesOptions,
)
from spawn_join_llm_provider.options import ReasoningEffort, Truncation


def test_protocol_kind_values() -> None:
    assert ProtocolKind.CHAT_COMPLETIONS.value == "chat_completions"
    assert ProtocolKind.RESPONSES.value == "responses"
    assert ProtocolKind.ANTHROPIC_MESSAGES.value == "anthropic_messages"


def test_chat_completions_defaults() -> None:
    options = ChatCompletionsOptions()
    assert options.temperature is None
    assert options.max_output_tokens is None
    assert options.top_p is None
    assert options.stop is None
    assert options.seed is None


def test_options_are_immutable() -> None:
    options = ChatCompletionsOptions(temperature=0.2)
    attribute = "temperature"
    with pytest.raises(FrozenInstanceError):
        setattr(options, attribute, 0.5)


def test_chat_completions_accepts_valid_values() -> None:
    options = ChatCompletionsOptions(
        temperature=2.0,
        max_output_tokens=1024,
        top_p=1.0,
        stop=("\n\n", "END"),
        seed=42,
    )
    assert options.stop == ("\n\n", "END")
    assert options.seed == 42


@pytest.mark.parametrize("temperature", [-0.1, 2.1, float("nan"), float("inf")])
def test_chat_completions_rejects_invalid_temperature(
    temperature: float,
) -> None:
    with pytest.raises(ConfigurationError):
        ChatCompletionsOptions(temperature=temperature)


@pytest.mark.parametrize("max_output_tokens", [0, -1])
def test_chat_completions_rejects_non_positive_max_tokens(
    max_output_tokens: int,
) -> None:
    with pytest.raises(ConfigurationError):
        ChatCompletionsOptions(max_output_tokens=max_output_tokens)


@pytest.mark.parametrize("top_p", [-0.1, 1.1])
def test_chat_completions_rejects_invalid_top_p(top_p: float) -> None:
    with pytest.raises(ConfigurationError):
        ChatCompletionsOptions(top_p=top_p)


def test_empty_stop_tuple_normalizes_to_none() -> None:
    assert ChatCompletionsOptions(stop=()).stop is None


def test_stop_values_must_not_be_empty() -> None:
    with pytest.raises(ConfigurationError):
        ChatCompletionsOptions(stop=("",))


def test_chat_completions_allows_whitespace_stop_sequences() -> None:
    options = ChatCompletionsOptions(stop=("\n\n", "   ", "\t"))
    assert options.stop == ("\n\n", "   ", "\t")


def test_responses_defaults_and_store_false() -> None:
    options = ResponsesOptions(store=False)
    assert options.store is False
    assert options.reasoning_effort is None
    assert options.truncation is None


def test_responses_accepts_valid_reasoning_and_truncation() -> None:
    options = ResponsesOptions(
        reasoning_effort="high",
        truncation="disabled",
    )
    assert options.reasoning_effort == "high"
    assert options.truncation == "disabled"


def test_responses_rejects_invalid_reasoning_effort() -> None:
    with pytest.raises(ConfigurationError):
        ResponsesOptions(
            reasoning_effort=cast(ReasoningEffort, "invalid"),
        )


def test_responses_rejects_invalid_truncation() -> None:
    with pytest.raises(ConfigurationError):
        ResponsesOptions(truncation=cast(Truncation, "invalid"))


@pytest.mark.parametrize("temperature", [0.0, 2.0])
def test_responses_accepts_temperature_boundaries(temperature: float) -> None:
    assert ResponsesOptions(temperature=temperature).temperature == temperature


@pytest.mark.parametrize("top_p", [0.0, 1.0])
def test_responses_accepts_top_p_boundaries(top_p: float) -> None:
    assert ResponsesOptions(top_p=top_p).top_p == top_p


def test_responses_accepts_minimum_max_output_tokens() -> None:
    assert ResponsesOptions(max_output_tokens=1).max_output_tokens == 1


@pytest.mark.parametrize("temperature", [-0.1, 2.1])
def test_responses_rejects_invalid_temperature(temperature: float) -> None:
    with pytest.raises(ConfigurationError):
        ResponsesOptions(temperature=temperature)


@pytest.mark.parametrize("top_p", [-0.1, 1.1])
def test_responses_rejects_invalid_top_p(top_p: float) -> None:
    with pytest.raises(ConfigurationError):
        ResponsesOptions(top_p=top_p)


@pytest.mark.parametrize("max_output_tokens", [0, -1])
def test_responses_rejects_non_positive_max_tokens(
    max_output_tokens: int,
) -> None:
    with pytest.raises(ConfigurationError):
        ResponsesOptions(max_output_tokens=max_output_tokens)


def test_anthropic_defaults() -> None:
    options = AnthropicMessagesOptions()
    assert options.thinking is None
    assert options.stop_sequences is None


def test_anthropic_accepts_budget_thinking() -> None:
    options = AnthropicMessagesOptions(
        max_output_tokens=4096,
        thinking=AnthropicThinkingBudget(budget_tokens=2048),
    )
    assert isinstance(options.thinking, AnthropicThinkingBudget)
    assert options.thinking.budget_tokens == 2048


def test_anthropic_accepts_adaptive_thinking() -> None:
    options = AnthropicMessagesOptions(
        thinking=AnthropicThinkingAdaptive(),
    )
    assert isinstance(options.thinking, AnthropicThinkingAdaptive)


@pytest.mark.parametrize("temperature", [0.0, 1.0])
def test_anthropic_accepts_temperature_boundaries(temperature: float) -> None:
    assert AnthropicMessagesOptions(temperature=temperature).temperature == temperature


@pytest.mark.parametrize("top_p", [0.0, 1.0])
def test_anthropic_accepts_top_p_boundaries(top_p: float) -> None:
    assert AnthropicMessagesOptions(top_p=top_p).top_p == top_p


def test_anthropic_accepts_minimum_max_output_tokens() -> None:
    assert AnthropicMessagesOptions(max_output_tokens=1).max_output_tokens == 1


@pytest.mark.parametrize("temperature", [-0.1, 1.1])
def test_anthropic_rejects_invalid_temperature(temperature: float) -> None:
    with pytest.raises(ConfigurationError):
        AnthropicMessagesOptions(temperature=temperature)


@pytest.mark.parametrize("top_p", [-0.1, 1.1])
def test_anthropic_rejects_invalid_top_p(top_p: float) -> None:
    with pytest.raises(ConfigurationError):
        AnthropicMessagesOptions(top_p=top_p)


@pytest.mark.parametrize("max_output_tokens", [0, -1])
def test_anthropic_rejects_non_positive_max_tokens(
    max_output_tokens: int,
) -> None:
    with pytest.raises(ConfigurationError):
        AnthropicMessagesOptions(max_output_tokens=max_output_tokens)


def test_anthropic_rejects_non_positive_top_k() -> None:
    with pytest.raises(ConfigurationError):
        AnthropicMessagesOptions(top_k=0)


def test_anthropic_rejects_empty_stop_sequence() -> None:
    with pytest.raises(ConfigurationError):
        AnthropicMessagesOptions(stop_sequences=("",))


def test_anthropic_allows_whitespace_stop_sequences() -> None:
    options = AnthropicMessagesOptions(stop_sequences=("\n\n", "   "))
    assert options.stop_sequences == ("\n\n", "   ")


def test_anthropic_empty_stop_tuple_normalizes_to_none() -> None:
    assert AnthropicMessagesOptions(stop_sequences=()).stop_sequences is None


def test_thinking_budget_requires_max_output_tokens() -> None:
    with pytest.raises(ConfigurationError):
        AnthropicMessagesOptions(
            thinking=AnthropicThinkingBudget(budget_tokens=2048),
        )


def test_thinking_budget_must_be_less_than_max_output_tokens() -> None:
    with pytest.raises(ConfigurationError):
        AnthropicMessagesOptions(
            max_output_tokens=2048,
            thinking=AnthropicThinkingBudget(budget_tokens=2048),
        )


def test_thinking_budget_minimum() -> None:
    with pytest.raises(ConfigurationError):
        AnthropicThinkingBudget(budget_tokens=1023)
