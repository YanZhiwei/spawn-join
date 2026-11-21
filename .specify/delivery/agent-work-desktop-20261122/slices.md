# Delivery slice plan — agent-work 桌面档 Phase 1

## Identity and approval

- **Delivery run / canonical path**: `agent-work-desktop-20261122` / `.specify/delivery/agent-work-desktop-20261122/`
- **Feature / spec / plan / tasks**: `specs/001-agent-work-desktop/{spec.md,plan.md,tasks.md}`
- **Baseline HEAD / worktree**: `5739be137b3a95caa7507f2db6f48e32fc6d5d57`；工作区含未提交的规划工件（specs 本地、ADR-0017 新增）
- **Design approval**: plan gate approved（2026-11-22）；指纹见 runtime plan receipt
- **Artifact policy**: ephemeral（`specs/` 本地；ADR/架构/证据持久化）
- **Planning timestamp**: 2026-11-22

## Execution and publication decision

- `pr_slicing` request: **auto**
- Internal review slicing: **multiple（6 个内部切片）**
- Execution mode: **single**
- Merge mode (legacy alias): single
- Publication mode: **single**
- Publication grouping: **one PR for all slices**
- Publication authorization: **pending** — slice approval 不授权远端发布
- Target branch: `main`
- Integration branch: N/A
- Stack provider: N/A
- Slice merge method: squash
- Final merge method: N/A（single 发布组；由一次 PR squash 完成）
- Target sync method: N/A
- Merge queue: no
- Delete branch after merge: yes
- Freeze integration before final review: yes（Ralph 结束前不发布）
- Why: 全部切片是加法式新包代码/测试，S6 才切换宿主；每个切片可独立回滚，仓库规则要求线性历史且 `auto` 在无 stacked 依赖时选择单一发布组。内部切片只作为评审边界，不产生多个远端 PR。

## Slice table

| ID | Goal | Kind | Depends on | Task IDs | Paths | Trunk-safe | Flag | Merge order | Publication group |
|---|---|---|---|---|---|---|---|---|---|
| S1 | 包骨架、质量/CI 边界、公共模型与端口 | foundation | - | T001–T004 | `packages/infra/agent-work/**`、`.specify/extensions/quality/quality-config.yml`、`.github/workflows/quality.yml`、README/docs 计数 | standalone | - | 1 | P1 |
| S2 | SQLite 存储：schema、claim、状态迁移、租约、保留 | behavior | S1 | T005–T006 | `packages/infra/agent-work/src/.../stores/sqlite.py`、`tests/` | standalone | - | 2 | P1 |
| S3 | 内存第二实现 + 存储契约测试 | behavior | S2 | T007–T008 | `.../stores/memory.py`、`tests/test_contract_store.py` | standalone | - | 3 | P1 |
| S4 | Runner 核心、租约/恢复、重试/期限/取消 | behavior | S3 | T009–T011 | `.../runner.py`、`tests/test_runner.py`、`test_lease_and_fencing.py`、`test_retry.py` | standalone | - | 4 | P1 |
| S5 | ZeroMQ 唤醒与常驻 serve、优雅关闭 | behavior | S4 | T012–T013 | `.../notify/zmq.py`、`tests/test_zmq_integration.py`、`test_shutdown.py` | standalone | - | 5 | P1 |
| S6 | personal-assistant 迁移、文档/ADR、最终验证 | release | S5 | T014–T017 | `packages/apps/personal-assistant/**`、`packages/infra/agent-work/README*`、`docs/**`、`examples/` | standalone | - | 6 | P1 |

## Publication groups

| Group | Kind | Internal slices | Remote base/head shape | Publication artifact | Issue relation | Authorization |
|---|---|---|---|---|---|---|
| P1 | layer | S1–S6 | 普通 feature branch → `main` | 一个 PR | N/A（无关联 Issue） | pending |

## Slice details

### S1 — 包骨架与契约

