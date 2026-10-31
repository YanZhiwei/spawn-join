# spawn-join-llm-provider-langchain

把**显式协议配置**转换成配置好的 LangChain `BaseChatModel`。

应用直接使用 LangChain 的消息、工具、流式输出和回调；这个包只负责：

- 根据 protocol / endpoint / model 创建 `ChatOpenAI` 或 `ChatAnthropic`；
- 把三种协议的类型化选项映射成 LangChain 构造参数；
- 在创建模型前校验配置和选项；
- 用 `SecretStr` 包装 API key。

它不重新定义消息、内容块、工具、请求/响应、流式事件或 `LLMProvider`。

## 为什么用这个包

如果应用已经以 LangChain 为运行时，直接用 `ChatOpenAI` / `ChatAnthropic` 也可以。这个包
解决的是**配置边界**：

- 协议由显式 `ProtocolKind` 决定，不根据模型名称猜测；
- `ChatModelConfig` 只包含推理需要的字段，不依赖 `ChannelConfig`；
- 选项有类型和范围校验，不通过任意 `**kwargs` 静默传递；
- 渠道/模型配置和 LangChain 构造细节集中在一个工厂里。

## 状态

`0.1.0`。当前工厂只做离线构造和校验：

- 不发真实 Provider 请求；
- 不实现 channel HTTP、`ChannelPool`、路由或健康选路；
- 默认 `max_retries=0`，不隐藏 SDK 重试。

## 安装

这些包属于 SpawnJoin monorepo，尚未发布到 PyPI。每个 Distribution 都是独立 uv project：

```powershell
uv sync --locked --directory packages/infra/llm-provider-langchain
```

运行时依赖：

- `spawn-join-llm-provider`
- `langchain-core`
- `langchain-openai`
- `langchain-anthropic`
- `pydantic`

## 快速开始

```python
import os

from langchain_core.messages import HumanMessage
from spawn_join_llm_provider import ChatCompletionsOptions, ProtocolKind
from spawn_join_llm_provider_langchain import ChatModelConfig, create_chat_model

config = ChatModelConfig(
    protocol=ProtocolKind.CHAT_COMPLETIONS,
    endpoint="https://api.example.com/v1",
    model="example-chat-model",
    timeout_seconds=60.0,
)

model = create_chat_model(
    config,
    api_key=os.environ["LLM_API_KEY"],
    options=ChatCompletionsOptions(temperature=0.2),
)

response = await model.ainvoke([HumanMessage(content="Hello")])
print(response.content)
```

`api_key` 只在调用时传入，并立即包装为 `pydantic.SecretStr`；不会进入配置对象、repr 或日志。

## 协议与选项

| 协议 | 返回类型 | 选项映射 |
|---|---|---|
| `chat_completions` | `ChatOpenAI`（`use_responses_api=False`） | `temperature`、`max_completion_tokens`、`top_p`、`stop_sequences`、`seed` |
| `responses` | `ChatOpenAI`（`use_responses_api=True`） | `temperature`、`max_completion_tokens`、`top_p`、`store`、`reasoning_effort`、`truncation` |
| `anthropic_messages` | `ChatAnthropic` | `temperature`、`max_tokens_to_sample`、`top_p`、`top_k`、`stop`、`thinking` |

三种协议都显式设置 `max_retries`（默认 `0`）、endpoint 和 timeout。

### Chat Completions

```python
from spawn_join_llm_provider import ChatCompletionsOptions

options = ChatCompletionsOptions(
    temperature=0.2,
    max_output_tokens=1024,
    top_p=0.9,
    stop=("\n\n", "END"),
    seed=42,
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

`AnthropicThinkingAdaptive()` 可用于自适应 thinking。budget 模式要求
`max_output_tokens` 存在且大于 `budget_tokens`。

## 工具调用

工具定义和工具选择使用 LangChain 原生 API：

```python
from langchain_core.tools import tool

