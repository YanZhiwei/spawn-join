## 摘要

- 解决的问题：SpawnJoin 缺少个人助理型 agent 的"work 机制与受控执行"——现有装配包刻意排除持久任务队列与沙箱（ADR-0010 触发条件命中）。
- 合并后的行为或契约：新增第 8 个 Distribution `spawn-join-personal-assistant`（`packages/apps/`），提供 sqlite3 工作项状态机（幂等键）、asyncio due 调度（并发/deadline/取消/中断重入队）、受限工作区装配（virtual-mode 守卫 + 权限门禁 + strict msgpack checkpointer）、HITL 审批持久化（对齐恢复命令）与五子命令 CLI；记忆 v1 排除（接缝留位，ADR-0015）。
- 本次不包含：多租户/授权/计费、IM 通道、Web UI、MCP Server、容器/远程沙箱、Postgres 部署实现、embeddings/记忆（ADR-0015 记录迁移接缝）。

## 关联问题与变更类型

无关联 Issue。

- [x] 新功能或新组件
- [ ] Bugfix 或契约修正
- [ ] 重构或简化
- [x] 文档或治理
- [ ] 发布准备

## 变更内容

| 位置 | 变更 | 原因 |
| --- | --- | --- |
| `packages/apps/personal-assistant/`（新） | 第 8 个 Distribution：config/errors/work/scheduler/approvals/host/cli + 60 离线测试 + 示例 | 个人助理宿主应用（ADR-0015） |
| `.specify/extensions/quality/quality-config.yml` | 新 profile `spawn-join-personal-assistant` | `unprofiled_changed_paths: block` 的解除 |
| `scripts/quality.ps1` | ValidateSet + 包枚举 + Build 链加入新包 | 质量门覆盖新 Distribution |
| `docs/decisions/agent/0015-*.md`（新）+ `docs/decisions/README.md` 索引行 | ADR-0015 Proposed→Accepted | 宿主边界/持久化基线/记忆留位/迁移接缝的长期决策 |
| `docs/architecture/{repository-map,package-boundaries}.md` | apps 分组/依赖方向/uv 表新增行 | 治理同步义务 |
| 根 `README.md`/`README.en.md` | 包选择表各加一行 | 包选择导航 |

## 验证

| 场景或检查 | 实际结果 | 证据 |
| --- | --- | --- |
| 全仓质量门（8 包：lock/sync/Black/isort/Ruff/Pyright strict/pytest/6 包构建+隔离安装+导入） | 全部退出 0，60 测试通过 | run `runtime/checks/outgoing-quality-gate.txt` |
| 门禁回归（15 故障注入场景） | 全部 PASS，无根级产物残留 | run `runtime/checks/outgoing-gate-regression.txt` |
| e2e：accept→run→report 完成闭环（fake model） | 摘要可见 | `tests/test_e2e_offline.py::test_us1_*` |
| e2e：幂等重放 | 第二次 accept exit 1，计数不变 | `test_us1_idempotency_replay_leaves_one_item` |
| e2e：硬杀恢复 | requeued 恰好一次，attempts=2，重跑一次 | `test_us2_interrupted_run_recovered_exactly_once` |
| e2e：批准执行/拒绝不执行 | 批准后 notes.txt 真实写入；拒绝后无文件且 failed(rejected) | `test_us3_approve_*` / `test_us3_reject_*` |
| e2e：越界写守卫 | `../../escape.txt` 即使批准也被拦截，无工作区外副作用 | `test_us1_escape_write_is_confined_even_when_approved` |
| 离线示例完整闭环 | accept→run 暂停→approve→report→`notes.txt exists: True` | `examples/offline_run.py` 实际运行输出 |
| docs/governance 检查 | 退出 0 | run `runtime/checks/T007-docs.txt` / `T007-governance.txt` |

- 未执行或未覆盖的验证及原因：真实 Provider 网络路径（离线边界，ADR-0008 语义内）；`test-governance.ps1` 未单独执行（治理检查已在全门内通过）；accepted-self-review（用户已在最终 review gate 明确接受）。

## 影响（仅填写适用项）

| 维度 | 影响 | 证据 |
| --- | --- | --- |
| 公共 API、命令、配置 | 新增 console 入口 `spawn-join-personal-assistant` 与 21 项显式导出；现有七包公共 API 零改动 | `__init__.py` `__all__`；全仓质量门七包全绿 |
| 持久化、迁移或数据兼容 | 新增宿主持久化（work.db/approvals.db/threads.db），无迁移（全新目录） | ADR-0015 持久化基线 |
| 安全、权限或敏感信息 | 凭据仅 `LLM_API_KEY` 环境变量；strict msgpack 反序列化白名单；工作区路径守卫 e2e 证实 | `test_us1_escape_*`；saver 断言 |
| 性能、资源或可观测性 | 单进程 asyncio 调度、并发上限可配；aiosqlite 连接宿主拥有幂等关闭 | scheduler/host |
| 依赖、供应链或发布 | 新增第三方仅 `langgraph-checkpoint-sqlite>=3.1.3,<4`（MIT）；独立 uv project/lock | pyproject/uv.lock |

