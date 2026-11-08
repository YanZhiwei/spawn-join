# ADR-0013: 真实 Channel Transport、凭据边界与模型目录桥接

- Status: Proposed
- Date: 2026-11-08
- Domain: llm-provider
- Classification: 本决策约束 LLM 渠道连接、Provider SDK 依赖、凭据解析、模型发现和适配包桥接，属于 `llm-provider` 领域。
- Decision owner: 仓库维护者
- Accepted by / date: 未批准
- Depends on: [ADR-0006](0006-langchain-first-llm-runtime.md)、[ADR-0008](0008-model-file-and-env-boundary.md)、[ADR-0009](0009-model-metadata-and-sync.md)
- Related: [包边界](../../architecture/package-boundaries.md)、[ADR-0010](../agent/0010-deepagents-product-boundary.md)
- Supersedes: 无；本 ADR 补齐 ADR-0006 明确延后的真实 channel transport，不替代 LangChain-first 推理运行时决策
- Superseded by: 无

## Context and drivers

`spawn-join-llm-provider` 已经定义了框架无关的 `Channel`、`ChannelConfig`、
`PingResult`、`ModelInfo`、`ModelPage` 和渠道错误，但仓库中没有任何生产实现；
`spawn-join-llm-provider-langchain` 只负责把 `ChatModelConfig` 转成原生
`BaseChatModel`，不处理连接检查或模型发现。

ADR-0006 明确把真实 channel HTTP、pool、路由和健康选路留待后续决策；
ADR-0008 明确不处理 channel 配置。由此形成两个断点：

```text
ChannelConfig -> ??? -> ping/list_models
ModelInfo     -> ??? -> ModelSummary / ChatModelConfig
```

用户要求在不重构 LangChain 的前提下补齐 channels，形成可用的闭环。需要回答：

1. channel transport 放在哪个 Distribution；
2. 凭据如何从 `ChannelConfig.credential_ref` 解析，且不进入配置、日志或错误；
3. 如何把 Provider SDK 的认证、超时、连接、限流、5xx、404 和畸形响应映射到稳定契约；
4. 如何把 `ChannelConfig`/`ModelInfo` 接到现有模型工厂，而不包装 `BaseChatModel`；
5. 哪些能力仍然明确不做。

## Options considered

1. **把 transport 放进 `spawn-join-llm-provider-langchain`**
   复用现有 SDK 和配置，但 channel 使用者会被迫安装 LangChain，且包从“模型工厂”
   扩成“网络/健康/目录客户端”。与 ADR-0006 的框架无关 channel 契约冲突。拒绝。

2. **把 transport 放进 `spawn-join-llm-provider`**
   类型同址，但会给框架无关的核心包引入 `openai`/`anthropic` SDK、网络和凭据副作用。
   违反依赖方向和包边界。拒绝。

3. **新增 `spawn-join-llm-channel` infra Distribution（采用）**
   独立拥有 Provider SDK、认证、分页和错误映射；协议包保持纯契约；适配包只做
   无网络桥接。代价是新增一个 Distribution 的锁文件、README、质量 Profile 和 CI 矩阵。

4. **只保留契约，不实现 transport**
   维持现状，但无法形成用户要求的闭环。拒绝。

## Decision

采用方案 3，并明确以下边界。

### Distribution 与依赖

新增 `packages/infra/llm-channel/`：

- Distribution：`spawn-join-llm-channel`
- import package：`spawn_join_llm_channel`
- 运行时依赖：
  - `spawn-join-llm-provider>=0.1.0,<0.2.0`
  - `openai>=3.0,<4`
  - `anthropic>=2.0,<3`
- 不依赖 LangChain、`spawn-join-llm-provider-langchain`、Common 或 Agent 包。
- 独立 `pyproject.toml`、`uv.lock`、`.venv`、`tests/`、`src/` layout、
  `py.typed`、LICENSE、中英文 README、质量 Profile 和 CI matrix。

依赖方向：

```text
spawn-join-llm-provider
    └── spawn-join-llm-channel
            ├── openai
            └── anthropic

spawn-join-llm-provider
    └── spawn-join-llm-provider-langchain
            └── langchain-core / langchain-openai / langchain-anthropic
```

