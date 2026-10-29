"""Public complete/stream regression tests for all three protocols."""

import asyncio
from typing import Any, cast

import pytest
from fakes import RecordingChatModel
from langchain_core.messages import AIMessage, AIMessageChunk

from spawn_join_llm_provider import (
    ChatRequest,
    ConfigurationError,
    Message,
    Role,
    StreamCompleted,
    TextBlock,
)
from spawn_join_llm_provider_langchain import (
    AnthropicMessagesConfig,
    ChatCompletionsConfig,
    ResponsesConfig,
    create_provider,
)
from spawn_join_llm_provider_langchain.config import ProviderConfig
from spawn_join_llm_provider_langchain.protocols import (
    AnthropicMessagesProvider,
    ChatCompletionsProvider,
    ResponsesProvider,
)


def _request() -> ChatRequest:
    return ChatRequest(
        messages=(Message(role=Role.USER, content=(TextBlock("hello"),)),)
    )


@pytest.mark.parametrize(
    ("provider_type", "config_type"),
    [
        (ChatCompletionsProvider, ChatCompletionsConfig),
        (ResponsesProvider, ResponsesConfig),
        (AnthropicMessagesProvider, AnthropicMessagesConfig),
    ],
)
def test_public_complete_path(
    provider_type: Any,
    config_type: Any,
) -> None:
    model = RecordingChatModel(response=AIMessage(content="answer"))
    provider = provider_type(
        model,
        config_type(model="test-model", credential_ref="KEY"),
    )

    response = asyncio.run(provider.complete(_request()))

    assert response.message.content[0] == TextBlock("answer")
    assert model.calls


@pytest.mark.parametrize(
    ("provider_type", "config_type"),
    [
        (ChatCompletionsProvider, ChatCompletionsConfig),
        (ResponsesProvider, ResponsesConfig),
        (AnthropicMessagesProvider, AnthropicMessagesConfig),
    ],
)
def test_public_stream_path(
    provider_type: Any,
    config_type: Any,
) -> None:
    model = RecordingChatModel(
        chunks=(
            AIMessageChunk(content="a"),
            AIMessageChunk(
                content="b",
                usage_metadata={
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "total_tokens": 2,
                },
            ),
        )
    )
    provider = provider_type(
        model,
        config_type(model="test-model", credential_ref="KEY"),
    )

    async def collect() -> list[Any]:
        return [event async for event in provider.stream(_request())]

    events = asyncio.run(collect())
    completed = events[-1]

    assert isinstance(completed, StreamCompleted)
    assert completed.message is not None
    assert completed.message.content[0] == TextBlock("ab")


def test_factory_rejects_base_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_API_KEY", "secret-value")
    with pytest.raises(ConfigurationError):
        create_provider(
            cast(
                Any,
                ProviderConfig(model="m", credential_ref="TEST_API_KEY"),
            )
        )
