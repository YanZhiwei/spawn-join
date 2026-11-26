# ADR-0014: DeepAgents 官方 P1 能力的公共边界

- Status: Proposed
- Date: 2026-11-15
- Domain: agent
- Classification: 本决策约束 `spawn-join-agent-deepagents` 的 P1 公共能力：beta rubric、backend/权限报告和 HITL helpers，属于 `agent` 领域。
- Decision owner: 仓库维护者
- Accepted by / date: 未批准
- Depends on: [ADR-0010](0010-deepagents-product-boundary.md)、[ADR-0012](0012-deepagents-official-p0.md)
- Related: [包边界](../../architecture/package-boundaries.md)、P1 Delivery packet `.specify/delivery/deepagents-p1-continuation-20261115/`
- Supersedes: 无；本 ADR 在 ADR-0010 的产品边界内补充 P1 的具体公共 seam
- Superseded by: 无

## Context and drivers

PR #57 为 `spawn-join-agent-deepagents` 增加了官方 DeepAgents P1 能力：可选 rubric 评分、
backend/权限的只读报告，以及围绕原生 LangGraph interrupt/resume 的 HITL helpers。
ADR-0010 已经确定了产品边界（原生 interrupt/resume、beta 能力显式 opt-in、报告脱敏），
ADR-0012 只覆盖官方 P0（该决策已于 2026-11-26 接受），两者都没有记录 P1 的具体公共 contract。

这些新增内容会长期影响调用方：

1. `allow_experimental_rubric` 与 `RubricConfiguration` 是一个 beta 装配 seam；
2. HITL helpers 生成的 batched/per-call payload 形状会随上游 LangChain 演进；
3. `PermissionReport` / `backend_kind` 字段改变了公开报告的可观察内容；
4. 这些类型一旦导出，后续变更需要兼容性说明和迁移策略。

因此需要一份独立 ADR 记录边界、拒绝项和验证状态，而不是只依赖 README。

## Options considered

1. **不新增 ADR，只依赖 ADR-0010** — 拒绝。ADR-0010 的原则不足以约束具体字段、
   beta gate 和 HITL payload key 约定，未来维护者无法从权威决策判断哪些属于稳定契约。
2. **把 P1 并入 ADR-0012** — 拒绝。ADR-0012 是已接受的 P0 决策，把 P1 塞入会
   混淆两个能力批次，也不能把 P0 的接受当作 P1 的授权。
3. **新增 ADR-0014（采用）** — 在 ADR-0010 边界内记录 P1 的具体公共 seam、拒绝项和
   验证状态；ADR-0012 的状态另行收口。
4. **导出 `backend_kind()` / `permission_report()` 作为公共 API** — 拒绝。它们是报告字段的
   内部实现；公共契约只需要 `ResourceReport.backend_kind` 和 `ResourceReport.permissions`。

## Decision

在 `spawn-join-agent-deepagents` 中采用以下 P1 公共边界。

### Rubric（beta）

- `RubricConfiguration` 是配置对象，包含 `BaseChatModel` grader、可选 `system_prompt`、
  tools、`max_iterations` 和 `on_evaluation`。
- `max_iterations` 必须是正整数原生 `int`；`bool`、浮点数、字符串和 `None` 抛出
  `RubricConfigurationError`。`model` 必须是 `BaseChatModel`。
- `rubric=` 只有在 `allow_experimental_rubric=True` 时才允许装配；原生
  `RubricMiddleware` 放进 `middleware.supervisor` 时同样需要该开关。
- 不能同时传 `rubric=` 和原生 `RubricMiddleware`；两者都表示同一个上游能力 seam。
- 未配置时行为完全不变：不追加 middleware、不增加 warning 或 `experimental_features`。
- `RubricReport` 只包含 enabled、迭代上限、grader 来源（`injected:<class>` 或
  `host_middleware`）和工具数量；不包含 prompt、工具名、模型参数或凭据。
- 真实 grader 执行依赖 provider structured output，默认测试不覆盖。

### Backend 与权限报告

- `ResourceReport.backend_kind` 输出稳定标签：`default_state`、`local_shell`、`sandbox`、
  `state`、`store`、`composite`、`filesystem`、`context_hub`、`custom`。
- `ResourceReport.permissions` 是 `PermissionReport`，只包含 allow/deny/interrupt/other
  计数；不包含路径、规则文本或工具参数。
- `backend_kind()` 和 `permission_report()` 是内部 helper，不进入 `__all__`。
- 未知 permission mode 计入 `other`，不静默丢弃。

### HITL helpers

