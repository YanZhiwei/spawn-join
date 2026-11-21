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

    fake = FakeChatModel()
    return ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, model=fake),
            ModelBinding(ModelPurpose.WORKER, model=fake),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )
