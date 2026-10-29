# spawn-join-llm-provider

与框架无关的 LLM 协议和领域抽象。

## 当前状态

`0.1.0` 提供公共消息、请求、响应、流式事件、三种协议的原生选项、模型能力、渠道契约和
稳定错误。协议包不依赖 LangChain、OpenAI/Anthropic SDK 或 HTTP 客户端。

## 公共边界

- 公共请求只包含可移植字段：消息、工具、工具选择、最大输出、`temperature`、`top_p`。
- 高级参数使用协议原生类型：
  - `ChatCompletionsOptions`
  - `ResponsesOptions`
  - `AnthropicMessagesOptions`
- 不支持即报错，不做有损映射、静默丢弃或自动降级。
- `ReasoningBlock.opaque_state` 保存多轮回传所需的协议状态。
- `Channel` 契约与推理 `LLMProvider` 分离；真实渠道 HTTP 实现尚未提供。
- 渠道配置只保存 `credential_ref`，不保存明文密钥。

## 安装与验证

```powershell
uv sync --locked --directory packages/core/llm-provider
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider
```

许可证见 [LICENSE](LICENSE)。
