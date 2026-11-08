"""Opt-in live Provider smoke tests; skipped without explicit environment flags."""

import asyncio
import os

import pytest
from spawn_join_llm_channel import create_channel

from spawn_join_llm_provider import ChannelConfig, ChannelStatus, ProtocolKind


def _enabled(flag: str, credential_env: str) -> bool:
    if os.environ.get(flag) != "1":
        return False
    value = os.environ.get(credential_env)
    return bool(value and value == value.strip())


@pytest.mark.skipif(
    not _enabled("SPAWN_JOIN_LIVE_OPENAI", "OPENAI_API_KEY"),
    reason="SPAWN_JOIN_LIVE_OPENAI and a valid OPENAI_API_KEY are required",
)
def test_openai_live_ping() -> None:
    async def run() -> ChannelStatus:
        config = ChannelConfig(
            name="live-openai",
            protocol=ProtocolKind.CHAT_COMPLETIONS,
            endpoint=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            credential_ref="OPENAI_API_KEY",
        )
        channel = create_channel(config)
        try:
            return (await channel.ping()).status
        finally:
            await channel.aclose()

    assert asyncio.run(run()) is ChannelStatus.OK


@pytest.mark.skipif(
    not _enabled("SPAWN_JOIN_LIVE_ANTHROPIC", "ANTHROPIC_API_KEY"),
    reason="SPAWN_JOIN_LIVE_ANTHROPIC and a valid ANTHROPIC_API_KEY are required",
)
def test_anthropic_live_ping() -> None:
    async def run() -> ChannelStatus:
        config = ChannelConfig(
            name="live-anthropic",
            protocol=ProtocolKind.ANTHROPIC_MESSAGES,
            endpoint=os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
            credential_ref="ANTHROPIC_API_KEY",
        )
        channel = create_channel(config)
        try:
            return (await channel.ping()).status
        finally:
            await channel.aclose()

    assert asyncio.run(run()) is ChannelStatus.OK
