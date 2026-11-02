"""Validation and redaction for metadata source URLs."""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from spawn_join_llm_provider import ConfigurationError

_SENSITIVE_QUERY_NAMES = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "auth",
        "authorization",
        "client_secret",
        "credential",
        "credentials",
        "key",
        "password",
        "secret",
        "signature",
        "sig",
        "token",
    }
)
_SENSITIVE_QUERY_FRAGMENTS = (
    "token",
    "secret",
    "key",
    "auth",
    "password",
    "credential",
    "signature",
)


def _normalize_query_name(name: str) -> str:
    return name.strip().lower().replace("-", "_")


def _is_sensitive_query_name(name: str) -> bool:
    normalized = _normalize_query_name(name)
    if normalized in _SENSITIVE_QUERY_NAMES:
        return True
    return any(fragment in normalized for fragment in _SENSITIVE_QUERY_FRAGMENTS)


def validate_source_url(url: str) -> str:
    """Return a safe source URL or raise a credential-safe error."""
    text = url.strip()
    if not text:
        raise ConfigurationError("source url must not be empty")
    try:
        parts = urlsplit(text)
    except ValueError as exc:
        raise ConfigurationError("source url must be a valid URL") from exc
    if parts.scheme.lower() not in {"http", "https"}:
        raise ConfigurationError("source url must use http or https")
    if not parts.hostname:
        raise ConfigurationError("source url must include a host")
    if any(character.isspace() or ord(character) < 32 for character in parts.netloc):
        raise ConfigurationError("source url authority must not contain whitespace")
    try:
        _ = parts.port
    except ValueError as exc:
        raise ConfigurationError("source url must contain a valid port") from exc
    if parts.username is not None or parts.password is not None:
        raise ConfigurationError("source url must not embed credentials")
    try:
        query = parse_qsl(parts.query, keep_blank_values=True)
    except ValueError as exc:
        raise ConfigurationError("source url query must be valid") from exc
    if any(_is_sensitive_query_name(name) for name, _ in query):
        raise ConfigurationError(
            "source url must not contain credential query parameters"
        )
    return text


def redact_url(url: str) -> str:
    """Return a display-safe URL without userinfo or sensitive query values."""
    try:
        parts = urlsplit(url)
    except ValueError:
        return "<invalid-url>"
    netloc = parts.netloc.rsplit("@", 1)[-1] if "@" in parts.netloc else parts.netloc
    try:
        query = parse_qsl(parts.query, keep_blank_values=True)
    except ValueError:
        query = []
    redacted_query = urlencode(
        [
            (name, "***" if _is_sensitive_query_name(name) else value)
            for name, value in query
        ],
        doseq=True,
    )
    return urlunsplit((parts.scheme, netloc, parts.path, redacted_query, ""))
