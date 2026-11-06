# spawn-join-llm-provider

[English](README.md) | [简体中文](README.zh-CN.md)

与框架无关的 LLM **channel 契约、协议选项和稳定错误**。

这个包不实现模型调用，也不重复 LangChain 的消息、工具或流式类型。它只保留 LangChain
不提供、但配置和运维确实需要的能力：

- 一个共享的 `EndpointConfig`（protocol、endpoint、timeout）；
- 一个 `Channel` 连接契约（`ping()`、`list_models()`）；
- 三种协议的类型化选项；
- 少量稳定的配置/渠道错误。

模型调用由
[`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/README.zh-CN.md)
负责；应用直接使用 LangChain 的 `BaseChatModel` 和消息类型。

**目录**

- [状态](#状态)
- [安装](#安装)
- [快速开始](#快速开始)
- [公共 API](#公共-api)
- [模型元数据契约](#模型元数据契约)
- [设计边界](#设计边界)
- [开发与验证](#开发与验证)
- [相关包](#相关包)
- [维护与发布](#维护与发布)

## 状态

`0.1.0`，早期开发，要求 Python `>=3.11`。当前只交付契约和离线测试：

- 没有真实 channel HTTP 实现；
- 没有 `ChannelPool`、模型路由或健康选路；
- 协议包只依赖 `spawn-join-core` 和通用校验库 Pydantic。

## 安装

这些包属于 SpawnJoin monorepo，尚未发布到 PyPI。每个 Distribution 都是独立 uv project：

```powershell
uv sync --locked --directory packages/core/llm-provider
```

从仓库根目录，在本包环境中验证导入：

```powershell
uv run --locked --directory packages/core/llm-provider python -c "import spawn_join_llm_provider"
```

在使用该环境的脚本中：

```python
import spawn_join_llm_provider
```

## 快速开始

### 完整示例：配置、渠道检查与模型列表

将下面整段保存到仓库根目录的 `channel_demo.py`，从仓库根目录执行：

```powershell
uv run --locked --project packages/core/llm-provider python channel_demo.py
```

`DemoChannel` 是示例自带的内存实现：返回固定结果，不访问示例 endpoint，也不读取密钥。
它演示如何实现与消费 `Channel`；真实 HTTP 连接检查需要应用提供自己的实现。

```python
import asyncio
from dataclasses import replace

from spawn_join_llm_provider import (
    Channel,
    ChannelConfig,
    ChannelStatus,
    ChatCompletionsOptions,
    ConfigurationError,
    ModelInfo,
    ModelPage,
    PingResult,
    ProtocolKind,
    UnsupportedChannelOperationError,
)


class DemoChannel:
    """An offline, single-page implementation for this example."""

    def __init__(self, config: ChannelConfig) -> None:
        self._config = config

    @property
    def config(self) -> ChannelConfig:
        return self._config

    async def ping(self) -> PingResult:
        return PingResult(status=ChannelStatus.OK)

    async def list_models(
        self, *, cursor: str | None = None, limit: int | None = None
    ) -> ModelPage:
        if cursor is not None:
            raise UnsupportedChannelOperationError("DemoChannel has only one page")
        if limit is not None and limit <= 0:
            raise ValueError("limit must be positive")
        return ModelPage(models=(ModelInfo(id="demo-model"),))


async def main() -> None:
    config = ChannelConfig(
        name="demo",
        credential_ref="demo-key-reference",
        protocol=ProtocolKind.CHAT_COMPLETIONS,
        endpoint="https://api.example.com/v1",
        timeout_seconds=30.0,
    )
    options = ChatCompletionsOptions(temperature=0.2, max_output_tokens=1024)
    channel: Channel = DemoChannel(config)
    health = await channel.ping()
    print(f"{channel.config.name}: {health.status.value}")
    if not health.ok:
        return
    page = await channel.list_models(limit=1)
    print("models:", ", ".join(model.id for model in page.models))
    print("max_output_tokens:", options.max_output_tokens)

    try:
        replace(config, timeout_seconds=0.0)
    except ConfigurationError:
        print("invalid timeout: rejected")


if __name__ == "__main__":
    asyncio.run(main())
```

预期输出：

```text
demo: ok
models: demo-model
max_output_tokens: 1024
invalid timeout: rejected
```

`credential_ref` 是引用名称，`options` 是独立的推理配置；渠道连通性检查不消费推理选项。
需要实际调用模型时，使用[适配包的完整快速开始](../../infra/llm-provider-langchain/README.zh-CN.md#快速开始)。
下面进一步说明各个配置类型。

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

### 思考参数：构造默认值与调用覆盖

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
[适配包的思考与思考强度](../../infra/llm-provider-langchain/README.zh-CN.md#思考与思考强度)。
具体模型和服务端必须支持所传参数；本包不做能力推断、强度到 token 预算的换算或自动降级。

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

`Channel` 是 `Protocol`，实现不需要继承基类。上方完整示例中的 `DemoChannel`
展示了全部三个成员：只读 `config` 属性、异步 `ping()` 与 `list_models()`。

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

## 模型元数据契约

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

### 完整示例：解析快照与覆盖元数据

将以下代码保存为仓库根目录的 `metadata_demo.py`，执行：

```powershell
uv run --locked --project packages/core/llm-provider python metadata_demo.py
```

模型、来源与哈希均为演示数据，不代表真实服务的能力或采集结果。所有操作在内存中完成。

```python
import json

from spawn_join_llm_provider import (
    ConfigurationError,
    apply_metadata_override,
    decode_metadata_document,
    parse_model_metadata_override,
)


def main() -> None:
    snapshot = {
        "schema_version": 1,
        "sources": {
            "demo": {
                "url": "https://example.com/catalog.json",
                "revision": "sha256:" + "0" * 64,
                "fetched_at": "2026-01-01T00:00:00Z",
                "license": "Example data only",
            }
        },
        "models": {
            "demo/chat": {
                "name": "Demo Chat",
                "type": "chat",
                "modalities": {"input": ["text"], "output": ["text"]},
                "limits": {"context": 8192, "output": 1024},
            }
        },
        "channels": {},
    }
    document = decode_metadata_document(json.dumps(snapshot))
    base = document.models["demo/chat"]
    override = parse_model_metadata_override({"limits": {"output": 512}})
    effective = apply_metadata_override(base, override)
    print("model:", base.key)
    print("base limits:", base.limits.context, base.limits.output)
    print("effective limits:", effective.limits.context, effective.limits.output)

    try:
        decode_metadata_document('{"schema_version": 1, "schema_version": 1}')
    except ConfigurationError:
        print("duplicate key: rejected")


if __name__ == "__main__":
    main()
```

预期输出：

```text
model: demo/chat
base limits: 8192 1024
effective limits: None 512
duplicate key: rejected
```

`limits` 整段替换，因此未在覆盖中声明的 `context` 变为 `None`（未知），原模型保持不变。
这里用标准库 `json.dumps` 编码输入字典；快照文件的生成和写入由同步工具负责。

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

- [`spawn-join-core`](../spawn-join-core/README.zh-CN.md)：共享配置、异常和类型。
- [`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/README.zh-CN.md)：
  LangChain 模型工厂、协议选项映射，以及 `model.yaml` / `.env` 解析。本包不读取
  文件或环境变量。

许可证见 [LICENSE](LICENSE)。

## 维护与发布

本包由 SpawnJoin 仓库维护者拥有，作者为 Yan Zhiwei。运行时源码位于
`src/spawn_join_llm_provider/`，离线测试位于 `tests/`。质量门需要 PowerShell 7、uv 0.7.13+、
Git 和 Node.js 22+，详见[质量前置条件](../../../docs/development/quality-gates.md#prerequisites)。
遵循[贡献规则](../../../AGENTS.md)，报告配置问题时提供最小复现。本包独立版本化，尚未
发布；当前未配置自动发布或包级 changelog。公共契约变更需同步测试、两种语言 README、
兼容性说明，并取得单独的发布授权。
