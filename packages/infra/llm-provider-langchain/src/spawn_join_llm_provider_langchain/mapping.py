"""Convert between SpawnJoin domain types and LangChain types."""

from collections.abc import Mapping
from typing import Any, cast

from langchain_core.language_models.model_profile import ModelProfile
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.messages.ai import UsageMetadata
from langchain_core.messages.tool import ToolCall

from spawn_join_llm_provider import (
    ChatRequest,
    ChatResponse,
    FinishReason,
    InvalidRequestError,
    JsonValue,
    MalformedResponseError,
    Message,
    ModelCapabilities,
    NamedToolChoice,
    OpaqueBlock,
    ReasoningBlock,
    ReasoningDelta,
    Role,
    StreamEvent,
    TextBlock,
    TextDelta,
    ToolCallBlock,
    ToolCallDelta,
    ToolChoice,
    ToolDefinition,
    ToolResultBlock,
    Usage,
)


def openai_tools(
    tools: tuple[ToolDefinition, ...],
) -> list[dict[str, object]]:
    """Convert tool definitions to the OpenAI function tool shape."""

    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": dict(tool.parameters),
            },
        }
        for tool in tools
    ]


def anthropic_tools(
    tools: tuple[ToolDefinition, ...],
) -> list[dict[str, object]]:
    """Convert tool definitions to the Anthropic Messages tool shape."""

    return [
        {
            "name": tool.name,
            "description": tool.description,
            "input_schema": dict(tool.parameters),
        }
        for tool in tools
    ]


def openai_common_kwargs(request: ChatRequest) -> dict[str, object]:
    """Build OpenAI-shaped common invocation kwargs."""

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
    return kwargs


def openai_tool_choice(choice: ToolChoice) -> object:
    """Map a common tool choice to the OpenAI Chat Completions shape."""

    if isinstance(choice, NamedToolChoice):
        return {
            "type": "function",
            "function": {"name": choice.name},
        }
    return choice


def responses_tool_choice(choice: ToolChoice) -> object:
    """Map a common tool choice to the Responses shape."""

    if isinstance(choice, NamedToolChoice):
        return {"type": "function", "name": choice.name}
    return choice


def to_langchain_messages(
    messages: tuple[Message, ...],
) -> list[BaseMessage]:
    """Convert domain messages to LangChain messages."""

    return [_to_langchain_message(message) for message in messages]


def from_langchain_message(  # noqa: C901 - protocol block dispatch
    message: AIMessage,
) -> Message:
    """Convert a LangChain assistant message to a domain message."""

    blocks: list[TextBlock | ReasoningBlock | ToolCallBlock | OpaqueBlock] = []
    for raw_block in message.content_blocks:
        block = cast(Mapping[str, object], raw_block)
        block_type = _as_str(block.get("type"))
        if block_type == "text":
            text = _as_str(block.get("text")) or ""
            blocks.append(TextBlock(text))
        elif block_type == "reasoning":
            blocks.append(
                ReasoningBlock(
                    text=_as_str(block.get("reasoning")),
                    opaque_state=_json_mapping(
                        block.get("extras"),
                        "reasoning extras",
                    ),
                )
            )
        elif block_type == "tool_call":
            blocks.append(_tool_call_from_mapping(block))
        elif block_type == "non_standard":
            blocks.append(_opaque_from_block(raw_block, block))
        else:
            blocks.append(
                OpaqueBlock(
                    provider_type=block_type or "unknown",
                    payload=_json_value(raw_block),
                )
            )

    if not blocks:
        if isinstance(message.content, str) and message.content:
            blocks.append(TextBlock(message.content))
        elif isinstance(message.content, list):
            for item in message.content:
                if isinstance(item, str) and item:
                    blocks.append(TextBlock(item))

    if not any(isinstance(block, ToolCallBlock) for block in blocks):
        for tool_call in message.tool_calls:
            blocks.append(
                _tool_call_from_mapping(cast(Mapping[str, object], tool_call))
            )

    return Message(role=Role.ASSISTANT, content=tuple(blocks))


