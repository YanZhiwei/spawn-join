"""Tests for the stable error hierarchy."""

import pytest

from spawn_join_llm_provider import (
    ChannelError,
    ChannelResponseError,
    ChannelUnavailableError,
    ConfigurationError,
    LLMProviderError,
    UnsupportedChannelOperationError,
)


def test_configuration_error_is_a_provider_error() -> None:
    assert issubclass(ConfigurationError, LLMProviderError)


@pytest.mark.parametrize(
    "error_type",
    [
        ChannelUnavailableError,
        UnsupportedChannelOperationError,
        ChannelResponseError,
    ],
)
def test_channel_errors_share_the_channel_base(
    error_type: type[ChannelError],
) -> None:
    assert issubclass(error_type, ChannelError)
    assert issubclass(error_type, LLMProviderError)


def test_errors_are_catchable_by_the_stable_base() -> None:
    with pytest.raises(LLMProviderError, match="channel unavailable"):
        raise ChannelUnavailableError("channel unavailable")


def test_error_messages_are_preserved() -> None:
    error = ConfigurationError("temperature must be between 0.0 and 2.0")
    assert str(error) == "temperature must be between 0.0 and 2.0"


def test_error_messages_do_not_require_provider_details() -> None:
    error = UnsupportedChannelOperationError("list_models")
    assert "list_models" in str(error)