- Acceptance outcome: 新包可构建/导入；质量 Profile 与 CI 矩阵包含第 9 个包；公共模型/端口导出。
- Task IDs: T001, T002, T003, T004
- Expected paths: `packages/infra/agent-work/**`（new）、`.specify/extensions/quality/quality-config.yml`（modify）、`.github/workflows/quality.yml`（modify）、`README*.md`/`AGENTS.md`/`docs/**` 计数（modify）
- Trunk-safe: standalone（加法式新包；未接入宿主）
- Publication group: P1
- Evidence: 新包不被任何运行时依赖；CI 仅新增 job；失败可回滚
- Target verification: `uv lock --check`、`uv sync --locked`、`quality.ps1 -Package spawn-join-agent-work`、`-Check docs`、`-Check governance`、actionlint
- Risk probes: 包导入边界、依赖方向；`pyzmq` 安装/导入
- Review focus: 包边界、公共导出、CI/Profile 计数一致、无旧库迁移残留
- Not in this slice: 存储/runner/ZMQ 行为
- Rollback: revert 单个提交；无数据/服务副作用
- Diff budget: ~600 行（profile/CI/文档计数导致超 400 行，接受为例外）

### S2 — SQLite 存储

- Acceptance outcome: 原子 claim、状态迁移、租约/fencing、保留清理可在 SQLite 上工作；首次启动创建当前 schema。
- Task IDs: T005, T006
- Expected paths: `.../stores/sqlite.py`（new）、`tests/test_sqlite_store.py`（new）
- Trunk-safe: standalone（包尚未被宿主使用）
- Publication group: P1
- Evidence: 行为测试不依赖宿主；schema 无旧库迁移
- Target verification: `pytest .../test_sqlite_store.py`；并发 claim 测试
- Risk probes: `BEGIN IMMEDIATE` 竞争、busy_timeout、租约过期回收
- Review focus: 事务边界、fencing、prune 不删未完成任务
- Not in this slice: 内存实现/runner
- Rollback: revert；无生产数据
- Diff budget: ~500 行（接受为例外）

### S3 — 第二实现与契约测试

- Acceptance outcome: 同一契约测试在 SQLite 与 InMemory 上通过；接口不依赖 SQLite。
- Task IDs: T007, T008
- Expected paths: `.../stores/memory.py`、`tests/test_contract_store.py`（new）
- Trunk-safe: standalone
- Publication group: P1
- Evidence: 参数化测试覆盖两实现
- Target verification: `pytest .../test_contract_store.py`
- Risk probes: 两个实现的语义差异（排序、时间、租约）
- Review focus: 契约完整性；无 SQLite 类型泄漏
- Not in this slice: runner 行为
- Rollback: revert
- Diff budget: ~400 行

### S4 — Runner 核心

- Acceptance outcome: `run_once` 执行、租约心跳、fencing、重试/退避/终态、deadline/取消、崩溃恢复。
- Task IDs: T009, T010, T011
- Expected paths: `.../runner.py`、`tests/test_runner.py`、`test_lease_and_fencing.py`、`test_retry.py`（new）
- Trunk-safe: standalone
- Publication group: P1
- Evidence: 故障注入测试；fake clock
- Target verification: 上述 pytest 文件
- Risk probes: 硬退出、心跳失败、时钟跳变、异常分类
- Review focus: 不吞错、关闭/取消传播、attempts 语义
- Not in this slice: ZMQ/常驻 serve
- Rollback: revert
- Diff budget: ~600 行（接受为例外）

### S5 — 唤醒与常驻

- Acceptance outcome: ZMQ 唤醒 + 轮询兜底；`serve` 常驻、优雅关闭 ≤10s；丢消息/重复消息安全。
- Task IDs: T012, T013
- Expected paths: `.../notify/zmq.py`、`tests/test_zmq_integration.py`、`test_shutdown.py`（new）
- Trunk-safe: standalone
- Publication group: P1
- Evidence: 临时端口集成测试；双 worker 竞争
- Target verification: 上述 pytest 文件
- Risk probes: 无订阅者、慢消费者、socket 关闭、关闭中超时
- Review focus: 消息只带 ID；丢消息不导致滞留；关闭幂等
- Not in this slice: 宿主迁移
- Rollback: revert
- Diff budget: ~450 行（接受为例外）