`spawn-join-llm-provider-langchain` 不依赖 `spawn-join-llm-channel`；桥接只需要协议包的
`ChannelConfig`/`ModelInfo`。

### Channel transport

- `OpenAIChannel`：支持 `ProtocolKind.CHAT_COMPLETIONS` 和
  `ProtocolKind.RESPONSES`，使用 `AsyncOpenAI.models.list()`。
- `AnthropicChannel`：支持 `ProtocolKind.ANTHROPIC_MESSAGES`，使用
  `AsyncAnthropic.models.list(after_id=..., limit=...)`。
- 两者实现 `Channel` 的 `config`、`ping()`、`list_models()`；额外提供
  `aclose()` 关闭自己持有的 SDK 客户端。
- `create_channel()` 按 `ProtocolKind` 显式分派；协议与实现不匹配时抛
  `ConfigurationError`。
- `ping()` 使用模型列表端点做轻量认证/可达性检查，不生成 completion。
- OpenAI-compatible 模型列表当前无分页参数，`next_cursor=None`；Anthropic 使用
  `has_more`/`last_id` 产生 cursor。
- `limit` 必须是正数；`limit <= 0` 在发起网络请求前拒绝。
- 空模型列表是合法成功。

### 协议补充

- `ChannelStatus` 增加 `UNSUPPORTED`，表示渠道可达但目标端点不提供模型列表能力。
- 新增 `ChannelAuthenticationError(ChannelError)`，用于 `list_models` 的 401/403；
  `ping` 继续用 `AUTHENTICATION_FAILED`。
- 现有枚举成员、错误层次和 `PingResult.ok` 语义保持不变。

### 错误映射

| 条件 | `ping` status | `list_models` error |
|---|---|---|
| 401/403 认证/权限 | `AUTHENTICATION_FAILED` | `ChannelAuthenticationError` |
| 超时 | `TIMEOUT` | `ChannelUnavailableError` |
| 连接失败 | `UNREACHABLE` | `ChannelUnavailableError` |
| 429 限流 | `UNREACHABLE` | `ChannelUnavailableError` |
| 5xx 服务端错误 | `UNREACHABLE` | `ChannelUnavailableError` |
| 404/405 不支持模型列表 | `UNSUPPORTED` | `UnsupportedChannelOperationError` |
| 畸形/校验失败 | `INVALID_RESPONSE` | `ChannelResponseError` |
| 其他 API 错误 | `INVALID_RESPONSE` | `ChannelResponseError` |

公开消息只使用固定文案，不拼接 SDK `str(exc)`、请求体、完整 URL 或密钥；原始异常通过
`raise ... from exc` 保留原因链。

### 凭据

优先级：

1. 注入的 SDK client；
2. 显式 `api_key`；
3. `credential_ref` 作为环境变量名，由默认 resolver 读取进程环境或调用方传入的映射。

- 缺失、空字符串或带前后空白的环境变量值抛 `ConfigurationError`。
- 不修改 `os.environ`，不读取 `.env`，不实现密钥管理服务、热轮换或多凭据池。
- `ChannelConfig` 不保存明文密钥；`repr`、日志、`PingResult.detail` 和公开错误不包含密钥。
- SDK 客户端默认 `max_retries=0`，不隐藏重试。

### 适配包桥接

在 `spawn-join-llm-provider-langchain` 增加无网络转换：

- `ChatModelConfig.from_channel(channel, *, model, max_retries=0)`：复制 protocol、
  endpoint、timeout，构造现有 `ChatModelConfig`。
- `ModelSummary.from_model_info(info, *, name=None)`：把 `ModelInfo` 转成只读摘要；
  不伪造元数据。
- `ModelSummary` 增加可选 `protocol`、`endpoint`、`timeout_seconds`、
  `max_retries`、`options` 字段；`ModelCatalog.models` 和 `get()` 从现有条目填充。
- `ModelCatalog` 增加 `get`、`names`、`__len__`、`__contains__`。
- `create_chat_model` 的签名、返回类型和行为不变；仍返回原生 `BaseChatModel`。

### 明确不处理