@tool
def lookup(order_id: str) -> str:
    """Look up an order."""
    return "shipped"

model_with_tools = model.bind_tools([lookup])
response = await model_with_tools.ainvoke(
    [HumanMessage(content="Where is order A-100?")]
)
```

`response.tool_calls` 是 LangChain 的 `AIMessage` 字段；应用把结果作为 `ToolMessage`
传回模型，不需要项目转换层。

## 流式输出

```python
async for chunk in model.astream([HumanMessage(content="Say hello.")]):
    if chunk.content:
        print(chunk.content, end="")
```

`astream` 产生 LangChain `AIMessageChunk`；文本、工具参数和 usage 元数据都直接来自
LangChain。

## 配置与错误

`ChatModelConfig` 继承共享 `EndpointConfig`，字段是扁平的：

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class ChatModelConfig(EndpointConfig):
    model: str
    max_retries: int = 0
```

它**不依赖 `ChannelConfig`**。只想调用模型时，不需要渠道名称或凭据引用。

以下情况在构造模型前抛 `ConfigurationError`：

| 情况 | 结果 |
|---|---|
| `api_key` 为空或只有空白 | `ConfigurationError` |
| `model` 为空或只有空白 | `ConfigurationError` |
| `max_retries < 0` | `ConfigurationError` |
| protocol / endpoint / timeout 非法 | `ConfigurationError`（继承自 `EndpointConfig`） |
| 选项类型与协议不匹配 | `ConfigurationError` |
| 选项值非法 | `ConfigurationError` |
| 未知 protocol 值 | `ConfigurationError` |

LangChain 调用阶段的异常由 LangChain/应用处理；本包不复制一套推理异常层次。

## 安全

- API key 只在工厂调用时传入，并包装为 `SecretStr`。
- `ChatModelConfig` 不保存 API key。
- endpoint 拒绝内嵌用户名/密码、空白/控制字符、非法 host/port。
- 配置和错误信息不要求输出完整私有 endpoint。
- 默认 `max_retries=0`，不隐藏 SDK 的自动重试。

## 设计边界

- 不定义 `Message`、内容块、工具、`ChatRequest`、`ChatResponse`、`StreamEvent` 或
  `LLMProvider`。
- 不提供 `map_options()` / `bind_options()` 之类的公共字典通道；选项在构造时映射。
- 不实现真实 channel HTTP、pool、路由、健康选路或 HTTP 连接池。
- 不根据模型名称推断协议；协议必须显式配置。
- 公共 API 只有 `ChatModelConfig` 和 `create_chat_model`，由
  [`test_public_api.py`](tests/test_public_api.py) 固定。

## 开发与验证

```powershell
uv lock --check --directory packages/infra/llm-provider-langchain
uv sync --locked --directory packages/infra/llm-provider-langchain
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain
```

质量命令包含 Black、isort、Ruff、Pyright strict、pytest、隔离构建/安装和导入检查。
默认测试只构造模型，不访问网络，不使用真实凭据。

维护者新增协议或选项时：

1. 在协议包增加类型化选项和校验；
2. 在 [`factory.py`](src/spawn_join_llm_provider_langchain/factory.py) 增加显式映射分支；
3. 在 [`test_factory.py`](tests/test_factory.py) 和
   [`test_public_api.py`](tests/test_public_api.py) 增加回归；
4. 检查
   [包边界](../../../docs/architecture/package-boundaries.md)、
   [质量门说明](../../../docs/development/quality-gates.md)
   和
   [ADR-0006](../../../docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md)
   是否仍然一致。

## 相关包

- [`spawn-join-llm-provider`](../../core/llm-provider/README.md)：endpoint、channel、
  协议选项和错误契约。
- [`spawn-join-core`](../../core/spawn-join-core/README.md)：共享配置、异常和类型。

许可证见 [LICENSE](LICENSE)。
