# spawn-join-llm-provider-langchain

把**显式协议配置**转换成配置好的 LangChain `BaseChatModel`。

应用直接使用 LangChain 的消息、工具、流式输出和回调；这个包只负责：

- 根据 protocol / endpoint / model 创建 `ChatOpenAI` 或 `ChatAnthropic`；
- 从显式 `model.yaml` 加载一组模型，按 `default` 或名字创建；
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
- `PyYAML`
- `python-dotenv`

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

## 模型文件与凭据

除了代码构造配置，也可以从显式路径的 `model.yaml` 加载一组模型：

```yaml
schema_version: 1
default: fast

models:
  fast:
    display_name: GPT Test Mini
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: gpt-test-mini
    timeout_seconds: 30
    max_retries: 1
    api_key_env: OPENAI_API_KEY
    options:
      temperature: 0.2
      max_output_tokens: 1024

  claude:
    protocol: anthropic_messages
    endpoint: https://api.anthropic.com
    model: claude-test
    api_key_env: ANTHROPIC_API_KEY
    options:
      max_output_tokens: 4096
      thinking:
        mode: budget
        budget_tokens: 2048
```

```python
from spawn_join_llm_provider_langchain import ModelCatalog

catalog = ModelCatalog.from_file()  # CWD/model.yaml + CWD/.env (if present)
model = catalog.create_chat_model()  # default: fast
claude = catalog.create_chat_model("claude")

for item in catalog.models:
    print(item.name, item.model, item.display_name)
```

`load_model_catalog("model.yaml", env_file=".env")` 是等价的函数入口，保留用于兼容。省略 `path` 时默认读取当前工作目录的 `model.yaml`；`env_file` 默认 `"auto"`，读取当前工作目录的 `.env`（存在时），`None` 关闭。

`.env` 只保存 key，模型文件只保存变量名：

```dotenv
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

规则：

- `.env` 默认读取当前工作目录的 `.env`（存在时，缺失跳过）；`env_file=None` 关闭；不搜索其他路径。
- 进程环境（或调用方传入的 `environ=`）优先于 `.env`。
- 进程环境存在但为空/空白时报错，不回退到 `.env`。
- `.env` 使用 `interpolate=False`，`${VAR}` 不会被展开，也不会读取进程环境。
- 加载时只快照 `api_key_env` 引用到的变量；不修改 `os.environ`。
- 不实现变量插值、内联 `api_key`、多文件合并或热重载。
- 所有校验失败抛 `ConfigurationError`，带 YAML 路径；错误和 `repr` 不含密钥或文件行内容。
- `display_name` 缺省回退为选择名；它不参与查找、`default` 或协议选择。

### 模型元数据快照

`schema_version: 2` 的条目可以选择性声明元数据：

```yaml
models:
  fast:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: gpt-5
    api_key_env: OPENAI_API_KEY
    metadata_ref: openai/gpt-5
    metadata_source:
      models.dev:
        provider: openai
        model: gpt-5
    metadata:
      pricing:
        currency: USD
        rates:
          - modality: text
            direction: input
            unit: per_million_tokens
            amount: 1.25
```

```python
catalog = ModelCatalog.from_file(
    "model.yaml",
    metadata_file="model-metadata.json",
)
summary = catalog.models[0]
print(summary.metadata_ref, summary.metadata)
```

规则：

- `metadata_ref` 使用 `<lab>/<model>` 显式匹配，不做名称模糊猜测。
- `metadata_source` 必须和 `metadata_ref` 同时存在；它只用于同步工具解析渠道覆盖，
  不参与协议选择或模型创建。
- 合并优先级：共享模型事实 → `channels.<条目名>` → 条目的 `metadata` 人工覆盖。
- `metadata_file=None` 时不读取快照，行为与 v1 完全一致；提供路径但文件缺失、JSON
  非法或 `base_model` 不匹配时抛 `ConfigurationError`。
- 加载快照不发起网络请求，也不搜索 AppData；路径必须显式传入。
- 元数据是只读描述，不驱动路由、降级或能力协商。

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
| 模型文件缺失、不可读或非 UTF-8 | `ConfigurationError`（含路径） |
| YAML 语法错误、重复键 | `ConfigurationError`（含行列，不含文件内容） |
| 递归 YAML 别名 | `ConfigurationError`（recursive alias，不含位置） |
| `schema_version` / 字段 / 选项非法 | `ConfigurationError`（含 YAML 路径） |
| 密钥变量缺失或为空 | `ConfigurationError`（含模型名与变量名） |
| 显式 `env_file` 路径不存在 | `ConfigurationError`（默认 `.env` 缺失时跳过） |

LangChain 调用阶段的异常由 LangChain/应用处理；本包不复制一套推理异常层次。

## 安全

- API key 只在工厂调用时传入，并包装为 `SecretStr`。
- `ChatModelConfig` 不保存 API key；`ModelCatalog` 只保留被 `api_key_env` 引用的
  `.env` 快照用于创建，不提供公开读取，`repr` 不显示。
- `.env` 默认读取当前工作目录的 `.env`（存在时）；`env_file=None` 关闭；`interpolate=False`，不会展开 `${VAR}`。
- 进程环境优先；进程环境存在但为空时报错，不回退到 `.env`。
- 加载时只快照被 `api_key_env` 引用的变量；不修改 `os.environ`。
- endpoint 拒绝内嵌用户名/密码、空白/控制字符、非法 host/port。
- 错误信息不拼接 YAML 行内容，不回显密钥值。
- 默认 `max_retries=0`，不隐藏 SDK 的自动重试。

## 设计边界

- 不定义 `Message`、内容块、工具、`ChatRequest`、`ChatResponse`、`StreamEvent` 或
  `LLMProvider`。
- 不提供 `map_options()` / `bind_options()` 之类的公共字典通道；选项在构造时映射。
- 不实现真实 channel HTTP、pool、路由、健康选路或 HTTP 连接池。
- 不根据模型名称推断协议；协议必须显式配置。
- 模型文件加载与环境变量解析归本适配包；协议包保持框架无关且不新增依赖。
- 公共 API 为 `ChatModelConfig`、`ModelCatalog`、`ModelSummary`、`create_chat_model`、
  `load_model_catalog`，由 [`test_public_api.py`](tests/test_public_api.py) 固定。

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
