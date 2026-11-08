# spawn-join-llm-provider-langchain

[简体中文](README.md) | [English](README.en.md)

Turn **explicit protocol configuration** into a configured LangChain `BaseChatModel`.

Applications use LangChain messages, tools, streaming output, and callbacks directly; this package
is responsible only for:

- creating `ChatOpenAI` or `ChatAnthropic` from protocol / endpoint / model;
- loading a set of models from an explicit `model.yaml` and creating one by `default` or name;
- mapping typed options for three protocols into LangChain constructor arguments;
- validating configuration and options before model creation;
- wrapping the API key with `SecretStr`.

It does not redefine messages, content blocks, tools, requests/responses, streaming events, or
`LLMProvider`.

**Contents**

- [Why use this package](#why-use-this-package)
- [Status](#status)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Model file and credentials](#model-file-and-credentials)
- [Protocols and options](#protocols-and-options)
- [Thinking and reasoning effort](#thinking-and-reasoning-effort)
- [Tool calling](#tool-calling)
- [Streaming](#streaming)
- [Configuration and errors](#configuration-and-errors)
- [Security](#security)
- [Design boundaries](#design-boundaries)
- [Development and verification](#development-and-verification)
- [Related packages](#related-packages)
- [Maintenance and releases](#maintenance-and-releases)

## Why use this package

If an application already runs on LangChain, using `ChatOpenAI` / `ChatAnthropic` directly is also
valid. This package solves the **configuration boundary**:

- protocol is decided by an explicit `ProtocolKind`, never guessed from a model name;
- `ChatModelConfig` contains only fields required for inference and does not depend on
  `ChannelConfig`;
- options have typed and range validation instead of being silently forwarded through arbitrary
  `**kwargs`;
- channel/model configuration and LangChain construction details are centralized in one factory.

## Status

`0.1.0`, early development; Python `>=3.11`. The factory performs offline construction
and validation; the returned model can make real requests when invoked:

- no real Provider requests;
- no channel HTTP, `ChannelPool`, routing, or health-based selection;
- `max_retries=0` by default, without hiding SDK retries.

## Installation

These packages belong to the SpawnJoin monorepo and are not published to PyPI. Each Distribution is
an independent uv project:

```powershell
uv sync --locked --directory packages/infra/llm-provider-langchain
```

Runtime dependencies:

- `spawn-join-llm-provider`
- `spawn-join-common[validation]`
- `langchain-core`
- `langchain-openai`
- `langchain-anthropic`
- `pydantic`
- `PyYAML`
- `python-dotenv`

## Quick start

### Offline construction: no credentials or service required

Save this as `construct_demo.py` at the repository root and run
`uv run --locked --project packages/infra/llm-provider-langchain python construct_demo.py`.
It only constructs and validates a model; it sends no request. The fake key cannot be used for
real calls. Expected output: `ChatOpenAI demo-model`.

```python
from spawn_join_llm_provider import ChatCompletionsOptions, ProtocolKind
from spawn_join_llm_provider_langchain import ChatModelConfig, create_chat_model

model = create_chat_model(
    ChatModelConfig(
        protocol=ProtocolKind.CHAT_COMPLETIONS,
        endpoint="https://api.example.com/v1",
        model="demo-model",
    ),
    api_key="offline-demo-not-a-real-key",
    options=ChatCompletionsOptions(temperature=0.2, max_output_tokens=1024),
)
print(type(model).__name__, model.model_name)
```

### Complete async invocation: connect your service

Save this as `quickstart.py` in the repository root. Set `LLM_API_KEY`, `LLM_BASE_URL`,
and `LLM_MODEL` for your service, then run
`uv run --locked --project packages/infra/llm-provider-langchain python quickstart.py`.
The invocation sends a request to that service; construction alone does not.

```python
import asyncio
import os

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from spawn_join_llm_provider import ChatCompletionsOptions, ProtocolKind
from spawn_join_llm_provider_langchain import ChatModelConfig, create_chat_model

def build_model() -> BaseChatModel:
    config = ChatModelConfig(
        protocol=ProtocolKind.CHAT_COMPLETIONS,
        endpoint=os.environ["LLM_BASE_URL"],
        model=os.environ["LLM_MODEL"],
        timeout_seconds=60.0,
    )
    return create_chat_model(
        config,
        api_key=os.environ["LLM_API_KEY"],
        options=ChatCompletionsOptions(temperature=0.2),
    )


async def main() -> None:
    model = build_model()
    response = await model.ainvoke([HumanMessage(content="Hello")])
    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())
```

This prints the service's response body; exact wording varies. The tool and streaming examples
below reuse `build_model()` from this file; importing it does not run `main()` or send a request.

`api_key` is passed only at call time and immediately wrapped as `pydantic.SecretStr`; it never
enters the configuration object, repr, or logs.

## Model file and credentials

Besides constructing configuration in code, a set of models can be loaded from an explicitly
pathed `model.yaml`:

```yaml
schema_version: 1
default: fast

models:
  fast:
    display_name: GPT Test Mini
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: gpt-test-mini
    timeout_seconds: 30
    max_retries: 1
    api_key_env: OPENAI_API_KEY
    options:
      temperature: 0.2
      max_output_tokens: 1024

  claude:
    protocol: anthropic_messages
    endpoint: https://api.anthropic.com
    model: claude-test
    api_key_env: ANTHROPIC_API_KEY
    options:
      max_output_tokens: 4096
      thinking:
        mode: budget
        budget_tokens: 2048
```

Save the YAML above as `model.yaml` at the repository root and set `OPENAI_API_KEY` and
`ANTHROPIC_API_KEY` (or use `.env` below). Save this code as `catalog_demo.py` and run
`uv run --locked --project packages/infra/llm-provider-langchain python catalog_demo.py`.
It constructs models only and lists the `fast` and `claude` entries. The example model names are
placeholders; replace them before making real calls.

```python
from spawn_join_llm_provider_langchain import ModelCatalog

catalog = ModelCatalog.from_file()  # CWD/model.yaml + CWD/.env (if present)
model = catalog.create_chat_model()  # default: fast
claude = catalog.create_chat_model("claude")

for item in catalog.models:
    print(item.name, item.model, item.display_name)
```

`load_model_catalog("model.yaml", env_file=".env")` is the equivalent function entry point retained
for compatibility. When `path` is omitted it reads `model.yaml` in the current working directory;
`env_file` defaults to `"auto"`, reading `.env` in the current working directory when present, and
`None` disables it.

`.env` stores keys only; the model file stores variable names only:

```dotenv
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

Rules:

- `.env` defaults to the current working directory's `.env` (missing file is skipped);
  `env_file=None` disables it; no other path is searched.
- Process environment (or a caller-provided `environ=`) takes precedence over `.env`.
- A present but empty/blank process variable raises an error instead of falling back to `.env`.
- `.env` uses `interpolate=False`; `${VAR}` is not expanded and process environment is not read.
- Only variables referenced by `api_key_env` are snapshotted at load time; `os.environ` is never
  modified.
- No variable interpolation, inline `api_key`, multi-file merge, or hot reload.
- All validation failures raise `ConfigurationError` with the YAML path; errors and `repr` contain
  no secret values or file line contents.
- A missing `display_name` falls back to the selection name; it participates in neither lookup,
  `default`, nor protocol selection.

### Model metadata snapshot

Entries with `schema_version: 2` may optionally declare metadata:

```yaml
schema_version: 2
default: fast
models:
  fast:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: gpt-5
    api_key_env: OPENAI_API_KEY
    metadata_ref: openai/gpt-5
    metadata_source:
      models.dev:
        provider: openai
        model: gpt-5
    metadata:
      pricing:
        currency: USD
        rates:
          - modality: text
            direction: input
            unit: per_million_tokens
            amount: 1.25
```

The v2 YAML above is a standalone model-file example. First generate `model-metadata.json`
following the [sync tool guide](../llm-model-sync/README.en.md#users-installation-and-daily-operations).
Save this as `metadata_catalog_demo.py` and run in the same adapter environment, with both data
files in the current directory and `OPENAI_API_KEY` configured.

```python
from spawn_join_llm_provider_langchain import ModelCatalog

catalog = ModelCatalog.from_file(
    "model.yaml",
    metadata_file="model-metadata.json",
)
summary = catalog.models[0]
print(summary.metadata_ref, summary.metadata)
```

Rules:

- `metadata_ref` uses explicit `<lab>/<model>` matching, never fuzzy name guessing.
- `metadata_source` must exist together with `metadata_ref`; it is used only by sync tools to
  resolve channel overrides, never for protocol selection or model creation.
- Merge precedence: shared model facts → `channels.<entry-name>` → the entry's manual `metadata`
  override.
- `metadata_file=None` reads no snapshot and behaves exactly like v1; a provided path with a missing
  file, invalid JSON, or mismatched `base_model` raises `ConfigurationError`.
- Loading a snapshot performs no network request and searches no AppData; the path must be explicit.
- Metadata is a read-only description and does not drive routing, degradation, or capability
  negotiation.
- Invalid `metadata_source` coordinates raise `ConfigurationError` with a field path and no invalid
  values in the public message. The original exception remains in `__cause__`; a full traceback may
  include the original input.

## Protocols and options

| Protocol | Return type | Option mapping |
|---|---|---|
| `chat_completions` | `ChatOpenAI` (`use_responses_api=False`) | `temperature`, `max_completion_tokens`, `top_p`, `stop_sequences`, `seed`, `reasoning_effort` |
| `responses` | `ChatOpenAI` (`use_responses_api=True`) | `temperature`, `max_completion_tokens`, `top_p`, `store`, `reasoning_effort`, `truncation` |
| `anthropic_messages` | `ChatAnthropic` | `temperature`, `max_tokens_to_sample`, `top_p`, `top_k`, `stop`, `thinking`, `reasoning_effort` |

All three protocols explicitly set `max_retries` (default `0`), endpoint, and timeout.

When Anthropic `max_output_tokens` is omitted, the factory preserves LangChain's native
model-specific output budget. Its value depends on the model and installed LangChain version.
Explicit configuration and native call-time `max_tokens` overrides remain supported.

### Chat Completions

```python
from spawn_join_llm_provider import ChatCompletionsOptions

options = ChatCompletionsOptions(
    temperature=0.2,
    max_output_tokens=1024,
    top_p=0.9,
    stop=("\n\n", "END"),
    seed=42,
    reasoning_effort="medium",
)
```

### Responses

```python
from spawn_join_llm_provider import ResponsesOptions

options = ResponsesOptions(
    temperature=0.1,
    max_output_tokens=2048,
    store=False,
    reasoning_effort="medium",
    truncation="disabled",
)
```

### Anthropic Messages

```python
from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    AnthropicThinkingBudget,
)

options = AnthropicMessagesOptions(
    temperature=0.5,
    max_output_tokens=4096,
    top_p=0.7,
    top_k=10,
    stop_sequences=("\n\n",),
    thinking=AnthropicThinkingBudget(budget_tokens=2048),
)
```

`AnthropicThinkingAdaptive()` can be used for adaptive thinking. Budget mode requires
`max_output_tokens` to exist and exceed `budget_tokens`.

## Thinking and reasoning effort

**Thinking can already be controlled through native LangChain call parameters, with no factory
change or new Options field.** `create_chat_model()` returns a native `BaseChatModel`; protocol
options are construction defaults, while per-call parameters go directly to LangChain and override
defaults according to its rules.

### Set effort for one call

The following is a complete async example. `protocol` must match the server interface and can be
`CHAT_COMPLETIONS`, `RESPONSES`, or `ANTHROPIC_MESSAGES`:

```python
import asyncio
import os

from langchain_core.messages import HumanMessage
from spawn_join_llm_provider import ProtocolKind
from spawn_join_llm_provider_langchain import ChatModelConfig, create_chat_model


async def main() -> None:
    model = create_chat_model(
        ChatModelConfig(
            protocol=ProtocolKind.CHAT_COMPLETIONS,
            endpoint=os.environ["LLM_BASE_URL"],
            model=os.environ["LLM_MODEL"],
            timeout_seconds=60.0,
        ),
        api_key=os.environ["LLM_API_KEY"],
    )

    response = await model.ainvoke(
        [HumanMessage(content="Analyze the pros and cons of this proposal")],
        reasoning_effort="high",
        max_tokens=8192,
    )
    print(response.content)


asyncio.run(main())
```

Set `LLM_BASE_URL`, `LLM_MODEL`, and `LLM_API_KEY` before running. The URL should be the API base
URL of the corresponding service; the model must support the selected protocol and parameters;
actually executing `ainvoke()` sends a request to that service. The example explicitly sets
`max_tokens` to satisfy Anthropic's required output budget; LangChain maps it to the corresponding
token-limit parameter for OpenAI protocols. The budget must still satisfy the target model's
limits.

LangChain maps the same `reasoning_effort` name per protocol:

| Protocol | Call parameter | Request mapping owned by LangChain |
|---|---|---|
| `chat_completions` | `reasoning_effort="high"` | `reasoning_effort` |
| `responses` | `reasoning_effort="high"` | `reasoning.effort` |
| `anthropic_messages` | `reasoning_effort="high"` | `output_config.effort` |

Applications need not assemble `reasoning` / `output_config` manually or convert effort into a
token budget. Anthropic `effort` is an alias of LangChain `reasoning_effort`; usually pass only one.

### Anthropic explicit thinking modes

The following snippets go inside an async function; `model` must be created with the
`ANTHROPIC_MESSAGES` protocol and must use a model that supports the mode.

```python
# Adaptive thinking with a specified effort.
response = await model.ainvoke(
    [HumanMessage(content="Analyze the pros and cons of this proposal")],
    thinking={"type": "adaptive"},
    reasoning_effort="high",
    max_tokens=8192,
)
```

For models that support a fixed budget or disabling thinking:

```python
# Fixed budget: budget_tokens is at least 1024 and less than max_tokens.
response = await model.ainvoke(
    [HumanMessage(content="Analyze the pros and cons of this proposal")],
    thinking={"type": "enabled", "budget_tokens": 2048},
    max_tokens=4096,
)

# Explicit disable: only for models that support disabled.
response = await model.ainvoke(
    [HumanMessage(content="Hello")],
    thinking={"type": "disabled"},
    max_tokens=4096,
)
```

### Defaults, compatibility, and boundaries

- All three Options types support `reasoning_effort` with `low` / `medium` / `high`;
  `AnthropicMessagesOptions` additionally supports fixed-budget and adaptive `thinking`.
  This does not restrict native call parameters.
- `None` in `Options` means "do not specify this default", not "explicitly disable thinking".
  Omitting `reasoning_effort` (or the whole `options` block) in YAML also means unspecified;
  an explicit `reasoning_effort: null` is rejected before model creation with a path-bearing
  `ConfigurationError`. Python `None` is not equivalent to YAML null.
- Same-named fields do not mean every model supports the same levels, and not every model allows
  disabling thinking. Effort is not a fixed token budget; behavior without `thinking` is determined
  by LangChain and the target model.
- The call shapes above were checked against `langchain-openai==1.7.3` and
  `langchain-anthropic==1.7.7` from the repository `uv.lock`. `langchain-core` and
  `langchain-anthropic` declare `>=1.5.0,<2.0`; `langchain-openai` keeps `>=1.0,<2.0`.
  A lower bound does not prove every intermediate version works; use `uv sync --locked` in this
  repository and verify the installed version elsewhere.
- OpenAI-compatible services may not support the same thinking extensions. This package does not
  guess model capabilities, switch protocols, or degrade parameters; unsupported-parameter errors
  come from LangChain / the server and are the application's responsibility.
- These examples document existing call entry points; they do not claim this project executed real
  Provider integration verification.

References: [LangChain OpenAI integration](https://docs.langchain.com/oss/python/integrations/chat/openai),
[LangChain Anthropic reasoning_effort](https://reference.langchain.com/python/langchain-anthropic/chat_models/ChatAnthropic/reasoning_effort).

## Tool calling

First save the complete `quickstart.py` and configure the same three environment variables.
Save this alongside it as `tools_demo.py` and run
`uv run --locked --project packages/infra/llm-provider-langchain python tools_demo.py`.
The model must support tools; this demonstrates one round of tool requests, application execution,
result messages and a final response.

```python
import asyncio

from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from quickstart import build_model


@tool
def lookup(order_id: str) -> str:
    """Look up the shipping status of a demo order."""
    return "shipped" if order_id == "A-100" else "unknown order"


async def main() -> None:
    model = build_model()
    messages: list[BaseMessage] = [HumanMessage(content="Where is order A-100?")]
    response = await model.bind_tools([lookup]).ainvoke(messages)
    messages.append(response)
    if not response.tool_calls:
        print(response.content)
        return
    for call in response.tool_calls:
        if call["name"] != lookup.name:
            raise ValueError("Unexpected tool requested")
        output = lookup.invoke(call["args"])
        messages.append(ToolMessage(content=str(output), tool_call_id=call["id"]))
    final = await model.ainvoke(messages)
    print(final.content)


if __name__ == "__main__":
    asyncio.run(main())
```

`response.tool_calls` is a LangChain `AIMessage` field; the application passes results back to the
model as `ToolMessage`, with no project conversion layer.

## Streaming

Reuse `quickstart.py` and its environment variables. Save this as `stream_demo.py` and run
`uv run --locked --project packages/infra/llm-provider-langchain python stream_demo.py`.
It prints text incrementally; the service determines the exact text and chunk boundaries.

```python
import asyncio

from langchain_core.messages import HumanMessage
from quickstart import build_model


async def main() -> None:
    model = build_model()
    async for chunk in model.astream([HumanMessage(content="Say hello.")]):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print()


if __name__ == "__main__":
    asyncio.run(main())
```

`astream` yields LangChain `AIMessageChunk`; text, tool arguments, and usage metadata all come
directly from LangChain.

## Configuration and errors

`ChatModelConfig` extends the shared `EndpointConfig`; fields are flat:

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class ChatModelConfig(EndpointConfig):
    model: str
    max_retries: int = 0
```

It **does not depend on `ChannelConfig`**. Calling a model requires neither a channel name nor a
credential reference.

The following raise `ConfigurationError` before a model is constructed:

| Situation | Result |
|---|---|
| `api_key` empty or whitespace only | `ConfigurationError` |
| `model` empty or whitespace only | `ConfigurationError` |
| `max_retries < 0` | `ConfigurationError` |
| invalid protocol / endpoint / timeout | `ConfigurationError` (from `EndpointConfig`) |
| option type does not match protocol | `ConfigurationError` |
| invalid option value | `ConfigurationError` |
| unknown protocol value | `ConfigurationError` |
| model file missing, unreadable, or non-UTF-8 | `ConfigurationError` (with path) |
| YAML syntax error or duplicate key | `ConfigurationError` (line/column, no file content) |
| recursive YAML alias | `ConfigurationError` (recursive alias, no position) |
| invalid `schema_version` / field / option | `ConfigurationError` (with YAML path) |
| secret variable missing or empty | `ConfigurationError` (model and variable names) |
| explicit `env_file` path missing | `ConfigurationError` (default `.env` missing is skipped) |

Exceptions during LangChain calls are handled by LangChain/the application; this package does not
copy an inference exception hierarchy.

## Security

- The API key is passed only at factory call time and wrapped as `SecretStr`.
- `ChatModelConfig` stores no API key; `ModelCatalog` keeps only the `.env` snapshot referenced by
  `api_key_env` for creation, exposes no public read, and hides it from `repr`.
- `.env` defaults to the current working directory's `.env` (when present); `env_file=None`
  disables it; `interpolate=False` means `${VAR}` is not expanded.
- Process environment takes precedence; a present but empty process variable raises instead of
  falling back to `.env`.
- Only variables referenced by `api_key_env` are snapshotted; `os.environ` is not modified.
- Endpoints reject embedded username/password, whitespace/control characters, and invalid
  host/port.
- Error messages do not concatenate YAML line contents or echo secret values.
- Default `max_retries=0` does not hide SDK automatic retries.

## Design boundaries

- Does not define `Message`, content blocks, tools, `ChatRequest`, `ChatResponse`, `StreamEvent`,
  or `LLMProvider`.
- Does not expose public dictionary channels such as `map_options()` / `bind_options()`; options are
  mapped at construction.
- Does not implement real channel HTTP, pooling, routing, health-based selection, or HTTP connection
  pools.
- Does not infer protocol from model names; protocol must be configured explicitly.
- Model-file loading and environment parsing belong to this adapter; the protocol package remains
  framework-independent and gains no dependency.
- Public API is `ChatModelConfig`, `ModelCatalog`, `ModelSummary`, `create_chat_model`,
  `load_model_catalog`, pinned by [`test_public_api.py`](tests/test_public_api.py).

Internal file shapes are declared in `model_file/_input.py`. Typed helpers in `_validation.py`
check shapes and strict value types, and `_schema.py` assembles the existing configuration objects.
Strict reading and Pydantic exception conversion reuse `spawn-join-common`; the error type,
null rules, and first-error order remain owned by this adapter.
These are private adapter implementation details, not new public APIs. YAML duplicate-key checks,
omitted versus explicit `null` values, domain-validation order, and safe error paths are preserved.
When adding a field, update its input model, domain mapping, and regression tests instead of
maintaining parallel allowed-key lists and per-field option readers. Entry-level fields are still
read in the original domain-construction order to preserve the first error for multiple invalid inputs.

## Development and verification

```powershell
uv lock --check --directory packages/infra/llm-provider-langchain
uv sync --locked --directory packages/infra/llm-provider-langchain
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain
```

The quality command includes Black, isort, Ruff, Pyright strict, pytest, isolated build/install,
and import checks. Default tests cover model construction, configuration parsing, and offline request
conversion; they use no network and no real credentials.

When adding a protocol or option, maintainers must:

1. add typed options and validation in the protocol package;
2. add an explicit mapping branch in
   [`factory.py`](src/spawn_join_llm_provider_langchain/factory.py);
3. add regressions in [`test_factory.py`](tests/test_factory.py) and
   [`test_public_api.py`](tests/test_public_api.py);
4. check [package boundaries](../../../docs/architecture/package-boundaries.md),
   [quality gates](../../../docs/development/quality-gates.md), and
   [ADR-0006](../../../docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md) for
   consistency.

## Related packages

- [`spawn-join-llm-provider`](../../core/llm-provider/README.en.md): endpoint, channel, protocol
  options, and error contracts.
- [`spawn-join-common`](../../core/common/README.en.md): shared strict reading and Pydantic
  exception conversion; this package keeps its own input schema, error type, null rules, and
  first-error order.
- [`spawn-join-core`](../../core/spawn-join-core/README.en.md): shared configuration, exceptions, and
  types.

See [LICENSE](LICENSE).

## Maintenance and releases

Owned by the SpawnJoin repository maintainers (author: Yan Zhiwei). Source lives in
`src/spawn_join_llm_provider_langchain/`; `tests/` contains offline contracts and fixtures.
Use PowerShell 7, uv 0.7.13+, Git, and Node.js 22+ for the quality gate. Follow
[contributor rules](../../../AGENTS.md); report issues with a minimal configuration without
credentials. This package is versioned independently and is not published; release automation
is not configured. Public API changes require synchronized tests, both README languages,
compatibility notes, and explicit release authorization.
