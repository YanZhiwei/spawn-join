# ADR-0010: DeepAgents 产品增强包的边界与公共契约

- Status: Proposed
- Date: 2026-11-04
- Domain: agent
- Classification: 本决策约束 DeepAgents 产品增强包的 Distribution 归属、模型用途与委派/资源公共契约、长期依赖方向和实验能力边界，属于 `agent` 领域。
- Decision owner: 仓库维护者
- Accepted by / date: 未批准
- Depends on: [ADR-0006](../llm-provider/0006-langchain-first-llm-runtime.md)、[ADR-0008](../llm-provider/0008-model-file-and-env-boundary.md)
- Related: [包边界](../../architecture/package-boundaries.md)、[仓库地图](../../architecture/repository-map.md)、[ADR-0009](../llm-provider/0009-model-metadata-and-sync.md)、Feature `011-deepagents-product-capabilities`
- Supersedes: 无
- Superseded by: 无

## Context and drivers

SpawnJoin 已有可独立分发的 Core、LLM 协议、LangChain 模型适配和模型元数据同步包，但还没有一个可复用的 DeepAgents 产品装配层。宿主应用如果直接调用 `create_deep_agent`，会重复处理以下真实问题：

1. 哪些模型用于 supervisor、worker 和 summarization，以及缺失时是否允许继承；
2. 声明式与 compiled 子代理如何进入同一装配，如何保留各自的图/中间件边界；
3. Middleware 在主图、委派边界和子图中的作用范围；
4. 子代理委派如何限制并发、排队、deadline 和取消，并区分钟类失败；
5. 宿主如何解释“子代理未注册/未入选/未调用/调用失败”，同时不泄露密钥；
6. Store、Backend、Checkpointer、MCP Session 和沙箱由谁创建、保持和关闭；
7. 如何把中断/恢复、streaming 和原生 LangGraph 语义原样交给宿主。

DeepAgents `0.7.32` 已提供模型—工具循环、子代理、Middleware、文件 Backend、Checkpoint、interrupt 和 streaming；0.7 还减少了隐式默认策略。SpawnJoin 不应复制这些机制，而应补上产品装配、校验、用途绑定、受控委派和诊断接缝。

本决策同时受以下约束：

- [ADR-0006](../llm-provider/0006-langchain-first-llm-runtime.md) 要求应用直接使用 LangChain 消息和 `BaseChatModel`，协议包保持框架无关；
- [ADR-0008](../llm-provider/0008-model-file-and-env-boundary.md) 要求 `model.yaml`、凭据解析和 `BaseChatModel` 创建留在 LangChain 适配包；
- 仓库要求每个 Distribution 独立安装、测试、构建、版本化和发布；网络、数据库、线程和文件等副作用必须有明确拥有者；
- 用户已确认首版六项产品能力，并明确模型相关能力显式依赖 `spawn-join-llm-provider-langchain`；
- 不把租户、授权、计费、产物台账、UI/事件协议、MCP Server、数据库或沙箱实现放入本包。

## Options considered

1. **只提供 `create_deep_agent` 的薄别名**
   代码最少，但不能表达模型用途、显式继承、Middleware 作用域、委派期限/并发/取消和装配诊断；真实产品仍会在宿主重复实现这些问题。拒绝。

2. **把 Agent 装配塞进 `spawn-join-llm-provider-langchain`**
   会迫使所有模型消费者安装 DeepAgents，并把 Agent 生命周期、委派策略和模型文件/凭据边界混在一起。违反依赖方向。拒绝。

3. **新增 `spawn-join-agent-deepagents` infra Distribution（采用）**
   作为独立发布边界，显式依赖 DeepAgents/LangChain 和模型适配包；保留原生 `BaseChatModel`、`SubAgent`/`CompiledSubAgent`、`AgentMiddleware` 和 LangGraph 图。宿主继续拥有业务工具、租户/授权、外部资源和 UI。代价是新增一个 Distribution、锁文件、质量 profile 和 CI 矩阵。

4. **把所有集成（MCP、数据库、沙箱、Web/SSE、观测后端）一并放入首版**
   会制造多个资源拥有者、额外发布依赖和不可验证的生命周期承诺。拒绝；这些能力按真实需求和独立发布周期另行设计。

