# ADR-0019: DeepAgents planning middleware public seam

- Status: Proposed
- Date: 2026-11-28
- Domain: agent
- Classification: 本决策约束 `spawn-join-agent-deepagents` 的 opt-in planning/todo 公共 seam，属于 `agent` 领域。
- Decision owner: 仓库维护者
- Accepted by / date: 未批准
- Depends on: [ADR-0010](0010-deepagents-product-boundary.md)、[ADR-0014](0014-deepagents-p1-capabilities.md)
- Related: [包边界](../../architecture/package-boundaries.md)、Delivery packet `.specify/delivery/deepagents-planning-middleware-20261128/`
- Supersedes: 无
- Superseded by: 无

## Context and drivers

DeepAgents `0.7.32` 的 `create_deep_agent` 默认栈只稳定包含 filesystem、subagent、
summarization 和 patch-tool-calls；`TodoListMiddleware` 不是默认能力，只在
`openai_codex` harness profile 中显式加入。真实产品开发型 agent 需要多步规划与
`write_todos`，但宿主不应依赖模型专属 profile，也不应重复实现 todo 状态和工具。

当前包已经提供 `MiddlewareConfiguration`，宿主可以注入原始
`TodoListMiddleware`，但该路径没有类型化配置、空白值校验、重复所有权检查、
文档和回归测试，也没有明确的 supervisor-only 语义。需要一个新的公共 seam 来
表达“显式启用 planning”，同时保持未配置时行为不变。

## Options considered

1. **只文档说明原始注入** — 拒绝。没有类型、校验、冲突规则和回归覆盖，不能称为
   一等支持。
2. **默认开启 planning 并注入所有 worker** — 拒绝。会改变所有现有图的工具、提示和
   token 行为；worker 级 todo 语义没有真实消费者证据。
3. **新增 opt-in `PlanningConfiguration`，仅作用于 supervisor（采用）** — 复用
   LangChain 原生 middleware，保持默认关闭，新增公共配置、校验、报告可见性和测试。
4. **在本包重新实现 todo 状态/工具** — 拒绝。复制上游实现并制造第二套 registry。

## Decision

### 公共 API

- 新增 `spawn_join_agent_deepagents.PlanningConfiguration`，字段为
  `system_prompt: str | None = None` 与 `tool_description: str | None = None`。
- `SupervisorSpec` 新增 `planning: PlanningConfiguration | None = None`；默认 `None`
  时既有装配行为不变。
- 配置对象不可变、`slots=True`，不持有 middleware 实例、模型、状态或凭据。
- 非字符串或空白字符串字段抛出 `MiddlewareConfigurationError`，错误前缀为
  `planning.<field>`。

### 装配语义

- 配置 planning 时，supervisor 栈恰好加入一个原生
  `TodoListMiddleware`；实例在每次 `build_supervisor` 时新建。
- 包内插入顺序：错误归一 → 宿主 supervisor middleware → planning →
  summarization → memory → rubric → diagnostics → delegation。既有 middleware
  的相对顺序和上游 `.name` 替换语义不变；`create_deep_agent` 会将新名称追加到
  core 名称之后，最终 base-stack 位置由上游决定，不能把包内列表顺序当作运行时栈顺序。
- planning 仅由 supervisor 装配；isolated 声明式 worker、compiled/async 子代理和
  worker middleware 作用域不变。`mode="fork"` 的声明式子代理按上游语义镜像
  supervisor middleware，因此可能获得 `TodoListMiddleware` 与 `write_todos`；
  这是上游 fork 继承行为，不是本包主动注入。fork 内的 todo 更新不会写回父级。
  没有 per-fork 的 planning 关闭开关：上游按 `.name` 合并且从不删除继承项；
  需要排除时优先提供同名替代 middleware，或不要同时启用 planning 与 fork。在 fork
  自身模型 profile 上配置 `excluded_middleware` 也会移除它，但 fork 与 supervisor
  共用 profile 时会同时移除 supervisor planning。宿主仍可通过现有 worker 作用域自行
  注入 planning。
- 若 `middleware.supervisor` 已包含 `TodoListMiddleware` 实例（含子类和改名实例）
  或同名 middleware，同时配置 planning 时在 `build_supervisor` 期间、构建图之前抛出
  `MiddlewareConfigurationError`，避免双实例竞争。
