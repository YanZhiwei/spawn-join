"""Protocol-native options for supported LLM protocols."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, TypeAlias


class ProtocolKind(StrEnum):
    """Supported LLM request/response protocol families."""

    CHAT_COMPLETIONS = "chat_completions"
    RESPONSES = "responses"
    ANTHROPIC_MESSAGES = "anthropic_messages"


@dataclass(frozen=True, slots=True)
class ChatCompletionsOptions:
    """Options that are native to the Chat Completions protocol."""

    stop: tuple[str, ...] = ()
    reasoning_effort: Literal["minimal", "low", "medium", "high"] | None = None


@dataclass(frozen=True, slots=True)
class ResponsesOptions:
    """Options that are native to the Responses protocol."""

    reasoning_effort: Literal["minimal", "low", "medium", "high"] | None = None
    reasoning_summary: Literal["auto", "concise", "detailed"] | None = None
    previous_response_id: str | None = None
    store: bool = False
    truncation: Literal["auto", "disabled"] | None = None
    include: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AnthropicThinkingBudget:
    """Anthropic thinking with an explicit token budget."""

    budget_tokens: int


@dataclass(frozen=True, slots=True)
class AnthropicThinkingAdaptive:
    """Anthropic adaptive thinking, optionally with a display mode."""

    display: Literal["summarized", "omitted"] | None = None


AnthropicThinking: TypeAlias = AnthropicThinkingBudget | AnthropicThinkingAdaptive


@dataclass(frozen=True, slots=True)
class AnthropicMessagesOptions:
    """Options that are native to the Anthropic Messages protocol."""

    thinking: AnthropicThinking | None = None
    stop_sequences: tuple[str, ...] = ()
    top_k: int | None = None


ProtocolOptions: TypeAlias = (
    ChatCompletionsOptions | ResponsesOptions | AnthropicMessagesOptions
)
