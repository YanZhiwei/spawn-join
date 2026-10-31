# ADR-0006: 以 LangChain 作为 LLM 运行时，保留渠道与协议选项

- Status: Accepted
- Date: 2026-10-31
- Domain: llm-provider
- Classification: 本决策约束 LLM 消息/模型运行时、协议包公共契约和依赖方向，属于 `llm-provider` 领域。
- Decision owner: 仓库维护者
- Accepted by / date: 用户 2026-10-31 批准 LangChain-first 设计与实现；final review `d6cdc37`
- Depends on: [ADR-0001](../engineering/0001-delivery-and-durable-design.md)、[ADR-0002](../engineering/0002-untrack-historical-feature-artifacts.md)
- Related: [包边界](../../architecture/package-boundaries.md)、[Constitution](../../../.specify/memory/constitution.md)
- Supersedes: 无（未合并 PR #16 中的旧候选设计不是 `main` 上的有效 ADR）
- Superseded by: 无

## Context and drivers

SpawnJoin 需要决定 LLM 消息和模型调用的长期运行时边界。此前在未合并的 PR #16 中提出了
一套框架无关的公共消息、内容块、工具定义、请求/响应、流式事件和 `LLMProvider` 协议，
并在其分支上记录了 Proposed 的 ADR-0005。该设计没有进入 `main`，也没有外部消费者。

当前事实：

- `main` 上 `packages/core/llm-provider` 与 `packages/infra/llm-provider-langchain` 只有骨架。
- 旧实现公共导出 54 个，适配层源码实际使用 41 个；消息、请求/响应、流式事件和
  `LLMProvider` 占公共面的大部分。
- LangChain 已提供 `BaseMessage`、`AIMessage`、`AIMessageChunk`、`ToolMessage`、
  `tool_calls`、`usage_metadata`、内容块和流式组合。
- Channel 契约没有真实 HTTP 实现或外部消费者，但它是 LangChain 不提供的连接和
  模型目录概念。
- 池、模型路由和健康选路尚未形成明确需求，不应在本决策中预设。

驱动因素：

1. 避免维护两套消息和工具契约；
2. 保持协议包与框架无关；
3. 保留 LangChain 不提供、且配置/运维确实需要的 channel 能力；
4. 缩小 `0.1.0` 公共 API 的兼容性负担；
5. 不用未经真实需求验证的 pool 或 HTTP 实现扩大范围。

## Options considered

1. **LangChain-first，协议包只保留 channel/options/errors（采用）**
   应用直接使用 LangChain 消息和 `BaseChatModel`；适配层负责显式协议配置到模型的工厂、
   选项映射和校验；协议包保留三种协议选项、channel 契约和少量错误。

2. **让 `spawn-join-llm-provider` 直接依赖 `langchain-core`**
   代码更少、类型统一，但协议包不再框架无关，包边界、ADR 和未来非 LangChain 适配都要
   改写；LangChain 升级会直接影响协议包公共 API。

3. **保留旧设计的公共消息和 `LLMProvider`**
   应用不直接接触 LangChain，但需要长期维护消息、工具、请求/响应、流式事件和映射层；
   与全仓库以 LangChain 为运行时的方向重复，且当前没有非 LangChain 消费者。

4. **只保留 channel，删除协议选项和错误**
   Channel 无法表达推理参数和配置失败，调用方只能退回到无类型字典或框架内部异常；
   不能形成稳定的协议边界。

## Decision

采用选项 1，并明确以下边界：

- 应用层直接使用 `langchain_core.messages` 的 `BaseMessage`、`AIMessage`、
  `AIMessageChunk`、`ToolMessage`，以及 `BaseChatModel.ainvoke`/`astream`。
- 不定义 `Message`、`Role`、内容块、工具定义、工具选择、`ChatRequest`、`ChatResponse`、
  `StreamEvent`、`LLMProvider`、`Usage`、`FinishReason` 或 `ModelCapabilities`。
- `spawn-join-llm-provider` 只保留：
  - `ProtocolKind` 与 `ChatCompletionsOptions`、`ResponsesOptions`、
    `AnthropicMessagesOptions`；
  - `Channel`、`ChannelConfig`、`ChannelStatus`、`PingResult`、`ModelInfo`、`ModelPage`；
  - `LLMProviderError`、`ConfigurationError`、`ChannelError`、
    `ChannelUnavailableError`、`UnsupportedChannelOperationError`、
    `ChannelResponseError`。
- `spawn-join-llm-provider-langchain` 只保留 `ChatModelConfig` 与 `create_chat_model`。
  工厂根据显式协议返回配置好的 `BaseChatModel`，不返回项目自定义 Provider 包装。
- 协议选项是模型构造时的类型化默认值；不公开任意字典映射或额外调用包装。逐次调用覆盖
  使用 LangChain 原生参数。
