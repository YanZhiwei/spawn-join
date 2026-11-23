# Decision Context — agent-work desktop Phase 1

- **LANE**: feature
- **DELIVERY_RUN**: `agent-work-desktop-20261122`
- **DECISION_CONTEXT_PATH**: `.specify/delivery/agent-work-desktop-20261122/decision-context.md`
- **Baseline**: `5739be137b3a95caa7507f2db6f48e32fc6d5d57` (`main`, clean)
- **Mode**: pre-spec discovery（只带约束与术语，不选定设计）

## Active constraints

| ID | Source / authority | Constraint | Impact on this request |
|---|---|---|---|
| DC-01 | `AGENTS.md` §1.1–1.2；`docs/architecture/package-boundaries.md` | 新能力必须有真实复用理由；Python 源码在 Distribution `src/`；包拥有独立 `pyproject.toml`、`uv.lock`、`.venv`、`tests/`；依赖方向单向 | 新包必须满足 Distribution 全套边界，不能放在 app 内伪装复用 |
| DC-02 | Constitution III（`.specify/memory/constitution.md:47-54`） | 至少两处稳定、真实复用后才提升共享抽象；文本相似不算理由 | 当前真实消费者只有 `personal-assistant`；提取属于维护者前瞻决策，必须记录例外与迁移门槛 |
| DC-03 | ADR-0010（Accepted） | `spawn-join-agent-deepagents` 负责装配；不实现数据库、后台调度；Store/Checkpointer/资源由宿主创建和关闭 | work 生命周期不得放入 `agent-deepagents` |
| DC-04 | ADR-0015（Accepted） | `personal-assistant` 拥有 work 存储、due 调度、HITL 持久化；SQLite 单写者；记忆不在 v1 | 迁移后必须修订 ADR-0015 §Decision 第 1 条；不能静默替代 |
| DC-05 | ADR-0016（Proposed，已合并） | 拥有持久化状态、队列/后台执行、自身常驻进程的可复用包默认桌面可运行；契约可通过端口切换服务端存储/队列；SaaS 能力归宿主；服务端禁用 SQLite | 决定默认 SQLite + ZeroMQ、端口化与 SaaS 接缝 |
| DC-06 | `.specify/extensions/delivery/delivery-config.yml`；`quality-config.yml`；docs-sync 配置 | 每包独立锁文件、质量 Profile、CI 矩阵、双语 README；`package_readme: required`；`pr_slicing: auto` | 新包需同时新增 Profile、CI 矩阵、README、包边界文档 |
| DC-07 | `artifact_policy: ephemeral` | `specs/` 本地执行工件不进 Git；长期契约与证据必须在 ADR/架构/证据根 | 探索包与 Spec 留在 `.specify`/`specs` 本地；ADR 与最终 evidence 需持久化 |

## Superseded or historical context

- ADR-0015 Option 3 曾明确“当下不提取 `spawn-join-agent-work`”，保留为提取路径（`docs/decisions/agent/0015-personal-assistant-host-boundary.md:31`）。
- ADR-0016 现在记录“桌面优先、服务端可替换”的前瞻策略，但**不自动替代 ADR-0015**；在真正迁移前，ADR-0015 仍描述当前所有权。
- 现有实现来源：`personal-assistant` 的 WorkStore/Scheduler 由 PR #73（`be49da9`）引入；`agent-deepagents` 的委派/恢复由 PR #32（`78aa339`）引入。

## Conflicts

1. **所有权冲突（可解）**：ADR-0015 把 work store/due scheduler 归宿主；本 Feature 计划迁移到 `agent-work`。解决方式：迁移切片中同步修订 ADR-0015 §Decision 第 1 条；在此之前不宣称已迁移成功。
2. **复用门槛冲突（已记录例外）**：Constitution III 要求两个真实消费者；当前只有一个。ADR-0016 已记录维护者决策与第二消费者门槛；Plan 必须把“何时保留在宿主”写成明确条件。

