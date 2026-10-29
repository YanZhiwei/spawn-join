"""Contract tests for channel and provider protocols using fakes."""

import asyncio
from collections.abc import AsyncIterator

from spawn_join_llm_provider import (
    Channel,
    ChannelCapabilities,
    ChannelConfig,
    ChannelStatus,
    ChatRequest,
    ChatResponse,
    FinishReason,
    LLMProvider,
    Message,
    ModelCapabilities,
    ModelInfo,
    ModelPage,
    PingResult,
    ProtocolKind,
    Role,
    StreamCompleted,
    StreamEvent,
    TextBlock,
    TextDelta,
)


class FakeChannel:
    """Small structural implementation of the public channel contract."""

    def __init__(self, config: ChannelConfig) -> None:
        self._config = config

    @property
    def config(self) -> ChannelConfig:
        return self._config

    @property
    def capabilities(self) -> ChannelCapabilities:
        return ChannelCapabilities(model_listing=True, health_check=True)

    async def ping(self) -> PingResult:
        return PingResult(
            status=ChannelStatus.OK,
            check_method="model_list",
            latency_ms=1,
        )

    async def list_models(
        self,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> ModelPage:
        del cursor, limit
        return ModelPage(models=(ModelInfo(id="model-1"),))


class FakeProvider:
    """Small structural implementation of the inference contract."""

    @property
    def protocol(self) -> ProtocolKind:
        return ProtocolKind.CHAT_COMPLETIONS

    @property
    def model(self) -> str:
        return "test-model"

    @property
    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(supports_tools=True)

    async def complete(self, request: ChatRequest) -> ChatResponse:
        del request
        return ChatResponse(
            message=Message(
                role=Role.ASSISTANT,
                content=(TextBlock("hello"),),
            ),
            usage=None,
            finish_reason=FinishReason.STOP,
        )

    def stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        del request

        async def events() -> AsyncIterator[StreamEvent]:
            yield TextDelta("hello")
            yield StreamCompleted(finish_reason=FinishReason.STOP)

        return events()


def test_channel_protocol_is_structurally_usable() -> None:
    channel: Channel = FakeChannel(
        ChannelConfig(
            protocol=ProtocolKind.CHAT_COMPLETIONS,
            base_url="https://example.invalid/v1",
            credential_ref="TEST_API_KEY",
        )
    )

    assert channel.config.protocol == ProtocolKind.CHAT_COMPLETIONS
    assert channel.capabilities.model_listing is True
    ping = asyncio.run(channel.ping())
    page = asyncio.run(channel.list_models())
    assert ping.status == ChannelStatus.OK
    assert page.models[0].id == "model-1"


def test_provider_protocol_is_structurally_usable() -> None:
    provider: LLMProvider = FakeProvider()
    request = ChatRequest(
        messages=(Message(role=Role.USER, content=(TextBlock("hi"),)),)
    )

    response = asyncio.run(provider.complete(request))
    assert response.message.content[0] == TextBlock("hello")

    async def collect() -> list[StreamEvent]:
        return [event async for event in provider.stream(request)]

    events = asyncio.run(collect())
    assert isinstance(events[0], TextDelta)
    assert isinstance(events[-1], StreamCompleted)


def test_public_all_exports_resolve() -> None:
    import spawn_join_llm_provider

    for name in spawn_join_llm_provider.__all__:
        assert getattr(spawn_join_llm_provider, name) is not None


def test_channel_contract_represents_empty_and_failure_results() -> None:
    empty_page = ModelPage(models=())
    failure = PingResult(
        status=ChannelStatus.UNSUPPORTED,
        check_method="none",
        latency_ms=0,
        message="model listing is not supported",
    )

    assert empty_page.models == ()
    assert empty_page.next_cursor is None
    assert failure.status == ChannelStatus.UNSUPPORTED
