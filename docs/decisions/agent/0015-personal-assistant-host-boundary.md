# ADR-0015: 个人助理宿主应用边界与持久化基线

- Status: Accepted
- Date: 2026-11-21
- Domain: agent
- Classification: 约束个人助理宿主 Distribution 的归属，以及 work 机制、审批与执行边界的所有权和持久化接缝，属于 agent 领域的组合层决策。
- Decision owner: 仓库维护者
- Accepted by / date: 仓库维护者 / 2026-11-21
- Depends on: [ADR-0010](0010-deepagents-product-boundary.md)、[ADR-0006](../llm-provider/0006-langchain-first-llm-runtime.md)、[ADR-0008](../llm-provider/0008-model-file-and-env-boundary.md)
- Related: [包边界](../../architecture/package-boundaries.md)、[ADR-0009](../llm-provider/0009-model-metadata-and-sync.md)（无调度先例）、[ADR-0011](../engineering/0011-common-helper-package.md)
- Supersedes: 无
- Superseded by: 无

## Context and drivers

个人助理型 agent 需要"work 机制"与"受控执行"，这两项能力被 ADR-0010 刻意排除在 `spawn-join-agent-deepagents` 之外（"不把租户、授权、计费、产物台账、UI/事件协议、MCP Server、数据库或沙箱实现放入本包"），其重评触发条件明确包含"真实的跨进程委派或持久任务队列需求"。本决策即该触发条件命中后的归属与基线选择。

已确认的需求事实（Delivery run `personal-assistant-20261121`，scope gate 三轮用户决策，2026-11-21）：

1. 单用户本地形态；入口为 CLI；
2. 沙箱级别 v1 = 受限工作区 + `FilesystemPermission` 门禁，默认不暴露 shell 执行工具（参照 OpenClaw 的"默认宿主执行 + 策略先行"姿态）；
3. 跨重启恢复引入 `langgraph-checkpoint-sqlite`（strict msgpack 白名单默认启用）；
4. **记忆（langmem、`BaseStore`、embeddings、记忆文件开发）v1 全部排除**，后续单独讨论；接缝留位。

仓库约束：`quality-config.yml` 的 `unprofiled_changed_paths: block` 要求新 Distribution 同步新增 quality profile；Constitution III 要求 ≥2 处稳定复用才提升共享抽象；Constitution V 要求推测性安全机制先获用户同意（已由 scope gate 满足）。

## Options considered

1. **不建包，以 examples 脚本验证闭环**：成本最低，但产品代码没有构建/测试/发布边界，违反 Distribution 为边界的仓库规则。拒绝。
2. **新增单一宿主 Distribution `packages/apps/personal-assistant`**（采用）：一次固定成本（锁文件、CI、quality profile、双语 README），换明确的产品边界与可验证交付；work/sandbox 作为组合层内部模块，各自单一职责。
3. **立即拆分 `spawn-join-agent-work` + `spawn-join-agent-sandbox` 独立包**：无第二个消费者，违反 Constitution III 提升条件；ADR-0010:181 的"第二个宿主"触发条件未出现。拒绝（当下），保留为提取路径（ADR-0018 已触发 `agent-work` 提取）。

## Decision

新增 `spawn-join-personal-assistant`（路径 `packages/apps/personal-assistant/`，import package `spawn_join_personal_assistant`，新 `apps` 架构分组），作为个人助理宿主应用组合现有九个 Distribution，并确定以下边界：

1. **拥有者**：长任务存储、租约、重试、唤醒与 runner 由 `spawn-join-agent-work` 拥有（ADR-0018）；
   宿主保留 HITL 审批持久化（复用原生 `pending_interrupts`/`resume_batched` 契约）、工作区装配、
   CLI 入口（`accept/due/run/serve/report/approve`）与全部资源生命周期（backend/checkpointer 的
   创建、保持、关闭）。Phase 1 中 `GoalRuntime` 为迁移接缝，全部 CLI 子命令仍走宿主兼容层。
2. **依赖方向**：仅依赖 `spawn-join-agent-deepagents`、`spawn-join-agent-work` 与
   `spawn-join-llm-provider-langchain`（经 `ModelCatalog.create_chat_model` 消费模型，不读
   `model.yaml` 原文与凭据，遵循 ADR-0008）；`apps → infra → core` 单向。
   **不修改任何现有 Distribution 的公共契约。**
3. **执行边界（v1 沙箱级别）**：`FilesystemBackend` 限定工作区根 + 显式 `FilesystemPermission` allow/deny/interrupt 规则；默认不暴露 shell 执行工具。不实现进程/容器/远程沙箱；升级路径为对上游 `BackendProtocol` 的可插拔后端实现，出现独立依赖面或第二个宿主时再评估拆包。
4. **持久化基线**：长任务工作项由 `spawn-join-agent-work` 的 SQLite schema 拥有；宿主数据目录中的
   审批记录与 thread 状态分别由宿主 SQLite 与 `langgraph-checkpoint-sqlite` 的
   `AsyncSqliteSaver` 拥有（strict msgpack 反序列化白名单默认启用）。Phase 1 不为旧 `work.db`
   提供迁移，首次启动创建当前 schema。
