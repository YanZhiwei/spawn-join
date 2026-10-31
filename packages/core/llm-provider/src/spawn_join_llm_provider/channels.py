"""Framework-independent channel contracts for connection checks and model discovery."""

import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Protocol
from urllib.parse import urlsplit

from .errors import ConfigurationError
from .options import ProtocolKind


def _validate_name(name: str) -> None:
    if not name or name != name.strip():
        raise ConfigurationError(
            "Channel name must be non-empty without surrounding whitespace"
        )
    if any(unicodedata.category(character).startswith("C") for character in name):
        raise ConfigurationError("Channel name must not contain control characters")


def _validate_hostname(hostname: str) -> None:
    if hostname.endswith(".."):
        raise ConfigurationError("Channel endpoint must contain a valid hostname")
    normalized = hostname[:-1] if hostname.endswith(".") else hostname
    if not normalized or len(normalized) > 253:
        raise ConfigurationError("Channel endpoint must contain a valid hostname")
    for label in normalized.split("."):
        if not label or len(label) > 63:
            raise ConfigurationError("Channel endpoint must contain a valid hostname")
        if label.startswith("-") or label.endswith("-"):
            raise ConfigurationError("Channel endpoint must contain a valid hostname")


def _validate_endpoint(endpoint: str) -> None:
    if endpoint != endpoint.strip():
        raise ConfigurationError(
            "Channel endpoint must not have surrounding whitespace"
        )
    if any(
        character.isspace() or unicodedata.category(character).startswith("C")
        for character in endpoint
    ):
        raise ConfigurationError(
            "Channel endpoint must not contain whitespace or control characters"
        )

    try:
        parsed = urlsplit(endpoint)
        port = parsed.port
    except ValueError as exc:
        raise ConfigurationError("Channel endpoint is not a valid URL") from exc

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigurationError("Channel endpoint must be an absolute http(s) URL")
    if parsed.username is not None or parsed.password is not None:
        raise ConfigurationError("Channel endpoint must not contain credentials")

    hostname = parsed.hostname
    if hostname is None:
        raise ConfigurationError("Channel endpoint must contain a valid hostname")
    _validate_hostname(hostname)
    if port is not None and not 1 <= port <= 65535:
        raise ConfigurationError("Channel endpoint must use a valid network port")


def _validate_credential_ref(credential_ref: str) -> None:
    if not credential_ref.strip():
        raise ConfigurationError("Channel credential_ref must not be empty")


def _validate_timeout(timeout_seconds: float) -> None:
    if not isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ConfigurationError("Channel timeout_seconds must be finite and positive")


@dataclass(frozen=True, slots=True)
class ChannelConfig:
    """A configured connection without a plaintext credential."""

    name: str
    protocol: ProtocolKind
    endpoint: str
    credential_ref: str
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        _validate_name(self.name)
        _validate_endpoint(self.endpoint)
        _validate_credential_ref(self.credential_ref)
        _validate_timeout(self.timeout_seconds)


class ChannelStatus(StrEnum):
    """Outcome of a channel connectivity and authentication check."""

    OK = "ok"
    AUTHENTICATION_FAILED = "authentication_failed"
    UNREACHABLE = "unreachable"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"


@dataclass(frozen=True, slots=True)
class PingResult:
    """Result of a channel check that does not generate a completion."""

    status: ChannelStatus
    latency_ms: float | None = None
    detail: str | None = None

    def __post_init__(self) -> None:
        if self.latency_ms is not None and (
            not isfinite(self.latency_ms) or self.latency_ms < 0
        ):
            raise ConfigurationError(
                "PingResult latency_ms must be finite and non-negative"
            )

    @property
    def ok(self) -> bool:
        """Return whether the channel check succeeded."""
        return self.status is ChannelStatus.OK


@dataclass(frozen=True, slots=True)
class ModelInfo:
    """A model identifier exposed by a channel."""

    id: str
    display_name: str | None = None

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ConfigurationError("ModelInfo id must not be empty")


@dataclass(frozen=True, slots=True)
class ModelPage:
    """A page of model identifiers; an empty page is a valid success."""

    models: tuple[ModelInfo, ...] = ()
    next_cursor: str | None = None


class Channel(Protocol):
    """A connection-level capability surface separate from inference providers."""

    @property
    def config(self) -> ChannelConfig:
        """Return the immutable channel configuration."""
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
        """Return a page of models or raise an explicit channel error.

        ``limit``, when provided, must be positive. An empty ``ModelPage`` is a
        successful result and must not be used to represent an unsupported
        operation or a failed request.
        """
        ...
