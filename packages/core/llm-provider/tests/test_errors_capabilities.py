"""Contract tests for stable errors and tri-state capabilities."""

import pytest

from spawn_join_llm_provider import (
    AuthenticationError,
    ChannelUnavailableError,
    ConfigurationError,
    ContextOverflowError,
    InvalidRequestError,
    LLMError,
    MalformedResponseError,
    ModelCapabilities,
    ModelNotFoundError,
    PermissionDeniedError,
    ProtocolKind,
    ProviderAPIError,
    ProviderConnectionError,
    ProviderTimeoutError,
    RateLimitError,
    UnsupportedChannelOperationError,
    UnsupportedParameterError,
)


def test_unsupported_parameter_error_carries_context() -> None:
    error = UnsupportedParameterError(
        "stop",
        protocol=ProtocolKind.RESPONSES,
        model="test-model",
    )

    assert error.parameter == "stop"
    assert error.protocol == ProtocolKind.RESPONSES
    assert error.model == "test-model"
    assert "stop" in str(error)
    assert "responses" in str(error)


@pytest.mark.parametrize(
    "error_type",
    [
        ConfigurationError,
        InvalidRequestError,
        AuthenticationError,
        PermissionDeniedError,
        RateLimitError,
        ProviderTimeoutError,
        ProviderConnectionError,
        ModelNotFoundError,
        ContextOverflowError,
        MalformedResponseError,
        ProviderAPIError,
        ChannelUnavailableError,
        UnsupportedChannelOperationError,
        UnsupportedParameterError,
    ],
)
def test_error_hierarchy(error_type: type[LLMError]) -> None:
    assert issubclass(error_type, LLMError)


def test_unsupported_parameter_is_an_invalid_request() -> None:
    assert issubclass(UnsupportedParameterError, InvalidRequestError)


def test_unsupported_channel_operation_names_operation() -> None:
    error = UnsupportedChannelOperationError("list_models")
    assert error.operation == "list_models"
    assert "list_models" in str(error)


def test_capabilities_unknown_is_not_false() -> None:
    unknown = ModelCapabilities()
    known_false = ModelCapabilities(supports_tools=False)

    assert unknown.supports_tools is None
    assert unknown.supports_reasoning is None
    assert known_false.supports_tools is False
