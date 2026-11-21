"""Deterministic offline test helpers for the host package."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import pytest
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool
from spawn_join_agent_deepagents import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
)
from spawn_join_personal_assistant import AppConfig

FAKE_RESPONSE = "host assembly fake response"


class FakeChatModel(BaseChatModel):
    """Return one fixed assistant message without any provider."""

    @property
    def _llm_type(self) -> str:
        return "spawn-join-host-fake"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        del messages, stop, run_manager, kwargs
        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content=FAKE_RESPONSE))]
        )

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable[..., Any] | BaseTool],
        *,
        tool_choice: Any | None = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        del tools, tool_choice, kwargs
        return self


class SequenceFakeChatModel(BaseChatModel):
    """Return a fixed sequence of assistant messages without a provider."""

    responses: list[AIMessage]
    index: int = 0

    @property
    def _llm_type(self) -> str:
        return "spawn-join-host-sequence-fake"

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


def _make_models(model: BaseChatModel) -> ModelBindings:
    """Bind one deterministic model to every purpose without credentials."""

    return ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, model=model),
            ModelBinding(ModelPurpose.WORKER, model=model),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )


@pytest.fixture
def make_sequence_model() -> Callable[[list[AIMessage]], BaseChatModel]:
    """Provide a factory for deterministic multi-response fake models."""

    def make(responses: list[AIMessage]) -> BaseChatModel:
        return SequenceFakeChatModel(responses=responses)

    return make


@pytest.fixture
def make_models() -> Callable[[BaseChatModel], ModelBindings]:
    """Provide a factory binding any deterministic model to all purposes."""

    return _make_models


@pytest.fixture
def fake_response() -> str:
    """The exact content the offline fake model always returns."""

    return FAKE_RESPONSE


@pytest.fixture
def host_config(tmp_path: Path) -> AppConfig:
    """A validated offline host configuration under a temp directory."""

    catalog = tmp_path / "model.yaml"
    catalog.write_text("schema_version: 1\n", encoding="utf-8")
    return AppConfig(
        data_dir=tmp_path / "data",
        workspace_root=tmp_path / "workspace",
        model_catalog_path=catalog,
    )


@pytest.fixture
def host_models() -> ModelBindings:
    """Model bindings that need no catalog, provider, or credentials."""

    return _make_models(FakeChatModel())
