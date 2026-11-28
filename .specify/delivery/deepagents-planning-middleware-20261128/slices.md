# 交付切片计划

## 身份与批准

- Delivery run / 规范路径：`deepagents-planning-middleware-20261128` /
  `.specify/delivery/deepagents-planning-middleware-20261128/`
- Feature / spec / plan / tasks：
  `specs/012-deepagents-planning-middleware/`（`spec.md`、`plan.md`、`tasks.md`）
- 基线 HEAD / 相关工作树改动：
  `87e809f2b8d405c19d9bced4bfda89d018fa430e`；规划开始时工作树干净。
- 设计批准：2026-11-28 Plan Gate `approve`；批准快照为探索包中记录的
  spec/plan 哈希。
- 工件策略：ephemeral（`specs/` 仅本地；ADR 跟踪）。
- 规划时间：2026-11-28

## 执行与发布决定

- `pr_slicing` 请求：auto
- 内部评审切片：single
- 执行模式：single
- 合并模式（旧别名）：single
- 发布模式：single
- 发布分组：所有切片一个 PR
- 发布授权：pending — 切片批准不授权远程发布
- 目标分支：`main`
- 集成分支：N/A
- Stack provider：N/A
- 切片合并方式：squash
- 最终合并方式：N/A（一个发布组）
- 目标同步方式：N/A
- 合并队列：no
- 合并后删除分支：yes
- 最终评审前冻结集成：no
- 选择理由：一个附加式包变更，只有一个 ADR/文档更新；没有独立回滚边界或 flag，
  多切片只会增加评审和发布开销，没有收益。

## 切片表

| ID | 目标 | 类型 | 依赖 | 任务 ID | 路径 | 主干安全 | Flag | 合并顺序 | 发布组 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | Opt-in supervisor planning seam | behavior | - | T001, T002, T003, T004 | `packages/infra/agent-deepagents/**`、`docs/decisions/agent/0019-*.md`、`docs/decisions/README.md` | standalone | - | 1 | P1 |

## 发布组

| 组 | 类型 | 内部切片 | 远程 base/head 形态 | 发布工件 | Issue 关系 | 授权 |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | layer | S1 | 普通功能分支 → `main` | 一个 PR | N/A | pending |

## 切片详情

### S1 — Opt-in supervisor planning seam

- 验收结果：`PlanningConfiguration` 公开；`SupervisorSpec.planning` 默认关闭；
  启用后向 supervisor 栈恰好添加一个原生 `TodoListMiddleware`；冲突和空白值在构建图
  之前失败；双语 README 和 ADR-0019 记录契约。
- 任务 ID：T001、T002、T003、T004
- 预计路径：
  - `packages/infra/agent-deepagents/src/spawn_join_agent_deepagents/planning.py` [新增]
  - `packages/infra/agent-deepagents/src/spawn_join_agent_deepagents/supervisor.py` [修改]
  - `packages/infra/agent-deepagents/src/spawn_join_agent_deepagents/__init__.py` [修改]
  - `packages/infra/agent-deepagents/tests/test_planning.py` [新增]
  - `packages/infra/agent-deepagents/tests/test_supervisor.py` [修改]
  - `packages/infra/agent-deepagents/tests/test_public_api.py` [修改]
  - `packages/infra/agent-deepagents/README.md` [修改]
  - `packages/infra/agent-deepagents/README.en.md` [修改]
  - `docs/decisions/agent/0019-deepagents-planning-middleware.md` [新增]
  - `docs/decisions/README.md` [修改]
- 主干安全：standalone — 附加式 API，默认关闭；未启用 planning 时包仍可构建和导入。
- 发布组：P1
- 证据：无 schema 迁移；功能在 `SupervisorSpec` 边界 opt-in，因此不需要 flag；
  现有测试是默认关闭的守卫。
- 目标验证：
  - `uv lock --check --directory packages/infra/agent-deepagents`
  - `uv sync --locked --directory packages/infra/agent-deepagents`
  - `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents`
  - `pwsh -NoProfile -File scripts/quality.ps1 -Check docs`
- Flag：N/A — `planning` 字段默认值就是关闭开关。
- 集成检查点：N/A
- 风险探针：fake model 图装配证明只有配置时才出现
  `TodoListMiddleware`/`write_todos`；重复注入在返回图之前失败。
- 评审重点：公共 API 形状、默认关闭行为、中间件顺序、worker 作用域不干扰、
  报告提示不泄漏、双语文档一致性。
- 本切片不包含：worker 级 planning、默认开启、领域工作流、真实模型 todo 行为。
- 回滚：移除 `planning` 字段/模块和文档，或停止配置；没有持久化数据或迁移。
- Diff 预算：少于 20 个文件、400 行改动；预计例外：无。

## 覆盖与验证

- 任务覆盖：T001–T004 各映射一次到 S1。
- 需求覆盖：FR-001/T001；FR-002–FR-003/FR-004/T002；FR-005/T001–T002；
  FR-006/T002；FR-007/T002 回归；FR-008/T003。
- 分类覆盖：standalone，因为功能 opt-in 且附加式；包质量和默认关闭测试提供主干安全证据。
- 行为探针覆盖：启用/禁用图装配和重复冲突探针在 T002。
- 依赖顺序：T001 → T002 → T003 → T004（无环、线性）。
- 发布覆盖：S1 → P1；P1 使用普通功能分支和一个 PR。
- 预算例外：无。
- 策略兼容：squash 合并；保持线性历史；无合并队列。
- 用户授权边界：切片批准单独记录；发布仍待用户明确授权。
- 待决事项：无。

## 合并与发布计划

- 执行顺序：S1
- Ralph 分支/拓扑：普通功能分支
- 每切片合并：一个发布组，N/A
- 发布组：P1 包含 S1，目标 `main`
- 最终 rollup：N/A
- 目标同步：N/A
- 队列/冻结：无队列；不冻结集成
- Issue 关闭：N/A
- 每切片/组回滚：回滚单个 PR；无数据迁移

## 批准记录

- SLICE_PLAN_VERDICT: ready
- SLICE_PLAN_FINGERPRINT: `sha256:96ba6bfc6f8c392df7fe5f863e0994f23b9c000a2b5da87685dffd72e537b661`
  对 spec.md、plan.md、tasks.md 及本 slices.md 的批准前正文计算；
  排除批准记录和本指纹行。
- SLICE_APPROVAL: approved
- Approved by: 用户（由 Delivery 协调者记录）
- Choice / accepted risks: 批准 S1 为单个 standalone 切片；接受 worker 级 planning
  和真实模型 todo 行为不在本次范围。
- Approved execution mode: single
- Approved publication mode: single
- Approved publication groups: P1 包含 S1；一个 PR 目标 `main`
- Publication authorization: pending — 需要用户单独授权
- Approved mode / snapshot:
  `single/single/P1@sha256:96ba6bfc6f8c392df7fe5f863e0994f23b9c000a2b5da87685dffd72e537b661`
- Approved at: 2026-11-28
