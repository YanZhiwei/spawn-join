"""Deterministic offline test helpers for the agent package."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import pytest
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool


class SequenceFakeChatModel(BaseChatModel):
    """Return a fixed sequence of assistant messages without a provider."""

    responses: list[AIMessage]
    index: int = 0

    @property
    def _llm_type(self) -> str:
        return "spawn-join-sequence-fake"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        del messages, stop, run_manager, kwargs
        if not self.responses:
            msg = "SequenceFakeChatModel requires at least one response"
            raise ValueError(msg)
        response = self.responses[min(self.index, len(self.responses) - 1)]
        self.index += 1
        return ChatResult(generations=[ChatGeneration(message=response)])

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable[..., Any] | BaseTool],
        *,
        tool_choice: Any | None = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        del tools, tool_choice, kwargs
        return self


@pytest.fixture
def fake_chat_model() -> SequenceFakeChatModel:
    """Provide a deterministic two-response model for package smoke tests."""

    return SequenceFakeChatModel(
        responses=[AIMessage(content="first"), AIMessage(content="second")]
    )


@pytest.fixture
def make_fake_model() -> Callable[[str], BaseChatModel]:
    """Provide a factory for distinct deterministic model instances."""

    def make(text: str) -> BaseChatModel:
        return SequenceFakeChatModel(responses=[AIMessage(content=text)])

    return make


@pytest.fixture
def make_sequence_model() -> Callable[[list[AIMessage]], BaseChatModel]:
    """Provide a factory for deterministic multi-response models."""

    def make(responses: list[AIMessage]) -> BaseChatModel:
        return SequenceFakeChatModel(responses=responses)

    return make
