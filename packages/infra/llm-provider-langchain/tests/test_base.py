"""Tests for the shared LangChain provider base class."""

import asyncio
import logging

import pytest
from fakes import RecordingChatModel
from langchain_core import exceptions as lc_exceptions
from langchain_core.messages import AIMessage, AIMessageChunk

from spawn_join_llm_provider import (
    AuthenticationError,
    ChatRequest,
    ContextOverflowError,
    FinishReason,
    InvalidRequestError,
    Message,
    Role,
    StreamCompleted,
    TextBlock,
    TextDelta,
)
from spawn_join_llm_provider_langchain.base import BaseLangChainProvider
from spawn_join_llm_provider_langchain.config import ChatCompletionsConfig


class ProviderUnderTest(BaseLangChainProvider):
    def _request_kwargs(self, request: ChatRequest) -> dict[str, object]:
        del request
        return {"stop": ["END"]}


def _config() -> ChatCompletionsConfig:
    return ChatCompletionsConfig(model="test-model", credential_ref="KEY")


def _request(prompt: str = "hello") -> ChatRequest:
    return ChatRequest(
        messages=(Message(role=Role.USER, content=(TextBlock(prompt),)),)
    )


def test_complete_maps_response_and_passes_kwargs() -> None:
    model = RecordingChatModel(
        response=AIMessage(
            content="answer",
            usage_metadata={
                "input_tokens": 3,
                "output_tokens": 2,
                "total_tokens": 5,
            },
        )
    )
    provider = ProviderUnderTest(model, _config())

    response = asyncio.run(provider.complete(_request()))

    assert response.message.content[0] == TextBlock("answer")
    assert response.usage is not None
    assert response.usage.total_tokens == 5
    assert model.calls


def test_stream_emits_deltas_and_completion() -> None:
    model = RecordingChatModel(
        chunks=(
            AIMessageChunk(content="a"),
            AIMessageChunk(
                content="b",
                usage_metadata={
                    "input_tokens": 1,
                    "output_tokens": 2,
                    "total_tokens": 3,
                },
            ),
        )
    )
    provider = ProviderUnderTest(model, _config())

    async def collect():
        return [event async for event in provider.stream(_request())]

    events = asyncio.run(collect())

    assert isinstance(events[0], TextDelta)
    assert isinstance(events[1], TextDelta)
    assert isinstance(events[-1], StreamCompleted)
    assert events[-1].finish_reason == FinishReason.UNKNOWN
    assert events[-1].usage is not None
    assert events[-1].usage.total_tokens == 3


def test_validation_failure_does_not_call_model() -> None:
    model = RecordingChatModel()
    provider = ProviderUnderTest(model, _config())
    invalid = ChatRequest(messages=())

    with pytest.raises(InvalidRequestError):
        asyncio.run(provider.complete(invalid))

    assert model.calls == []


@pytest.mark.parametrize(
    ("langchain_error", "domain_error"),
    [
        (
            lc_exceptions.ContextOverflowError("secret context"),
            ContextOverflowError,
        ),
        (
            lc_exceptions.ModelAuthenticationError("secret auth"),
            AuthenticationError,
        ),
    ],
)
def test_langchain_errors_are_mapped_and_causes_preserved(
    langchain_error: Exception,
    domain_error: type[Exception],
) -> None:
    model = RecordingChatModel(error=langchain_error)
    provider = ProviderUnderTest(model, _config())

    with pytest.raises(Exception) as caught:
        asyncio.run(provider.complete(_request()))

    assert isinstance(caught.value, domain_error)
    assert caught.value.__cause__ is langchain_error


def test_cancellation_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = RecordingChatModel()
    provider = ProviderUnderTest(model, _config())

    async def raise_cancel(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise asyncio.CancelledError

    monkeypatch.setattr(RecordingChatModel, "agenerate_prompt", raise_cancel)

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(provider.complete(_request()))


def test_logs_contain_metadata_but_not_content(
    caplog: pytest.LogCaptureFixture,
) -> None:
    secret_prompt = "PROMPT_SECRET_123"
    model = RecordingChatModel(error=RuntimeError("ERROR_SECRET_456"))
    provider = ProviderUnderTest(model, _config())

    with caplog.at_level(logging.INFO, logger="spawn_join.llm"):
        with pytest.raises(RuntimeError):
            asyncio.run(provider.complete(_request(secret_prompt)))

    assert "llm.request.start" in caplog.text
    assert any(
        getattr(record, "llm_model", None) == "test-model" for record in caplog.records
    )
    assert secret_prompt not in caplog.text
    assert "ERROR_SECRET_456" not in caplog.text
