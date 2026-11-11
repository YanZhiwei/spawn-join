"""Anthropic channel transport tests."""

import asyncio
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from anthropic import AsyncAnthropic
from spawn_join_llm_channel._anthropic import AnthropicChannel

from spawn_join_llm_provider import (
    ChannelAuthenticationError,
    ChannelConfig,
    ChannelResponseError,
    ChannelStatus,
    ConfigurationError,
    ProtocolKind,
)

from . import _sdk


class _Page:
    def __init__(
        self,
        entries: list[tuple[str, str | None]],
        *,
        has_more: bool = False,
        last_id: str | None = None,
    ) -> None:
        self.data = [
            SimpleNamespace(id=model_id, display_name=display_name)
            for model_id, display_name in entries
        ]
        self.has_more = has_more
        self.last_id = last_id


class _Models:
    def __init__(
        self, page: object | None = None, error: Exception | None = None
    ) -> None:
        self.list = (
            AsyncMock(return_value=page)
            if error is None
            else AsyncMock(side_effect=error)
        )


class _Client:
    def __init__(
        self, page: object | None = None, error: Exception | None = None
    ) -> None:
        self.models = _Models(page=page, error=error)
        self.close = AsyncMock()


def _config() -> ChannelConfig:
    return ChannelConfig(
        name="test",
        protocol=ProtocolKind.ANTHROPIC_MESSAGES,
        endpoint="https://api.example.com",
        credential_ref="ANTHROPIC_API_KEY",
        timeout_seconds=1.0,
    )


def _channel(client: _Client) -> AnthropicChannel:
    return AnthropicChannel(_config(), client=cast(AsyncAnthropic, client))


def test_config_is_preserved() -> None:
    config = _config()
    channel = AnthropicChannel(config, api_key="sk-test")
    assert channel.config is config


def test_ping_success() -> None:
    client = _Client(page=_Page([("claude", "Claude")]))
    result = asyncio.run(_channel(client).ping())
    assert result.status is ChannelStatus.OK
    client.models.list.assert_awaited_once_with(limit=1, timeout=1.0)


def test_ping_auth_failure() -> None:
    client = _Client(error=_sdk.anthropic_auth())
    result = asyncio.run(_channel(client).ping())
    assert result.status is ChannelStatus.AUTHENTICATION_FAILED


def test_list_models_maps_display_name_and_cursor() -> None:
    client = _Client(
        page=_Page(
            [("claude", "Claude"), ("claude-mini", None)],
            has_more=True,
            last_id="claude-mini",
        )
    )
    page = asyncio.run(_channel(client).list_models(cursor="start", limit=2))
    assert [model.id for model in page.models] == ["claude", "claude-mini"]
    assert page.models[1].display_name is None
    assert page.next_cursor == "claude-mini"
    client.models.list.assert_awaited_once_with(
        after_id="start",
        limit=2,
        timeout=1.0,
    )


def test_list_models_without_options() -> None:
    client = _Client(page=_Page([("claude", "Claude")]))
    page = asyncio.run(_channel(client).list_models())
    assert page.next_cursor is None
    client.models.list.assert_awaited_once_with(timeout=1.0)


def test_list_models_does_not_fabricate_cursor() -> None:
    client = _Client(page=_Page([("claude", "Claude")], has_more=True, last_id=None))
    page = asyncio.run(_channel(client).list_models())
    assert page.next_cursor is None


@pytest.mark.parametrize("limit", [0, -1])
def test_list_models_rejects_non_positive_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="limit must be positive"):
        asyncio.run(_channel(_Client(page=_Page([]))).list_models(limit=limit))


def test_list_models_auth_error_is_stable() -> None:
    client = _Client(error=_sdk.anthropic_auth())
    with pytest.raises(
        ChannelAuthenticationError, match="authentication failed"
    ) as info:
        asyncio.run(_channel(client).list_models())
    assert info.value.__cause__ is not None


@pytest.mark.parametrize(
    "page",
    [
        SimpleNamespace(data=None),
        SimpleNamespace(data="not-a-list"),
        SimpleNamespace(data=[SimpleNamespace(id="")]),
    ],
)
def test_ping_malformed_page_is_invalid_response(page: object) -> None:
    result = asyncio.run(_channel(_Client(page=page)).ping())
    assert result.status is ChannelStatus.INVALID_RESPONSE
    assert result.detail == "invalid response"


@pytest.mark.parametrize(
    "page",
    [
        SimpleNamespace(data=None),
        SimpleNamespace(data="not-a-list"),
        SimpleNamespace(data=[SimpleNamespace(id="")]),
    ],
)
def test_list_models_malformed_page_raises_stable_error(page: object) -> None:
    with pytest.raises(ChannelResponseError, match="invalid model listing response"):
        asyncio.run(_channel(_Client(page=page)).list_models())


@pytest.mark.parametrize("api_key", ["", " ", " key", "key "])
def test_explicit_api_key_is_validated(api_key: str) -> None:
    with pytest.raises(ConfigurationError, match="API key must be non-empty"):
        AnthropicChannel(_config(), api_key=api_key)


def test_protocol_mismatch_is_rejected() -> None:
    config = ChannelConfig(
        name="test",
        protocol=ProtocolKind.CHAT_COMPLETIONS,
        endpoint="https://api.example.com",
        credential_ref="ANTHROPIC_API_KEY",
    )
    with pytest.raises(ConfigurationError, match="anthropic_messages"):
        AnthropicChannel(config, api_key="sk-test")


def test_aclose_closes_the_client() -> None:
    client = _Client(page=_Page([]))
    asyncio.run(_channel(client).aclose())
    client.close.assert_awaited_once_with()
