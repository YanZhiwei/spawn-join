"""OpenAI-compatible channel transport for connection checks and model listing."""

from __future__ import annotations

from collections.abc import Mapping
from time import perf_counter

import openai
from openai import AsyncOpenAI

from spawn_join_llm_provider import (
    ChannelConfig,
    ChannelResponseError,
    ChannelStatus,
    ConfigurationError,
    ModelPage,
    PingResult,
    ProtocolKind,
)

from ._credentials import resolve_api_key, validate_api_key
from ._errors import list_error, ping_result
from ._page import InvalidPageError, model_infos

_OPENAI_PROTOCOLS = frozenset({ProtocolKind.CHAT_COMPLETIONS, ProtocolKind.RESPONSES})


def _elapsed_ms(start: float) -> float:
    return max(0.0, (perf_counter() - start) * 1000.0)


class OpenAIChannel:
    """A channel over an OpenAI-compatible ``/models`` endpoint."""

    def __init__(
        self,
        config: ChannelConfig,
        *,
        api_key: str | None = None,
        client: AsyncOpenAI | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        if config.protocol not in _OPENAI_PROTOCOLS:
            raise ConfigurationError(
                "OpenAIChannel requires chat_completions or responses"
            )
        self._config = config
        if client is not None:
            self._client = client
            return
        key = (
            validate_api_key(api_key)
            if api_key is not None
            else resolve_api_key(config.credential_ref, environ=environ)
        )
        self._client = AsyncOpenAI(
            api_key=key,
            base_url=config.endpoint,
            timeout=config.timeout_seconds,
            max_retries=0,
        )

    @property
    def config(self) -> ChannelConfig:
        """Return the immutable channel configuration."""
        return self._config

    async def ping(self) -> PingResult:
        """Check reachability/authentication with a lightweight models request."""
        start = perf_counter()
        try:
            page = await self._client.models.list(timeout=self._config.timeout_seconds)
            model_infos(page)
        except (openai.APIError, TimeoutError, OSError) as exc:
            return ping_result(exc, latency_ms=_elapsed_ms(start))
        except (AttributeError, TypeError, ValueError, InvalidPageError):
            return PingResult(
                status=ChannelStatus.INVALID_RESPONSE,
                latency_ms=_elapsed_ms(start),
                detail="invalid response",
            )
        return PingResult(status=ChannelStatus.OK, latency_ms=_elapsed_ms(start))

    async def list_models(
        self,
        *,
        cursor: str | None = None,
        limit: int | None = None,
    ) -> ModelPage:
        """Return one OpenAI-compatible model page."""
        if limit is not None and limit <= 0:
            raise ValueError("limit must be positive")
        if cursor is not None:
            raise ValueError("cursor is not supported for OpenAI-compatible listing")
        try:
            page = await self._client.models.list(timeout=self._config.timeout_seconds)
            models = model_infos(page)
        except (openai.APIError, TimeoutError, OSError) as exc:
            raise list_error(exc) from exc
        except (AttributeError, TypeError, ValueError, InvalidPageError) as exc:
            raise ChannelResponseError("invalid model listing response") from exc
        if limit is not None:
            models = models[:limit]
        return ModelPage(models=models, next_cursor=None)

    async def aclose(self) -> None:
        """Close the owned SDK client."""
        await self._client.close()


__all__ = ["OpenAIChannel"]
