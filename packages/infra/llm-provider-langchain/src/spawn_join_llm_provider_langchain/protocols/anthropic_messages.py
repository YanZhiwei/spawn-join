"""Anthropic Messages protocol provider."""

from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    AnthropicThinkingAdaptive,
    AnthropicThinkingBudget,
    ChatRequest,
    NamedToolChoice,
    UnsupportedParameterError,
)

from ..base import BaseLangChainProvider
from ..mapping import anthropic_tools


class AnthropicMessagesProvider(BaseLangChainProvider):
    """Provider for Anthropic Messages endpoints."""

    def _request_kwargs(self, request: ChatRequest) -> dict[str, object]:
        kwargs: dict[str, object] = {}
        if request.max_output_tokens is not None:
            kwargs["max_tokens"] = request.max_output_tokens
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        if request.tools:
            kwargs["tools"] = anthropic_tools(request.tools)
            kwargs["tool_choice"] = self._tool_choice(request)

        options = request.options
        if options is None:
            return kwargs
        if not isinstance(options, AnthropicMessagesOptions):
            raise UnsupportedParameterError(
                "options",
                protocol=self.protocol,
                model=self.model,
            )
        if options.stop_sequences:
            kwargs["stop"] = list(options.stop_sequences)
        if options.top_k is not None:
            kwargs["top_k"] = options.top_k
        if options.thinking is not None:
            kwargs["thinking"] = self._thinking(options)
        return kwargs

    def _tool_choice(self, request: ChatRequest) -> object:
        choice = request.tool_choice
        if isinstance(choice, NamedToolChoice):
            return {"type": "tool", "name": choice.name}
        if choice == "none":
            raise UnsupportedParameterError(
                "tool_choice",
                protocol=self.protocol,
                model=self.model,
            )
        if choice == "required":
            return "any"
        return choice

    def _thinking(self, options: AnthropicMessagesOptions) -> object:
        thinking = options.thinking
        if isinstance(thinking, AnthropicThinkingBudget):
            return {
                "type": "enabled",
                "budget_tokens": thinking.budget_tokens,
            }
        if isinstance(thinking, AnthropicThinkingAdaptive):
            result: dict[str, object] = {"type": "adaptive"}
            if thinking.display is not None:
                result["display"] = thinking.display
            return result
        raise UnsupportedParameterError(
            "thinking",
            protocol=self.protocol,
            model=self.model,
        )