## Decision

采用选项 3，并确定以下长期边界：

### Distribution 与依赖方向

新增 `spawn-join-agent-deepagents`，路径 `packages/infra/agent-deepagents/`，import package `spawn_join_agent_deepagents`。运行时依赖限定为：

```text
deepagents>=0.7.32,<0.8
langchain>=1.4.7,<2.0
langchain-core>=1.7.0,<2.0
langgraph>=1.2,<2
spawn-join-llm-provider-langchain>=0.1.0,<0.2.0
```

依赖方向保持单向：

```text
spawn-join-agent-deepagents
├── deepagents -> langchain -> langgraph
├── langchain
├── langchain-core
├── langgraph
└── spawn-join-llm-provider-langchain
    └── spawn-join-llm-provider
        └── spawn-join-core
```

Core、协议包和模型包不得反向依赖本包。本包不依赖 `spawn-join-llm-model-sync`，也不把模型元数据同步、缓存或网络副作用带入运行时。

### 模型用途

- `SUPERVISOR`、`WORKER`、`SUMMARIZATION` 是稳定用途；
- supervisor 必须直接绑定，不得继承；
- worker/summarization 只能通过显式 `inherit_from` 继承；缺失时失败，不隐式回退到 supervisor 或 Catalog 默认模型；
- `SUMMARIZATION` 默认必须显式绑定，因为 DeepAgents 默认栈始终包含 summarization；
- 配置绑定通过 `ModelCatalog.create_chat_model` 创建，Agent 包不解析 YAML、不读取密钥、不选择 Provider SDK；
- 保留原生 `BaseChatModel` 注入入口，支持宿主已有模型和离线测试；
- compiled 子代理拥有自己的模型，本包不替换。

### 子代理与 Middleware

- 稳定契约覆盖声明式 `SubAgent` 与 `CompiledSubAgent`；
- 唯一名称和必填字段在调用上游前校验，上游仍是最终执行权威；
- 声明式子代理接收显式 worker 模型、worker middleware 和生成的 summarization middleware；
- compiled 子代理保留自己的图、模型、内部中间件和 approval 配置，本包不注入；
- Middleware 分为 supervisor、workers、per-subagent override 三个作用域；同名替换遵循 DeepAgents 0.7 语义，本包不实现第二套 registry；
- 用户不得占用保留的 `"SummarizationMiddleware"` 名称，summarization 模型只能通过用途绑定设置；
- fork 子代理是 beta，只能通过显式 `allow_experimental_fork` 开启，且不进入稳定兼容承诺。

### 委派

- 提供显式、可复用的 `DelegationController` 和有界 FIFO 策略；不使用进程全局隐式状态；
- `max_concurrency`、`max_queue`、`deadline_seconds` 分别约束活动数、等待数和总期限；
- 队列满、deadline、父级取消、worker 失败和中断具有可区分语义；
- deadline 覆盖排队与执行；到期通过 asyncio 取消正在执行的操作；
- 本包不把同步调用包装成可抢占的 deadline：`invoke`/`stream` 配置策略时，首次 `task` 调用明确抛出 `UnsupportedSyncDelegationError`；不配置策略时保持原生行为；
- 控制器绑定一个事件循环，可跨运行复用，不能跨进程或跨线程共享。

### 诊断

- 返回不可变 `AssemblyReport`，描述安全版本、模型来源、子代理、Middleware 作用域、资源和实验能力；
- 提供可选的同步/异步回调，发送脱敏 `DiagnosticEvent`，区分 selected/queued/started/completed/failed/timed_out/cancelled/interrupted/rejected；
- 相关性来自 task tool call id 和原生 runtime execution info；不复制 LangChain callbacks 或 LangGraph streaming；
- 回调异常不被静默吞掉；宿主负责日志、追踪、UI、持久化和背压；
- 报告和事件不得包含密钥、endpoint、prompt、原始消息或异常消息。

### 资源与恢复

