# spawn-join-llm-provider

[English](README.md) | [简体中文](README.zh-CN.md)

Framework-independent LLM **channel contracts, protocol options, and stable errors**.

This package does not implement model calls and does not redefine LangChain messages, tools, or
streaming types. It keeps only what LangChain does not provide but configuration and operations
genuinely need:

- one shared `EndpointConfig` (protocol, endpoint, timeout);
- one `Channel` connection contract (`ping()`, `list_models()`);
- typed options for three protocols;
- a small set of stable configuration/channel errors.

Model invocation belongs to
[`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/README.md); applications
use LangChain `BaseChatModel` and message types directly.

**Contents**

- [Status](#status)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Public API](#public-api)
- [Model metadata contract](#model-metadata-contract)
- [Design boundaries](#design-boundaries)
- [Development and verification](#development-and-verification)
- [Related packages](#related-packages)
- [Maintenance and releases](#maintenance-and-releases)

## Status

`0.1.0`, early development; Python `>=3.11`. This release delivers contracts and offline tests only:

- no real channel HTTP implementation;
- no `ChannelPool`, model routing, or health-based selection;
- the protocol package depends only on `spawn-join-core` and the general validation library Pydantic.

## Installation

These packages belong to the SpawnJoin monorepo and are not published to PyPI. Each Distribution
is an independent uv project:

```powershell
uv sync --locked --directory packages/core/llm-provider
```

From the repository root, verify the import in this package's environment:

```powershell
uv run --locked --directory packages/core/llm-provider python -c "import spawn_join_llm_provider"
```

In a script running in that environment:

```python
import spawn_join_llm_provider
```

## Quick start

### 1. Describe an endpoint

`EndpointConfig` is the shared flat configuration containing only protocol, endpoint, and timeout:

```python
from spawn_join_llm_provider import EndpointConfig, ProtocolKind

endpoint = EndpointConfig(
    protocol=ProtocolKind.CHAT_COMPLETIONS,
    endpoint="https://api.example.com/v1",
    timeout_seconds=30.0,
)
```

### 2. Describe a channel

`ChannelConfig` extends `EndpointConfig` with a channel name and credential reference:

```python
from spawn_join_llm_provider import ChannelConfig, ProtocolKind

config = ChannelConfig(
    name="openai-primary",
    credential_ref="openai-default",
    protocol=ProtocolKind.CHAT_COMPLETIONS,
    endpoint="https://api.example.com/v1",
    timeout_seconds=30.0,
)
```

- `name` is a non-sensitive, human-readable channel identifier used in logs and error locations.
- `credential_ref` is only a secret reference, never plaintext.
- `endpoint` must be an absolute `http(s)` URL without embedded username/password.
- All fields are keyword-only; invalid values raise `ConfigurationError` at construction.

### 3. Use protocol options

```python
from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    AnthropicThinkingBudget,
    ChatCompletionsOptions,
    ResponsesOptions,
)

chat = ChatCompletionsOptions(temperature=0.2, max_output_tokens=1024)
responses = ResponsesOptions(store=False, reasoning_effort="medium")
anthropic = AnthropicMessagesOptions(
    max_output_tokens=4096,
    thinking=AnthropicThinkingBudget(budget_tokens=2048),
)
```

Options express protocol-native parameters only; they do not contain tool definitions or tool
choice. Use LangChain `bind_tools` / `tool_choice` for tool calls.

### Thinking parameters: construction defaults and per-call overrides

These `Options` cover only some **construction-time defaults**, not the full set of LangChain call
capabilities:

| Option type | Thinking defaults configurable here |
|---|---|
| `ChatCompletionsOptions` | no thinking field yet |
| `ResponsesOptions` | `reasoning_effort`: `low`, `medium`, `high` |
| `AnthropicMessagesOptions` | `thinking`: fixed token budget or adaptive mode |

**A missing Options field does not mean the model call cannot think.** The factory returns a
native LangChain `BaseChatModel`; applications can pass `reasoning_effort`, Anthropic `thinking`,
and other native parameters directly to `ainvoke()` without extending protocol options or
converting requests themselves.

For example, an already-created model can set per-call thinking strength:

```python
# Inside an async function; model was created by create_chat_model().
response = await model.ainvoke(
    [HumanMessage(content="Analyze the pros and cons of this proposal")],
    reasoning_effort="high",
    max_tokens=8192,
)
```

`HumanMessage` comes from `langchain_core.messages`. For a complete construction example,
Anthropic thinking modes, and compatibility notes, see
[the adapter's thinking guide](../../infra/llm-provider-langchain/README.md#thinking-and-reasoning-effort).
The actual model and server must support the parameters; this package performs no capability
inference, strength-to-token-budget conversion, or automatic degradation.

## Public API

### Configuration types

| Type | Purpose |
|---|---|
| `EndpointConfig` | protocol + endpoint + timeout; shared base for `ChannelConfig` and `ChatModelConfig` |
| `ChannelConfig` | `EndpointConfig` + `name` + `credential_ref` |
| `ProtocolKind` | `chat_completions`, `responses`, `anthropic_messages` |
| `ChatCompletionsOptions` | native Chat Completions options |
| `ResponsesOptions` | native Responses options |
| `AnthropicMessagesOptions` | native Anthropic Messages options |
| `ProtocolOptions` | union of the three option types |

### Channel contract

```python
from spawn_join_llm_provider import Channel

class MyChannel:
    @property
    def config(self) -> ChannelConfig: ...

    async def ping(self) -> PingResult: ...

    async def list_models(
        self, *, cursor: str | None = None, limit: int | None = None
    ) -> ModelPage: ...
