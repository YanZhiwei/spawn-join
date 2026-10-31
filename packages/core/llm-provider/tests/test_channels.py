"""Tests for channel configuration and the channel contract."""

import asyncio
from dataclasses import FrozenInstanceError
from typing import cast

import pytest

from spawn_join_llm_provider import (
    Channel,
    ChannelConfig,
    ChannelResponseError,
    ChannelStatus,
    ChannelUnavailableError,
    ConfigurationError,
    ModelInfo,
    ModelPage,
    PingResult,
    ProtocolKind,
    UnsupportedChannelOperationError,
)


def _config(
    *,
    name: str = "primary",
    protocol: ProtocolKind = ProtocolKind.CHAT_COMPLETIONS,
    endpoint: str = "https://api.example.com/v1",
    credential_ref: str = "openai-default",
    timeout_seconds: float = 30.0,
) -> ChannelConfig:
    return ChannelConfig(
        name=name,
        protocol=protocol,
        endpoint=endpoint,
        credential_ref=credential_ref,
        timeout_seconds=timeout_seconds,
    )


class FakeChannel:
    """A minimal structural Channel used by contract tests."""

    def __init__(
        self,
        config: ChannelConfig,
        *,
        ping_result: PingResult | None = None,
        page: ModelPage | None = None,
        ping_error: Exception | None = None,
        list_error: Exception | None = None,
    ) -> None:
        self._config = config
        self._ping_result = ping_result
        self._page = page
        self._ping_error = ping_error
        self._list_error = list_error

    @property
    def config(self) -> ChannelConfig:
        return self._config

    async def ping(self) -> PingResult:
        if self._ping_error is not None:
            raise self._ping_error
        assert self._ping_result is not None
        return self._ping_result

    async def list_models(
        self,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> ModelPage:
        del cursor
        if limit is not None and limit <= 0:
            raise ValueError("limit must be positive")
        if self._list_error is not None:
            raise self._list_error
        assert self._page is not None
        return self._page


def test_channel_config_reads_all_fields() -> None:
    config = _config()
    assert config.name == "primary"
    assert config.protocol is ProtocolKind.CHAT_COMPLETIONS
    assert config.endpoint == "https://api.example.com/v1"
    assert config.credential_ref == "openai-default"
    assert config.timeout_seconds == 30.0


@pytest.mark.parametrize("protocol", ["chat_completions", 1, None])
def test_channel_protocol_must_be_a_protocol_kind(protocol: object) -> None:
    with pytest.raises(ConfigurationError):
        _config(protocol=cast(ProtocolKind, protocol))


@pytest.mark.parametrize(
    "name",
    [
        "",
        " primary",
        "primary ",
        "bad\nname",
        "bad\x7fname",
        "bad\u0085name",
        "bad\u009fname",
    ],
)
def test_channel_name_must_be_a_safe_label(name: str) -> None:
    with pytest.raises(ConfigurationError):
        _config(name=name)


@pytest.mark.parametrize(
    "endpoint",
    [
        "ftp://api.example.com/v1",
        "https:///v1",
        "https://user:pass@api.example.com/v1",
        "https://api example.com/v1",
        "https://api.example.com:99999/v1",
        "not-a-url",
        " https://api.example.com/v1",
        "https://api.example.com/v1 ",
        "https://api.example.com/v1\n",
        "https://./v1",
        "https://-bad-/v1",
        "https://api..example.com/v1",
        "https://api.example.com../v1",
        "https://" + "a" * 64 + ".example.com/v1",
        "https://" + "a" * 250 + ".com/v1",
    ],
)
def test_channel_endpoint_must_be_a_safe_absolute_url(endpoint: str) -> None:
    with pytest.raises(ConfigurationError):
        _config(endpoint=endpoint)


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://localhost:8080/v1",
        "https://127.0.0.1/v1",
        "https://[::1]/v1",
        "https://api.example.com./v1",
    ],
)
def test_channel_endpoint_accepts_valid_hosts(endpoint: str) -> None:
    assert _config(endpoint=endpoint).endpoint == endpoint


