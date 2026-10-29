"""Channel contracts for connection checks and model discovery."""

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Protocol
from urllib.parse import urlsplit

from .errors import ConfigurationError
from .options import ProtocolKind


@dataclass(frozen=True, slots=True)
class ChannelConfig:
    """A configured connection without a plaintext credential."""

    protocol: ProtocolKind
    base_url: str
    credential_ref: str
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        try:
            parsed = urlsplit(self.base_url)
            port = parsed.port
        except ValueError as exc:
            raise ConfigurationError("Channel base_url is not a valid URL") from exc

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ConfigurationError("Channel base_url must be an absolute http(s) URL")
        if parsed.username is not None or parsed.password is not None:
            raise ConfigurationError("Channel base_url must not contain credentials")

        hostname = parsed.hostname
        if (
            hostname is None
            or not hostname.strip()
            or any(character.isspace() or ord(character) < 32 for character in hostname)
        ):
            raise ConfigurationError("Channel base_url must contain a valid hostname")
        if port is not None and not 1 <= port <= 65535:
            raise ConfigurationError("Channel base_url must use a valid network port")
        if not self.credential_ref.strip():
            raise ConfigurationError("Channel credential_ref must not be empty")
        if not isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ConfigurationError(
                "Channel timeout_seconds must be finite and positive"
            )


@dataclass(frozen=True, slots=True)
class ChannelCapabilities:
    """Optional channel operations declared by an implementation."""

    model_listing: bool = False
    health_check: bool = True


class ChannelStatus(StrEnum):
    """Outcome of a channel connectivity/authentication check."""

    OK = "ok"
    AUTH_FAILED = "auth_failed"
    UNREACHABLE = "unreachable"
    TIMEOUT = "timeout"
    UNSUPPORTED = "unsupported"
    INVALID_RESPONSE = "invalid_response"


@dataclass(frozen=True, slots=True)
class PingResult:
    """Result of a channel check that does not generate a completion."""

    status: ChannelStatus
    check_method: str
    latency_ms: int
    message: str | None = None


@dataclass(frozen=True, slots=True)
class ModelInfo:
    """A model identifier exposed by a channel."""

    id: str
    display_name: str | None = None


@dataclass(frozen=True, slots=True)
class ModelPage:
    """A page of model identifiers; an empty page is a valid result."""

    models: tuple[ModelInfo, ...]
    next_cursor: str | None = None


class Channel(Protocol):
    """A connection-level capability surface separate from inference providers."""

    @property
    def config(self) -> ChannelConfig:
        """Return the immutable channel configuration."""
        ...

    @property
    def capabilities(self) -> ChannelCapabilities:
        """Return the optional operations implemented by this channel."""
        ...

    async def ping(self) -> PingResult:
        """Check reachability and authentication without generating a completion."""
        ...

    async def list_models(
        self,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> ModelPage:
        """Return a page of models or raise an explicit unsupported error."""
        ...