## 审查身份

- `base_revision`：`4f5b79c734e027ecbad3c2d999819d529958c80e`（main）
- `reviewed_head`：`f14b14858714032c2804dc2fc139a338de42dfaa`
- `content_fingerprint`：spec `a689e889…` / plan `4ed9b339…` / slices 呈现 `e1f4311d…`（scope/design/execution 三门哈希验证批准）
- `requirements_fingerprint`：spec SHA-256 `a689e889f1367e5cb470810cbf0870ae0ccce1ca1aa3df81e243d45d458c76f6`
- native Review report / receipt：`.specify/delivery/personal-assistant-20261121/runtime/review-report-outgoing-refresh.md`（ticket `c9d77656…`）
- 发布后的 `original_pr_head` / `published_head`：待发布或实际值

## 本地 AI Code Review 与修复历程

| 轮次 | 工具 / 方法 | 审查版本或范围 | 主要发现与状态 | 修复 / 复审结论 |
| --- | --- | --- | --- | --- |
| 7×任务级 | 六维 Review（accepted-self-review） | T001–T007 各 pre-commit 快照 | 各轮零阻断发现 | 各任务 task-gate PASS 后单任务提交 |
| 集成轮 | 六维 Review（outgoing-diff） | `ff33326` 全 diff | 零发现 | PASS |
| 集成轮刷新 | 六维 Review（outgoing-diff） | `f14b148`（ADR 接受后） | 零发现（delta 仅两个治理文档） | PASS；require review ready |

- 最终 AI 审查结论：`REVIEW_VERDICT: pass`（六维全过，零 findings）
- 未解决问题与剩余风险：真实 Provider 网络路径未测（离线边界）；accepted-self-review 降级已由用户在最终 review gate（Q8）明确接受
- 本地报告或证据：run `runtime/review-report-outgoing-refresh.md` + native receipts
- [ ] 未执行本地 AI Code Review（请说明原因）
- [x] 已执行；实现者已处理或明确记录每个问题，最终代码已重新审查

## 评审重点

- 入口或建议阅读顺序：ADR-0015 → 包 README → `host.py`（装配与守卫）→ `scheduler.py`（调度语义）→ `approvals.py`（审批簿记）→ `cli.py`（`_drive_to_outcome` 单一执行尾巴）→ `tests/test_e2e_offline.py`
- 关键行为、边界或设计取舍：单写者假设（一数据目录一进程）；astream 必须完整消费后才可 resume（提前 break 破坏 checkpoint——T005 探针实证）；deepagents write_file 参数名为 `file_path`（同前实证）；`RUNNING→QUEUED` 恢复边为中断重跑而设
- 需要人工或特定环境验证：连接真实模型服务的 `run` 路径（需 model.yaml + LLM_API_KEY）

## 条件章节

### 架构、设计或 ADR

- 当前设计、入口、归属与依赖方向：`apps → infra → core` 单向；`spawn-join-personal-assistant` → {agent-deepagents, llm-provider-langchain, langgraph-checkpoint-sqlite}
- 设计变化与原因：ADR-0010 排除项获得归宿（预期演进，非契约冲突）
- ADR / 决策链接：[ADR-0015](docs/decisions/agent/0015-personal-assistant-host-boundary.md)（Accepted，记录已审阅 HEAD）
- 设计图或接口说明：ADR-0015 内嵌数据流文字图

### Slice / Stack

- Slice 与目标：S1 脚手架/治理 → S2 存储/装配 → S3 调度/审批 → S4 CLI/e2e → S5 文档收口
- Base 分支、依赖及合并顺序：单发布组 P1，普通 Ralph 分支 → `main` squash
- 本层不包含：记忆、多租户、IM 通道、容器沙箱、Postgres 实现
- 本层回滚：revert 整个 squash 合并提交（新路径纯增量，无状态迁移）

## 回滚

revert squash 合并提交即可（全部路径为新增或追加式文档行；无数据迁移；SQLite 文件为运行期产物不入库）。

## 提交前确认

- [x] 我理解并能解释本次提交的变更。
- [x] 验证结果来自实际执行；未执行项、环境限制和剩余风险已明确标出。
- [x] 本次实际 diff 与 `reviewed_head` / 审查范围一致。
- [x] 阻断性 Review 问题已解决，或已记录明确的 owner 与处理决定。
- [x] 关联 ADR、文档、迁移和兼容性说明与最终代码一致。
