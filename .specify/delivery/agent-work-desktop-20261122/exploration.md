# Exploration and scope packet — agent-work 桌面档 Phase 1

## Request and investigation

- **Request and desired outcome**: 把 `personal-assistant` 内的长任务生命周期（工作项存储、due 调度、
  重试、恢复）提取为可复用的运行时包，先满足桌面单用户形态，同时定义可替换接口，供后续 SaaS
  档接入 Postgres/MQ 时复用。
- **Delivery run / canonical packet path**:
  `agent-work-desktop-20261122` / `.specify/delivery/agent-work-desktop-20261122/exploration.md`
- **Feature location / Bug slug**: 尚未创建；由后续 specify 生成真实路径，本包不预造 `specs/` 目录。
- **Investigation**: new capability（新 Distribution + 现有宿主迁移）。
- **Provisional lane / recommended lane**: Feature。理由：新包、跨包依赖、持久化数据、公共契约、
  架构决策与 CI/质量边界变化。
- **Baseline HEAD / relevant working-tree changes**:
  `5739be137b3a95caa7507f2db6f48e32fc6d5d57`；工作区干净。
- **Governing instructions / ADRs**: `AGENTS.md`、Constitution（尤其 III/IV/V）、
  `docs/architecture/package-boundaries.md`、ADR-0010、ADR-0015、ADR-0016、`delivery-config.yml`、
  `quality-config.yml`、docs-sync 配置。
- **Tools / fallback / freshness limitations**: CodeGraph（232 files / 3,961 nodes，索引可用）、
  直接源码阅读、`git log`、GitHub/PyPI 官方 README 与文档。未做运行时压测；未检索 GitHub Issues
  历史（仓库无 open issue）。

### Outcome and problem framing

**目标**：长任务在桌面环境可持久化、跨重启恢复、失败可重试、可观测，且实现可被后续 app 复用。

**不是目标**：多租户 SaaS 实现、Web UI、MCP Server、远程沙箱、记忆能力、Temporal 平台接入。

**已由用户在本轮明确的设计决定**：

1. 包名为 `spawn-join-agent-work`（单数），独立 infra Distribution；
2. 桌面档默认 **SQLite + ZeroMQ**（保留 ZMQ，不改成纯进程内）；ZeroMQ 只做唤醒；
3. SaaS 档后续使用 **Postgres + `LISTEN/NOTIFY` 或 MQ**；Phase 1 不实现；
4. Phase 1 只做桌面闭环 + 可替换接口；Postgres/MQ/Temporal 留到后续；
5. 用 `InMemoryWorkStore` 作为第二个实现，验证接口不是 SQLite 专属；
6. 持久化采用 store-first：消息丢失由轮询兜底；at-least-once + 幂等。

**成功条件**：迁移后 `personal-assistant` 行为等价、现有测试全绿；契约测试同时覆盖 SQLite 与
InMemory；ZMQ 丢消息/重复消息/崩溃恢复有测试；新包进入 CI 与质量门。

## Concepts, boundaries, and research questions

| Term | Meaning in this request | Ambiguity or excluded meaning |
|---|---|---|
| WorkItem | 可持久化、可领取、可重试的工作单元 | 不是 LangGraph thread；thread 由 checkpointer 管理 |
| WorkStore | 任务真相：状态机、原子 claim、租约、重试、保留 | 不是 broker；不负责进程调度之外的生命周期 |
| Notifier | 只发“有新任务/该重试”的唤醒信号 | payload 只带 `work_id`/queue，不带业务正文 |
| Lease / fencing | `owner + token + until`；旧 token 写回被拒 | 不承诺 exactly-once 副作用 |
| Namespace | 预留隔离维度，默认 `default` | Phase 1 不实现租户/认证 |
| `waiting` | 等外部决定（审批/依赖）的状态 | runner 不 claim；宿主 `resume` 回 `queued` |
| `dead` | 重试耗尽/终止后的终态 | 区别于不可重试的 `failed`；命名映射在 Plan 记录 |

- **Domain boundary**: `agent-work` 拥有任务生命周期与存储/唤醒适配器；`agent-deepagents` 继续只做
  图装配；`personal-assistant` 拥有产品语义（goal、审批、输出）。三者不互相反向依赖。

