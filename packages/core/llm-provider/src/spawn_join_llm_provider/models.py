"""Framework-independent messages, requests, responses, and stream events."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Literal, TypeAlias

from .options import ProtocolOptions
from .types import JsonValue


def _empty_json_object() -> Mapping[str, JsonValue]:
    return {}


class Role(StrEnum):
    """Message roles in a chat-style request."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True, slots=True)
class TextBlock:
    """Text content."""

    text: str
    type: Literal["text"] = "text"


@dataclass(frozen=True, slots=True)
class ReasoningBlock:
    """Reasoning content with protocol-native state required for round-trips."""

    text: str | None = None
    opaque_state: Mapping[str, JsonValue] = field(default_factory=_empty_json_object)
    type: Literal["reasoning"] = "reasoning"


@dataclass(frozen=True, slots=True)
class ToolCallBlock:
    """A model request to call a client tool."""

    id: str
    name: str
    arguments: Mapping[str, JsonValue] = field(default_factory=_empty_json_object)
    type: Literal["tool_call"] = "tool_call"


@dataclass(frozen=True, slots=True)
class ToolResultBlock:
    """The result of a client tool call."""

    tool_call_id: str
    content: str
    type: Literal["tool_result"] = "tool_result"


@dataclass(frozen=True, slots=True)
class OpaqueBlock:
    """A protocol block this package does not interpret, preserved verbatim."""

    provider_type: str
    payload: JsonValue
    type: Literal["opaque"] = "opaque"


ContentBlock: TypeAlias = (
    TextBlock | ReasoningBlock | ToolCallBlock | ToolResultBlock | OpaqueBlock
)


@dataclass(frozen=True, slots=True)
class Message:
    """A message with a role and ordered content blocks."""

    role: Role
    content: tuple[ContentBlock, ...]


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """A client tool exposed to the model."""

    name: str
    description: str
    parameters: Mapping[str, JsonValue] = field(default_factory=_empty_json_object)


@dataclass(frozen=True, slots=True)
class NamedToolChoice:
    """Force a specific client tool."""

    name: str


ToolChoice: TypeAlias = Literal["auto", "none", "required"] | NamedToolChoice


@dataclass(frozen=True, slots=True)
class ChatRequest:
    """A protocol-independent request with optionally native protocol options."""

    messages: tuple[Message, ...]
    tools: tuple[ToolDefinition, ...] = ()
    tool_choice: ToolChoice = "auto"
    max_output_tokens: int | None = None
    temperature: float | None = None
    top_p: float | None = None
    options: ProtocolOptions | None = None
    request_id: str | None = None


@dataclass(frozen=True, slots=True)
class Usage:
    """Token accounting returned by a provider."""

    input_tokens: int
    output_tokens: int
    total_tokens: int
    reasoning_tokens: int | None = None
    cache_read_tokens: int | None = None
    cache_creation_tokens: int | None = None


class FinishReason(StrEnum):
    """Normalized completion reasons."""

    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """A complete assistant response."""

    message: Message
    usage: Usage | None
    finish_reason: FinishReason
    provider_finish_reason: str | None = None
    response_id: str | None = None


@dataclass(frozen=True, slots=True)
class TextDelta:
    """An incremental text fragment."""

    text: str


@dataclass(frozen=True, slots=True)
class ReasoningDelta:
    """An incremental reasoning fragment."""

    text: str


@dataclass(frozen=True, slots=True)
class ToolCallDelta:
    """An incremental tool-call fragment; arguments may be incomplete JSON."""

    index: int | None
    id: str | None
    name: str | None
    arguments_delta: str


@dataclass(frozen=True, slots=True)
class StreamCompleted:
    """The terminal event of a successful stream."""

    finish_reason: FinishReason
    provider_finish_reason: str | None = None
    usage: Usage | None = None
    response_id: str | None = None


StreamEvent: TypeAlias = TextDelta | ReasoningDelta | ToolCallDelta | StreamCompleted
