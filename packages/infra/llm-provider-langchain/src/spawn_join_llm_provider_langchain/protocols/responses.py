"""Responses protocol provider."""

from langchain_core.messages import AIMessage

from spawn_join_llm_provider import (
    ChatRequest,
    FinishReason,
    ResponsesOptions,
    UnsupportedParameterError,
)

from ..base import BaseLangChainProvider
from ..mapping import openai_common_kwargs, responses_tool_choice


class ResponsesProvider(BaseLangChainProvider):
    """Provider for OpenAI-compatible Responses endpoints."""

    def _finish_reason(
        self,
        message: AIMessage,
        provider_finish_reason: str | None,
    ) -> FinishReason:
        reason = super()._finish_reason(message, provider_finish_reason)
        if reason is FinishReason.STOP and message.tool_calls:
            return FinishReason.TOOL_CALLS
        return reason

    def _request_kwargs(self, request: ChatRequest) -> dict[str, object]:
        kwargs = openai_common_kwargs(request)
        if request.tools:
            kwargs["tool_choice"] = responses_tool_choice(request.tool_choice)

        options = request.options
        if options is None:
            kwargs["store"] = False
            return kwargs
        if not isinstance(options, ResponsesOptions):
            raise UnsupportedParameterError(
                "options",
                protocol=self.protocol,
                model=self.model,
            )

        kwargs["store"] = options.store
        reasoning: dict[str, str] = {}
        if options.reasoning_effort is not None:
            reasoning["effort"] = options.reasoning_effort
        if options.reasoning_summary is not None:
            reasoning["summary"] = options.reasoning_summary
        if reasoning:
            kwargs["reasoning"] = reasoning
        if options.previous_response_id is not None:
            kwargs["previous_response_id"] = options.previous_response_id
        if options.truncation is not None:
            kwargs["truncation"] = options.truncation
        if options.include:
            kwargs["include"] = list(options.include)
        return kwargs
