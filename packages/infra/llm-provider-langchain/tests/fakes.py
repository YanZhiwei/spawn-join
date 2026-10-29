"""Recording fake chat models for offline adapter tests."""

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field


def _empty_calls() -> list[tuple[list[BaseMessage], dict[str, Any]]]:
    return []


class RecordingChatModel(BaseChatModel):
    """Fake model that records invocation messages and kwargs."""

    response: AIMessage = Field(default_factory=lambda: AIMessage(content="ok"))
    chunks: tuple[AIMessageChunk, ...] = ()
    calls: list[tuple[list[BaseMessage], dict[str, Any]]] = Field(
        default_factory=_empty_calls
    )
    error: Exception | None = None
    cancel: bool = False

    @property
    def _llm_type(self) -> str:
        return "recording-chat-model"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        del stop, run_manager
        self.calls.append((list(messages), dict(kwargs)))
        if self.cancel:
            raise asyncio.CancelledError
        if self.error is not None:
            raise self.error
        return ChatResult(generations=[ChatGeneration(message=self.response)])

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        del stop, run_manager
        self.calls.append((list(messages), dict(kwargs)))
        if self.cancel:
            raise asyncio.CancelledError
        if self.error is not None:
            raise self.error
        for chunk in self.chunks:
            yield ChatGenerationChunk(message=chunk)

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        del stop, run_manager
        self.calls.append((list(messages), dict(kwargs)))
        if self.cancel:
            raise asyncio.CancelledError
        if self.error is not None:
            raise self.error
        return ChatResult(generations=[ChatGeneration(message=self.response)])

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        del stop, run_manager
        self.calls.append((list(messages), dict(kwargs)))
        if self.cancel:
            raise asyncio.CancelledError
        if self.error is not None:
            raise self.error
        for chunk in self.chunks:
            yield ChatGenerationChunk(message=chunk)