def from_langchain_usage(usage: UsageMetadata | None) -> Usage | None:
    """Convert LangChain usage metadata, preserving unknown details."""

    if usage is None:
        return None

    input_tokens = usage["input_tokens"]
    output_tokens = usage["output_tokens"]
    total_tokens = usage["total_tokens"]

    input_details = usage.get("input_token_details") or {}
    output_details = usage.get("output_token_details") or {}
    return Usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        reasoning_tokens=output_details.get("reasoning"),
        cache_read_tokens=input_details.get("cache_read"),
        cache_creation_tokens=input_details.get("cache_creation"),
    )


def from_langchain_response(
    message: AIMessage,
    *,
    provider_finish_reason: str | None,
    finish_reason: FinishReason,
) -> ChatResponse:
    """Build a complete response from a LangChain assistant message."""

    return ChatResponse(
        message=from_langchain_message(message),
        usage=from_langchain_usage(message.usage_metadata),
        finish_reason=finish_reason,
        provider_finish_reason=provider_finish_reason,
        response_id=response_id_from_message(message),
    )


def finish_reason_from_value(value: str | None) -> FinishReason:
    """Map a provider finish reason to the stable domain enum."""

    if value is None:
        return FinishReason.UNKNOWN
    normalized = value.lower()
    if normalized in {"stop", "end_turn", "stop_sequence"}:
        return FinishReason.STOP
    if normalized in {"length", "max_tokens"}:
        return FinishReason.LENGTH
    if normalized in {"tool_calls", "tool_use"}:
        return FinishReason.TOOL_CALLS
    if normalized in {"content_filter", "refusal"}:
        return FinishReason.CONTENT_FILTER
    if normalized == "error":
        return FinishReason.ERROR
    return FinishReason.UNKNOWN


def provider_finish_reason_from_message(
    message: AIMessage | AIMessageChunk,
) -> str | None:
    """Read the provider-native finish reason without interpreting it."""

    for key in ("finish_reason", "stop_reason"):
        value = message.response_metadata.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def finish_reason_from_message(
    message: AIMessage | AIMessageChunk,
) -> FinishReason:
    """Map the provider-native finish reason to the domain enum."""

    return finish_reason_from_value(provider_finish_reason_from_message(message))


def response_id_from_message(message: AIMessage | AIMessageChunk) -> str | None:
    """Return a response/message identifier when the provider exposes one."""

    if isinstance(message.id, str) and message.id:
        return message.id
    value = message.response_metadata.get("id")
    if isinstance(value, str) and value:
        return value
    return None


def stream_events_from_chunk(chunk: AIMessageChunk) -> list[StreamEvent]:
    """Convert one LangChain chunk to ordered domain delta events."""

    events: list[StreamEvent] = []
    for raw_block in chunk.content_blocks:
        block = cast(Mapping[str, object], raw_block)
        block_type = _as_str(block.get("type"))
        if block_type == "text":
            text = _as_str(block.get("text"))
            if text:
                events.append(TextDelta(text))
        elif block_type == "reasoning":
            reasoning = _as_str(block.get("reasoning"))
            if reasoning:
                events.append(ReasoningDelta(reasoning))

    for tool_call in chunk.tool_call_chunks:
        raw_index = tool_call.get("index")
        index = raw_index if isinstance(raw_index, int) else None
        tool_id = tool_call.get("id")
        name = tool_call.get("name")
        arguments = tool_call.get("args") or ""
        if tool_id is None and name is None and not arguments:
            continue
        events.append(
            ToolCallDelta(
                index=index,
                id=tool_id if isinstance(tool_id, str) else None,
                name=name if isinstance(name, str) else None,
                arguments_delta=arguments,
            )
        )

    if not events and isinstance(chunk.content, str) and chunk.content:
        events.append(TextDelta(chunk.content))
    return events


def capabilities_from_profile(
    profile: ModelProfile | None,
) -> ModelCapabilities:
    """Convert a LangChain model profile to the project capability type."""

    if profile is None:
        return ModelCapabilities()

    efforts = profile.get("reasoning_effort_levels")
    return ModelCapabilities(
        context_window=profile.get("max_input_tokens"),
        max_output_tokens=profile.get("max_output_tokens"),
        supports_tools=profile.get("tool_calling"),
        supports_tool_choice=profile.get("tool_choice"),
        supports_tool_call_streaming=profile.get("tool_call_streaming"),
        supports_structured_output=profile.get("structured_output"),
        supports_reasoning=profile.get("reasoning_output"),
        reasoning_efforts=frozenset(efforts) if efforts else None,
        supports_temperature=profile.get("temperature"),
    )


