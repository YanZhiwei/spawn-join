"""Shared endpoint configuration for channels and LangChain models."""

import unicodedata
from dataclasses import dataclass
from math import isfinite
from urllib.parse import urlsplit

from .errors import ConfigurationError
from .options import ProtocolKind


def _is_protocol_kind(value: object) -> bool:
    return isinstance(value, ProtocolKind)


def _validate_hostname(hostname: str) -> None:
    if hostname.endswith(".."):
        raise ConfigurationError("Endpoint must contain a valid hostname")
    normalized = hostname[:-1] if hostname.endswith(".") else hostname
    if not normalized or len(normalized) > 253:
        raise ConfigurationError("Endpoint must contain a valid hostname")
    for label in normalized.split("."):
        if not label or len(label) > 63:
            raise ConfigurationError("Endpoint must contain a valid hostname")
        if label.startswith("-") or label.endswith("-"):
            raise ConfigurationError("Endpoint must contain a valid hostname")


def _validate_endpoint(endpoint: str) -> None:
    if endpoint != endpoint.strip():
        raise ConfigurationError("Endpoint must not have surrounding whitespace")
    if any(
        character.isspace() or unicodedata.category(character).startswith("C")
        for character in endpoint
    ):
        raise ConfigurationError(
            "Endpoint must not contain whitespace or control characters"
        )

    try:
        parsed = urlsplit(endpoint)
        port = parsed.port
    except ValueError as exc:
        raise ConfigurationError("Endpoint is not a valid URL") from exc

    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ConfigurationError("Endpoint must be an absolute http(s) URL")
    if parsed.username is not None or parsed.password is not None:
        raise ConfigurationError("Endpoint must not contain credentials")

    hostname = parsed.hostname
    if hostname is None:
        raise ConfigurationError("Endpoint must contain a valid hostname")
    _validate_hostname(hostname)
    if port is not None and not 1 <= port <= 65535:
        raise ConfigurationError("Endpoint must use a valid network port")


def _validate_timeout(timeout_seconds: float) -> None:
    if not isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ConfigurationError("Endpoint timeout_seconds must be finite and positive")


@dataclass(frozen=True, slots=True, kw_only=True)
class EndpointConfig:
    """Protocol, endpoint and timeout shared by channels and model configs."""

    protocol: ProtocolKind
    endpoint: str
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if not _is_protocol_kind(self.protocol):
            raise ConfigurationError("Endpoint protocol must be a ProtocolKind")
        _validate_endpoint(self.endpoint)
        _validate_timeout(self.timeout_seconds)
