# spawn-join-llm-provider

与 LangChain 无关的 LLM 渠道契约、协议选项和稳定错误。

## 边界

- 只依赖 `spawn-join-core`。
- 不依赖 LangChain、OpenAI/Anthropic SDK 或 HTTP 客户端。
- 不定义消息、内容块、工具、请求/响应、流式事件或 Provider 包装层。
- 不实现真实渠道 HTTP，也不提供 `ChannelPool`、路由或健康选路。

LangChain 消息和模型运行时由
[`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/) 提供。

## 协议选项

```python
from spawn_join_llm_provider import (
    ChatCompletionsOptions,
    ProtocolKind,
    ResponsesOptions,
)

chat_options = ChatCompletionsOptions(temperature=0.2, max_output_tokens=1024)
responses_options = ResponsesOptions(store=False, reasoning_effort="medium")
```

三种协议选项分别对应 `chat_completions`、`responses` 和 `anthropic_messages`。
选项在构造时校验；非法值抛出 `ConfigurationError`，不会被静默丢弃。

## Endpoint 配置

`EndpointConfig` 是共享的扁平 endpoint 契约：

```python
from spawn_join_llm_provider import EndpointConfig, ProtocolKind

endpoint = EndpointConfig(
    protocol=ProtocolKind.CHAT_COMPLETIONS,
    endpoint="https://api.example.com/v1",
    timeout_seconds=30.0,
)
```

`ChannelConfig` 和适配层的 `ChatModelConfig` 都继承它，因此协议、endpoint 和 timeout
只有一份校验。模型配置不需要 channel 专属字段。

## 渠道契约

```python
from spawn_join_llm_provider import ChannelConfig, ProtocolKind

config = ChannelConfig(
    name="openai-primary",
    protocol=ProtocolKind.CHAT_COMPLETIONS,
    endpoint="https://api.example.com/v1",
    credential_ref="openai-default",
    timeout_seconds=30.0,
)
```

`ChannelConfig` 继承 `protocol`、`endpoint` 和 `timeout_seconds`，只增加 `name` 和
`credential_ref`。`name` 是非敏感、人类可读的渠道标识，用于日志和错误定位；唯一性由
调用方或未来的渠道注册表负责。`credential_ref` 只是密钥引用，不是明文密钥。

`Channel` 提供：

```python
async def ping() -> PingResult: ...
async def list_models(
    *, cursor: str | None = None, limit: int | None = None
) -> ModelPage: ...
```

`ping()` 只检查连通性和认证，不执行生成请求。`PingResult` 用 `ChannelStatus` 区分
`ok`、`authentication_failed`、`unreachable`、`timeout` 和 `invalid_response`。

`list_models()` 的五种情况必须可区分：

| 结果 | 表示 |
|---|---|
| 成功，有模型 | `ModelPage(models=(...))` |
| 成功，无模型 | `ModelPage(models=())` |
| 渠道不支持 | `UnsupportedChannelOperationError` |
| 请求失败 | `ChannelUnavailableError` |
| 响应畸形 | `ChannelResponseError` |

本包只交付契约；真实 HTTP 实现需要单独的 Feature 和集成证据。

## 使用与验证

```python
import spawn_join_llm_provider
```

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider
```

许可证见 [LICENSE](LICENSE)。