- 不把 `TodoListMiddleware` 加入全局保留名；planning 关闭时原始注入保持可用。

### 报告与安全

- 继续使用现有 `MiddlewareScopeReport.supervisor_names` 暴露实际 middleware 名称；
  启用时包含 `"TodoListMiddleware"`。
- 不新增 planning 专用报告类型，不把 `system_prompt`、`tool_description`、消息内容、
  模型参数或凭据写入报告、诊断或日志。
- 不承诺 todo 的持久化、跨进程恢复或 exactly-once；宿主继续拥有 checkpointer、
  会话身份和产品流程语义。

### 依赖与范围

- 不新增 Distribution、运行时依赖或反向依赖；`TodoListMiddleware` 来自现有
  `langchain` 依赖。
- 不修改 DeepAgents 默认栈、执行循环、模型用途、资源所有权或 MCP 集成。
- 覆盖需求/设计/测试/评审等领域工作流不在本决策内；那属于宿主业务层或独立包。

## Key design and diagrams

```text
SupervisorSpec(planning=PlanningConfiguration(...))
  -> validate planning fields
  -> reject host supervisor TodoListMiddleware
  -> new TodoListMiddleware(system_prompt?, tool_description?)
  -> supervisor middleware stack
       error normalization
       host supervisor middleware
       planning  <-- added
       summarization
       memory / rubric / diagnostics / delegation
  -> create_deep_agent (upstream merges by .name)
  -> AssemblyReport.middleware.supervisor_names includes "TodoListMiddleware"
```

关键不变量：

1. `planning=None` 时既有工具、提示和 middleware 名称不变。
2. 同一 supervisor 作用域最多一个 planning middleware。
3. 本包不主动向 isolated worker/compiled/async 子代理注入 planning；fork 继承是上游行为。
4. 报告只记录名称，不记录自定义 prompt/description。

## Consequences and migration

收益：

- 产品开发型宿主用一个显式配置即可获得原生 `write_todos`，不再依赖模型 profile；
- 默认关闭，不影响现有消费者；
- 冲突在构建图前失败，行为可测试、可报告；
- 复用 LangChain/DeepAgents 原生实现，不新增依赖或第二套 registry。

成本与限制：

- 新增一个公共配置类型和 `SupervisorSpec` 字段，需按 `0.x` semver 维护；
- planning 仅 supervisor，worker 需要时仍由宿主显式注入；
- 真实模型的 todo 行为与持久化不在包内验证，属于宿主责任；
- 上游 `TodoListMiddleware` 名称/签名变化需要兼容性检查。

重新评估触发条件：

- DeepAgents/LangChain 改变 `TodoListMiddleware` 名称、签名或状态合并语义；
- 出现真实消费者要求 worker 级 planning 或默认开启；
- 需要把 planning 与产品开发领域工作流（需求/设计/评审）合并为独立包。

## Verification and implementation status

本 ADR 在实现完成并经独立 Review 前保持 **Proposed**。实现位于
[`packages/infra/agent-deepagents/`](../../../packages/infra/agent-deepagents/)；
公共契约以该包 README 和 `__init__.py` 为准，测试位于
[`packages/infra/agent-deepagents/tests/`](../../../packages/infra/agent-deepagents/tests/)。

验证覆盖：

- `PlanningConfiguration` 默认值、空白/非字符串校验和不可变性；
- 未配置 planning 时 middleware 名称与工具不变；
- 配置后 supervisor 栈包含 `TodoListMiddleware` 且图暴露 `write_todos`；
- 自定义 prompt/description 不进入报告；
- 宿主重复 `TodoListMiddleware` 在构建图前失败；
- 包级质量命令、严格类型、构建和隔离安装通过。

实际命令、退出码和残余风险记录在 Delivery evidence 中，不在本 ADR 复制。

## Revision history

- 2026-11-28：提出 opt-in、supervisor-only 的 planning middleware public seam；
  状态为 Proposed。
- 2026-11-28：补充包内插入顺序与上游最终栈位置的区别，以及 fork 子代理继承
  supervisor middleware 的上游语义；不改变公共 API。