| Question / decision affected | Evidence and source identity | Conclusion / conflicting evidence | Remaining gap, impact, and next owner |
|---|---|---|---|
| 是否可以把 work 放进 `agent-deepagents`？ | ADR-0010；`agent-deepagents/README.md:680-681`；`recovery.py:1-6` | 否。该包明确不实现数据库/后台调度，资源由宿主拥有 | 无；Plan 保持 |
| 是否保留 SQLite 作为桌面默认？ | `personal-assistant/README.md:929-930`；`scheduler.py:82-107`；ADR-0016 | 是。单写者限制只影响多进程/多机，桌面单用户可接受 | 未压测；Plan 记录容量假设 |
| ZeroMQ 是否是正确性必需？ | GoodJob `LISTEN/NOTIFY` + polling；ZeroMQ 无持久化/ack | 不是。ZMQ 仅降低唤醒延迟；轮询兜底；用户已决定保留 ZMQ | 需在测试中证明丢消息不影响正确性 |
| 是否现在实现 Postgres/MQ？ | ADR-0016；Constitution III；Oban/GoodJob/Que | 否。Phase 1 只做桌面；SaaS 适配器后续 | 无；属于排除范围 |
| 现有调度是否满足长任务？ | `cli.py:302` 单次 `run_due`；`scheduler.py:69-80` | 否。无常驻循环、无租约/心跳、无退避重试 | Phase 1 补 runner |
| 接口如何避免 SQLite 专属？ | `execution.py:133-142` 的资源绑定教训；Constitution IV | 端口 + `InMemoryWorkStore` 契约测试；SQL 子集与 Clock 注入 | 需在 Plan 定义具体签名 |

## Findings

- **Facts**:
  - `personal-assistant` 已有 `WorkStore`（SQLite）与 `Scheduler`（单周期 due、deadline、重启重排队）；
  - `agent-deepagents` 已提供 `SupervisorSpec`、委派控制、checkpointer 透传与诊断，但不拥有存储；
  - 仓库质量门要求每个 Distribution 有独立锁文件、Profile、CI 矩阵、双语 README；
  - ADR-0016 已合并，明确桌面优先/服务端可替换与 `namespace` 接缝；
  - `pyzmq` 27.3.0 为 BSD-3-Clause，wheel 覆盖 cp311/cp312-abi3/cp314t（manylinux/win_amd64）。
- **Hypotheses**:
  - 桌面单用户的任务速率远低于 SQLite 写瓶颈；需要压测确认；
  - ZMQ 的 PUB/SUB 丢消息不会影响正确性，前提是轮询间隔与 claim 语义正确。
- **Recommendations**: 按“新包 + 桌面默认适配器 + 第二实现契约测试”推进；Phase 1 不引入 Postgres/MQ。
- **Unknowns**: SQLite claim 吞吐；pyzmq 在目标桌面平台的打包体积/启动成本；旧 `work.db` 迁移策略。

## Current directory tree

```text
D:\Repos\spawn-join\
├── packages/apps/personal-assistant/
│   ├── pyproject.toml                         # 当前第 8 个 Distribution；独立锁/测试
│   ├── src/spawn_join_personal_assistant/
│   │   ├── config.py                          # data_dir/并发/deadline 校验
│   │   ├── host.py                            # supervisor + SQLite checkpointer 装配
│   │   ├── scheduler.py                       # 单周期 due、deadline、重启重排队
│   │   ├── cli.py                             # accept/due/run/report/approve；run=单周期
│   │   └── work/store.py                      # SQLite WorkStore/状态机/幂等键
│   └── tests/                                 # 60 用例（工作项/调度/审批/e2e）
├── packages/infra/agent-deepagents/
│   ├── src/spawn_join_agent_deepagents/
│   │   ├── supervisor.py                      # build_supervisor；store/memory 接缝
│   │   ├── execution.py                       # 进程内委派并发/队列/期限
│   │   ├── recovery.py                        # checkpointer 校验/thread 身份
│   │   └── subagents.py                       # 声明/编译/远程异步子代理
│   └── tests/
├── .specify/extensions/quality/quality-config.yml   # 包 Profile 与治理 Profile
├── .github/workflows/quality.yml                    # 8 包 × 3 组合矩阵
├── docs/architecture/package-boundaries.md          # 包职责/依赖方向
├── docs/decisions/agent/0010-deepagents-product-boundary.md
├── docs/decisions/agent/0015-personal-assistant-host-boundary.md
└── docs/decisions/engineering/0016-desktop-first-service-ready-packages.md
```

## Current flow

```text
CLI run (cli.py:268)
  → WorkStore(data_dir/work.db) + ApprovalBook
  → Scheduler(max_concurrency, deadline).recover_interrupted()
  → Scheduler.run_due(execute)            # 只跑一个周期
      → mark RUNNING (attempts+1)
      → executor = drive_to_outcome
          → open_host_session → build_supervisor → graph.ainvoke
      → complete/fail + deadline
  → CLI 退出
```

