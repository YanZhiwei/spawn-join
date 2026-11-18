"""Malformed successful responses must not leak SDK parse errors."""

import asyncio
from collections.abc import Callable

import httpx2
import pytest
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from spawn_join_llm_channel import AnthropicChannel, OpenAIChannel

from spawn_join_llm_provider import (
    ChannelConfig,
    ChannelResponseError,
    ChannelStatus,
    ProtocolKind,
)

_Handler = Callable[[httpx2.Request], httpx2.Response]


def _config(protocol: ProtocolKind) -> ChannelConfig:
    return ChannelConfig(
        name="test",
        protocol=protocol,
        endpoint="https://test/v1",
        credential_ref="TEST_KEY",
        timeout_seconds=1.0,
    )


def _openai_client(handler: _Handler) -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key="sk-test",
        base_url="https://test/v1",
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
    )


def _anthropic_client(
    handler: _Handler,
) -> AsyncAnthropic:
    return AsyncAnthropic(
        api_key="sk-test",
        base_url="https://test",
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
    )


def _malformed_cases() -> list[_Handler]:
    def body(payload: object) -> _Handler:
        def handler(request: httpx2.Request) -> httpx2.Response:
            return httpx2.Response(200, json=payload, request=request)

        return handler

    def non_json(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, text="<html>not json</html>", request=request)

    return [body({}), body({"data": None}), body({"data": "not-a-list"}), non_json]


@pytest.mark.parametrize("handler", _malformed_cases())
def test_openai_malformed_ping_is_invalid_response(handler: _Handler) -> None:
    async def run() -> ChannelStatus:
        channel = OpenAIChannel(
            _config(ProtocolKind.CHAT_COMPLETIONS),
            client=_openai_client(handler),
        )
        try:
            return (await channel.ping()).status
        finally:
            await channel.aclose()

    assert asyncio.run(run()) is ChannelStatus.INVALID_RESPONSE


@pytest.mark.parametrize("handler", _malformed_cases())
def test_openai_malformed_list_raises_stable_error(handler: _Handler) -> None:
    async def run() -> None:
        channel = OpenAIChannel(
            _config(ProtocolKind.CHAT_COMPLETIONS),
            client=_openai_client(handler),
        )
        try:
            with pytest.raises(ChannelResponseError):
                await channel.list_models()
        finally:
            await channel.aclose()

    asyncio.run(run())


@pytest.mark.parametrize("handler", _malformed_cases())
def test_anthropic_malformed_ping_is_invalid_response(handler: _Handler) -> None:
    async def run() -> ChannelStatus:
        channel = AnthropicChannel(
            _config(ProtocolKind.ANTHROPIC_MESSAGES),
            client=_anthropic_client(handler),
        )
        try:
            return (await channel.ping()).status
        finally:
            await channel.aclose()

    assert asyncio.run(run()) is ChannelStatus.INVALID_RESPONSE


@pytest.mark.parametrize("handler", _malformed_cases())
def test_anthropic_malformed_list_raises_stable_error(handler: _Handler) -> None:
    async def run() -> None:
        channel = AnthropicChannel(
            _config(ProtocolKind.ANTHROPIC_MESSAGES),
            client=_anthropic_client(handler),
        )
        try:
            with pytest.raises(ChannelResponseError):
                await channel.list_models()
        finally:
            await channel.aclose()

    asyncio.run(run())
