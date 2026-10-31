"""Framework-independent channel contracts for connection checks and model discovery."""

import unicodedata
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import Protocol

from .endpoints import EndpointConfig
from .errors import ConfigurationError


def _validate_name(name: str) -> None:
    if not name or name != name.strip():
        raise ConfigurationError(
            "Channel name must be non-empty without surrounding whitespace"
        )
    if any(unicodedata.category(character).startswith("C") for character in name):
        raise ConfigurationError("Channel name must not contain control characters")


def _validate_credential_ref(credential_ref: str) -> None:
    if not credential_ref.strip():
        raise ConfigurationError("Channel credential_ref must not be empty")


@dataclass(frozen=True, slots=True, kw_only=True)
class ChannelConfig(EndpointConfig):
    """A named connection configuration without a plaintext credential."""

    name: str
    credential_ref: str

    def __post_init__(self) -> None:
        EndpointConfig.__post_init__(self)
        _validate_name(self.name)
        _validate_credential_ref(self.credential_ref)


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
