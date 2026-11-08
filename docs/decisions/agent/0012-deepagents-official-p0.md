# ADR-0012: DeepAgents 官方 P0 能力的产品化接线

- Status: Proposed
- Date: 2026-11-08
- Domain: agent
- Classification: 约束 `spawn-join-agent-deepagents` 如何接入 DeepAgents 0.7.x 的 async
  子代理、Memory/Skills 和 Harness/Provider profile；属于 agent 领域的公共契约决策。
- Decision owner: 仓库维护者
- Accepted by / date: 待评审
- Depends on: [ADR-0010](0010-deepagents-product-boundary.md)
- Related: [包边界](../../architecture/package-boundaries.md)、
  [仓库地图](../../architecture/repository-map.md)
- Supersedes: 无
- Superseded by: 无

## Context and drivers

`spawn-join-agent-deepagents` 的 v1 已覆盖 supervisor 装配、模型用途、声明式/compiled
子代理、Middleware 作用域、受控委派、诊断和恢复。DeepAgents `0.7.32` 还提供三项对产品
开发直接有用的官方能力，但包目前只做原始透传或完全不支持：

1. **AsyncSubAgent**：`create_deep_agent` 通过 `graph_id` 识别远程 Agent Protocol 子代理，
   并自动装配 `AsyncSubAgentMiddleware`。当前 `SupervisorSpec.subagents` 不接受该形态，
   传入原生字典会进入 compiled 分支并触发 `AttributeError`。
2. **Memory / Skills**：官方 `MemoryMiddleware` 与 `SkillsMiddleware` 接受 source 列表；
   当前包只接受 `Sequence[str]`，没有形状校验、memory 前缀缓存选择或装配报告。
3. **Harness / Provider profile**：官方 beta API 通过进程级注册表影响模型/中间件；
   当前包既不感知也不报告，`general-purpose` 的装配报告可能失真。

这些能力会扩展公共 API 和执行语义，需要单独记录边界与 beta 风险。

## Options considered

1. **继续由宿主直接调用上游 API**
   不新增公共契约，但无法统一校验、beta 开关和报告；异步子代理的错误形态也不稳定。
   拒绝作为唯一方案。
2. **把三项能力都做成稳定默认**
   违反 ADR-0010 的“beta 能力显式 opt-in”原则，且 async 依赖远程部署、profile 是进程级
   副作用。拒绝。
3. **在现有 Agent Distribution 内做可选、显式开启的产品化接线**
   保持一个装配边界，新增配置对象、校验和报告；beta 能力默认关闭。接受。

## Decision

在 `spawn-join-agent-deepagents` 内新增以下公共契约，全部为可选能力：

### Async subagents

- 新增 `AsyncSubAgentDefinition` 与 `SubAgentKind.ASYNC`，覆盖名称、描述、`graph_id`、
  `url`、`headers`、`webhook`、`update_strategy`、`notify_parent`、`mode`。
- 必须显式设置 `SupervisorSpec(allow_experimental_async_subagents=True)`；默认关闭。
  `mode="fork"` 是两层 beta 的叠加，还需要 `allow_experimental_fork=True`。
- `general-purpose` 是包保留的默认子代理名称，异步形态不得使用。
- 异步子代理不接收包注入的 model、middleware 或 summarization；报告只记录
  `kind=async`、`model_source=remote:<graph_id>`，不记录 URL、headers、webhook 或任务正文。
- 未知子代理形态、空白 `graph_id`、重复名称在 `create_deep_agent` 前以
  `SubagentConfigurationError`/`MiddlewareConfigurationError` 失败。

### Memory / Skills

- 新增 `MemoryConfiguration(sources, cache_memory_prefix=True)` 与
  `SkillsConfiguration(sources)`；拒绝空、空白、重复 source，不在装配期读取 source。
- 旧的 `Sequence[str]` 写法继续接受。
- `cache_memory_prefix=False` 时由包构造 `MemoryMiddleware` 并向上游传 `memory=None`；
  此时没有可替换的上游默认实例，fork 子代理也不会继承这份 memory，且拒绝用户提供同名
  middleware。默认路径继续由上游管理。
- 装配报告新增 `ContextReport`，只记录 source 数量、前缀缓存和管理方式。

### Harness / Provider profiles

- 新增 `ProfilesConfiguration`、`HarnessProfileBinding`、`ProviderProfileBinding`；在
  `create_deep_agent` 前调用上游注册函数。
- 必须显式设置 `allow_experimental_profiles=True`；注册是进程级副作用，文档必须说明。
  上游没有反注册 API，因此多 key 注册在中途失败时可能保留先前 key。
- 校验 key 非空、同组 key 唯一，并拒绝排除包保留 Middleware 名：
  `SummarizationMiddleware`、`spawn_join_delegation_policy`、`spawn_join_diagnostics`；
  包管理 memory 时还包括 `MemoryMiddleware`。
- Provider profile 只影响上游从字符串构造模型的路径；本包传入已解析的 `BaseChatModel`，
  不保证其对实例生效。
- 装配报告新增 `ProfileReport`，只记录本次注册的 key；不声称完整内省最终图。

### Errors and reporting

- 新增 `ContextConfigurationError` 和 `ProfileConfigurationError`，继承
  `AgentConfigurationError`。
- 所有新增失败发生在装配前，消息不含凭据、私有 URL、headers 或用户内容。
- 上游异常保留 `__cause__`。

## Key design and diagrams

```text
Host
├── models / tools / host resources
├── SupervisorSpec
│     ├── subagents: declarative | compiled | async
│     ├── memory / skills: sequence or configuration
│     ├── profiles: harness/provider bindings + beta gates
│     └── middleware / delegation / diagnostics / recovery
└── build_supervisor
      -> validate forms, sources, profile keys, beta gates
      -> apply profiles (process-wide, explicit)
      -> resolve models and summarization
      -> convert subagents to native forms (async untouched by package middleware)
      -> create_deep_agent
      -> SupervisorAssembly(graph, report)
```

## Consequences and migration

好处：

- 三项官方能力有统一、可测试、显式开启的产品入口；
- 异步子代理不再以 `AttributeError` 失败；
- Memory/Skills 的配置错误在装配前可见，报告不泄露敏感路径；
- profile 的 beta 和进程级副作用被记录，保留名冲突被阻止。

成本与限制：

- 公共 API 增加 9 个类型/错误；`0.x` preview 内按文档化变更管理；
- async 依赖远程 Agent Protocol 部署和异步执行路径，本包不实现服务端；
- profile 注册无法完全隔离，包只记录本次注册的 key；
- 不实现 MCP Server、数据库、沙箱、UI、租户/授权/计费、生产观测后端或发布自动化。

## Verification and implementation status

实现位置：`packages/infra/agent-deepagents/`。本 ADR 在评审时保持 Proposed；只有当前
评审通过的 repository HEAD 与本决策一致后才改为 Accepted。

验证覆盖：

- async beta 门控、原生 kwargs、报告字段、未知形态与重复名称；
- memory/skills 的空/空白/重复校验、旧写法兼容、memory 前缀缓存两条路径、同名冲突；
- profile beta 门控、key 唯一、保留名冲突、注册顺序、异常 cause、报告 key；
- 0.7.32 上游契约测试仍通过；
- 包级质量门、文档检查和 `git diff --check`。

未覆盖：真实远程 Agent Protocol 服务、真实模型 profile 行为、跨进程 profile 隔离。

## Revision history

- 2026-11-08：创建 Proposed ADR，记录三项 P0 能力的产品化接线、beta 风险和边界。
