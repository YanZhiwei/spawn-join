"""OpenAI-compatible channel transport tests."""

import asyncio
from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest
from openai import AsyncOpenAI
from spawn_join_llm_channel._openai import OpenAIChannel

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
    def __init__(self, ids: list[str]) -> None:
        self.data = [SimpleNamespace(id=value) for value in ids]


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


def _config(protocol: ProtocolKind = ProtocolKind.CHAT_COMPLETIONS) -> ChannelConfig:
    return ChannelConfig(
        name="test",
        protocol=protocol,
        endpoint="https://api.example.com/v1",
        credential_ref="OPENAI_API_KEY",
        timeout_seconds=1.0,
    )


def _channel(client: _Client) -> OpenAIChannel:
    return OpenAIChannel(_config(), client=cast(AsyncOpenAI, client))


def test_config_is_preserved() -> None:
    config = _config()
    channel = OpenAIChannel(config, api_key="sk-test")
    assert channel.config is config


def test_ping_success() -> None:
    client = _Client(page=_Page(["a"]))
    result = asyncio.run(_channel(client).ping())
    assert result.status is ChannelStatus.OK
    assert result.latency_ms is not None and result.latency_ms >= 0
    client.models.list.assert_awaited_once_with(timeout=1.0)


def test_ping_auth_failure() -> None:
    client = _Client(error=_sdk.openai_auth())
    result = asyncio.run(_channel(client).ping())
    assert result.status is ChannelStatus.AUTHENTICATION_FAILED
    assert result.detail == "authentication failed"


def test_ping_not_found_is_unsupported() -> None:
    result = asyncio.run(_channel(_Client(error=_sdk.openai_not_found())).ping())
    assert result.status is ChannelStatus.UNSUPPORTED


def test_list_models_returns_one_page_and_applies_limit() -> None:
    client = _Client(page=_Page(["a", "b"]))
    page = asyncio.run(_channel(client).list_models(limit=1))
    assert [model.id for model in page.models] == ["a"]
    assert page.next_cursor is None


def test_list_models_empty_page_is_success() -> None:
    page = asyncio.run(_channel(_Client(page=_Page([]))).list_models())
    assert page.models == ()
    assert page.next_cursor is None


@pytest.mark.parametrize("limit", [0, -1])
def test_list_models_rejects_non_positive_limit(limit: int) -> None:
    with pytest.raises(ValueError, match="limit must be positive"):
        asyncio.run(_channel(_Client(page=_Page([]))).list_models(limit=limit))


def test_list_models_rejects_cursor() -> None:
    with pytest.raises(ValueError, match="cursor is not supported"):
        asyncio.run(_channel(_Client(page=_Page([]))).list_models(cursor="next"))


def test_list_models_auth_error_is_stable() -> None:
    client = _Client(error=_sdk.openai_auth())
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
        OpenAIChannel(_config(), api_key=api_key)


def test_protocol_mismatch_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="chat_completions or responses"):
        OpenAIChannel(_config(ProtocolKind.ANTHROPIC_MESSAGES), api_key="sk-test")


def test_aclose_closes_the_client() -> None:
    client = _Client(page=_Page([]))
    asyncio.run(_channel(client).aclose())
    client.close.assert_awaited_once_with()
