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

## 思考与思考强度

**当前就可以通过 LangChain 原生调用参数控制思考，无需修改工厂或新增 Options 字段。**
`create_chat_model()` 返回原生 `BaseChatModel`；协议选项是构造默认值，单次调用参数直接
交给 LangChain，并按其规则覆盖默认值。

### 单次调用设置强度

以下是完整异步调用示例。`protocol` 必须与服务端接口匹配，可选择
`CHAT_COMPLETIONS`、`RESPONSES` 或 `ANTHROPIC_MESSAGES`：

```python
import asyncio
import os

from langchain_core.messages import HumanMessage
from spawn_join_llm_provider import ProtocolKind
from spawn_join_llm_provider_langchain import ChatModelConfig, create_chat_model


async def main() -> None:
    model = create_chat_model(
        ChatModelConfig(
            protocol=ProtocolKind.CHAT_COMPLETIONS,
            endpoint=os.environ["LLM_BASE_URL"],
            model=os.environ["LLM_MODEL"],
            timeout_seconds=60.0,
        ),
        api_key=os.environ["LLM_API_KEY"],
    )

    response = await model.ainvoke(
        [HumanMessage(content="分析这个方案的优缺点")],
        reasoning_effort="high",
        max_tokens=8192,
    )
    print(response.content)


asyncio.run(main())
```

运行前设置 `LLM_BASE_URL`、`LLM_MODEL` 和 `LLM_API_KEY`。地址应使用对应服务的 API
base URL，模型必须支持所选协议和参数；实际执行 `ainvoke()` 会向该服务发送请求。
示例显式设置 `max_tokens`，以满足 Anthropic 的必填输出预算；LangChain 会为 OpenAI
协议转换为相应的 token 上限参数。预算值仍需符合目标模型限制。

同一个 `reasoning_effort` 名称由 LangChain 按协议处理：

| 协议 | 调用参数 | LangChain 负责的请求映射 |
|---|---|---|
| `chat_completions` | `reasoning_effort="high"` | `reasoning_effort` |
| `responses` | `reasoning_effort="high"` | `reasoning.effort` |
| `anthropic_messages` | `reasoning_effort="high"` | `output_config.effort` |

不需要在应用中手工组装 `reasoning` / `output_config`，也不需要把强度换算成 token
预算。Anthropic 的 `effort` 是 LangChain `reasoning_effort` 的别名；通常只传一个即可。

### Anthropic 显式思考模式

以下片段放在异步函数内，`model` 必须由 `ANTHROPIC_MESSAGES` 协议创建，并使用支持
相应模式的模型：

```python
# 自适应思考，并指定投入强度。
response = await model.ainvoke(
    [HumanMessage(content="分析这个方案的优缺点")],
    thinking={"type": "adaptive"},
    reasoning_effort="high",
    max_tokens=8192,
)
```

对于支持固定预算或关闭思考的模型，也可以分别使用：

```python
# 固定预算：budget_tokens 至少为 1024，且小于 max_tokens。
response = await model.ainvoke(
    [HumanMessage(content="分析这个方案的优缺点")],
    thinking={"type": "enabled", "budget_tokens": 2048},
    max_tokens=4096,
)

# 显式关闭：仅适用于支持 disabled 的模型。
response = await model.ainvoke(
    [HumanMessage(content="你好")],
    thinking={"type": "disabled"},
    max_tokens=4096,
)
```

### 默认值、兼容性与边界

- 当前 `ChatCompletionsOptions` 没有 `reasoning_effort`；`ResponsesOptions` 已支持
  `low` / `medium` / `high`；`AnthropicMessagesOptions` 已支持固定预算和自适应
  `thinking`，但没有 `reasoning_effort`。这不限制原生调用参数入口。
- `Options` 中的 `None` 表示不指定该默认值，不表示显式关闭思考。不传调用覆盖值时，
  继续使用模型构造配置及 LangChain / 服务端默认行为。
- 字段同名不代表各模型支持相同等级，也不保证所有模型都允许关闭思考。思考强度不等于
  固定 token 预算；不指定 `thinking` 时的行为由 LangChain 和目标模型决定。
- 上述调用形状对照了仓库 `uv.lock` 中的 `langchain-openai==1.7.3` 和
  `langchain-anthropic==1.7.7`。不能仅凭包声明的 `>=1.0` 下限断言旧版本支持全部示例；
  在仓库内请使用 `uv sync --locked`，其他环境应核对实际安装版本。
- 兼容 OpenAI 的服务未必支持相同的思考扩展。本包不猜测模型能力、不自动切换协议或
  降级参数；不支持参数时的异常由 LangChain / 服务端产生，应用负责处理。
- 这些示例说明现有调用入口，不代表本项目已执行真实 Provider 集成验证。

参考：[LangChain OpenAI 集成](https://docs.langchain.com/oss/python/integrations/chat/openai)、
[LangChain Anthropic reasoning_effort](https://reference.langchain.com/python/langchain-anthropic/chat_models/ChatAnthropic/reasoning_effort)。

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
