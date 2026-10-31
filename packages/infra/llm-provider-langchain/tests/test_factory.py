"""Tests for the LangChain chat model factory."""

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    AnthropicThinkingAdaptive,
    AnthropicThinkingBudget,
    ChatCompletionsOptions,
    ConfigurationError,
    ProtocolKind,
    ResponsesOptions,
)
from spawn_join_llm_provider_langchain.config import ChatModelConfig
from spawn_join_llm_provider_langchain.factory import create_chat_model


def _config(protocol: ProtocolKind) -> ChatModelConfig:
    return ChatModelConfig(
        protocol=protocol,
        endpoint="https://api.example.com/v1",
        model="example-model",
        timeout_seconds=42.0,
    )


def test_chat_completions_factory_maps_options() -> None:
    model = create_chat_model(
        _config(ProtocolKind.CHAT_COMPLETIONS),
        api_key="sk-test-secret",
        options=ChatCompletionsOptions(
            temperature=0.2,
            max_output_tokens=1024,
            top_p=0.9,
            stop=("\n\n", "END"),
            seed=42,
        ),
    )

    assert isinstance(model, ChatOpenAI)
    assert isinstance(model, BaseChatModel)
    assert model.use_responses_api is False
    assert model.model_name == "example-model"
    assert model.openai_api_base == "https://api.example.com/v1"
    assert model.request_timeout == 42.0
    assert model.max_retries == 0
    assert model.temperature == 0.2
    assert model.max_tokens == 1024
    assert model.top_p == 0.9
    assert model.stop == ["\n\n", "END"]
    assert model.seed == 42
    assert isinstance(model.openai_api_key, SecretStr)
    assert model.openai_api_key.get_secret_value() == "sk-test-secret"
    assert "sk-test-secret" not in repr(model)


def test_responses_factory_maps_options() -> None:
    model = create_chat_model(
        _config(ProtocolKind.RESPONSES),
        api_key="sk-test-secret",
        options=ResponsesOptions(
            temperature=0.1,
            max_output_tokens=2048,
            top_p=0.8,
            store=False,
            reasoning_effort="medium",
            truncation="disabled",
        ),
    )

    assert isinstance(model, ChatOpenAI)
    assert model.use_responses_api is True
    assert model.openai_api_base == "https://api.example.com/v1"
    assert model.request_timeout == 42.0
    assert model.max_retries == 0
    assert model.temperature == 0.1
    assert model.max_tokens == 2048
    assert model.top_p == 0.8
    assert model.store is False
    assert model.reasoning_effort == "medium"
    assert model.truncation == "disabled"
    assert isinstance(model.openai_api_key, SecretStr)
    assert model.openai_api_key.get_secret_value() == "sk-test-secret"
    assert "sk-test-secret" not in repr(model)


def test_anthropic_factory_maps_options() -> None:
    model = create_chat_model(
        _config(ProtocolKind.ANTHROPIC_MESSAGES),
        api_key="sk-test-secret",
        options=AnthropicMessagesOptions(
            temperature=0.5,
            max_output_tokens=4096,
            top_p=0.7,
            top_k=10,
            stop_sequences=("\n\n",),
            thinking=AnthropicThinkingBudget(budget_tokens=2048),
        ),
    )

    assert isinstance(model, ChatAnthropic)
    assert isinstance(model, BaseChatModel)
    assert model.model == "example-model"
    assert model.anthropic_api_url == "https://api.example.com/v1"
    assert model.default_request_timeout == 42.0
    assert model.max_retries == 0
    assert model.temperature == 0.5
    assert model.max_tokens == 4096
    assert model.top_p == 0.7
    assert model.top_k == 10
    assert model.stop_sequences == ["\n\n"]
    assert model.thinking == {"type": "enabled", "budget_tokens": 2048}
    assert isinstance(model.anthropic_api_key, SecretStr)
    assert model.anthropic_api_key.get_secret_value() == "sk-test-secret"
    assert "sk-test-secret" not in repr(model)


def test_anthropic_adaptive_thinking_mapping() -> None:
    model = create_chat_model(
        _config(ProtocolKind.ANTHROPIC_MESSAGES),
        api_key="sk-test-secret",
        options=AnthropicMessagesOptions(
            max_output_tokens=4096,
            thinking=AnthropicThinkingAdaptive(),
        ),
    )

    assert isinstance(model, ChatAnthropic)
    assert model.thinking == {"type": "adaptive"}


def test_factory_without_options_uses_safe_defaults() -> None:
    chat = create_chat_model(
        _config(ProtocolKind.CHAT_COMPLETIONS),
        api_key="sk-test-secret",
    )
    responses = create_chat_model(
        _config(ProtocolKind.RESPONSES),
        api_key="sk-test-secret",
    )
    anthropic = create_chat_model(
        _config(ProtocolKind.ANTHROPIC_MESSAGES),
        api_key="sk-test-secret",
    )

    assert isinstance(chat, ChatOpenAI)
    assert chat.use_responses_api is False
    assert chat.max_retries == 0
    assert chat.temperature is None
    assert chat.stop is None
    assert isinstance(responses, ChatOpenAI)
    assert responses.use_responses_api is True
    assert responses.max_retries == 0
    assert isinstance(anthropic, ChatAnthropic)
    assert anthropic.max_retries == 0
    assert anthropic.temperature is None
    assert anthropic.stop_sequences is None


def test_factory_rejects_protocol_option_mismatch() -> None:
    with pytest.raises(ConfigurationError):
        create_chat_model(
            _config(ProtocolKind.CHAT_COMPLETIONS),
            api_key="sk-test-secret",
            options=ResponsesOptions(),
        )


def test_factory_rejects_empty_api_key() -> None:
    with pytest.raises(ConfigurationError):
        create_chat_model(
            _config(ProtocolKind.CHAT_COMPLETIONS),
            api_key="   ",
        )


def test_factory_rejects_negative_retries() -> None:
    with pytest.raises(ConfigurationError):
        ChatModelConfig(
            protocol=ProtocolKind.CHAT_COMPLETIONS,
            endpoint="https://api.example.com/v1",
            model="example-model",
            max_retries=-1,
        )