### S6 — 宿主迁移与收口

- Acceptance outcome: `personal-assistant` 使用 `agent-work`，现有 60 用例全绿；文档/ADR/CI 收口；无旧库迁移。
- Task IDs: T014, T015, T016, T017
- Expected paths: `packages/apps/personal-assistant/{pyproject.toml,src/**,tests/**}`、`packages/infra/agent-work/README*`、`docs/architecture/package-boundaries.md`、`docs/decisions/agent/0015-*.md`、`examples/minimal_runner.py`
- Trunk-safe: standalone（行为等价由测试守卫；可 revert）
- Publication group: P1
- Evidence: 宿主回归 + 新包质量门 + docs/governance/static + CI 27 组合
- Target verification: `quality.ps1 -Package spawn-join-personal-assistant`、`-Package spawn-join-agent-work`、`-Check docs/governance/static`
- Risk probes: 行为等价、CLI `run` 兼容、`serve` 关闭
- Review focus: 迁移未改变业务语义；ADR-0015 所有权修订；README 完整
- Not in this slice: Postgres/MQ/Temporal/多租户
- Rollback: revert；无生产数据
- Diff budget: ~600 行（接受为例外）

## Coverage and validation

- **Task coverage**: T001–T017 全部映射且仅映射一次（S1:1–4, S2:5–6, S3:7–8, S4:9–11, S5:12–13, S6:14–17）。
- **Requirement coverage**: FR-001..FR-020 由 T005–T015 覆盖；SC-001..SC-008 由 T008/T010/T011/T013/T014/T017 与 CI 覆盖。
- **Classification coverage**: 所有切片为 standalone（加法式/可回滚）；无 flag/integration-only。
- **Behavioral probe coverage**: S2 claim 竞争；S4 硬退出/心跳；S5 丢消息/关闭；S6 宿主回归。
- **Dependency order**: S1→S2→S3→S4→S5→S6，无环。
- **Publication coverage**: S1–S6 → P1（唯一 layer group）；无 rollup。
- **Budget exceptions**: S1/S2/S4/S5/S6 预计超过 400 行，接受为实现/文档整体边界；理由见各切片。
- **Policy compatibility**: PR + 线性历史 + required `Quality Gate`；squash 合并；删除分支。
- **User authorization boundary**: slice approval 单独记录；publication 另行授权。
- **Open decisions**: 无；`waiting`、打包、唯一范围、保留期已在 Plan 固定。

## Merge and publication plan

- Execution order: S1 → S2 → S3 → S4 → S5 → S6（Ralph 普通 feature 分支）
- Ralph branch/topology: `ralph/agent-work-desktop-20261122`
- Per-slice merge: N/A（single 发布组）
- Publication groups: P1 = S1–S6 → `main`，一个 PR
- Final rollup: N/A
- Target sync: N/A
- Queue/freeze: no queue；最终 Review 前冻结发布
- Issue closure: N/A
- Rollback per slice: revert 对应提交；无生产数据/远端服务

## Approval record

- **SLICE_PLAN_VERDICT**: ready
- **SLICE_PLAN_FINGERPRINT**: sha256:1791583e7245b2444fc69b8abb49c7bc6cd412d9bec71ed036abf470b258c866
- **SLICE_APPROVAL**: approved
- **Approved by**: 仓库维护者（用户，2026-11-22）
- **Choice / accepted risks**: approve；接受 single 执行/发布、六个内部切片、S1/S2/S4/S5/S6 预算例外、不做旧库迁移
- **Approved execution mode**: single
- **Approved publication mode**: single
- **Approved publication groups**: P1（S1–S6）
- **Publication authorization**: pending（发布仍需单独授权）
- **Approved mode / snapshot**: execution=single；publication=single；group=P1；plan fingerprint `93e8f462…`；slices fingerprint `sha256:1791583e…`
- **Approved at**: 2026-11-22