## Open decisions the plan must resolve

- `waiting` 是否作为核心状态（runner 不 claim，宿主 `resume`）；
- `failed` 与 `dead` 的终态语义；
- `queue` 与 `namespace` 是否第一批进入 schema；
- payload 是否保持不透明 bytes；
- 桌面安装层：pyzmq 进 base 还是 `[desktop]` extra；
- 唯一任务范围、保留/归档策略；
- 迁移 `personal-assistant` 的数据目录与旧 `work.db` 兼容方式；
- 公共 API 的版本化与兼容承诺。

## Missing evidence

- 未做 SQLite claim 吞吐/锁竞争基准；结论只能支持“桌面规模”而非量化容量。
- `pyzmq` 27.3.0 为 BSD-3-Clause，已核实 wheel 覆盖 cp311/cp312-abi3/cp314t（manylinux/win_amd64）；`libzmq` 为 MPL-2.0，需在依赖评审中记录。
- 无 Postgres 适配器或生产负载证据；SaaS 结论仅为设计可行性，不是已实现能力。
- 未检索 GitHub Issues/PR 中与该包同名的历史讨论（仓库无 open issue）；外部参考以官方 README/文档为准。

## Terminology

| Term | Meaning in this request | Ambiguity / excluded meaning |
|---|---|---|
| WorkItem | 一条可持久化、可领取、可重试的工作单元 | 不是 LangGraph thread；thread 由 checkpointer 拥有 |
| WorkStore | 任务真相：状态机、原子 claim、租约、重试、保留 | 不是消息 broker |
| Notifier | 只发“有新任务/该重试”的唤醒信号 | 不承载任务正文，不是真相 |
| Lease | 带 owner/token/until 的领取租约 | 不是永久锁；过期可回收 |
| Fencing token | 防止旧 worker 写回的租约标识 | 不承诺 exactly-once 副作用 |
| Runner | claim → 执行 → 续租 → complete/fail/retry/defer | 不是调度中心；不解释业务语义 |
| Namespace | 预留的隔离维度（默认 `default`） | 第一批不实现租户/认证 |

## Pre-plan resolution

- **ADR 依赖已跟随**：ADR-0010（装配包不拥有 DB/后台调度）→ 新包独立；ADR-0015（宿主当前拥有
  work 存储/调度）→ 迁移时修订；ADR-0016（桌面优先/服务端可替换）→ 默认 SQLite+ZMQ、端口化。
- **与代码对照**：`config.py:64-68` 要求显式 `data_dir`；`scheduler.py:82-107` 单周期；
  `cli.py:302` 单次 `run_due`；`work/store.py:95-171` 单写者 SQLite；`agent-deepagents` 无存储。
- **冲突处理**：ADR-0015 所有权由 ADR-0018 设计覆盖，但迁移落地前不宣称完成；实施切片同步修订
  ADR-0015 §Decision 第 1 条。Constitution III 单消费者例外已在 ADR-0016 记录，本 Plan 不扩大。
- **Plan 已定的开放项**：`waiting` 为显式状态且 runner 不自动领取；`failed`（不可重试）与
  `dead`（重试耗尽）分开；`queue`+`namespace` 第一批进 schema；payload 为不透明 bytes；pyzmq
  进基础依赖；唯一范围 `namespace+queue+kind+idempotency_key`；保留默认 30 天；旧库先备份。
- **新增 Proposed ADR**：`docs/decisions/engineering/0018-agent-work-package-boundary.md`。
- **2026-11-22 用户决定（范围收紧）**：产品尚未上线，`personal-assistant` **不需要旧库迁移**。
  Spec/Plan/Data Model/ADR-0018 已改为“首次启动直接创建当前 schema”；已批准的 exploration
  packet 保持原字节（历史快照），差异由本记录与重新呈现的 Plan gate 承载。
- **仍缺证据**：SQLite 轻量基准、pyzmq 桌面打包体积、Postgres 可行性；由 Tasks/后续切片验证。