缺口：无常驻循环、无租约/心跳、失败无退避重试、无跨进程 worker、无保留/清理。

## Project history and external references

| Source / repository | Issue / PR / commit / version | Read paths and evidence | Relevance / adopted idea | Rejected parts / constraints / scope impact |
|---|---|---|---|---|
| 本项目：宿主应用 | PR #73 `be49da9` | `scheduler.py`、`work/store.py`、`cli.py` | 迁移基线与行为等价回归 | 不保留单周期/无重试限制 |
| 本项目：DeepAgents 委派/恢复 | PR #32 `78aa339` | `execution.py`、`recovery.py` | 并发/期限/checkpointer 透传语义 | 不把其内存队列当持久任务队列 |
| 本项目：ADR-0016 | PR #82 `5739be1` | ADR 全文 | 桌面默认/服务端可替换/namespace | 不在本 Feature 实现 SaaS 适配器 |
| Oban | Apache-2.0；README main | DB 真相、事务内入队、唯一任务、优先级、优雅关闭、保留历史 | 采纳语义 | 不采纳 Elixir/进程隔离模型 |
| GoodJob | README main | Postgres advisory locks、`SKIP LOCKED`、`LISTEN/NOTIFY`、`poll_interval`、重试 | 采纳“DB 真相 + 通知 + 轮询” | 不引入 Rails 依赖 |
| Que | README master | advisory locks、ACID、多 worker | 采纳 claim 语义 | Ruby 专属实现不复制 |
| pgmq | README main | visibility timeout、archive/retention | 参考租约/归档 | 不作为 Phase 1 依赖 |
| Temporal | README main；官方文档 | durable execution、Activity 重试/心跳、Task Queue | 参考失败语义 | 平台依赖过重，Phase 1 不采用 |
| Celery | 文档 | `acks_late`、visibility timeout、`retry_backoff` | 参考 at-least-once/退避 | broker 耦合；不采用 |
| LangGraph persistence | 官方文档 | checkpointer/store；checkpoint 增长需 prune | 采纳恢复与保留提醒 | 不把 store 当任务队列 |
| ZeroMQ | 官方指南/模式 | PUB/SUB、Paranoid Pirate/Majordomo 存活模式 | 采纳“唤醒 + 心跳”模式 | 不用 ZMQ 承载任务真相 |

- **Search coverage**: `codegraph_explore`（SupervisorSpec、DelegationPolicy、AsyncSubAgent）、
  `git log`（execution/recovery、scheduler/store）、PyPI 元数据（pyzmq/psycopg）、官方 README。
- **External research**: performed（有界）。
- **Evidence gaps**: SQLite 压测、桌面打包体积、旧数据库迁移；由 Plan/Tasks 安排验证。

## Options and candidate change tree

| Option | Description | Verdict |
|---|---|---|
| A. 新建 `spawn-join-agent-work`，桌面默认 SQLite+ZMQ | 契约/适配器分离；迁移宿主；InMemory 第二实现 | **推荐**：满足复用与双档位，不违反 ADR-0010 |
| B. 放进 `agent-deepagents` | 新 app 直接复用 | 拒绝：ADR-0010 明确排除 DB/后台调度；存储契约会污染装配包 |
| C. 保留在 `personal-assistant`，只抽端口 | 改动最小 | 拒绝：不满足“后续 app 复用”；app 继续拥有 infra 能力 |
| D. 新包同时实现 Postgres/MQ | 一步到位 | 拒绝：无真实 SaaS 需求/环境，违反 YAGNI；Phase 1 只做桌面 |
| E. 直接用 Temporal/Celery | 成熟 | 拒绝：引擎/平台级替换，桌面过重；Phase 1 不采用 |

