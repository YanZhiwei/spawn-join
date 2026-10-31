# spawn-join-llm-provider-langchain

把显式协议配置转换成配置好的 LangChain `BaseChatModel`。

## 边界

- 依赖 `spawn-join-llm-provider`、`langchain-core`、`langchain-openai`、
  `langchain-anthropic` 和 `pydantic`。
- LangChain 类型只留在本包和应用层，不泄漏回协议包或 Core。
- 不定义消息、内容块、工具、请求/响应、流式事件或 `LLMProvider`。
- 不实现真实 channel HTTP、`ChannelPool`、路由或健康选路。

应用直接使用 `langchain_core.messages`：

```python
from langchain_core.messages import HumanMessage
from spawn_join_llm_provider import (
    ChannelConfig,
    ChatCompletionsOptions,
    ProtocolKind,
)
from spawn_join_llm_provider_langchain import ChatModelConfig, create_chat_model

config = ChatModelConfig(
    channel=ChannelConfig(
        name="openai-primary",
        protocol=ProtocolKind.CHAT_COMPLETIONS,
        endpoint="https://api.example.com/v1",
        credential_ref="openai-default",
        timeout_seconds=60.0,
    ),
    model="example-chat-model",
)

model = create_chat_model(
    config,
    api_key="resolved-at-runtime",
    options=ChatCompletionsOptions(temperature=0.2),
)
response = await model.ainvoke([HumanMessage(content="Hello")])
```

`api_key` 只在调用时传入，并立即包装为 `SecretStr`；配置、repr 和日志中不保存明文密钥。

## 协议与选项

| 协议 | 返回类型 | 选项映射 |
|---|---|---|
| `chat_completions` | `ChatOpenAI`（`use_responses_api=False`） | `temperature`、`max_completion_tokens`、`top_p`、`stop_sequences`、`seed` |
| `responses` | `ChatOpenAI`（`use_responses_api=True`） | `temperature`、`max_completion_tokens`、`top_p`、`store`、`reasoning_effort`、`truncation` |
| `anthropic_messages` | `ChatAnthropic` | `temperature`、`max_tokens_to_sample`、`top_p`、`top_k`、`stop`、`thinking` |

三种协议都显式设置 `max_retries`，默认 `0`。协议与选项不匹配、空 key、空模型名或负重试
会在构造模型前抛出 `ConfigurationError`。

工具调用和流式输出使用 LangChain 原生 API：

```python
from langchain_core.tools import tool

@tool
def lookup(order_id: str) -> str:
    """Look up an order."""
    return "shipped"

model_with_tools = model.bind_tools([lookup])
```

`ainvoke` 返回 `AIMessage`，`astream` 产生 `AIMessageChunk`；项目不做消息转换。

## 使用与验证

```python
import spawn_join_llm_provider_langchain
```

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain
```

默认测试只构造模型，不访问网络、不需要真实凭据。真实 Provider 请求和 channel HTTP 不在
本包当前范围。

许可证见 [LICENSE](LICENSE)。
