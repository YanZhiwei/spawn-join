"""Map Provider SDK failures to the stable channel contract."""

from enum import StrEnum

import anthropic
import openai

from spawn_join_llm_provider import (
    ChannelAuthenticationError,
    ChannelError,
    ChannelResponseError,
    ChannelStatus,
    ChannelUnavailableError,
    PingResult,
    UnsupportedChannelOperationError,
)


class _ErrorKind(StrEnum):
    AUTHENTICATION = "authentication"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    RATE_LIMIT = "rate_limit"
    SERVER = "server"
    UNSUPPORTED = "unsupported"
    RESPONSE = "response"
    OTHER = "other"


def _is_authentication(exc: Exception) -> bool:
    return isinstance(
        exc,
        (
            openai.AuthenticationError,
            openai.PermissionDeniedError,
            anthropic.AuthenticationError,
            anthropic.PermissionDeniedError,
        ),
    )


def _is_timeout(exc: Exception) -> bool:
    return isinstance(
        exc,
        (openai.APITimeoutError, anthropic.APITimeoutError, TimeoutError),
    )


def _is_connection(exc: Exception) -> bool:
    return isinstance(
        exc,
        (
            openai.APIConnectionError,
            anthropic.APIConnectionError,
            ConnectionError,
            OSError,
        ),
    )


def _is_response_validation(exc: Exception) -> bool:
    return isinstance(
        exc,
        (openai.APIResponseValidationError, anthropic.APIResponseValidationError),
    )


def _is_rate_limit(exc: Exception) -> bool:
    return isinstance(exc, (openai.RateLimitError, anthropic.RateLimitError))


def _is_server_error(exc: Exception) -> bool:
    return isinstance(exc, (openai.InternalServerError, anthropic.InternalServerError))


def _status_code(exc: Exception) -> int | None:
    if isinstance(exc, (openai.APIStatusError, anthropic.APIStatusError)):
        return exc.status_code
    return None


def _status_kind(status_code: int | None) -> _ErrorKind | None:
    if status_code in {401, 403}:
        return _ErrorKind.AUTHENTICATION
    if status_code in {404, 405}:
        return _ErrorKind.UNSUPPORTED
    if status_code == 429:
        return _ErrorKind.RATE_LIMIT
    if status_code is not None and status_code >= 500:
        return _ErrorKind.SERVER
    return None


def _classify(exc: Exception) -> _ErrorKind:
    if _is_authentication(exc):
        return _ErrorKind.AUTHENTICATION
    if _is_timeout(exc):
        return _ErrorKind.TIMEOUT
    if _is_connection(exc):
        return _ErrorKind.CONNECTION
    if _is_response_validation(exc):
        return _ErrorKind.RESPONSE
    status_kind = _status_kind(_status_code(exc))
    if status_kind is not None:
        return status_kind
    if _is_rate_limit(exc):
        return _ErrorKind.RATE_LIMIT
    if _is_server_error(exc):
        return _ErrorKind.SERVER
    if isinstance(exc, (openai.APIError, anthropic.APIError)):
        return _ErrorKind.RESPONSE
    return _ErrorKind.OTHER


def _ping_status(kind: _ErrorKind) -> ChannelStatus:
    match kind:
        case _ErrorKind.AUTHENTICATION:
            return ChannelStatus.AUTHENTICATION_FAILED
        case _ErrorKind.TIMEOUT:
            return ChannelStatus.TIMEOUT
        case _ErrorKind.CONNECTION | _ErrorKind.RATE_LIMIT | _ErrorKind.SERVER:
            return ChannelStatus.UNREACHABLE
        case _ErrorKind.UNSUPPORTED:
            return ChannelStatus.UNSUPPORTED
        case _ErrorKind.RESPONSE | _ErrorKind.OTHER:
            return ChannelStatus.INVALID_RESPONSE


def _detail(kind: _ErrorKind) -> str:
    match kind:
        case _ErrorKind.AUTHENTICATION:
            return "authentication failed"
        case _ErrorKind.TIMEOUT:
            return "request timed out"
        case _ErrorKind.CONNECTION:
            return "channel is unreachable"
        case _ErrorKind.RATE_LIMIT:
            return "channel is rate limited"
        case _ErrorKind.SERVER:
            return "channel is unavailable"
        case _ErrorKind.UNSUPPORTED:
            return "model listing is not supported"
        case _ErrorKind.RESPONSE | _ErrorKind.OTHER:
            return "invalid response"


def ping_result(exc: Exception, *, latency_ms: float) -> PingResult:
    """Return a safe ping result for a Provider SDK failure."""
    kind = _classify(exc)
    return PingResult(
        status=_ping_status(kind),
        latency_ms=latency_ms,
        detail=_detail(kind),
    )


def list_error(exc: Exception) -> ChannelError:
    """Return the stable channel error for a failed model listing."""
    kind = _classify(exc)
    match kind:
        case _ErrorKind.AUTHENTICATION:
            return ChannelAuthenticationError("authentication failed")
        case _ErrorKind.TIMEOUT | _ErrorKind.CONNECTION | _ErrorKind.RATE_LIMIT:
            return ChannelUnavailableError("channel is unavailable")
        case _ErrorKind.SERVER:
            return ChannelUnavailableError("channel is unavailable")
        case _ErrorKind.UNSUPPORTED:
            return UnsupportedChannelOperationError("model listing is not supported")
        case _ErrorKind.RESPONSE | _ErrorKind.OTHER:
            return ChannelResponseError("invalid model listing response")
