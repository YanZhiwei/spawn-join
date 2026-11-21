"""为可运行示例提供的确定性离线假模型。"""

from __future__ import annotations

from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class FakeChatModel(BaseChatModel):
    """不依赖任何 Provider，返回固定序列的 assistant 消息。"""

    responses: list[AIMessage]
    index: int = 0

    @property
    def _llm_type(self) -> str:
        return "spawn-join-example-fake"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        del messages, stop, run_manager, kwargs
        if not self.responses:
            msg = "FakeChatModel requires at least one response"
            raise ValueError(msg)
        response = self.responses[min(self.index, len(self.responses) - 1)]
        self.index += 1
        return ChatResult(generations=[ChatGeneration(message=response)])

    def bind_tools(
        self, tools: object, *, tool_choice: object = None, **kwargs: object
    ) -> BaseChatModel:
        del tools, tool_choice, kwargs
        return self
