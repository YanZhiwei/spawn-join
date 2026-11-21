# Delivery slice plan — personal-assistant-20261121

## Identity and approval

- Delivery run / canonical path: `personal-assistant-20261121` / `.specify/delivery/personal-assistant-20261121/`
- Feature / spec / plan / tasks: `specs/personal-assistant-host-20261121/`（spec `a689e889…`、plan `4ed9b339…`、tasks 见 tasks.md）
- Baseline HEAD / relevant working-tree changes: `4f5b79c`；工作树含未跟踪的 Proposed ADR `docs/decisions/agent/0015-personal-assistant-host-boundary.md`（唯一计划内路径；specs/ 与 run 工作区按策略本地忽略）
- Design approval: plan gate `approve`（2026-11-21，呈现指纹 spec `a689e889…` / plan `4ed9b339…` / packet `d7ad97cd…`；接受限制：accepted-self-review 降级、参照研究未做 issue 级深挖）
- Artifact policy: ephemeral（specs/ 本地忽略；Proposed ADR 走 tracked 提交）
- Planning timestamp: 2026-11-21

## Execution and publication decision

- `pr_slicing` request: auto（delivery-config）
- Internal review slicing: multiple（5 个内部评审切片）
- Execution mode: single（普通 Ralph 分支，无 stacked/integration）
- Publication mode: single（一个发布组、一个最终 PR）
- Publication grouping: 一个 PR 覆盖全部切片
- Publication authorization: pending —— 切片批准不授权远端发布
- Target branch: `main`（线性历史 + squash 规则集）
- Integration branch: N/A
- Stack provider: manual（delivery-config）
- Slice merge method: squash
- Final merge method: squash（delivery-config `final: squash`）
- Target sync method: merge（仅未来 integration 场景适用）
- Merge queue: no
- Delete branch after merge: yes
- Freeze integration before final review: yes（单组模式即最终评审前冻结）
- Why this execution/publication choice: 全部任务落在**新增**路径（`packages/apps/**`）+ 4 个治理文档与 quality-config 的追加式修改，无 trunk 风险行为变更；ADR-0007/0003 线性历史 + required Quality Gate 规则集下，单发布组 squash 是最小且合规拓扑；无 flag 基础设施，不适用 flagged/stacked。

## Slice table

| ID | Goal | Kind | Depends on | Task IDs | Paths | Trunk-safe | Flag | Merge order | Publication group |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | 第 8 个 Distribution 脚手架可构建、被质量门与治理文档覆盖 | foundation | - | T001 | `packages/apps/personal-assistant/**`（新）、`.specify/extensions/quality/quality-config.yml`、`docs/architecture/repository-map.md`、`docs/architecture/package-boundaries.md`、根 `README.md`/`README.en.md` | standalone | - | 1 | P1 |
| S2 | 工作项存储 + supervisor 装配（受限工作区/权限/strict msgpack） | behavior | S1 | T002, T003 | `src/spawn_join_personal_assistant/work/**`、`host.py`、对应 tests | standalone | - | 2 | P1 |
| S3 | due 调度 + 审批暂停/恢复闭环 | behavior | S2 | T004, T005 | `scheduler.py`、`approvals.py`、对应 tests | standalone | - | 3 | P1 |
| S4 | CLI 与四条用户故事离线端到端 | behavior | S3 | T006 | `cli.py`、`examples/offline_run.py`、`test_cli.py`、`test_e2e_offline.py` | standalone | - | 4 | P1 |
| S5 | 文档与索引终态收口 | release | S4 | T007 | `docs/decisions/README.md`、包双语 README、根 README 核对 | standalone | - | 5 | P1 |

## Publication groups

| Group | Kind | Internal slices | Remote base/head shape | Publication artifact | Issue relation | Authorization |
| --- | --- | --- | --- | --- | --- | --- |
| P1 | layer | S1, S2, S3, S4, S5 | 普通 Ralph 分支 → `main`（squash） | 一个 PR | N/A（无 issue 跟踪项） | pending |

`pr_slicing: single` 语义下的单一 `layer` 组：Ralph 使用普通 feature 分支，全部切片 squash 为一个最终 PR；无 rollup 组。

## Slice details

### S1 — Distribution 脚手架与治理覆盖

