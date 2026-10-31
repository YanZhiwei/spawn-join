"""Configuration and pre-call validation for LangChain model creation."""

from dataclasses import dataclass

from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    ChatCompletionsOptions,
    ConfigurationError,
    EndpointConfig,
    ProtocolKind,
    ProtocolOptions,
    ResponsesOptions,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ChatModelConfig(EndpointConfig):
    """Endpoint settings plus the model name and retry policy."""

    model: str
    max_retries: int = 0

    def __post_init__(self) -> None:
        EndpointConfig.__post_init__(self)
        if not self.model or self.model != self.model.strip():
            raise ConfigurationError(
                "Chat model must be non-empty without surrounding whitespace"
            )
        if self.max_retries < 0:
            raise ConfigurationError("Chat model max_retries must be non-negative")


def validate_api_key(api_key: str) -> None:
    """Reject empty or whitespace-padded API keys before constructing a model."""
    if not api_key or api_key != api_key.strip():
        raise ConfigurationError(
            "API key must be non-empty without surrounding whitespace"
        )


def _is_option_type(
    value: object,
    expected: tuple[type[object], ...],
) -> bool:
    return isinstance(value, expected)


def validate_options(
    protocol: ProtocolKind,
    options: ProtocolOptions | None,
) -> None:
    """Reject options that do not belong to the configured protocol."""
    if options is None:
        return

    match protocol:
        case ProtocolKind.CHAT_COMPLETIONS:
            expected = (ChatCompletionsOptions,)
        case ProtocolKind.RESPONSES:
            expected = (ResponsesOptions,)
        case ProtocolKind.ANTHROPIC_MESSAGES:
            expected = (AnthropicMessagesOptions,)
        case _:
            raise ConfigurationError(f"Unsupported protocol: {protocol}")

    if not _is_option_type(options, expected):
        protocol_label = getattr(protocol, "value", str(protocol))
        raise ConfigurationError(
            f"{type(options).__name__} is not valid for {protocol_label}"
        )


def validate_request(
    config: ChatModelConfig,
    *,
    api_key: str,
    options: ProtocolOptions | None,
) -> None:
    """Validate a model request before any LangChain object is constructed."""
    validate_api_key(api_key)
    validate_options(config.protocol, options)
