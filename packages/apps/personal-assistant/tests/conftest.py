"""宿主包的确定性离线测试辅助。"""

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
    """不依赖任何 Provider，返回一条固定的 assistant 消息。"""

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
    """不依赖 Provider，返回固定序列的 assistant 消息。"""

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
    """把一个确定性模型绑定到每个用途，全程不需要凭据。"""

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
    """提供构造确定性多响应假模型的工厂。"""

    def make(responses: list[AIMessage]) -> BaseChatModel:
        return SequenceFakeChatModel(responses=responses)

    return make


@pytest.fixture
def make_models() -> Callable[[BaseChatModel], ModelBindings]:
    """提供把任意确定性模型绑定到全部用途的工厂。"""

    return _make_models


@pytest.fixture
def fake_response() -> str:
    """离线假模型始终返回的确切内容。"""

    return FAKE_RESPONSE


@pytest.fixture
def host_config(tmp_path: Path) -> AppConfig:
    """临时目录下已校验的离线宿主配置。"""

    catalog = tmp_path / "model.yaml"
    catalog.write_text("schema_version: 1\n", encoding="utf-8")
    return AppConfig(
        data_dir=tmp_path / "data",
        workspace_root=tmp_path / "workspace",
        model_catalog_path=catalog,
    )


@pytest.fixture
def host_models() -> ModelBindings:
    """不需要目录、Provider 或凭据的模型绑定。"""

    return _make_models(FakeChatModel())
