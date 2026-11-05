# spawn-join-llm-provider

[简体中文](#中文) | [English](#english)

## 中文

与框架无关的 LLM **channel 契约、协议选项和稳定错误**。

这个包不实现模型调用，也不重复 LangChain 的消息、工具或流式类型。它只保留 LangChain
不提供、但配置和运维确实需要的能力：

- 一个共享的 `EndpointConfig`（protocol、endpoint、timeout）；
- 一个 `Channel` 连接契约（`ping()`、`list_models()`）；
- 三种协议的类型化选项；
- 少量稳定的配置/渠道错误。

模型调用由
[`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/README.md)
负责；应用直接使用 LangChain 的 `BaseChatModel` 和消息类型。

### 状态

`0.1.0`。当前只交付契约和离线测试：

- 没有真实 channel HTTP 实现；
- 没有 `ChannelPool`、模型路由或健康选路；
- 协议包只依赖 `spawn-join-core` 和通用校验库 Pydantic。

### 安装

这些包属于 SpawnJoin monorepo，尚未发布到 PyPI。每个 Distribution 都是独立 uv project：

```powershell
uv sync --locked --directory packages/core/llm-provider
```

在仓库内直接导入：

```python
import spawn_join_llm_provider
```

### 快速开始

#### 1. 描述一个 endpoint

`EndpointConfig` 是共享的扁平配置，只包含协议、endpoint 和 timeout：

```python
from spawn_join_llm_provider import EndpointConfig, ProtocolKind

endpoint = EndpointConfig(
    protocol=ProtocolKind.CHAT_COMPLETIONS,
    endpoint="https://api.example.com/v1",
    timeout_seconds=30.0,
)
```

#### 2. 描述一个渠道

`ChannelConfig` 继承 `EndpointConfig`，增加渠道名称和凭据引用：

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

- `name` 是非敏感、人类可读的渠道标识，用于日志和错误定位。
- `credential_ref` 只是密钥引用，不是明文密钥。
- `endpoint` 必须是绝对 `http(s)` URL，且不能内嵌用户名/密码。
- 所有字段都是 keyword-only，非法值在构造时抛 `ConfigurationError`。

#### 3. 使用协议选项

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

选项只表达协议原生参数，不包含工具定义或工具选择；工具调用使用 LangChain 的
`bind_tools` / `tool_choice`。

#### 思考参数：构造默认值与调用覆盖

这里的 `Options` 只覆盖模型**构造时的部分默认值**，不是 LangChain 调用能力的完整清单：

| 选项类型 | 当前可配置的思考默认值 |
|---|---|
| `ChatCompletionsOptions` | 尚无思考字段 |
| `ResponsesOptions` | `reasoning_effort`：`low`、`medium`、`high` |
| `AnthropicMessagesOptions` | `thinking`：固定 token 预算或自适应模式 |

**没有对应的 Options 字段，不代表模型调用不支持思考。** 工厂返回的是 LangChain
原生 `BaseChatModel`，应用可在 `ainvoke()` 等调用中直接传入 `reasoning_effort`、
Anthropic `thinking` 等原生参数，不需要扩展协议选项或自行转换请求。

例如，已创建的模型可以这样设置单次调用的思考强度：

```python
# 在 async 函数内；model 由 create_chat_model() 创建。
response = await model.ainvoke(
    [HumanMessage(content="分析这个方案的优缺点")],
    reasoning_effort="high",
    max_tokens=8192,
)
```

`HumanMessage` 来自 `langchain_core.messages`。完整构造示例、Anthropic 思考模式和
兼容性说明见
[适配包的思考与思考强度](../../infra/llm-provider-langchain/README.md#思考与思考强度)。
具体模型和服务端必须支持所传参数；本包不做能力推断、强度到 token 预算的换算或自动降级。

### 公共 API

#### 配置类型

| 类型 | 用途 |
|---|---|
| `EndpointConfig` | protocol + endpoint + timeout，`ChannelConfig` 和 `ChatModelConfig` 的共同基类 |
| `ChannelConfig` | `EndpointConfig` + `name` + `credential_ref` |
| `ProtocolKind` | `chat_completions`、`responses`、`anthropic_messages` |
| `ChatCompletionsOptions` | Chat Completions 原生选项 |
| `ResponsesOptions` | Responses 原生选项 |
| `AnthropicMessagesOptions` | Anthropic Messages 原生选项 |
| `ProtocolOptions` | 三种选项的联合类型 |

#### Channel 契约

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

`Channel` 是 `Protocol`，实现不需要继承基类。

`ping()` 只检查连通性和认证，不执行生成请求。`PingResult` 的 `ChannelStatus`：

| 状态 | 含义 |
|---|---|
| `ok` | 连通性和认证成功 |
| `authentication_failed` | 凭据无效或权限不足 |
| `unreachable` | 网络/DNS/连接失败 |
| `timeout` | 检查超时 |
| `invalid_response` | 响应无法解析或不符合契约 |

`list_models()` 的结果语义：

| 情况 | 表示 |
|---|---|
| 成功，有模型 | `ModelPage(models=(...))` |
| 成功，无模型 | `ModelPage(models=())` |
| 渠道不支持 | `UnsupportedChannelOperationError` |
| 网络/认证/超时失败 | `ChannelUnavailableError` |
| 响应无法解析 | `ChannelResponseError` |

空列表是合法的“没有模型”，不能用来表示失败或不支持。

#### 错误

```text
LLMProviderError
├── ConfigurationError
└── ChannelError
    ├── ChannelUnavailableError
    ├── UnsupportedChannelOperationError
    └── ChannelResponseError
```

配置非法、选项与协议不匹配、endpoint 无效、凭据引用为空或 timeout 非正数都会在构造时
抛 `ConfigurationError`。

### 模型元数据契约

`spawn_join_llm_provider.metadata` 提供只读、可校验的模型元数据类型：

- `ModelMetadata`、`ModelModalities`、`ModelCapabilitiesMetadata`、`ModelReasoning`、
  `ModelLimits`、`ModelPricing`、`ModelPriceRate`、`ModelPriceTier`；
- `ModelMetadataDocument`、`ModelSource`、`ModelChannel`、`ModelMetadataOverride`；
- `parse_model_metadata_document`、`parse_model_metadata_override`、
  `apply_metadata_override`、`decode_metadata_document`、`reject_duplicate_keys`。

实现使用 Pydantic dataclass 做边界字段校验，但公共对象仍是 dataclass，支持
`dataclasses.replace`、`frozen`、`slots` 和 `kw_only`。未知字段、类型错误和嵌套模型
由 Pydantic 校验；重复费率、排序、跨字段引用等业务不变量仍由 `__post_init__` 维护。
Pydantic 是通用校验依赖，不引入 LangChain、Provider SDK 或网络/文件副作用。

约束：

- 这些类型只描述事实，不参与协议选择、路由、降级或能力协商；它们不是 ADR-0006 禁止的
  运行时 `ModelCapabilities` 抽象。
- 价格使用带 `modality`、`direction`、`unit`、`amount` 的费率列表；金额必须有限且
  非负，单位必须显式；支持可选的长上下文阶梯。
- 快照文档只接受 `schema_version: 1`，未知字段、未知枚举和重复费率在解析时拒绝；
  顶层费率、阶梯费率和阶梯阈值按规范排序。
- 覆盖采用整段替换：`pricing`、`limits`、`capabilities`、`modalities`、`status`；
  不做字段级深合并。
- 本包不读取文件、不访问网络；快照文件和同步命令属于
  `spawn-join-llm-model-sync`。

长期边界见
[ADR-0009](../../../docs/decisions/llm-provider/0009-model-metadata-and-sync.md)。

### 设计边界

- 不定义 `Message`、内容块、工具、请求/响应、流式事件或 `LLMProvider`。
- 不依赖 LangChain、OpenAI/Anthropic SDK 或 HTTP 客户端。
- 不实现真实渠道 HTTP、pool、路由或健康选路。
- `ChannelConfig` 只保证单个配置对象内的字段合法；跨配置唯一性由调用方或未来注册表负责。
- 公开 API 由 `tests/test_public_api.py` 固定，新增或删除符号需要同步契约和评审。

### 开发与验证

```powershell
uv lock --check --directory packages/core/llm-provider
uv sync --locked --directory packages/core/llm-provider
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider
```

质量命令包含 Black、isort、Ruff、Pyright strict、pytest、隔离构建/安装和导入检查。
测试默认不访问网络，不使用真实凭据。

维护者变更公共 API 时：

1. 更新 `src/spawn_join_llm_provider/` 和对应测试；
2. 同步更新 [`__init__.py`](src/spawn_join_llm_provider/__init__.py) 和
   [`test_public_api.py`](tests/test_public_api.py) 中的精确导出；
3. 检查
   [包边界](../../../docs/architecture/package-boundaries.md)
   和
   [ADR-0006](../../../docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md)
   是否仍然一致。

### 相关包

- [`spawn-join-core`](../spawn-join-core/README.md)：共享配置、异常和类型。
- [`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/README.md)：
  LangChain 模型工厂、协议选项映射，以及 `model.yaml` / `.env` 解析。本包不读取
  文件或环境变量。

许可证见 [LICENSE](LICENSE)。

## English

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

### Status

`0.1.0`. This release delivers contracts and offline tests only:

- no real channel HTTP implementation;
- no `ChannelPool`, model routing, or health-based selection;
- the protocol package depends only on `spawn-join-core` and the general validation library Pydantic.

### Installation

These packages belong to the SpawnJoin monorepo and are not published to PyPI. Each Distribution
is an independent uv project:

```powershell
uv sync --locked --directory packages/core/llm-provider
```

Import directly inside the repository:

```python
import spawn_join_llm_provider
```

### Quick start

#### 1. Describe an endpoint

`EndpointConfig` is the shared flat configuration containing only protocol, endpoint, and timeout:

```python
from spawn_join_llm_provider import EndpointConfig, ProtocolKind

endpoint = EndpointConfig(
    protocol=ProtocolKind.CHAT_COMPLETIONS,
    endpoint="https://api.example.com/v1",
    timeout_seconds=30.0,
)
```

#### 2. Describe a channel

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

#### 3. Use protocol options

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

#### Thinking parameters: construction defaults and per-call overrides

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

### Public API

#### Configuration types

| Type | Purpose |
|---|---|
| `EndpointConfig` | protocol + endpoint + timeout; shared base for `ChannelConfig` and `ChatModelConfig` |
| `ChannelConfig` | `EndpointConfig` + `name` + `credential_ref` |
| `ProtocolKind` | `chat_completions`, `responses`, `anthropic_messages` |
| `ChatCompletionsOptions` | native Chat Completions options |
| `ResponsesOptions` | native Responses options |
| `AnthropicMessagesOptions` | native Anthropic Messages options |
| `ProtocolOptions` | union of the three option types |

#### Channel contract

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

#### Errors

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

### Model metadata contract

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

### Design boundaries

- Does not define `Message`, content blocks, tools, requests/responses, streaming events, or
  `LLMProvider`.
- Does not depend on LangChain, OpenAI/Anthropic SDKs, or an HTTP client.
- Does not implement real channel HTTP, pooling, routing, or health-based selection.
- `ChannelConfig` guarantees validity only inside one configuration object; cross-config uniqueness
  belongs to the caller or a future registry.
- Public API is pinned by `tests/test_public_api.py`; adding or removing symbols requires a
  synchronized contract and review.

### Development and verification

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

### Related packages

- [`spawn-join-core`](../spawn-join-core/README.md): shared configuration, exceptions, and types.
- [`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/README.md): LangChain
  model factory, protocol option mapping, and `model.yaml` / `.env` parsing. This package reads no
  files or environment variables.

See [LICENSE](LICENSE).
