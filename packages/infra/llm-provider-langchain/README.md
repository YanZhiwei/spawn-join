# spawn-join-llm-provider-langchain

基于 LangChain 的 SpawnJoin LLM 协议适配层。

## 当前状态

`0.1.0` 提供三个显式选择的协议 Provider：

| 配置 | Provider | LangChain 入口 |
|---|---|---|
| `ChatCompletionsConfig` | `ChatCompletionsProvider` | `ChatOpenAI(use_responses_api=False)` |
| `ResponsesConfig` | `ResponsesProvider` | `ChatOpenAI(use_responses_api=True)` |
| `AnthropicMessagesConfig` | `AnthropicMessagesProvider` | `ChatAnthropic` |

`credential_ref` 是环境变量名，不是密钥值。工厂显式设置 `max_retries=0`；Responses 请求
默认显式发送 `store=False`。

## 使用示例

```python
import asyncio

from spawn_join_llm_provider import ChatRequest, Message, ProtocolKind, Role, TextBlock
from spawn_join_llm_provider_langchain import ChatCompletionsConfig, create_provider

provider = create_provider(
    ChatCompletionsConfig(
        model="<model>",
        credential_ref="LLM_API_KEY",
        base_url="https://example.com/v1",
    )
)
response = asyncio.run(
    provider.complete(
        ChatRequest(
            messages=(Message(role=Role.USER, content=(TextBlock("Hello"),)),)
        )
    )
)
```

高级参数使用协议原生选项；不支持或类型不匹配会在网络调用前失败。

## 边界

- 本包拥有 LangChain 类型、协议配置、参数映射和调用日志。
- LangChain 类型不进入 `spawn-join-llm-provider`。
- 默认测试使用 fake 模型，不需要真实凭据或网络。
- 真实渠道 `ping()`/`list_models()`、Azure 专用认证/deployment 尚未实现。

## 验证

```powershell
uv sync --locked --directory packages/infra/llm-provider-langchain
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain
```

许可证见 [LICENSE](LICENSE)。
