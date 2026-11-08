"""SDK error mapping tests."""

import pytest
from spawn_join_llm_channel._errors import list_error, ping_result

from spawn_join_llm_provider import (
    ChannelAuthenticationError,
    ChannelResponseError,
    ChannelStatus,
    ChannelUnavailableError,
    UnsupportedChannelOperationError,
)

from . import _sdk


def test_authentication_maps_to_authentication_failed() -> None:
    result = ping_result(_sdk.openai_auth(), latency_ms=1.0)
    assert result.status is ChannelStatus.AUTHENTICATION_FAILED
    assert result.detail == "authentication failed"


def test_timeout_maps_to_timeout() -> None:
    result = ping_result(_sdk.openai_timeout(), latency_ms=1.0)
    assert result.status is ChannelStatus.TIMEOUT
    assert result.detail == "request timed out"


def test_connection_maps_to_unreachable() -> None:
    result = ping_result(_sdk.openai_connection(), latency_ms=1.0)
    assert result.status is ChannelStatus.UNREACHABLE


def test_rate_limit_and_server_map_to_unreachable() -> None:
    rate = ping_result(_sdk.openai_rate_limit(), latency_ms=1.0)
    server = ping_result(_sdk.openai_server(), latency_ms=1.0)
    assert rate.status is ChannelStatus.UNREACHABLE
    assert server.status is ChannelStatus.UNREACHABLE


def test_not_found_maps_to_unsupported() -> None:
    result = ping_result(_sdk.openai_not_found(), latency_ms=1.0)
    assert result.status is ChannelStatus.UNSUPPORTED


@pytest.mark.parametrize("status_code", [401, 403])
def test_generic_auth_status_maps_to_authentication_failed(status_code: int) -> None:
    result = ping_result(_sdk.openai_status(status_code), latency_ms=1.0)
    assert result.status is ChannelStatus.AUTHENTICATION_FAILED
    assert isinstance(
        list_error(_sdk.openai_status(status_code)),
        ChannelAuthenticationError,
    )


def test_response_validation_maps_to_invalid_response() -> None:
    result = ping_result(_sdk.openai_validation(), latency_ms=1.0)
    assert result.status is ChannelStatus.INVALID_RESPONSE


def test_unknown_exception_maps_to_invalid_response() -> None:
    result = ping_result(ValueError("boom"), latency_ms=1.0)
    assert result.status is ChannelStatus.INVALID_RESPONSE
    assert "boom" not in (result.detail or "")


def test_list_errors_are_stable_and_safe() -> None:
    auth = list_error(_sdk.openai_auth())
    timeout = list_error(_sdk.openai_timeout())
    unsupported = list_error(_sdk.openai_not_found())
    response = list_error(_sdk.openai_validation())
    assert isinstance(auth, ChannelAuthenticationError)
    assert isinstance(timeout, ChannelUnavailableError)
    assert isinstance(unsupported, UnsupportedChannelOperationError)
    assert isinstance(response, ChannelResponseError)
    assert "sk-" not in str(auth)


def test_anthropic_errors_share_the_mapping() -> None:
    assert (
        ping_result(_sdk.anthropic_auth(), latency_ms=1.0).status
        is ChannelStatus.AUTHENTICATION_FAILED
    )
    assert isinstance(
        list_error(_sdk.anthropic_not_found()),
        UnsupportedChannelOperationError,
    )
