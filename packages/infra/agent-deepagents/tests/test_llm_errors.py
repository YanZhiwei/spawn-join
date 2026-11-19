"""Runtime model error classification and normalization."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from langchain_core.exceptions import (
    ContextOverflowError,
    ModelAuthenticationError,
    ModelConnectionError,
    ModelRateLimitError,
    ModelTimeoutError,
)
from langgraph.errors import GraphInterrupt
from spawn_join_agent_deepagents.errors import (
    AgentConfigurationError,
    ContextOverflowLLMError,
    LLMCallError,
    LLMErrorCode,
)
from spawn_join_agent_deepagents.llm_errors import (
    LLMErrorNormalizationMiddleware,
    classify_llm_error,
    normalize_llm_error,
)


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("This model's maximum context length is 8192", LLMErrorCode.CONTEXT_OVERFLOW),
        ("Content Exists Risk", LLMErrorCode.CONTENT_REJECTED),
        ("insufficient balance", LLMErrorCode.INSUFFICIENT_BALANCE),
        ("budget exceeded", LLMErrorCode.SPEND_QUOTA_EXHAUSTED),
        ("429 Too Many Requests", LLMErrorCode.RATE_LIMIT),
        ("request timed out", LLMErrorCode.TIMEOUT),
        ("connection reset by peer", LLMErrorCode.CONNECTION),
        ("401 unauthorized", LLMErrorCode.AUTHENTICATION),
        ("unexpected provider failure", LLMErrorCode.INTERNAL_ERROR),
    ],
)
def test_classify_llm_error_maps_stable_categories(
    message: str,
    expected: LLMErrorCode,
) -> None:
    assert classify_llm_error(RuntimeError(message)) is expected


def test_quota_markers_map_to_spend_quota() -> None:
    assert (
        classify_llm_error(RuntimeError("Error code: 429 - insufficient_quota"))
        is LLMErrorCode.SPEND_QUOTA_EXHAUSTED
    )
    assert (
        classify_llm_error(RuntimeError("Your credit balance is too low"))
        is LLMErrorCode.SPEND_QUOTA_EXHAUSTED
    )


@pytest.mark.parametrize(
    "message",
    [
        "max_tokens=4032 exceeds the configured limit",
        "request id 14290 not found",
    ],
)
def test_digits_do_not_trigger_status_classification(message: str) -> None:
    assert classify_llm_error(RuntimeError(message)) is LLMErrorCode.INTERNAL_ERROR


@pytest.mark.parametrize(
    ("error_type", "expected"),
    [
        (ModelAuthenticationError, LLMErrorCode.AUTHENTICATION),
        (ModelRateLimitError, LLMErrorCode.RATE_LIMIT),
        (ModelTimeoutError, LLMErrorCode.TIMEOUT),
        (ModelConnectionError, LLMErrorCode.CONNECTION),
    ],
)
def test_native_model_errors_map_to_stable_categories(
    error_type: type[Exception],
    expected: LLMErrorCode,
) -> None:
    assert classify_llm_error(error_type("provider failure")) is expected


def test_context_overflow_keeps_both_types_and_hides_the_prompt() -> None:
    error = normalize_llm_error(ContextOverflowError("secret prompt text"))

    assert isinstance(error, LLMCallError)
    assert isinstance(error, ContextOverflowError)
    assert isinstance(error, ContextOverflowLLMError)
    assert error.code is LLMErrorCode.CONTEXT_OVERFLOW
    assert "secret prompt" not in str(error)


def test_normalize_is_idempotent() -> None:
    first = normalize_llm_error(RuntimeError("429 too many requests"))

    assert normalize_llm_error(first) is first


def test_normalized_message_hides_provider_details() -> None:
    original = RuntimeError("https://private.example/v1 failed with sk-secret")
    error = normalize_llm_error(original)

    assert "private.example" not in str(error)
    assert "sk-secret" not in str(error)
    assert error.__cause__ is original


def test_middleware_normalizes_sync_errors() -> None:
    middleware = LLMErrorNormalizationMiddleware()

    def handler(request: Any) -> Any:
        del request
        raise RuntimeError("429 too many requests")

    with pytest.raises(LLMCallError) as caught:
        middleware.wrap_model_call(object(), handler)

    assert caught.value.code is LLMErrorCode.RATE_LIMIT
    assert isinstance(caught.value.__cause__, RuntimeError)


def test_middleware_normalizes_async_errors() -> None:
    middleware = LLMErrorNormalizationMiddleware()

    async def handler(request: Any) -> Any:
        del request
        raise RuntimeError("request timed out")

    with pytest.raises(LLMCallError) as caught:
        asyncio.run(middleware.awrap_model_call(object(), handler))

    assert caught.value.code is LLMErrorCode.TIMEOUT


def test_middleware_propagates_cancellation() -> None:
    middleware = LLMErrorNormalizationMiddleware()

    async def handler(request: Any) -> Any:
        del request
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        asyncio.run(middleware.awrap_model_call(object(), handler))


def test_middleware_propagates_graph_interrupt() -> None:
    middleware = LLMErrorNormalizationMiddleware()

    def handler(request: Any) -> Any:
        del request
        raise GraphInterrupt()

    with pytest.raises(GraphInterrupt):
        middleware.wrap_model_call(object(), handler)


def test_middleware_keeps_existing_llm_call_error() -> None:
    middleware = LLMErrorNormalizationMiddleware()
    original = LLMCallError(LLMErrorCode.AUTHENTICATION, "safe")

    def handler(request: Any) -> Any:
        del request
        raise original

    with pytest.raises(LLMCallError) as caught:
        middleware.wrap_model_call(object(), handler)

    assert caught.value is original


def test_middleware_propagates_configuration_errors() -> None:
    middleware = LLMErrorNormalizationMiddleware()

    def handler(request: Any) -> Any:
        del request
        raise AgentConfigurationError("configuration")

    with pytest.raises(AgentConfigurationError):
        middleware.wrap_model_call(object(), handler)