5. **记忆留位**：v1 不实现任何记忆能力；`SupervisorSpec.store`/`memory` 透传接缝保留，后续讨论（候选参照 langmem 证据已留档于 Delivery run packet）落地时不需要重构装配层。
6. **生产迁移接缝（只记录、不实现）**：checkpointer → `AsyncPostgresSaver`；work 表 → Postgres 迁移策略；均以接口抽象为界，v1 不交付迁移工具。

明确不处理的相邻问题：多租户/授权/计费、IM 用户消息通道、Web UI、MCP Server、cron 丰富语法、embeddings、Postgres 部署。

## Key design and diagrams

以下为 v1 基线；work 所有权已由 ADR-0018 迁移到 `spawn-join-agent-work`（`GoalRuntime` 接缝）。

```text
CLI (accept|due|run|serve|report|approve)
  → AppConfig 校验 → WorkStore(SQLite, 单写者; 兼容层)
  → Scheduler(asyncio) → HostAssembly: build_supervisor(
        models ← ModelCatalog, backend=FilesystemBackend(workspace_root),
        permissions=allow/deny/interrupt, interrupt_on=审批动作,
        checkpointer=AsyncSqliteSaver(strict msgpack), tools=()  # 无 shell)
  → graph.ainvoke(thread_id ↔ 工作项) → interrupt → ApprovalStore → resume_batched → 落库
```

不变量：工作项状态迁移全部落库带时间戳、非法迁移报错；幂等键在存储层唯一；agent 文件副作用不出工作区根；日志与记录不含凭据。

## Consequences and migration

收益：

- "接活 → 执行 → 审批 → 汇报 → 重启恢复"闭环有独立可验证的交付边界；
- ADR-0010 的排除项获得明确归宿，装配包公共契约零改动；
- 记忆与 Postgres 以接缝留位，后续演进不需重构。

成本与限制：

- 仓库第 8 个 Distribution 的固定成本（uv 锁、CI 矩阵、quality profile、双语 README、ADR 索引更新）；
- SQLite 单写者约束：多进程同时打开同一数据目录不支持（需显式检测或文档声明）；
- 工作区文件 backend 非隔离边界，安全依赖权限门禁与"默认无 shell"（与 OpenClaw 同为默认非沙箱姿态，风险已被用户在 scope gate 接受）；
- checkpointer 数据库包含序列化状态，反序列化风险由 strict msgpack 白名单缓解。

重新评估触发条件：

- 记忆讨论重启并决定落地（候选：langmem 或对 `BaseStore` 的等价实现；证据已在 run packet 留档）；
- 出现第二个宿主需要 work/sandbox 能力，或沙箱需要独立依赖面（容器/远程 SDK）→ 提取独立 Distribution；
- 出现真实 Postgres 部署需求 → 迁移工具与部署面设计；
- DeepAgents 0.8 或 LangChain 2.x 改变 `create_deep_agent`/interrupt/checkpointer 契约。

## Verification and implementation status

本 ADR 已由仓库维护者于 2026-11-21 批准为 **Accepted**（最终 outgoing-diff Review
`pass` + 人工 review gate 确认 accepted-self-review 降级后批准）。实现位于
[`packages/apps/personal-assistant/`](../../../packages/apps/personal-assistant/)，公共契约以该包的
[`README.md`](../../../packages/apps/personal-assistant/README.md) 和 `__init__.py` 为准；测试位于
[`packages/apps/personal-assistant/tests/`](../../../packages/apps/personal-assistant/tests/)
（2026-11-21 交付时 60 用例；2026-11-22 迁移后 75 用例）。2026-11-21 交付审阅 HEAD：
`ff33326134c363cc3b06bd8097c6ed43113b1976`
（Ralph 分支 `ralph/personal-assistant-host-20261121`，base `main 4f5b79c…`）。

验证覆盖：spec 全部 9 条 FR 与 US1–US4/SC-001..005（e2e 真实文件副作用）；幂等重放、
硬杀恢复（attempts 递增且重跑一次）、批准/拒绝两路径（批准写入、拒绝不执行）、
越界写守卫（即使批准也被拦截）、thread 断点续跑；Pyright strict、隔离构建/安装/导入、
门禁回归 15 场景。实际命令、退出码和残余风险记录在 Delivery evidence 中，不在本 ADR 复制。

残余限制（如实）：真实 Provider 网络路径未测（离线边界，ADR-0008 语义内）；
本 run 为 accepted-self-review（用户在最终 review gate 明确接受）。

## Revision history

- 2026-11-21：提出个人助理宿主边界、work/审批所有权、v1 执行边界、SQLite 持久化基线、记忆留位与生产迁移接缝；状态为 Proposed。
- 2026-11-21：实现与验证完成（七个任务、五个切片，60 用例含 e2e）；仓库维护者批准为 Accepted。
- 2026-11-22：work 存储/调度所有权迁移到 `spawn-join-agent-work`（ADR-0018）；宿主保留 HITL
  审批与 CLI，`GoalRuntime` 为迁移接缝；测试增至 75 用例。
