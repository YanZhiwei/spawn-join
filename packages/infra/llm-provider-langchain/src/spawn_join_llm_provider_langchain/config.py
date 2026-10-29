"""Configuration objects for LangChain-backed LLM providers."""

from dataclasses import dataclass
from math import isfinite
from urllib.parse import urlsplit

from spawn_join_llm_provider import (
    ConfigurationError,
    ModelCapabilities,
    ProtocolKind,
)


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    """Common configuration without a plaintext credential."""

    model: str
    credential_ref: str
    base_url: str | None = None
    timeout_seconds: float = 30.0
    capabilities: ModelCapabilities | None = None

    @property
    def protocol(self) -> ProtocolKind:
        """Return the protocol selected by the concrete configuration."""
        raise NotImplementedError

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ConfigurationError("Provider model must not be empty")
        if not self.credential_ref.strip():
            raise ConfigurationError("Provider credential_ref must not be empty")
        if not isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ConfigurationError(
                "Provider timeout_seconds must be finite and positive"
            )
        if self.base_url is not None:
            _validate_base_url(self.base_url)


@dataclass(frozen=True, slots=True)
class ChatCompletionsConfig(ProviderConfig):
    """Configuration for an OpenAI-compatible Chat Completions endpoint."""

    @property
    def protocol(self) -> ProtocolKind:
        return ProtocolKind.CHAT_COMPLETIONS


@dataclass(frozen=True, slots=True)
class ResponsesConfig(ProviderConfig):
    """Configuration for an OpenAI-compatible Responses endpoint."""

    @property
    def protocol(self) -> ProtocolKind:
        return ProtocolKind.RESPONSES


@dataclass(frozen=True, slots=True)
class AnthropicMessagesConfig(ProviderConfig):
    """Configuration for an Anthropic Messages endpoint."""

    @property
    def protocol(self) -> ProtocolKind:
        return ProtocolKind.ANTHROPIC_MESSAGES


ProviderConfigType = ChatCompletionsConfig | ResponsesConfig | AnthropicMessagesConfig


def _validate_base_url(base_url: str) -> None:
    try:
        parsed = urlsplit(base_url)
        _ = parsed.port
    except ValueError as exc:
        raise ConfigurationError("Provider base_url is not a valid URL") from exc

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigurationError("Provider base_url must be an absolute http(s) URL")
    if parsed.username is not None or parsed.password is not None:
        raise ConfigurationError("Provider base_url must not contain credentials")

    hostname = parsed.hostname
    if (
        hostname is None
        or not hostname.strip()
        or any(character.isspace() or ord(character) < 32 for character in hostname)
    ):
        raise ConfigurationError("Provider base_url must contain a valid hostname")
