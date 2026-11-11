# spawn-join-llm-channel

[简体中文](README.md) | [English](README.en.md)

把显式的 `ChannelConfig` 变成真实的 OpenAI-compatible 或 Anthropic 渠道连接：检查
连通性/认证、分页列出模型，并把结果交给现有的 LangChain 模型工厂或应用目录。它**不**
依赖 LangChain，也不包装 `BaseChatModel`。

## 目录

- [为什么用这个包](#为什么用这个包)
- [状态](#状态)
- [安装](#安装)
- [快速开始](#快速开始)
- [凭据](#凭据)
- [错误映射](#错误映射)
- [分页与限制](#分页与限制)
- [生命周期](#生命周期)
- [测试](#测试)
- [设计边界](#设计边界)
- [相关包](#相关包)

## 为什么用这个包

`spawn-join-llm-provider` 定义了框架无关的 `Channel` 契约，但没有真实 Provider 实现。
这个包补上两层能力：

- `OpenAIChannel`：`chat_completions` / `responses` 协议的 `/models` 检查与列表；
- `AnthropicChannel`：`anthropic_messages` 协议的 `/v1/models` 检查与列表。

应用可以用 `ChannelConfig -> ping/list_models -> ModelInfo` 先验证渠道，再把选中的
模型交给 `spawn-join-llm-provider-langchain` 的 `ChatModelConfig.from_channel()`。

## 状态

`0.1.0`，早期开发，要求 Python `>=3.11`。当前只实现渠道连接检查和模型发现：

- 不生成 completion；
- 不做 pool、路由、健康选路或 failover；
- 不读取 `model.yaml`、`.env` 或密钥管理服务；
- 不自动把发现结果写入模型文件；
- 不依赖 LangChain。

## 安装

这些包属于 SpawnJoin monorepo，尚未发布到 PyPI。每个 Distribution 都是独立 uv project：

```powershell
uv sync --locked --directory packages/infra/llm-channel
```

运行时依赖：

- `spawn-join-llm-provider`
- `openai`
- `anthropic`

## 快速开始

### 离线检查（fake client，无网络）

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
        client=FakeClient(),  # 真实应用使用 AsyncOpenAI
    )
    print(await channel.ping())
    page = await channel.list_models(limit=10)
    print(page.models)
    await channel.aclose()


asyncio.run(main())
```

### 真实连接

设置 `OPENAI_API_KEY` 或 `ANTHROPIC_API_KEY`，并把 `endpoint` 指向实际 API：

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
channel = create_channel(config)  # 从环境变量解析密钥
```

`create_channel()` 按 `ProtocolKind` 返回 `OpenAIChannel` 或 `AnthropicChannel`。
真实调用需要网络和有效凭据；本仓库的默认测试不会发起此类请求。

Anthropic 的 `endpoint` 会作为 SDK 的 `base_url`，因此通常使用 API 源站
`https://api.anthropic.com`，不要再追加 `/v1`（SDK 会请求 `/v1/models`）；
OpenAI-compatible 端点通常本身包含 `/v1`。显式 `api_key` 也会经过非空/无前后空白校验。

## 凭据

优先级：

1. 注入的 SDK client（`OpenAIChannel(..., client=...)`）；
2. 显式 `api_key`；
3. `credential_ref` 作为环境变量名，从进程环境读取。

`credential_ref` 不保存明文密钥；缺失、空或带前后空白的环境变量值会抛
`ConfigurationError`。本包不修改 `os.environ`，不读取 `.env`。

## 错误映射

| 条件 | `ping()` | `list_models()` |
|---|---|---|
| 401/403 | `AUTHENTICATION_FAILED` | `ChannelAuthenticationError` |
| 超时 | `TIMEOUT` | `ChannelUnavailableError` |
| 连接失败 | `UNREACHABLE` | `ChannelUnavailableError` |
| 429 | `UNREACHABLE` | `ChannelUnavailableError` |
| 5xx | `UNREACHABLE` | `ChannelUnavailableError` |
| 404/405 | `UNSUPPORTED` | `UnsupportedChannelOperationError` |
| 畸形响应 | `INVALID_RESPONSE` | `ChannelResponseError` |
| 其他 API 错误 | `INVALID_RESPONSE` | `ChannelResponseError` |

公开消息只使用固定文案，不拼接 SDK `str(exc)`、请求体、完整 URL 或密钥；原始异常通过
`raise ... from exc` 保留原因链。

## 分页与限制

- `list_models(limit=...)` 的 `limit` 必须是正数；`limit <= 0` 在请求前抛 `ValueError`。
- OpenAI-compatible 模型列表当前是单页；`next_cursor` 为 `None`，传入 `cursor` 会抛
  `ValueError`。
- Anthropic 使用 `after_id`/`limit` 和 `has_more`/`last_id`；有下一页时返回 cursor。
- 空模型列表是合法的成功结果。
- 404/405 表示渠道可达但不提供模型列表能力，不是认证失败。

## 生命周期

`OpenAIChannel` / `AnthropicChannel` 持有 SDK 客户端；使用完毕后调用
`await channel.aclose()`。如果注入 client，调用方应知悉 `aclose()` 会关闭该 client；
共享 client 的生命周期由调用方管理。

## 测试

```powershell
uv lock --check --directory packages/infra/llm-channel
uv sync --locked --directory packages/infra/llm-channel
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-channel
```

默认真实 Provider 测试会 skip。显式启用：

```powershell
$env:SPAWN_JOIN_LIVE_OPENAI = "1"
$env:OPENAI_API_KEY = "..."
uv run --locked --project packages/infra/llm-channel pytest packages/infra/llm-channel/tests/test_live.py -q
```

无凭据时 skip 不等于通过；交付报告会明确标记未执行。

## 设计边界

- 不定义消息、内容块、请求/响应或 `BaseChatModel`；
- 不实现 pool、路由、健康选路、failover、限流或并发控制；
- 不新增 `channels.yaml`、远程配置中心、热重载或密钥管理服务；
- 不自动修改 `model.yaml`；
- 公共 API 为 `OpenAIChannel`、`AnthropicChannel`、`ChatChannel`、`create_channel`，
  由 `tests/test_public_api.py` 固定。

## 相关包

- [`spawn-join-llm-provider`](../../core/llm-provider/README.md)：`Channel` 契约、选项、
  元数据和稳定错误。
- [`spawn-join-llm-provider-langchain`](../llm-provider-langchain/README.md)：
  `ChatModelConfig.from_channel`、`ModelSummary.from_model_info` 和原生模型工厂。
- [`spawn-join-llm-model-sync`](../llm-model-sync/README.md)：模型元数据快照同步。

许可证见 [LICENSE](LICENSE)。
