"""Preflight validation for common fields, protocol options, and capabilities."""

from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    AnthropicThinkingBudget,
    ChatCompletionsOptions,
    ChatRequest,
    InvalidRequestError,
    ModelCapabilities,
    NamedToolChoice,
    ProtocolKind,
    ResponsesOptions,
    Role,
    ToolResultBlock,
    UnsupportedParameterError,
)

_REASONING_EFFORTS = frozenset({"minimal", "low", "medium", "high"})
_REASONING_SUMMARIES = frozenset({"auto", "concise", "detailed"})
_TRUNCATIONS = frozenset({"auto", "disabled"})


def validate_request(
    request: ChatRequest,
    *,
    protocol: ProtocolKind,
    model: str,
    capabilities: ModelCapabilities,
) -> None:
    """Validate a request before any network call is made."""

    _validate_common(request)
    _validate_options(request, protocol=protocol, model=model)
    _validate_capabilities(
        request,
        protocol=protocol,
        model=model,
        capabilities=capabilities,
    )


def _validate_common(  # noqa: C901 - explicit field checks stay together
    request: ChatRequest,
) -> None:
    if not request.messages:
        raise InvalidRequestError("messages must not be empty")
    if request.request_id is not None and not request.request_id.strip():
        raise InvalidRequestError("request_id must not be blank")
    if request.max_output_tokens is not None and request.max_output_tokens <= 0:
        raise InvalidRequestError("max_output_tokens must be positive")
    if request.temperature is not None and request.temperature < 0:
        raise InvalidRequestError("temperature must be non-negative")
    if request.top_p is not None and not 0 <= request.top_p <= 1:
        raise InvalidRequestError("top_p must be between 0 and 1")

    tool_names: set[str] = set()
    for tool in request.tools:
        if not tool.name.strip():
            raise InvalidRequestError("tool names must not be empty")
        if tool.name in tool_names:
            raise InvalidRequestError(f"duplicate tool name {tool.name!r}")
        tool_names.add(tool.name)

    if isinstance(request.tool_choice, NamedToolChoice):
        if request.tool_choice.name not in tool_names:
            raise InvalidRequestError(
                f"tool_choice references unknown tool " f"{request.tool_choice.name!r}"
            )
    elif request.tool_choice == "required" and not request.tools:
        raise InvalidRequestError("tool_choice='required' requires at least one tool")

    for message in request.messages:
        if not message.content:
            raise InvalidRequestError("message content must not be empty")
        has_tool_result = any(
            isinstance(block, ToolResultBlock) for block in message.content
        )
        if message.role == Role.TOOL:
            if not has_tool_result:
                raise InvalidRequestError("TOOL messages require a ToolResultBlock")
            for block in message.content:
                if not isinstance(block, ToolResultBlock):
                    raise InvalidRequestError(
                        "TOOL messages may only contain ToolResultBlock values"
                    )
                if not block.tool_call_id.strip():
                    raise InvalidRequestError(
                        "ToolResultBlock.tool_call_id must not be blank"
                    )
        elif has_tool_result:
            raise InvalidRequestError("ToolResultBlock is only valid in TOOL messages")


def _validate_options(
    request: ChatRequest,
    *,
    protocol: ProtocolKind,
    model: str,
) -> None:
    options = request.options
    if options is None:
        return

    if protocol == ProtocolKind.CHAT_COMPLETIONS:
        if not isinstance(options, ChatCompletionsOptions):
            raise UnsupportedParameterError(
                "options",
                protocol=protocol,
                model=model,
            )
        _validate_chat_completions_options(options)
        return

    if protocol == ProtocolKind.RESPONSES:
        if not isinstance(options, ResponsesOptions):
            raise UnsupportedParameterError(
                "options",
                protocol=protocol,
                model=model,
            )
        _validate_responses_options(options)
        return

    if not isinstance(options, AnthropicMessagesOptions):
        raise UnsupportedParameterError(
            "options",
            protocol=protocol,
            model=model,
        )
    _validate_anthropic_options(options, request=request, model=model)


def _validate_chat_completions_options(
    options: ChatCompletionsOptions,
) -> None:
    for value in options.stop:
        if not value:
            raise InvalidRequestError("stop values must not be empty")
    if (
        options.reasoning_effort is not None
        and options.reasoning_effort not in _REASONING_EFFORTS
    ):
        raise InvalidRequestError("invalid reasoning_effort")