- Acceptance outcome: `quality.ps1 -Package spawn-join-personal-assistant` 全绿；repository-map/package-boundaries/根 README 含新包条目。
- Task IDs: T001
- Expected paths: 新 `packages/apps/personal-assistant/**`；修改 quality-config（追加 profile）、两份架构文档、根 README 双语。
- Trunk-safe: standalone（纯新增 + 追加式文档行；无既有行为变更）
- Publication group: P1
- Evidence: 新包不触碰任何现有 Distribution 源码；profile 追加符合 `unprofiled_changed_paths: block` 的唯一解除方式。
- Target verification: `uv lock --check / uv sync --locked --directory packages/apps/personal-assistant`；`pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-personal-assistant`；`-Check docs`、`-Check governance`。
- Flag: N/A
- Integration checkpoints: N/A
- Risk probes: N/A（纯脚手架；无并发/恢复行为）
- Review focus: 依赖方向（AC-02）、profile 命令真实性、README 双语同语义。
- Not in this slice: 任何业务行为（归 S2-S4）。
- Rollback: revert 单个任务提交（新增路径无残留状态；quality-config/profile 行随之回退）。
- Diff budget: 约 15 文件、~500 行（含双语 README 初版与声明性配置）。**例外说明**：行数超 `slice_warn_lines: 400` 提示线——成因为 README 规则要求的完整双语初版，不可拆出可独立评审单元；文件数 < `slice_warn_files: 20`。

### S2 — 工作项存储与装配

- Acceptance outcome: 幂等键唯一/非法迁移报错（test_work_store）；装配断言 workspace 根/权限/strict msgpack/无 shell 工具（test_host_assembly）。
- Task IDs: T002, T003
- Expected paths: `work/models.py`、`work/store.py`、`host.py` + 两测试文件（均新）。
- Trunk-safe: standalone（新包内新增模块）
- Publication group: P1
- Evidence: 无既有消费者；公共导出仅经本包 `__init__.py`。
- Target verification: 包级质量门；`test_work_store`/`test_host_assembly` 全过。
- Flag: N/A
- Risk probes: `test_host_assembly` 的 fake model 装配冒烟 = 最小并发/恢复探针前置（真实探针在 S3/S4）。
- Review focus: 状态机非法路径、异常分类、资源生命周期（AC-03/04/05/06/08）。
- Not in this slice: 调度与审批（S3）。
- Rollback: revert 任务提交；SQLite 文件为运行期产物不入库。
- Diff budget: ~6 文件、~500 行（测试为主）。

### S3 — 调度与审批

- Acceptance outcome: due 拾取/并发/取消/deadline/重启重入队（test_scheduler）；interrupt→批准→resume 与拒绝两路径（test_approvals）。
- Task IDs: T004, T005
- Expected paths: `scheduler.py`、`approvals.py` + 两测试文件。
- Trunk-safe: standalone
- Publication group: P1
- Evidence: 全部离线 fake model；副作用以受控 tmpdir 文件计数验证。
- Target verification: 包级质量门；两测试文件全过。
- Flag: N/A
- Risk probes: 重启重入队幂等探针（并发/恢复行为的核心证据）。
- Review focus: 取消传播、deadline 落库类别、审批决定对齐契约（AC-07、FR-003/004/006）。
- Not in this slice: CLI 入口与 e2e（S4）。
- Rollback: revert 任务提交。
- Diff budget: ~4 文件、~500 行。

### S4 — CLI 与端到端

- Acceptance outcome: 五个子命令冒烟 + US1–US4 主路径 e2e（越界 deny、重启恢复、审批两路径、幂等重放）全部离线可复现。
- Task IDs: T006
- Expected paths: `cli.py`、`examples/offline_run.py`、`test_cli.py`、`test_e2e_offline.py`。
- Trunk-safe: standalone
- Publication group: P1
- Evidence: SC-001..SC-005 逐条映射到 e2e 断言。
- Target verification: 包级质量门 + `uv run --locked --directory packages/apps/personal-assistant python examples/offline_run.py`。
- Flag: N/A
- Risk probes: e2e 即集成探针（装配×存储×调度×审批全链）。
- Review focus: 退出码稳定性、日志无凭据（FR-007/008）。
- Not in this slice: 文档终态（S5）。
- Rollback: revert 任务提交。
- Diff budget: ~4 文件、~600 行（e2e 为主）。