- Store、Backend、Checkpointer、MCP Session、沙箱和业务工具由宿主创建、保持有效并关闭；
- 包只校验必需资源/身份并透传，不创建或关闭宿主资源；
- `interrupt_on` 需要 checkpointer；恢复使用原生 `thread_id`、`Command(resume=...)` 和 LangGraph 语义；
- 包不承诺 exactly-once 副作用，也不替代宿主的资源池、健康检查或持久化策略。

## Key design and diagrams

```text
Host
├── ModelCatalog / BaseChatModel
├── business tools, middleware, subagents
├── Store / Backend / Checkpointer / MCP / sandbox
└── SupervisorSpec
      -> build_supervisor
         -> validate models/subagents/middleware/resources
         -> resolve purposes + summarization replacement
         -> build native SubAgent/CompiledSubAgent
         -> add policy/diagnostics middleware
         -> create_deep_agent
      -> SupervisorAssembly(graph, report, controller)
Host -> native graph.ainvoke/astream -> LangGraph execution
```

Delegation state machine:

```text
requested
├── queue full -> rejected
├── slot free -> started -> completed | failed | timed_out | cancelled | interrupted
└── slot busy -> queued
    ├── cancelled/timed_out -> cancelled | timed_out
    └── granted -> started -> ...
```

## Consequences and migration

收益：

- 宿主获得一个可复用的产品装配层，而不是重复实现 DeepAgents 接线；
- 模型用途、显式继承和 summarization 行为可检查，不依赖隐式默认；
- 委派并发、排队、期限、取消和诊断形成可测试契约；
- 原生图、Checkpoint、interrupt、resume、streaming 和 LangChain callbacks 保持可用；
- 新 Distribution 可独立安装、测试、构建和发布。

成本与限制：

- 新增一个 Distribution、锁文件、质量 profile、CI 矩阵和文档维护面；
- 运行时锁定 `deepagents<0.8`；0.8 兼容需要单独验证和决策；
- governed delegation 仅异步；同步策略明确不支持；
- fork 为 beta，不承诺长期兼容；
- 不提供 MCP/数据库/沙箱/观测后端实现，宿主必须继续拥有这些资源；
- `ModelCatalog` 在装配时可能读取环境/.env 快照；本包只使用其公开 API，不记录密钥；
- 当前没有既有发布消费者，迁移成本为零，但公共 API 从 `0.1.0` 开始仍需按 semver 管理。

重新评估触发条件：

- DeepAgents 0.8 或 LangChain 2.x 发布并改变 `create_deep_agent`/Middleware/子代理契约；
- 出现真实的跨进程委派或持久任务队列需求；
- 出现第二个宿主需要 lifecycle adapter、MCP 集成或观测后端；
- 同步执行成为主要使用方式，且需要可抢占 deadline；
- 模型用途需要从固定三种扩展为可配置命名用途。

## Verification and implementation status

本 ADR 为 **Proposed**，尚未批准，也不代表实现完成。设计依据和验证计划位于：

- Feature Spec：`specs/011-deepagents-product-capabilities/spec.md`
- Plan：`specs/011-deepagents-product-capabilities/plan.md`
- 研究：`specs/011-deepagents-product-capabilities/research.md`
- 数据模型/公共契约：`specs/011-deepagents-product-capabilities/data-model.md`、`contracts/public-api.md`
- 探索包：`.specify/delivery/011-deepagents-product-capabilities/exploration.md`
- 决策上下文：`.specify/delivery/011-deepagents-product-capabilities/decision-context.md`

计划验证包括：模型用途/继承/缺失、子代理唯一性与两种形态、Middleware 作用域与 summarization 替换、并发/队列/deadline/取消/失败、诊断脱敏与事件序列、Checkpoint/interrupt/resume、独立 wheel/sdist 与隔离安装、质量 profile/CI、文档/治理/静态检查。实际命令、退出码和残余风险由 Delivery evidence 记录，不复制到本 ADR。

在维护者批准、实现和独立评审完成前，不得将本 ADR 标记为 Accepted，也不得把 Plan 中的计划验证表述为已通过。

## Revision history

- 2026-11-04：提出 DeepAgents 产品增强包的 Distribution 边界、模型用途、委派、诊断和资源契约；状态为 Proposed。