@pytest.mark.parametrize("credential_ref", ["", "   "])
def test_channel_credential_ref_must_not_be_empty(credential_ref: str) -> None:
    with pytest.raises(ConfigurationError):
        _config(credential_ref=credential_ref)


@pytest.mark.parametrize(
    "timeout_seconds",
    [0.0, -1.0, float("nan"), float("inf")],
)
def test_channel_timeout_must_be_finite_and_positive(
    timeout_seconds: float,
) -> None:
    with pytest.raises(ConfigurationError):
        _config(timeout_seconds=timeout_seconds)


def test_ping_result_ok_property() -> None:
    assert PingResult(status=ChannelStatus.OK).ok is True
    assert PingResult(status=ChannelStatus.AUTHENTICATION_FAILED).ok is False


def test_ping_result_rejects_negative_latency() -> None:
    with pytest.raises(ConfigurationError):
        PingResult(status=ChannelStatus.OK, latency_ms=-1.0)


def test_ping_result_rejects_non_finite_latency() -> None:
    with pytest.raises(ConfigurationError):
        PingResult(status=ChannelStatus.OK, latency_ms=float("nan"))


def test_model_info_requires_an_id() -> None:
    with pytest.raises(ConfigurationError):
        ModelInfo(id="   ")


def test_model_page_allows_empty_and_non_empty_results() -> None:
    empty = ModelPage()
    non_empty = ModelPage(
        models=(ModelInfo(id="model-a", display_name="Model A"),),
        next_cursor="next",
    )
    assert empty.models == ()
    assert non_empty.models[0].id == "model-a"
    assert non_empty.next_cursor == "next"


def test_fake_channel_satisfies_the_protocol() -> None:
    channel: Channel = FakeChannel(_config())
    assert channel.config.name == "primary"


@pytest.mark.parametrize("status", list(ChannelStatus))
def test_fake_channel_ping_statuses(status: ChannelStatus) -> None:
    channel = FakeChannel(
        _config(),
        ping_result=PingResult(status=status, latency_ms=1.5),
    )
    result = asyncio.run(channel.ping())
    assert result.status is status
    assert result.ok is (status is ChannelStatus.OK)


def test_fake_channel_empty_model_page() -> None:
    channel = FakeChannel(_config(), page=ModelPage())
    page = asyncio.run(channel.list_models())
    assert page.models == ()
    assert page.next_cursor is None


def test_fake_channel_non_empty_model_page() -> None:
    channel = FakeChannel(
        _config(),
        page=ModelPage(
            models=(ModelInfo(id="model-a"), ModelInfo(id="model-b")),
            next_cursor="cursor-2",
        ),
    )
    page = asyncio.run(channel.list_models(limit=2))
    assert [model.id for model in page.models] == ["model-a", "model-b"]
    assert page.next_cursor == "cursor-2"


@pytest.mark.parametrize(
    "error_type",
    [
        UnsupportedChannelOperationError,
        ChannelUnavailableError,
        ChannelResponseError,
    ],
)
def test_fake_channel_list_models_errors_are_distinguishable(
    error_type: type[Exception],
) -> None:
    channel = FakeChannel(
        _config(),
        list_error=error_type("list_models failed"),
    )
    with pytest.raises(error_type):
        asyncio.run(channel.list_models())


def test_fake_channel_rejects_non_positive_limit() -> None:
    channel = FakeChannel(_config(), page=ModelPage())
    with pytest.raises(ValueError, match="limit must be positive"):
        asyncio.run(channel.list_models(limit=0))


def test_fake_channel_can_raise_ping_error() -> None:
    channel = FakeChannel(
        _config(),
        ping_error=ChannelUnavailableError("unreachable"),
    )
    with pytest.raises(ChannelUnavailableError):
        asyncio.run(channel.ping())


def test_channel_config_is_immutable() -> None:
    config = _config()
    attribute = "name"
    with pytest.raises(FrozenInstanceError):
        setattr(config, attribute, "other")