- CLI；闭环由库 API 提供，未来 CLI 在独立 Feature 中增加；
- `channels.yaml`、渠道注册表、多文件合并、热重载、远程配置中心；
- pool、路由、健康选路、failover、限流、并发控制；
- Azure OpenAI、Bedrock、Vertex 等新 Provider；
- embedding/rerank/image/audio 工厂；
- Agent purpose binding/产品装配改动；
- 自动把发现结果写入 `model.yaml`；
- 默认质量门中的真实 Provider 请求。

## Key design and diagrams

```text
应用
  └── spawn-join-llm-channel
        ├── OpenAIChannel  -> AsyncOpenAI.models.list()
        ├── AnthropicChannel -> AsyncAnthropic.models.list()
        ├── create_channel(ChannelConfig)
        └── credential_ref -> env resolver / explicit api_key / injected client

ChannelConfig + ModelInfo
  └── spawn-join-llm-provider-langchain (pure bridge)
        ├── ChatModelConfig.from_channel(...)
        └── ModelSummary.from_model_info(...)
              └── create_chat_model(...) -> 原生 BaseChatModel
```

关键不变量：

1. 协议包不引入 Provider SDK、网络或凭据。
2. Channel 包不依赖 LangChain。
3. 适配包不实现网络 channel，不包装 `BaseChatModel`。
4. 公开错误不包含密钥或原始请求体。
5. 空模型列表是成功；404/405 是 `UNSUPPORTED`，不是认证失败。
6. 真实 Provider 测试是 opt-in，默认测试不访问网络。
7. 元数据保持描述性，不用于自动路由或能力协商。

## Consequences and migration

收益：

- 补齐 `ChannelConfig -> ping/list_models -> ModelInfo -> ChatModelConfig ->
  create_chat_model` 的可用链路；
- channel 使用者无需安装 LangChain；
- 认证、超时、限流、5xx 和“不支持模型列表”有稳定语义；
- 模型目录可只读检视，UI 不必二次解析 YAML；
- 现有 `model.yaml`、元数据快照和模型工厂行为不变。

成本与限制：

- 新增一个 Distribution 的锁文件、README、质量 Profile、CI matrix 和维护责任；
- 新包与 `openai`/`anthropic` SDK 版本耦合，升级需要回归；
- 真实 Provider 行为在当前环境未验证，需要 opt-in live tests 或用户环境补证；
- `credential_ref` 作为环境变量名是默认约定，不是通用密钥引用标准；
- OpenAI-compatible 模型列表无分页，`next_cursor` 永远为 `None`；
- 不提供 pool/路由/健康选路，不能把本 ADR 解释为高可用能力。

迁移：

- 现有 `model.yaml` 和 `ModelCatalog` 调用方不需要修改；
- 新增字段有默认值，`ModelSummary` 的现有构造方式保持可用；
- `ChannelStatus.UNSUPPORTED` 是新增枚举成员；对枚举做穷举匹配的调用方需要更新；
- `ChannelAuthenticationError` 是新增子类；现有 `except ChannelError` 仍可捕获；
- 库 API 是新增入口，不影响现有包。

重新评估触发条件：

- 出现第二个 channel transport 复用需求或新的 Provider；
- 需要 `channels.yaml`、渠道注册表或 UI 渠道管理；
- 需要 pool、路由、健康选路或 failover；
- 需要密钥管理服务、热轮换或远程配置；
- 需要 embedding/image/audio 工厂。

## Verification and implementation status

本 ADR 当前为 `Proposed`，仅表示设计候选，不代表实现已完成。计划验证：

- 协议包：新枚举成员/错误子类、公共导出、现有 185 个测试；
- 新 channel 包：fake client 覆盖成功、认证、超时、连接、限流、5xx、404/不支持、
  空列表、分页、limit 校验和凭据解析；
- 适配包：`from_channel`、`ModelSummary.from_model_info`、目录检视和现有 301 个测试；
- 新包独立锁文件、构建、隔离安装、质量 Profile 和 CI matrix；
- 全仓库质量门、docs/governance、`git diff --check`；
- 真实 Provider live tests 默认 skip；无凭据时明确报告未执行。

实际命令、退出码和残余风险由 Delivery evidence 记录；在获得 reviewed HEAD 之前不得将
本 ADR 改为 `Accepted`。

## Revision history

- 2026-11-08：提出真实 channel transport、协议补充、凭据边界和适配桥接的候选决策。