### S5 — 文档与索引收口

- Acceptance outcome: ADR 索引含 0015 行；包双语 README 终版与实际导出/命令一致；docs/governance 检查全绿。
- Task IDs: T007
- Expected paths: `docs/decisions/README.md`（含英文版如需）、包 `README.md`/`README.en.md`、根 README 双语核对。
- Trunk-safe: standalone（文档追加/修订）
- Publication group: P1
- Evidence: ADR 索引义务（docs/decisions/README.md"新增或变更 ADR 时同时更新索引"）；README 规则要求双语同变更同步。
- Target verification: `-Check docs`、`-Check governance`；package-readme 判定前置条件满足。
- Flag: N/A
- Risk probes: N/A（文档）
- Review focus: 双语语义一致、命令可复现、不虚构功能。
- Not in this slice: 无（收尾）。
- Rollback: revert 任务提交。
- Diff budget: ~5 文件、~400 行。

## Coverage and validation

- Task coverage: T001→S1；T002,T003→S2；T004,T005→S3；T006→S4；T007→S5。每任务恰好映射一个切片；无跨切片任务。
- Requirement coverage: FR-001/002→S2；FR-003/004→S3（存储面 S2）；FR-005→S2；FR-006→S3；FR-007→S4；FR-008→S2（配置面 S1）+S4；FR-009→S2。US1→S2/S4；US2→S3/S4；US3→S3/S4；US4→S4；SC-001..005→S4；AC-01..10→S1(01/02/09/10)、S2(03/04/05/06/08)、S3(07)、S5(10)。
- Classification coverage: 全部 standalone——所有行为路径为新增 Distribution 内新增模块；既有仓库仅 4 处追加式文档/配置修改，集中在 S1/S5。
- Behavioral probe coverage: 重启/并发/恢复探针在 S3（单元级）与 S4（e2e 级）；装配冒烟在 S2。
- Dependency order: S1→S2→S3→S4→S5，无环、线性。
- Publication coverage: 5 个切片 → 唯一层组 P1；无 rollup。
- Budget exceptions: S1 行数超提示线（双语 README 初版），接受理由见详情；其余切片在阈值内。
- Policy compatibility: 线性历史 + squash + required Quality Gate 规则集兼容；无 merge queue；分支合并后删除。
- User authorization boundary: 切片批准（本 gate）≠ 发布授权；远端 PR 创建/合并需另行授权。
- Open decisions: 无。

## Merge and publication plan

- Execution order: S1, S2, S3, S4, S5（单分支顺序执行）
- Ralph branch/topology: 普通 feature 分支（`ralph/` 前缀按配置），无 stacked 层分支
- Per-slice merge: N/A（单一发布组；切片为内部评审边界）
- Publication groups: P1（S1..S5 → `main`，squash）
- Final rollup: N/A
- Target sync: N/A
- Queue/freeze: 最终评审前冻结分支
- Issue closure: 无关联 issue；PR 模板按项目静态模板
- Rollback per slice: revert 对应任务提交（见各切片 Rollback）

## Approval record

- SLICE_PLAN_VERDICT: ready
- SLICE_PLAN_FINGERPRINT: SHA-256 按文件；呈现哈希（runtime present 2026-11-21）：slices.md `e1f4311d5a0d38ae0827b3171cfe5d108a14492c8f2a94efae5a94fd7fc77813`、spec `a689e889…`、plan `4ed9b339…`、tasks `ea104e62…` @ HEAD `4f5b79c`
- SLICE_APPROVAL: approved
- Approved by: 人类用户（组合执行/切片门选择"批准执行"，2026-11-21）
- Choice / accepted risks: approve；接受已声明项——S1 行数预算例外（双语 README 初版成因）、accepted-self-review 降级、参照研究未做 issue 级深挖；Analyze pass（阻断性发现为零）
- Approved execution mode: single
- Approved publication mode: single
- Approved publication groups: P1（S1–S5 → `main` squash 单 PR；发布授权 pending，另行申请）
- Approved mode / snapshot: execution=single、publication=single、组=P1；HEAD `4f5b79c`、slices `e1f4311d…`、tasks `ea104e62…`
- Publication authorization: pending
- Approved at: 2026-11-21（组合门 decide --name execution --choice approve 已按哈希记录）