```text
D:\Repos\spawn-join\
├── packages/infra/agent-work/                         [new] 第 9 个 Distribution
│   ├── pyproject.toml                                  [new] 依赖 pyzmq；dev group pytest
│   ├── uv.lock                                         [new] 独立锁
│   ├── src/spawn_join_agent_work/
│   │   ├── __init__.py                                 [new] 显式公共导出
│   │   ├── models.py                                   [new] WorkSpec/WorkItem/WorkState/WorkResult
│   │   ├── policies.py                                 [new] RetryPolicy/LeasePolicy/ConcurrencyPolicy
│   │   ├── protocols.py                                [new] WorkStore/Notifier/Clock/WorkExecutor
│   │   ├── runner.py                                   [new] claim→execute→heartbeat→finalize
│   │   ├── errors.py                                   [new] 稳定异常语义
│   │   ├── stores/sqlite.py                            [new] 默认存储（WAL/claim/租约/保留）
│   │   ├── stores/memory.py                            [new] 第二实现（测试/示例）
│   │   └── notify/zmq.py                               [new] 默认唤醒（PUB/SUB）
│   ├── tests/                                          [new] 契约/runner/崩溃/ZMQ 集成
│   └── examples/                                       [new] 最小可运行示例
├── packages/apps/personal-assistant/
│   ├── pyproject.toml                                  [modify] 依赖 agent-work
│   ├── src/.../scheduler.py                            [modify] 适配 WorkRunner 或保留薄封装
│   ├── src/.../work/store.py                           [modify] 迁移/兼容旧数据
│   ├── src/.../cli.py                                  [modify] 新增常驻 serve；run 保持兼容
│   └── tests/                                          [modify] 行为等价回归
├── .specify/extensions/quality/quality-config.yml       [modify] 新包 Profile
├── .github/workflows/quality.yml                        [modify] 9 包矩阵（27 组合）
├── README.md / README.en.md                             [modify] 包表 8→9
├── docs/architecture/package-boundaries.md              [modify] agent-work 职责/依赖
├── docs/architecture/repository-map.md                  [modify] apps/infra 树
├── docs/development/quality-gates.md                    [modify] 8→9、24→27、Profile 计数
├── AGENTS.md                                            [modify] 配置基线 8→9
├── docs/decisions/agent/0015-...                        [modify] 迁移时修订 work 所有权
└── docs/decisions/engineering/0016-...                  [modify] 收口时 Proposed→Accepted
```

## Scope, risks, and verification

- **Included**: 新包与桌面默认适配器；`InMemoryWorkStore`；`WorkRunner`；ZMQ notifier；迁移
  `personal-assistant`；包文档/质量 Profile/CI 矩阵/架构与计数同步；ADR-0015 迁移修订、ADR-0016 收口。
- **Excluded**: Postgres/MQ/Temporal 适配器；多租户/认证/配额；Web UI；MCP Server；远程沙箱；
  记忆能力；保留归档分级（仅基础 prune）。
- **Interfaces / compatibility / migration**: 公共契约新增；`personal-assistant` 行为保持等价；
  旧 `work.db` 需兼容读取或显式迁移；数据目录默认值变化需保留显式配置；服务端禁用 SQLite。
- **Verification（计划，尚未执行）**:
  - `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-work`
  - `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-personal-assistant`
  - `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` / `-Check governance` / `-Check static`
  - 契约测试：SQLite + InMemory；ZMQ 集成（双 worker、丢消息、重复消息）；崩溃/租约/fencing/退避/关闭
  - CI：9 × 3 = 27 组合 + Governance + Quality Gate
- **Verification limits**: SQLite 容量/吞吐未压测；pyzmq 桌面打包体积未测；Postgres 可行性未验证。
- **Decision blockers / questions**: 无 scope 级阻塞；`waiting`、`queue/namespace`、打包 extras、
  唯一范围、保留策略属于 Plan 决策，不阻止 scope 讨论。

## Checkpoint record

- **EXPLORATION_VERDICT**: ready
- **Evidence location**: `.specify/delivery/agent-work-desktop-20261122/exploration.md`
- **SCOPE_APPROVAL**: pending

## Phase handoff

- **Receiving owner**: `speckit.specify`（scope 批准后）。
- **Required reading**:
  - 本包 `Findings`、`Options`、`Scope`、`Phase handoff`；
  - `.specify/delivery/agent-work-desktop-20261122/decision-context.md`（DC-01..DC-07）；
  - `docs/decisions/engineering/0016-desktop-first-service-ready-packages.md`（Proposed，约束）；
  - `docs/decisions/agent/0015-personal-assistant-host-boundary.md`（迁移时修订所有权）；
  - `docs/decisions/agent/0010-deepagents-product-boundary.md`（不把 DB/调度放进装配包）；
  - `AGENTS.md` §1.1–1.2、`docs/architecture/package-boundaries.md`。
- **Input identity**: run `agent-work-desktop-20261122`；baseline `5739be1`；工作区干净；
  scope approval 尚未记录。
- **Expected return**: `specs/<feature-id>/spec.md` + `FEATURE_DIR:` 绑定；范围若 materially 扩大
  （例如 Phase 1 引入 Postgres/MQ），回到 scope gate。
- **Explicit limitations**: SQLite 压测、桌面打包体积、旧数据库迁移未验证；Plan/Tasks 必须安排。
