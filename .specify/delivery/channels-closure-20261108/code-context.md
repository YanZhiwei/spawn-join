# Code Context — channels-closure-20261108

## Existing code map

| Path | Responsibility | Change |
|---|---|---|
| `packages/core/llm-provider/src/spawn_join_llm_provider/channels.py` | Framework-independent `Channel`, `ChannelConfig`, `PingResult`, `ModelInfo`, `ModelPage` | Add `ChannelStatus.UNSUPPORTED` |
| `packages/core/llm-provider/src/spawn_join_llm_provider/errors.py` | Stable channel errors | Add `ChannelAuthenticationError(ChannelError)` |
| `packages/core/llm-provider/src/spawn_join_llm_provider/__init__.py` | Public protocol exports | Export the new error |
| `packages/core/llm-provider/tests/test_channels.py` | Contract/fake-channel tests | Cover `UNSUPPORTED` |
| `packages/core/llm-provider/tests/test_errors.py` | Error hierarchy tests | Cover auth subclass |
| `packages/core/llm-provider/tests/test_public_api.py` | Exact public surface | Add new export |
| `packages/infra/llm-provider-langchain/src/spawn_join_llm_provider_langchain/config.py` | `ChatModelConfig` validation | Add `from_channel` classmethod |
| `packages/infra/llm-provider-langchain/src/spawn_join_llm_provider_langchain/model_file/_catalog.py` | `ModelCatalog`/`ModelSummary` | Add optional fields, `from_model_info`, lookup methods |
| `packages/infra/llm-provider-langchain/src/spawn_join_llm_provider_langchain/factory.py` | Native `BaseChatModel` factory | No change |
| `packages/infra/llm-provider-langchain/tests/` | Existing 301 offline tests | Add bridge/inspection tests |
| `scripts/quality.ps1` | Six-package quality map | Add new package |
| `.github/workflows/quality.yml` | Six-package CI matrix | Add new package |
| `.specify/extensions/quality/quality-config.yml` | Package profiles | Add new package profile |

## Reuse points

- `ChannelConfig` already validates protocol/endpoint/timeout/name/credential_ref;
  do not duplicate validation.
- `PingResult`, `ModelInfo`, `ModelPage` are already frozen dataclasses; reuse
  them exactly.
- `ChatModelConfig` already validates model/retries/endpoint; `from_channel`
  must call its constructor, not duplicate rules.
- `ModelSummary`/`ModelCatalog` already validate YAML; new lookup methods must
  reuse `_resolve_entry` and `CatalogEntry`.
- Existing adapter `create_chat_model` must remain untouched.

## Interface seams

```text
ChannelConfig (protocol) -> OpenAIChannel/AnthropicChannel (new)
ChannelConfig (protocol) -> ChatModelConfig.from_channel (adapter)
ModelInfo (protocol)    -> ModelSummary.from_model_info (adapter)
ModelSummary (adapter)  -> ModelCatalog.get/names/... (adapter)
```

## Test map

- Protocol: `packages/core/llm-provider/tests/`
- Channel: `packages/infra/llm-channel/tests/`
- Adapter: `packages/infra/llm-provider-langchain/tests/`
- Offline loop: channel tests + adapter bridge tests; no network.
- Live: `packages/infra/llm-channel/tests/test_live.py`, skipped without
  `SPAWN_JOIN_LIVE_OPENAI` / `SPAWN_JOIN_LIVE_ANTHROPIC`.

## Explicit non-changes

- No `model.yaml` schema change.
- No `channels.yaml`.
- No `BaseChatModel` wrapper.
- No pool/routing/health.
- No Agent package change.