def _validate_responses_options(options: ResponsesOptions) -> None:
    if (
        options.previous_response_id is not None
        and not options.previous_response_id.strip()
    ):
        raise InvalidRequestError("previous_response_id must not be blank")
    if (
        options.reasoning_effort is not None
        and options.reasoning_effort not in _REASONING_EFFORTS
    ):
        raise InvalidRequestError("invalid reasoning_effort")
    if (
        options.reasoning_summary is not None
        and options.reasoning_summary not in _REASONING_SUMMARIES
    ):
        raise InvalidRequestError("invalid reasoning_summary")
    if options.truncation is not None and options.truncation not in _TRUNCATIONS:
        raise InvalidRequestError("invalid truncation")
    for value in options.include:
        if not value:
            raise InvalidRequestError("include values must not be empty")


def _validate_anthropic_options(  # noqa: C901 - protocol constraint matrix
    options: AnthropicMessagesOptions,
    *,
    request: ChatRequest,
    model: str,
) -> None:
    for value in options.stop_sequences:
        if not value:
            raise InvalidRequestError("stop_sequences values must not be empty")
    if options.top_k is not None and options.top_k <= 0:
        raise InvalidRequestError("top_k must be positive")

    thinking = options.thinking
    if thinking is None:
        return
    if options.top_k is not None:
        raise UnsupportedParameterError(
            "top_k",
            protocol=ProtocolKind.ANTHROPIC_MESSAGES,
            model=model,
        )
    if isinstance(thinking, AnthropicThinkingBudget):
        if thinking.budget_tokens < 1024:
            raise InvalidRequestError("thinking budget must be at least 1024 tokens")
        if request.max_output_tokens is None:
            raise InvalidRequestError("thinking budget requires max_output_tokens")
        if request.max_output_tokens <= thinking.budget_tokens:
            raise InvalidRequestError(
                "max_output_tokens must exceed the thinking budget"
            )
        if request.temperature is not None and request.temperature != 1.0:
            raise InvalidRequestError(
                "temperature must be 1.0 when thinking budget is enabled"
            )
        if request.tool_choice == "required" or isinstance(
            request.tool_choice, NamedToolChoice
        ):
            raise InvalidRequestError(
                "forced tool choice is incompatible with thinking"
            )
        return
    if thinking.display not in {None, "summarized", "omitted"}:
        raise InvalidRequestError("invalid thinking display mode")


def _validate_capabilities(
    request: ChatRequest,
    *,
    protocol: ProtocolKind,
    model: str,
    capabilities: ModelCapabilities,
) -> None:
    if capabilities.supports_tools is False and request.tools:
        raise UnsupportedParameterError(
            "tools",
            protocol=protocol,
            model=model,
        )
    if capabilities.supports_tool_choice is False and request.tool_choice != "auto":
        raise UnsupportedParameterError(
            "tool_choice",
            protocol=protocol,
            model=model,
        )
    if capabilities.supports_temperature is False and request.temperature is not None:
        raise UnsupportedParameterError(
            "temperature",
            protocol=protocol,
            model=model,
        )
    if (
        capabilities.max_output_tokens is not None
        and request.max_output_tokens is not None
        and request.max_output_tokens > capabilities.max_output_tokens
    ):
        raise InvalidRequestError("max_output_tokens exceeds the model maximum")

    effort = _reasoning_effort(request)
    if effort is not None:
        if capabilities.supports_reasoning is False:
            raise UnsupportedParameterError(
                "reasoning_effort",
                protocol=protocol,
                model=model,
            )
        if (
            capabilities.reasoning_efforts is not None
            and effort not in capabilities.reasoning_efforts
        ):
            raise UnsupportedParameterError(
                "reasoning_effort",
                protocol=protocol,
                model=model,
            )

    if (
        isinstance(request.options, AnthropicMessagesOptions)
        and request.options.thinking is not None
        and capabilities.supports_reasoning is False
    ):
        raise UnsupportedParameterError(
            "thinking",
            protocol=protocol,
            model=model,
        )


def _reasoning_effort(request: ChatRequest) -> str | None:
    options = request.options
    if isinstance(options, (ChatCompletionsOptions, ResponsesOptions)):
        return options.reasoning_effort
    return None
