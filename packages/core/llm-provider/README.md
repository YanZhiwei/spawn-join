# spawn-join-llm-provider

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

## 状态

`0.1.0`。当前只交付契约和离线测试：

- 没有真实 channel HTTP 实现；
- 没有 `ChannelPool`、模型路由或健康选路；
- 协议包只依赖 `spawn-join-core`。

## 安装

这些包属于 SpawnJoin monorepo，尚未发布到 PyPI。每个 Distribution 都是独立 uv project：

```powershell
uv sync --locked --directory packages/core/llm-provider
```

在仓库内直接导入：

```python
import spawn_join_llm_provider
```

## 快速开始

### 1. 描述一个 endpoint

`EndpointConfig` 是共享的扁平配置，只包含协议、endpoint 和 timeout：

```python
from spawn_join_llm_provider import EndpointConfig, ProtocolKind

endpoint = EndpointConfig(
    protocol=ProtocolKind.CHAT_COMPLETIONS,
    endpoint="https://api.example.com/v1",
    timeout_seconds=30.0,
)
```

### 2. 描述一个渠道

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

### 3. 使用协议选项

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

## 公共 API

### 配置类型

| 类型 | 用途 |
|---|---|
| `EndpointConfig` | protocol + endpoint + timeout，`ChannelConfig` 和 `ChatModelConfig` 的共同基类 |
| `ChannelConfig` | `EndpointConfig` + `name` + `credential_ref` |
| `ProtocolKind` | `chat_completions`、`responses`、`anthropic_messages` |
| `ChatCompletionsOptions` | Chat Completions 原生选项 |
| `ResponsesOptions` | Responses 原生选项 |
| `AnthropicMessagesOptions` | Anthropic Messages 原生选项 |
| `ProtocolOptions` | 三种选项的联合类型 |

### Channel 契约

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

### 错误

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

## 设计边界

- 不定义 `Message`、内容块、工具、请求/响应、流式事件或 `LLMProvider`。
- 不依赖 LangChain、OpenAI/Anthropic SDK 或 HTTP 客户端。
- 不实现真实渠道 HTTP、pool、路由或健康选路。
- `ChannelConfig` 只保证单个配置对象内的字段合法；跨配置唯一性由调用方或未来注册表负责。
- 公开 API 由 `tests/test_public_api.py` 固定，新增或删除符号需要同步契约和评审。

## 开发与验证

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

## 相关包

- [`spawn-join-core`](../spawn-join-core/README.md)：共享配置、异常和类型。
- [`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/README.md)：
  LangChain 模型工厂和协议选项映射。

许可证见 [LICENSE](LICENSE)。