```

`Channel` is a `Protocol`; implementations do not need to inherit a base class.

`ping()` checks connectivity and authentication only and performs no generation request.
`PingResult`'s `ChannelStatus` values:

| Status | Meaning |
|---|---|
| `ok` | connectivity and authentication succeeded |
| `authentication_failed` | invalid credential or insufficient permission |
| `unreachable` | network/DNS/connection failure |
| `timeout` | check timed out |
| `invalid_response` | response could not be parsed or violated the contract |

`list_models()` result semantics:

| Situation | Representation |
|---|---|
| success with models | `ModelPage(models=(...))` |
| success with no models | `ModelPage(models=())` |
| operation unsupported | `UnsupportedChannelOperationError` |
| network/auth/timeout failure | `ChannelUnavailableError` |
| unparseable response | `ChannelResponseError` |

An empty list is a legitimate "no models" result and must not represent failure or unsupported
operation.

### Errors

```text
LLMProviderError
├── ConfigurationError
└── ChannelError
    ├── ChannelUnavailableError
    ├── UnsupportedChannelOperationError
    └── ChannelResponseError
```

Invalid configuration, options that do not match the protocol, invalid endpoints, blank credential
references, or non-positive timeouts raise `ConfigurationError` at construction.

## Model metadata contract

`spawn_join_llm_provider.metadata` provides read-only, validated model metadata types:

- `ModelMetadata`, `ModelModalities`, `ModelCapabilitiesMetadata`, `ModelReasoning`,
  `ModelLimits`, `ModelPricing`, `ModelPriceRate`, `ModelPriceTier`;
- `ModelMetadataDocument`, `ModelSource`, `ModelChannel`, `ModelMetadataOverride`;
- `parse_model_metadata_document`, `parse_model_metadata_override`,
  `apply_metadata_override`, `decode_metadata_document`, `reject_duplicate_keys`.

Implementation uses Pydantic dataclasses for boundary field validation, while public objects remain
dataclasses supporting `dataclasses.replace`, `frozen`, `slots`, and `kw_only`. Unknown fields,
type errors, and nested models are validated by Pydantic; business invariants such as duplicate
rates, ordering, and cross-field references remain in `__post_init__`. Pydantic is a general
validation dependency; no LangChain, Provider SDK, or network/file side effect is introduced.

Constraints:

- These types describe facts only; they do not participate in protocol selection, routing,
  degradation, or capability negotiation. They are not the runtime `ModelCapabilities` abstraction
  forbidden by ADR-0006.
- Prices use rate lists with `modality`, `direction`, `unit`, and `amount`; amounts must be finite
  and non-negative, units must be explicit, and optional long-context tiers are supported.
- Snapshot documents accept `schema_version: 1` only; unknown fields, unknown enums, and duplicate
  rates are rejected during parsing; top-level rates, tier rates, and tier thresholds are sorted.
- Overrides replace whole blocks: `pricing`, `limits`, `capabilities`, `modalities`, `status`; no
  field-level deep merge is performed.
- This package reads no files and accesses no network; snapshot files and sync commands belong to
  `spawn-join-llm-model-sync`.

See [ADR-0009](../../../docs/decisions/llm-provider/0009-model-metadata-and-sync.md) for the
long-term boundary.

## Design boundaries

- Does not define `Message`, content blocks, tools, requests/responses, streaming events, or
  `LLMProvider`.
- Does not depend on LangChain, OpenAI/Anthropic SDKs, or an HTTP client.
- Does not implement real channel HTTP, pooling, routing, or health-based selection.
- `ChannelConfig` guarantees validity only inside one configuration object; cross-config uniqueness
  belongs to the caller or a future registry.
- Public API is pinned by `tests/test_public_api.py`; adding or removing symbols requires a
  synchronized contract and review.

## Development and verification

```powershell
uv lock --check --directory packages/core/llm-provider
uv sync --locked --directory packages/core/llm-provider
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider
```

The quality command includes Black, isort, Ruff, Pyright strict, pytest, isolated build/install,
and import checks. Tests use no network and no real credentials by default.

When changing public API, maintainers must:

1. update `src/spawn_join_llm_provider/` and the corresponding tests;
2. synchronize exact exports in [`__init__.py`](src/spawn_join_llm_provider/__init__.py) and
   [`test_public_api.py`](tests/test_public_api.py);
3. check [package boundaries](../../../docs/architecture/package-boundaries.md) and
   [ADR-0006](../../../docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md) for
   consistency.

## Related packages

- [`spawn-join-core`](../spawn-join-core/README.md): shared configuration, exceptions, and types.
- [`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/README.md): LangChain
  model factory, protocol option mapping, and `model.yaml` / `.env` parsing. This package reads no
  files or environment variables.

See [LICENSE](LICENSE).

## Maintenance and releases

Owned by the SpawnJoin repository maintainers (author: Yan Zhiwei). Runtime source is in
`src/spawn_join_llm_provider/`, with offline tests in `tests/`. The quality gate requires
PowerShell 7, uv 0.7.13+, Git, and Node.js 22+; see [quality prerequisites](../../../docs/development/quality-gates.md#prerequisites).
Follow [contributor rules](../../../AGENTS.md) and include a minimal reproducer when reporting
configuration problems. This package is independently versioned and unpublished; no automated
release or package-specific changelog is configured. Public-contract changes require tests,
both README languages, compatibility notes, and separate release authorization.