def _to_langchain_message(  # noqa: C901 - protocol block dispatch
    message: Message,
) -> BaseMessage:
    if message.role == Role.TOOL:
        tool_result = next(
            (block for block in message.content if isinstance(block, ToolResultBlock)),
            None,
        )
        if tool_result is None:
            raise InvalidRequestError("TOOL messages require a ToolResultBlock")
        return ToolMessage(
            content=tool_result.content,
            tool_call_id=tool_result.tool_call_id,
        )

    content: list[dict[str, object]] = []
    tool_calls: list[dict[str, object]] = []
    for block in message.content:
        if isinstance(block, TextBlock):
            content.append({"type": "text", "text": block.text})
        elif isinstance(block, ReasoningBlock):
            reasoning: dict[str, object] = {"type": "reasoning"}
            if block.text is not None:
                reasoning["reasoning"] = block.text
            if block.opaque_state:
                reasoning["extras"] = dict(block.opaque_state)
            content.append(reasoning)
        elif isinstance(block, ToolCallBlock):
            tool_calls.append(
                {
                    "type": "tool_call",
                    "id": block.id,
                    "name": block.name,
                    "args": dict(block.arguments),
                }
            )
        elif isinstance(block, OpaqueBlock):
            content.append(
                {
                    "type": "non_standard",
                    "value": {
                        "provider_type": block.provider_type,
                        "payload": block.payload,
                    },
                }
            )
        else:
            raise InvalidRequestError("ToolResultBlock is only valid in TOOL messages")

    content_value = cast(list[str | dict[str, Any]] | None, content or None)
    if message.role == Role.ASSISTANT:
        return AIMessage(
            content=content_value,
            tool_calls=cast(list[ToolCall], tool_calls),
        )
    if message.role == Role.SYSTEM:
        return SystemMessage(content=cast(list[str | dict[str, Any]], content))
    if message.role == Role.USER:
        return HumanMessage(content=cast(list[str | dict[str, Any]], content))
    raise InvalidRequestError(f"Unsupported message role {message.role!r}")


def _tool_call_from_mapping(block: Mapping[str, object]) -> ToolCallBlock:
    tool_id = _as_str(block.get("id"))
    name = _as_str(block.get("name"))
    if tool_id is None or name is None:
        raise MalformedResponseError("Tool call is missing an id or name")
    return ToolCallBlock(
        id=tool_id,
        name=name,
        arguments=_json_mapping(block.get("args"), "tool arguments"),
    )


def _opaque_from_block(
    raw_block: object,
    block: Mapping[str, object],
) -> OpaqueBlock:
    value = block.get("value")
    if isinstance(value, Mapping):
        value_map = cast(Mapping[str, object], value)
        provider_type = _as_str(value_map.get("provider_type"))
        if provider_type is not None and "payload" in value_map:
            return OpaqueBlock(
                provider_type=provider_type,
                payload=_json_value(value_map.get("payload")),
            )
    return OpaqueBlock(
        provider_type="non_standard",
        payload=_json_value(raw_block),
    )


def _as_str(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _json_mapping(
    value: object,
    field: str,
) -> Mapping[str, JsonValue]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise MalformedResponseError(f"{field} must be a JSON object")
    value_map = cast(Mapping[str, object], value)
    result: dict[str, JsonValue] = {}
    for key, item in value_map.items():
        result[key] = _json_value(item)
    return result


def _json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        value_map = cast(Mapping[str, object], value)
        return {str(key): _json_value(item) for key, item in value_map.items()}
    if isinstance(value, (list, tuple)):
        sequence = cast(list[object] | tuple[object, ...], value)
        return [_json_value(item) for item in sequence]
    raise MalformedResponseError(
        f"Value of type {type(value).__name__} is not JSON-compatible"
    )
