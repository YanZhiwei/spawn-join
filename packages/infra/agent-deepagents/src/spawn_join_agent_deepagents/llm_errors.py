"""Runtime model-call error classification and normalization."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware
from langchain_core.exceptions import (
    ContextOverflowError,
    ModelAuthenticationError,
    ModelConnectionError,
    ModelPermissionDeniedError,
    ModelRateLimitError,
    ModelTimeoutError,
)
from langgraph.errors import GraphBubbleUp

from .errors import (
    AgentConfigurationError,
    ContextOverflowLLMError,
    LLMCallError,
    LLMErrorCode,
)
from .middleware import LLM_ERROR_MIDDLEWARE_NAME

_CONTEXT_OVERFLOW_MARKERS = (
    "context_length_exceeded",
    "maximum context length",
    "exceeds the context window",
    "contextwindowexceedederror",
    "context window exceeded",
    "context limit exceeded",
    "prompt is too long",
    "input tokens exceed",
    "input tokens exceed the configured limit",
    "reduce the length of the messages",
)

_CONTENT_REJECTION_MARKERS = (
    "content exists risk",
    "content_filter",
)

_SPEND_QUOTA_MARKERS = (
    "budgetexceeded",
    "budget_exceeded",
    "budget exceeded",
    "spend quota",
    "spend_quota",
    "quota exhausted",
    "insufficient_quota",
    "insufficient quota",
    "exceeded your current quota",
    "credit balance",
    "billing hard limit",
)

_TEXT_RULES: tuple[tuple[LLMErrorCode, tuple[str, ...]], ...] = (
    (LLMErrorCode.CONTEXT_OVERFLOW, _CONTEXT_OVERFLOW_MARKERS),
    (LLMErrorCode.CONTENT_REJECTED, _CONTENT_REJECTION_MARKERS),
    (
        LLMErrorCode.AUTHENTICATION,
        ("unauthorized", "invalid api key", "forbidden", "permission denied"),
    ),
    (
        LLMErrorCode.INSUFFICIENT_BALANCE,
        ("insufficient balance", "insufficient_balance", "insufficient credits"),
    ),
    (
        LLMErrorCode.RATE_LIMIT,
        ("ratelimit", "rate limit", "too many requests"),
    ),
    (LLMErrorCode.TIMEOUT, ("timeout", "timed out")),
    (LLMErrorCode.CONNECTION, ("connection", "connect", "network", "unreachable")),
)

_MESSAGES: dict[LLMErrorCode, str] = {
    LLMErrorCode.CONTEXT_OVERFLOW: (
        "The model context window was exceeded. Start a new conversation or "
        "reduce the input."
    ),
    LLMErrorCode.CONTENT_REJECTED: (
        "The model provider rejected the request content. Rephrase the request "
        "or start a new conversation."
    ),
    LLMErrorCode.INSUFFICIENT_BALANCE: (
        "The model account has insufficient balance. Check the account or switch "
        "models."
    ),
    LLMErrorCode.SPEND_QUOTA_EXHAUSTED: (
        "The spend quota for this period is exhausted. Try again later or contact "
        "an administrator."
    ),
    LLMErrorCode.RATE_LIMIT: "The model is rate limited. Try again later.",
    LLMErrorCode.TIMEOUT: "The model request timed out. Try again later.",
    LLMErrorCode.CONNECTION: "The model service is unreachable. Try again later.",
    LLMErrorCode.AUTHENTICATION: (
        "The model configuration is not usable. Contact an administrator."
    ),
    LLMErrorCode.INTERNAL_ERROR: "The model could not respond. Try again later.",
}


def _status_code(exc: Exception) -> int | None:
    for name in ("status_code", "status", "http_status", "http_status_code"):
        value = getattr(exc, name, None)
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def _has_spend_marker(text: str) -> bool:
    return any(marker in text for marker in _SPEND_QUOTA_MARKERS)


def _native_model_code(exc: Exception, text: str) -> LLMErrorCode | None:
    if isinstance(exc, (ModelAuthenticationError, ModelPermissionDeniedError)):
        return LLMErrorCode.AUTHENTICATION
    if isinstance(exc, ModelRateLimitError):
        if _has_spend_marker(text):
            return LLMErrorCode.SPEND_QUOTA_EXHAUSTED
        return LLMErrorCode.RATE_LIMIT
    if isinstance(exc, ModelTimeoutError):
        return LLMErrorCode.TIMEOUT
    if isinstance(exc, ModelConnectionError):
        return LLMErrorCode.CONNECTION
    return None


def _status_code_rule(status: int | None, text: str) -> LLMErrorCode | None:
    if status in (401, 403):
        return LLMErrorCode.AUTHENTICATION
    if status == 402:
        return LLMErrorCode.INSUFFICIENT_BALANCE
    if status == 429:
        if _has_spend_marker(text):
            return LLMErrorCode.SPEND_QUOTA_EXHAUSTED
        return LLMErrorCode.RATE_LIMIT
    return None


def _text_rule(text: str) -> LLMErrorCode:
    for code, markers in _TEXT_RULES:
        if any(marker in text for marker in markers):
            return code
    return LLMErrorCode.INTERNAL_ERROR


def classify_llm_error(exc: Exception) -> LLMErrorCode:
    """Map one provider exception to a stable category without SDK imports."""
    if isinstance(exc, ContextOverflowError):
        return LLMErrorCode.CONTEXT_OVERFLOW

    text = f"{type(exc).__name__} {exc}".lower()

    native = _native_model_code(exc, text)
    if native is not None:
        return native

    by_status = _status_code_rule(_status_code(exc), text)
    if by_status is not None:
        return by_status

    if _has_spend_marker(text):
        return LLMErrorCode.SPEND_QUOTA_EXHAUSTED
    return _text_rule(text)


def normalize_llm_error(exc: Exception) -> LLMCallError:
    """Return a redacted error and attach the original as ``__cause__``.

    The middleware re-raises with ``from exc``; direct callers also keep the
    diagnosis channel because this function sets ``__cause__`` itself.
    """
    if isinstance(exc, LLMCallError):
        return exc

    code = classify_llm_error(exc)
    message = _MESSAGES[code]
    normalized: LLMCallError
    if code is LLMErrorCode.CONTEXT_OVERFLOW:
        normalized = ContextOverflowLLMError(code, message)
    else:
        normalized = LLMCallError(code, message)
    normalized.__cause__ = exc
    return normalized


class LLMErrorNormalizationMiddleware(AgentMiddleware[Any, Any, Any]):
    """Normalize model-call failures into stable, redacted errors.

    Only model-call failures are caught. Configuration errors, LangGraph control
    flow (``GraphBubbleUp``), and cancellation propagate unchanged. The middleware
    adds no logging and never copies provider text into the public message; the
    original exception stays in ``__cause__``.

    Note: DeepAgents inserts host middleware after its own base stack, so
    summarization middleware errors may bypass this seam.
    """

    @property
    def name(self) -> str:
        return LLM_ERROR_MIDDLEWARE_NAME

    def wrap_model_call(
        self,
        request: Any,
        handler: Callable[[Any], Any],
    ) -> Any:
        try:
            return handler(request)
        except (AgentConfigurationError, GraphBubbleUp):
            raise
        except Exception as exc:
            raise normalize_llm_error(exc) from exc

    async def awrap_model_call(
        self,
        request: Any,
        handler: Callable[[Any], Awaitable[Any]],
    ) -> Any:
        try:
            return await handler(request)
        except (AgentConfigurationError, GraphBubbleUp):
            raise
        except Exception as exc:
            raise normalize_llm_error(exc) from exc


__all__ = [
    "LLMErrorNormalizationMiddleware",
    "classify_llm_error",
    "normalize_llm_error",
]