- `pending_interrupts()` 读取原生 `__interrupt__`，接受映射序列、单个映射、单个
  interrupt 对象；缺失、`None`、字符串或缺少 `value` 的条目返回空 tuple，不抛异常、
  不伪造条目。
- `approve_decision`、`edit_decision`、`reject_decision`、`respond_decision` 只构造
  LangChain `HumanInTheLoopMiddleware` 期望的 decision 字典。
- `resume_batched` 的 decision 数量/顺序必须与 `action_requests` 对齐；
  `resume_per_call` 使用原生 interrupt id；`resume_with` 透传调用方 payload。
- helpers 不批准、不持久化、不创建 checkpointer、不承诺 exactly-once；宿主负责
  `thread_id`、checkpointer、审批记录和重试。
- `PendingInterrupt.value` 是宿主拥有的原始 payload，可能含工具参数或路径，不应直接
  写入未脱敏日志。

### 依赖与范围

- 不新增 Distribution、运行时依赖或反向依赖；仍由 `spawn-join-agent-deepagents` 拥有。
- 不进入 Core、协议包、模型适配包或 channel 包。
- 不覆盖真实 grader/provider 调用、HITL 持久化/checkpointer、远程 async/profile、
  CLI 或错误归一（#59）。

## Key design and diagrams

```text
SupervisorSpec
  ├── rubric + allow_experimental_rubric=True
  │     └── native RubricMiddleware -> supervisor middleware stack
  ├── middleware.supervisor: native RubricMiddleware
  │     └── same beta gate, exclusive with rubric=
  └── backend/permissions
        └── ResourceReport(backend_kind, PermissionReport counts)

Native interrupt state
  └── pending_interrupts -> PendingInterrupt(tuple)
        ├── approve/edit/reject/respond decision dicts
        └── resume_batched / resume_per_call / resume_with -> Command
```

关键不变量：

1. beta 能力必须显式开启，且不能被包内 `rubric=` 路径静默绕过。
2. 报告只输出稳定标签和计数，不泄露路径、规则、prompt 或凭据。
3. HITL helper 不拥有审批状态，也不自动批准。
4. 所有新增字段都有默认值；未配置时既有装配行为不变。

## Consequences and migration

收益：

- P1 能力有可发现的公共入口和安全报告；
- rubric 的 beta 性质、HITL 的非持久化边界和 backend 报告的脱敏规则有权威记录；
- 后续上游变化可以在本 ADR 上做兼容性评估。

成本与限制：

- 上游 `RubricMiddleware` 和 HITL payload 仍可能变化，beta seam 需要跟随升级；
- 真实 rubric grader 执行和跨进程 HITL 不在默认验证范围；
- `AssemblyReport.rubric` 和 `ResourceReport` 的新字段是增量，但依赖位置参数构造的
  调用方需要改用关键字参数；
- 不提供审批存储、重试、exactly-once 或 UI。

迁移：

- 既有调用方不需要修改；未配置 rubric 时行为不变；
- 使用 `ResourceReport` / `AssemblyReport` 位置参数的调用方应改用关键字参数；
- 需要 rubric 的调用方必须显式设置 `allow_experimental_rubric=True`；
- 需要 HITL 的调用方必须提供 checkpointer 和稳定 `thread_id`。

## Verification and implementation status

本 ADR 当前为 `Proposed`。探索、决策上下文和切片记录在
`.specify/delivery/deepagents-p1-continuation-20261115/`，验证状态、合并结果与限制记录在其
`evidence.md`。2026-11-26 的独立六维 Review 在 HEAD `7942509` 上执行，结论为 `blocked`：
原生 `RubricMiddleware` 的 beta gate 只覆盖 supervisor 作用域（F1），原生 `tool_count`
读取错误（F2），`SupervisorSpec` 位置参数兼容性被破坏（F3），并有迁移说明和测试缺口。
因此本 ADR 保持 `Proposed`，待修复并复评后再接受。完整报告见
`.specify/delivery/adr-lifecycle-closure-20261126/reviews/adr-0014-review.md`。

计划验证：

- 包级质量门：Black/isort/Ruff/Pyright/pytest/build/隔离安装；
- rubric：beta gate、非法配置、原生 middleware 绕过、报告字段；
- backend/permission：所有稳定标签、未知 mode 计数、不泄露路径；
- HITL：malformed/empty 输入、decision 形状、batched/per_call resume；
- 文档：中英文 README、公共 API、示例；
- 真实 grader/provider、HITL 持久化和远程 async/profile 明确未执行。

## Revision history

- 2026-11-15：提出 P1 rubric、backend/权限报告和 HITL helpers 的公共边界。
- 2026-11-26：独立六维 Review 结论为 blocked（F1–F3 等），状态保持 Proposed。
