"""Protocol-native option contracts shared by channel and LangChain adapters."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal, TypeAlias, cast

from .errors import ConfigurationError


class ProtocolKind(StrEnum):
    """Explicit wire protocol used by a channel."""

    CHAT_COMPLETIONS = "chat_completions"
    RESPONSES = "responses"
    ANTHROPIC_MESSAGES = "anthropic_messages"


def _require_range(
    value: float | None,
    *,
    minimum: float,
    maximum: float,
    field: str,
) -> None:
    if value is None:
        return
    if not minimum <= value <= maximum:
        raise ConfigurationError(f"{field} must be between {minimum} and {maximum}")


def _require_positive_int(value: int | None, *, field: str) -> None:
    if value is not None and value <= 0:
        raise ConfigurationError(f"{field} must be positive")


def _normalize_stop(
    values: object,
    *,
    field: str,
) -> tuple[str, ...] | None:
    if values is None:
        return None
    if not isinstance(values, tuple):
        raise ConfigurationError(f"{field} must be a tuple of strings")
    if not values:
        return None
    normalized: list[str] = []
    for value in cast(tuple[object, ...], values):
        if not isinstance(value, str) or value == "":
            raise ConfigurationError(f"{field} values must be non-empty strings")
        normalized.append(value)
    return tuple(normalized)


@dataclass(frozen=True, slots=True)
class ChatCompletionsOptions:
    """Options for the OpenAI Chat Completions protocol."""

    temperature: float | None = None
    max_output_tokens: int | None = None
    top_p: float | None = None
    stop: tuple[str, ...] | None = None
    seed: int | None = None

    def __post_init__(self) -> None:
        _require_range(self.temperature, minimum=0.0, maximum=2.0, field="temperature")
        _require_positive_int(self.max_output_tokens, field="max_output_tokens")
        _require_range(self.top_p, minimum=0.0, maximum=1.0, field="top_p")
        object.__setattr__(
            self,
            "stop",
            _normalize_stop(self.stop, field="stop"),
        )


ReasoningEffort: TypeAlias = Literal["low", "medium", "high"]
Truncation: TypeAlias = Literal["auto", "disabled"]


@dataclass(frozen=True, slots=True)
class ResponsesOptions:
    """Options for the OpenAI Responses protocol."""

    temperature: float | None = None
    max_output_tokens: int | None = None
    top_p: float | None = None
    store: bool | None = None
    reasoning_effort: ReasoningEffort | None = None
    truncation: Truncation | None = None

    def __post_init__(self) -> None:
        _require_range(self.temperature, minimum=0.0, maximum=2.0, field="temperature")
        _require_positive_int(self.max_output_tokens, field="max_output_tokens")
        _require_range(self.top_p, minimum=0.0, maximum=1.0, field="top_p")
        if self.reasoning_effort not in {None, "low", "medium", "high"}:
            raise ConfigurationError(
                "reasoning_effort must be one of: low, medium, high"
            )
        if self.truncation not in {None, "auto", "disabled"}:
            raise ConfigurationError("truncation must be one of: auto, disabled")


@dataclass(frozen=True, slots=True)
class AnthropicThinkingBudget:
    """Anthropic extended thinking with an explicit token budget."""

    budget_tokens: int

    def __post_init__(self) -> None:
        if self.budget_tokens < 1024:
            raise ConfigurationError("thinking budget_tokens must be at least 1024")


@dataclass(frozen=True, slots=True)
class AnthropicThinkingAdaptive:
    """Anthropic adaptive thinking without a fixed token budget."""


AnthropicThinking: TypeAlias = AnthropicThinkingBudget | AnthropicThinkingAdaptive


def _is_thinking(value: object) -> bool:
    return isinstance(
        value,
        (AnthropicThinkingBudget, AnthropicThinkingAdaptive),
    )


@dataclass(frozen=True, slots=True)
class AnthropicMessagesOptions:
    """Options for the Anthropic Messages protocol."""

    temperature: float | None = None
    max_output_tokens: int | None = None
    top_p: float | None = None
    top_k: int | None = None
    stop_sequences: tuple[str, ...] | None = None
    thinking: AnthropicThinking | None = None

    def __post_init__(self) -> None:
        _require_range(self.temperature, minimum=0.0, maximum=1.0, field="temperature")
        _require_positive_int(self.max_output_tokens, field="max_output_tokens")
        _require_range(self.top_p, minimum=0.0, maximum=1.0, field="top_p")
        _require_positive_int(self.top_k, field="top_k")
        object.__setattr__(
            self,
            "stop_sequences",
            _normalize_stop(self.stop_sequences, field="stop_sequences"),
        )
        if self.thinking is not None and not _is_thinking(self.thinking):
            raise ConfigurationError(
                "thinking must be AnthropicThinkingBudget or "
                "AnthropicThinkingAdaptive"
            )
        if isinstance(self.thinking, AnthropicThinkingBudget):
            if self.max_output_tokens is None:
                raise ConfigurationError(
                    "max_output_tokens is required when thinking budget is set"
                )
            if self.thinking.budget_tokens >= self.max_output_tokens:
                raise ConfigurationError(
                    "thinking budget_tokens must be less than max_output_tokens"
                )


ProtocolOptions: TypeAlias = (
    ChatCompletionsOptions | ResponsesOptions | AnthropicMessagesOptions
)
