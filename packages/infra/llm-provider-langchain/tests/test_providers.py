"""Tests for protocol provider parameter mapping and factory selection."""

from typing import Any, cast

import pytest
from fakes import RecordingChatModel

from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    AnthropicThinkingAdaptive,
    AnthropicThinkingBudget,
    ChatCompletionsOptions,
    ChatRequest,
    Message,
    ProtocolKind,
    ResponsesOptions,
    Role,
    TextBlock,
    ToolDefinition,
    UnsupportedParameterError,
)
from spawn_join_llm_provider_langchain import (
    AnthropicMessagesConfig,
    ChatCompletionsConfig,
    ResponsesConfig,
    create_provider,
)
from spawn_join_llm_provider_langchain.protocols import (
    AnthropicMessagesProvider,
    ChatCompletionsProvider,
    ResponsesProvider,
)


def _request(**kwargs: Any) -> ChatRequest:
    defaults: dict[str, Any] = {
        "messages": (Message(role=Role.USER, content=(TextBlock("hello"),)),)
    }
    defaults.update(kwargs)
    return ChatRequest(**defaults)


def _kwargs(provider: object, request: ChatRequest) -> dict[str, object]:
    return cast(Any, provider)._request_kwargs(request)


def test_chat_completions_maps_native_options() -> None:
    provider = ChatCompletionsProvider(
        RecordingChatModel(),
        ChatCompletionsConfig(model="m", credential_ref="KEY"),
    )
    request = _request(
        max_output_tokens=4096,
        temperature=0.2,
        top_p=0.9,
        tools=(ToolDefinition(name="lookup", description="lookup"),),
        options=ChatCompletionsOptions(
            stop=("END",),
            reasoning_effort="low",
        ),
    )

    kwargs = _kwargs(provider, request)

    assert kwargs["max_tokens"] == 4096
    assert kwargs["stop"] == ["END"]
    assert kwargs["reasoning_effort"] == "low"
    tools = cast(list[dict[str, object]], kwargs["tools"])
    assert tools[0]["type"] == "function"


def test_chat_completions_rejects_foreign_options() -> None:
    provider = ChatCompletionsProvider(
        RecordingChatModel(),
        ChatCompletionsConfig(model="m", credential_ref="KEY"),
    )
    with pytest.raises(UnsupportedParameterError):
        _kwargs(provider, _request(options=ResponsesOptions()))


def test_responses_defaults_store_off_and_maps_session_options() -> None:
    provider = ResponsesProvider(
        RecordingChatModel(),
        ResponsesConfig(model="m", credential_ref="KEY"),
    )
    request = _request(
        options=ResponsesOptions(
            reasoning_effort="high",
            reasoning_summary="auto",
            previous_response_id="resp-1",
            include=("reasoning.encrypted_content",),
        )
    )

    kwargs = _kwargs(provider, request)

    assert kwargs["store"] is False
    assert kwargs["previous_response_id"] == "resp-1"
    assert kwargs["include"] == ["reasoning.encrypted_content"]
    assert kwargs["reasoning"] == {"effort": "high", "summary": "auto"}


def test_responses_rejects_chat_completions_options() -> None:
    provider = ResponsesProvider(
        RecordingChatModel(),
        ResponsesConfig(model="m", credential_ref="KEY"),
    )
    with pytest.raises(UnsupportedParameterError):
        _kwargs(
            provider,
            _request(options=ChatCompletionsOptions(stop=("END",))),
        )


def test_anthropic_maps_budget_thinking_and_tools() -> None:
    provider = AnthropicMessagesProvider(
        RecordingChatModel(),
        AnthropicMessagesConfig(model="m", credential_ref="KEY"),
    )
    request = _request(
        max_output_tokens=4096,
        temperature=1.0,
        tools=(ToolDefinition(name="lookup", description="lookup"),),
        options=AnthropicMessagesOptions(
            thinking=AnthropicThinkingBudget(budget_tokens=2048),
            stop_sequences=("END",),
        ),
    )

    kwargs = _kwargs(provider, request)

    assert kwargs["max_tokens"] == 4096
    assert kwargs["thinking"] == {"type": "enabled", "budget_tokens": 2048}
    assert kwargs["stop"] == ["END"]
    tools = cast(list[dict[str, object]], kwargs["tools"])
    assert tools[0]["input_schema"] == {}


def test_anthropic_maps_adaptive_thinking() -> None:
    provider = AnthropicMessagesProvider(
        RecordingChatModel(),
        AnthropicMessagesConfig(model="m", credential_ref="KEY"),
    )
    kwargs = _kwargs(
        provider,
        _request(
            options=AnthropicMessagesOptions(
                thinking=AnthropicThinkingAdaptive(display="summarized")
            )
        ),
    )

    assert kwargs["thinking"] == {
        "type": "adaptive",
        "display": "summarized",
    }


def test_factory_selects_protocol_without_model_name_inference(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_API_KEY", "secret-value")

    chat = create_provider(
        ChatCompletionsConfig(model="test-model", credential_ref="TEST_API_KEY")
    )
    responses = create_provider(
        ResponsesConfig(model="test-model", credential_ref="TEST_API_KEY")
    )
    anthropic = create_provider(
        AnthropicMessagesConfig(
            model="test-model",
            credential_ref="TEST_API_KEY",
        )
    )

    assert isinstance(chat, ChatCompletionsProvider)
    assert isinstance(responses, ResponsesProvider)
    assert isinstance(anthropic, AnthropicMessagesProvider)
    chat_model = cast(Any, chat)._model
    responses_model = cast(Any, responses)._model
    anthropic_model = cast(Any, anthropic)._model
    assert chat_model.use_responses_api is False
    assert responses_model.use_responses_api is True
    assert chat_model.max_retries == 0
    assert responses_model.max_retries == 0
    assert anthropic_model.max_retries == 0
    assert {chat.protocol, responses.protocol, anthropic.protocol} == {
        ProtocolKind.CHAT_COMPLETIONS,
        ProtocolKind.RESPONSES,
        ProtocolKind.ANTHROPIC_MESSAGES,
    }
