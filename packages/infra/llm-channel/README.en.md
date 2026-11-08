# spawn-join-llm-channel

[简体中文](README.md) | [English](README.en.md)

Turn an explicit `ChannelConfig` into a real OpenAI-compatible or Anthropic
channel connection: check reachability/authentication, page through models,
and hand the selected model to the existing LangChain model factory or
application catalog. It does **not** depend on LangChain and does **not** wrap
`BaseChatModel`.

## Contents

- [Why this package](#why-this-package)
- [Status](#status)
- [Install](#install)
- [Quick start](#quick-start)
- [Credentials](#credentials)
- [Error mapping](#error-mapping)
- [Pagination and limits](#pagination-and-limits)
- [Lifecycle](#lifecycle)
- [Testing](#testing)
- [Design boundaries](#design-boundaries)
- [Related packages](#related-packages)

## Why this package

`spawn-join-llm-provider` defines a framework-independent `Channel` contract
but has no real provider implementation. This package supplies:

- `OpenAIChannel`: `/models` checks and listing for `chat_completions` and
  `responses`;
- `AnthropicChannel`: `/v1/models` checks and listing for
  `anthropic_messages`.

Applications can validate a channel first (`ChannelConfig -> ping/list_models
-> ModelInfo`) and then pass the selected model to
`ChatModelConfig.from_channel()` in `spawn-join-llm-provider-langchain`.

## Status

`0.1.0`, early development, Python `>=3.11`. Only connection checks and model
discovery are implemented:

- no completion generation;
- no pool, routing, health selection, or failover;
- no `model.yaml`, `.env`, or secret-manager integration;
- no automatic writes to a model file;
- no LangChain dependency.

## Install

These packages are part of the SpawnJoin monorepo and are not published to
PyPI. Each Distribution is an independent uv project:

```powershell
uv sync --locked --directory packages/infra/llm-channel
```

Runtime dependencies:

- `spawn-join-llm-provider`
- `openai`
- `anthropic`

## Quick start

### Offline check with a fake client

```python
import asyncio

from spawn_join_llm_provider import ChannelConfig, ProtocolKind
from spawn_join_llm_channel import OpenAIChannel


class FakeModels:
    async def list(self, *, timeout=None):
        return type("Page", (), {"data": [type("Model", (), {"id": "gpt-test"})()]})()


class FakeClient:
    def __init__(self) -> None:
        self.models = FakeModels()

    async def close(self) -> None:
        pass


async def main() -> None:
    channel = OpenAIChannel(
        ChannelConfig(
            name="demo",
            protocol=ProtocolKind.CHAT_COMPLETIONS,
            endpoint="https://api.example.com/v1",
            credential_ref="OPENAI_API_KEY",
        ),
        client=FakeClient(),
    )
    print(await channel.ping())
    page = await channel.list_models(limit=10)
    print(page.models)
    await channel.aclose()


asyncio.run(main())
```

### Real connection

Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` and point `endpoint` at the real API:

```python
from spawn_join_llm_provider import ChannelConfig, ProtocolKind
from spawn_join_llm_channel import create_channel

config = ChannelConfig(
    name="openai",
    protocol=ProtocolKind.CHAT_COMPLETIONS,
    endpoint="https://api.openai.com/v1",
    credential_ref="OPENAI_API_KEY",
    timeout_seconds=30,
)
channel = create_channel(config)
```

`create_channel()` returns `OpenAIChannel` or `AnthropicChannel` based on
`ProtocolKind`. Real calls need network access and valid credentials; the
default test suite does not make such calls.

Anthropic `endpoint` is passed as the SDK `base_url`, so use the API origin
`https://api.anthropic.com` without an extra `/v1` (the SDK requests
`/v1/models`). OpenAI-compatible endpoints usually include `/v1`. Explicit
`api_key` values are also validated for non-empty, unpadded text.

## Credentials

Priority:

1. injected SDK client (`OpenAIChannel(..., client=...)`);
2. explicit `api_key`;
3. `credential_ref` as an environment-variable name.

`credential_ref` never stores a plaintext key. Missing, empty, or
whitespace-padded values raise `ConfigurationError`. The package does not
mutate `os.environ` and does not read `.env`.

## Error mapping

| Condition | `ping()` | `list_models()` |
|---|---|---|
| 401/403 | `AUTHENTICATION_FAILED` | `ChannelAuthenticationError` |
| Timeout | `TIMEOUT` | `ChannelUnavailableError` |
| Connection failure | `UNREACHABLE` | `ChannelUnavailableError` |
| 429 | `UNREACHABLE` | `ChannelUnavailableError` |
| 5xx | `UNREACHABLE` | `ChannelUnavailableError` |
| 404/405 | `UNSUPPORTED` | `UnsupportedChannelOperationError` |
| Malformed response | `INVALID_RESPONSE` | `ChannelResponseError` |
| Other API error | `INVALID_RESPONSE` | `ChannelResponseError` |

Public messages use fixed text and never concatenate SDK `str(exc)`, request
bodies, full URLs, or keys; the original exception is preserved with
`raise ... from exc`.

## Pagination and limits

- `list_models(limit=...)` requires a positive limit; non-positive values raise
  `ValueError` before any request.
- OpenAI-compatible listing is currently a single page; `next_cursor` is
  `None` and a non-`None` cursor raises `ValueError`.
- Anthropic uses `after_id`/`limit` and `has_more`/`last_id`; a cursor is
  returned when another page exists.
- An empty model page is a valid success.
- 404/405 means the channel is reachable but does not support model listing,
  not that authentication failed.

## Lifecycle

`OpenAIChannel` and `AnthropicChannel` own an SDK client; call
`await channel.aclose()` when finished. If a client is injected, `aclose()`
still closes it; shared-client ownership remains with the caller.

## Testing

```powershell
uv lock --check --directory packages/infra/llm-channel
uv sync --locked --directory packages/infra/llm-channel
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-channel
```

Live provider tests are skipped by default. Enable explicitly:

```powershell
$env:SPAWN_JOIN_LIVE_OPENAI = "1"
$env:OPENAI_API_KEY = "..."
uv run --locked --project packages/infra/llm-channel pytest packages/infra/llm-channel/tests/test_live.py -q
```

A skip is not a pass; delivery evidence marks it as unexecuted.

## Design boundaries

- No messages, content blocks, request/response objects, or `BaseChatModel`.
- No pool, routing, health selection, failover, rate limiting, or concurrency
  control.
- No `channels.yaml`, remote configuration, hot reload, or secret manager.
- No automatic `model.yaml` writes.
- Public API is exactly `OpenAIChannel`, `AnthropicChannel`, `ChatChannel`,
  `create_channel`, fixed by `tests/test_public_api.py`.

## Related packages

- [`spawn-join-llm-provider`](../../core/llm-provider/README.en.md): `Channel`
  contract, options, metadata, and stable errors.
- [`spawn-join-llm-provider-langchain`](../llm-provider-langchain/README.en.md):
  `ChatModelConfig.from_channel`, `ModelSummary.from_model_info`, and the native
  model factory.
- [`spawn-join-llm-model-sync`](../llm-model-sync/README.en.md): model metadata
  snapshot sync.

License: [LICENSE](LICENSE).