- 本决策不做 `ChannelPool`、模型路由、健康选路、HTTP 连接池或真实 channel HTTP。
- 包名暂时保留 `spawn-join-llm-provider`；更名需要单独决策。
- 未合并 PR #16 不作为实现基线；本决策从 `main` 重新实现。

## Key design and diagrams

```text
业务应用
  └── langchain_core.messages / BaseChatModel
        └── spawn-join-llm-provider-langchain
              ├── ChatModelConfig
              ├── create_chat_model
              ├── 协议选项 -> LangChain 构造参数
              └── 调用前校验

spawn-join-llm-provider
  ├── ProtocolKind
  ├── 三种协议选项
  ├── Channel / ChannelConfig / PingResult / ModelPage
  └── 配置与渠道错误
```

依赖方向保持：

```text
spawn-join-core
    └── spawn-join-llm-provider
            └── spawn-join-llm-provider-langchain
                    └── 业务应用
```

关键约束：

1. `spawn-join-llm-provider` 不依赖 LangChain、具体 Provider SDK 或 HTTP 客户端。
2. `ChannelConfig` 和适配层 `ChatModelConfig` 继承共享 `EndpointConfig`
   （protocol/endpoint/timeout）；`ChatModelConfig` 不依赖 `ChannelConfig`，模型配置不需要
   渠道名称或凭据引用。
3. `ChannelConfig.name` 是非敏感、人类可读的渠道标识，用于日志和错误定位；跨配置唯一性
   由调用方或未来注册表负责。
4. `create_chat_model` 显式设置 `use_responses_api`（OpenAI 分支）和 `max_retries`，不根据
   模型名称推断协议。
5. 选项与协议不匹配、值非法、密钥为空或模型名为空时，在构造模型前抛
   `ConfigurationError`。
6. `Channel.ping()` 返回结构化 `PingResult`，不执行生成请求；`Channel.list_models()` 用
   空页表达成功但无模型，用异常区分不支持、不可用和畸形响应。
7. `ChannelConfig` 只保存非敏感 `name` 和 `credential_ref`；API key 只在工厂调用时传入并
   包装为 `SecretStr`，不进入 repr、日志或提交。

## Consequences and migration

收益：

- 应用直接使用 LangChain 生态，工具调用、流式输出、结构化输出和回调不需要项目转换。
- 协议包公共面显著缩小，框架升级不会直接改变 channel/options 契约。
- channel 契约保留 LangChain 不提供的连接和目录能力，为后续真实实现留出稳定边界。
- 模型配置不依赖 channel 专属字段；只想调用模型时不需要构造 `ChannelConfig`。

成本与限制：

- 应用与 LangChain 版本耦合；替换非 LangChain 运行时需要新的适配层。
- 本 Feature 只有 channel 契约，没有真实 HTTP 实现；不能声称已完成渠道运维能力。
- 选项是构造时默认值；同一模型实例需要不同参数时需要重新构造，或直接使用 LangChain
  原生调用参数。
- `spawn-join-llm-provider` 的名称比新职责更窄，但重命名会牵动目录、import、锁文件和
  文档，留待单独变更。

迁移：

- 由于旧实现未进入 `main`，没有已发布调用方需要迁移。
- 未合并 PR #16 保持参考状态；关闭或标记 superseded 需要维护者另行授权。
- 未来若出现真实 pool/路由需求，应新建 ADR 和 Feature，不静默扩展本决策。

## Verification and implementation status

本 ADR 的 Accepted 只表示设计决策已获维护者批准；实现和质量门结果由 Delivery evidence
单独记录。最终独立评审在 `d6cdc37` 通过。

实现验证包括：

- `spawn-join-llm-provider` 的公共导出和依赖边界；
- 三个协议的选项校验和 fake channel 行为；
- 工厂返回 `BaseChatModel`、`use_responses_api`、`max_retries`、endpoint/timeout 和
  API key 掩码；
- 两个 Distribution 的 Black/isort/Ruff/Pyright/pytest/隔离构建；
- 文档、治理和静态检查；
- `git diff --check` 和工作区构建副作用。

S1/S2 已在 `ralph/008-langchain-first-llm-runtime` 分支实现：core 包 129 个测试、
adapter 包 38 个测试，两个包的质量门和隔离构建通过；docs/governance 检查通过。真实
channel HTTP、Provider 请求、pool 和路由仍未实现或执行。

实际命令、退出码和残余风险记录在 Delivery evidence 中；本 ADR 不复制这些运行结果。

## Revision history

- 2026-10-31：提出 LangChain-first、channel-only 的候选决策。
- 2026-10-31：用户批准设计与实现；最终独立评审在 `d6cdc37` 通过，ADR 由 Proposed 改为
  Accepted。
