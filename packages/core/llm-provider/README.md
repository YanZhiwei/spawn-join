# spawn-join-llm-provider

SpawnJoin 的框架无关 LLM 协议与领域抽象。

## 当前状态

`0.1.0` 提供公共消息、请求/响应、流式事件、三种协议的原生选项、模型能力、渠道契约和
稳定错误。协议包不依赖 LangChain、OpenAI/Anthropic SDK 或 HTTP 客户端。

## 使用

```python
from spawn_join_llm_provider import (
    ChatCompletionsOptions,
    ChatRequest,
    Message,
    Role,
    TextBlock,
)

request = ChatRequest(
    messages=(
        Message(role=Role.USER, content=(TextBlock("Hello"),)),
    ),
    max_output_tokens=256,
    options=ChatCompletionsOptions(stop=("END",)),
)
```

本包只定义类型和契约，不发起网络请求。实际 Provider 实现见
[`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/README.md)。

## 公共 API

| 类别 | 主要类型 |
| --- | --- |
| 消息与内容 | `Message`、`Role`、`TextBlock`、`ReasoningBlock`、`ToolCallBlock`、`ToolResultBlock` |
| 请求与响应 | `ChatRequest`、`ChatResponse`、`Usage`、`FinishReason`、`StreamEvent` |
| 协议选项 | `ChatCompletionsOptions`、`ResponsesOptions`、`AnthropicMessagesOptions` |
| 能力与渠道 | `ModelCapabilities`、`Channel`、`ChannelConfig`、`PingResult`、`ModelPage` |
| 错误 | `LLMError` 及其认证、限流、超时、上下文超限等子类 |
| Provider 契约 | `LLMProvider`、`ProtocolKind` |

公共 API 通过包的 `__init__.py` 显式导出；内部模块不是稳定契约。

## 边界

- 公共请求只包含可移植字段：消息、工具、工具选择、最大输出、`temperature`、`top_p`。
- 高级参数使用协议原生类型；不建立统一的推理/上下文语义层。
- 不支持即报错，不做有损映射、静默丢弃或自动降级。
- `ReasoningBlock.opaque_state` 保存多轮回传所需的协议状态。
- `Channel` 契约与推理 `LLMProvider` 分离；真实渠道 HTTP 实现尚未提供。
- 渠道配置只保存 `credential_ref`，不保存明文密钥。
- 依赖方向固定为 `spawn-join-llm-provider-langchain -> spawn-join-llm-provider -> spawn-join-core`。

## 验证

仓库内开发使用独立 uv project：

```powershell
uv sync --locked --directory packages/core/llm-provider
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider
```

## 相关文档

- [包边界与依赖方向](../../../docs/architecture/package-boundaries.md)
- [ADR-0005：协议原生 LLM 契约与渠道边界](../../../docs/decisions/llm-provider/0005-protocol-native-llm-contracts.md)
- [LangChain 适配层](../../infra/llm-provider-langchain/README.md)
- [LICENSE](LICENSE)
