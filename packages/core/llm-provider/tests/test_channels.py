"""Validation tests for the public channel configuration contract."""

import pytest

from spawn_join_llm_provider import (
    ChannelConfig,
    ConfigurationError,
    ProtocolKind,
)


def test_valid_channel_config() -> None:
    config = ChannelConfig(
        protocol=ProtocolKind.CHAT_COMPLETIONS,
        base_url="https://example.com/v1",
        credential_ref="TEST_API_KEY",
        timeout_seconds=5.0,
    )

    assert config.base_url == "https://example.com/v1"
    assert config.timeout_seconds == 5.0


def test_valid_http_channel_config() -> None:
    config = ChannelConfig(
        protocol=ProtocolKind.CHAT_COMPLETIONS,
        base_url="http://localhost:8000/v1",
        credential_ref="TEST_API_KEY",
    )

    assert config.base_url == "http://localhost:8000/v1"


@pytest.mark.parametrize(
    "base_url",
    [
        "ftp://example.com/v1",
        "https://",
        "https://user:secret@example.com/v1",
        "not-a-url",
        "https://[::1",
        "https://exa mple.com/v1",
        "https://example.com:bad/v1",
        "https://example.com:70000/v1",
        "https://example.com:0/v1",
    ],
)
def test_channel_config_rejects_unsafe_or_invalid_urls(base_url: str) -> None:
    with pytest.raises(ConfigurationError):
        ChannelConfig(
            protocol=ProtocolKind.RESPONSES,
            base_url=base_url,
            credential_ref="TEST_API_KEY",
        )


@pytest.mark.parametrize("timeout_seconds", [0.0, -1.0, float("nan"), float("inf")])
def test_channel_config_rejects_invalid_timeouts(timeout_seconds: float) -> None:
    with pytest.raises(ConfigurationError):
        ChannelConfig(
            protocol=ProtocolKind.ANTHROPIC_MESSAGES,
            base_url="https://example.com",
            credential_ref="TEST_API_KEY",
            timeout_seconds=timeout_seconds,
        )


def test_channel_config_rejects_empty_credential_reference() -> None:
    with pytest.raises(ConfigurationError):
        ChannelConfig(
            protocol=ProtocolKind.CHAT_COMPLETIONS,
            base_url="https://example.com",
            credential_ref="   ",
        )
