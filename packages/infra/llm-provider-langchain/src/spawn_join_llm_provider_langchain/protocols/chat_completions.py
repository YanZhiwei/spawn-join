"""Chat Completions protocol provider."""

from spawn_join_llm_provider import (
    ChatCompletionsOptions,
    ChatRequest,
    UnsupportedParameterError,
)

from ..base import BaseLangChainProvider
from ..mapping import openai_tool_choice, openai_tools


class ChatCompletionsProvider(BaseLangChainProvider):
    """Provider for OpenAI-compatible Chat Completions endpoints."""

    def _request_kwargs(self, request: ChatRequest) -> dict[str, object]:
        kwargs: dict[str, object] = {}
        if request.max_output_tokens is not None:
            kwargs["max_tokens"] = request.max_output_tokens
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.top_p is not None:
            kwargs["top_p"] = request.top_p
        if request.tools:
            kwargs["tools"] = openai_tools(request.tools)
            kwargs["tool_choice"] = openai_tool_choice(request.tool_choice)

        options = request.options
        if options is None:
            return kwargs
        if not isinstance(options, ChatCompletionsOptions):
            raise UnsupportedParameterError(
                "options",
                protocol=self.protocol,
                model=self.model,
            )
        if options.stop:
            kwargs["stop"] = list(options.stop)
        if options.reasoning_effort is not None:
            kwargs["reasoning_effort"] = options.reasoning_effort
        return kwargs
