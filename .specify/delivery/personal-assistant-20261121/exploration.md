# Exploration and scope packet — personal-assistant-20261121

> 修订记录：
> - 2026-11-21 第一版呈现（hash `ead5697f…`）拒绝：调整点=记忆考虑 langmem + 生产部署考量 → 补验 langmem/langGraph store 生态后出第二版。
> - 2026-11-21 第二版呈现（hash `26e3aae8…`，含 langmem+自建 SQLite store）拒绝：用户决定**记忆先不做、后续讨论**（Q2' 选"仅工作区文件"语义合并为：v1 不做任何记忆开发）→ 出第三版。两次 `scope: reject` 均已记录 runtime。
> - 本第三版：范围**收窄**——移除记忆模块（langmem、自建 BaseStore、embeddings、记忆文件开发），保留工作项/调度/审批/checkpointer/CLI；langmem 调研结论保留在参照表中供后续讨论复用。

## Request and investigation

- Request and desired outcome: 在 SpawnJoin 之上构建**个人助理型 agent（personal assistant）**——接活、跨会话持久推进、受控执行、审批暂停/恢复、完成汇报。**记忆（langmem/BaseStore/嵌入/记忆文件开发）v1 不做，后续单独讨论**（用户 2026-11-21 决定）。
- Delivery run / canonical packet path: `personal-assistant-20261121` / `.specify/delivery/personal-assistant-20261121/exploration.md`
- Feature location / Bug slug: 尚未创建；由 Specify 创建，不预造路径。
- Investigation: **new capability**。
- Provisional lane / recommended lane: feature / **feature**。
- Baseline HEAD / relevant working-tree changes: `4f5b79c`（main，干净）。本 run 只在本地忽略的 `.specify/delivery/personal-assistant-20261121/` 写运行记录。
- Governing instructions / ADRs: AGENTS.md、Constitution v1.0.0、ADR-0006/0008/0009/0010/0011/0012/0013/0014、`package-boundaries.md`、`quality-config.yml`（`unprofiled_changed_paths: block`）。
- Tools / fallback / freshness limitations: 直接读取源码并引用行号（supervisor.py / execution.py / backends.py）；CodeGraph 本轮未调用；webfetch 于 2026-11-21 验证：OpenClaw（README + sandboxing docs）、Khoj、Letta、langmem（GitHub + PyPI 0.0.30）、langgraph-checkpoint-sqlite（PyPI 3.1.3 + reference.langchain.com）；Delivery runtime 以 CPython 3.13.5（uv 管理）执行。

### Outcome and problem framing

- 期望结果（desired outcome）：最小可用闭环——**接活 → 调度执行 → （审批暂停/恢复）→ 完成落库并汇报 → 重启后可继续**；记忆留接缝、不做实现。
- 可检查的成功条件：
  1. 离线端到端测试（fake model）：录入工作项 → 调度执行 → 触发审批 → 批准后 resume → 状态机走到 `completed`；
  2. 模拟重启后，未完成工作项可再调度（幂等键防重复），thread 状态经 SQLite checkpointer 恢复；
  3. agent 文件副作用限制在配置的工作区根内，越界写被 deny/interrupt（用户已选：工作区+权限门禁）。
- 既有约束：ADR-0010 禁止把 work/sandbox/数据库塞进 `agent-deepagents`；ADR-0008 凭据边界；Constitution V 推测性机制需用户同意（已通过 Q2/Q3/Q4 决策落地）。
- 形态说明：随记忆移出，Q1'（SQLite vs Postgres-first）只剩唯一合理解——**单用户本地 + SQLite + 可迁移接缝**（Postgres-first 的动机本是记忆 store 复用）。若用户仍要 v1 即 Postgres 服务形态，请在门上拒绝并说明。

## Concepts, boundaries, and research questions

| Term | Meaning in this request / authoritative source | Ambiguity or excluded meaning |
| --- | --- | --- |
| work item（工作项） | 持久化、可恢复、可重试的执行单元（状态机） | ≠ 委派（DelegationController，进程内）；≠ thread 状态 |
| workspace（工作区） | DeepAgents Backend 虚拟文件根 | 不是安全隔离边界 |
| sandbox（沙箱） | 隔离工具执行的后端；OpenClaw：控制面留宿主、仅工具执行进沙箱 | 本仓库仅 `backend_kind` 分类（backends.py:22-41） |
| 记忆（memory） | **v1 排除**；`SupervisorSpec.store`/`memory` 透传接缝保留并写入 ADR，langmem 调研结论留档 | 不在本次 Feature 内做任何实现/工具/存储开发 |
| BaseStore / BaseCheckpointSaver | LangGraph 抽象；v1 只用 checkpointer（SQLite），store 不使用 | 官方无 SQLite store（已核实）——后续记忆讨论时再议 |
| personal assistant（个人助理） | 组合层宿主应用 | 不是新模型协议/新 agent 框架 |

- Domain boundary: 包含——work 存储（stdlib `sqlite3`）、调度循环、装配接线、审批持久化、CLI、生产迁移接缝文档。**不包含（v1）**——记忆任何形式的开发。不改——`agent-deepagents` 公共契约。Non-goals（v1）——多租户、IM 通道、Web UI、MCP Server、容器沙箱、cron 语法、embeddings、langmem。

| Question / decision affected | Evidence and source identity | Conclusion / conflicting evidence | Remaining gap, impact, and next owner |
| --- | --- | --- | --- |
| work/sandbox 拥有者？ | ADR-0010:34/47-48/173 + 触发条件 180-181 | 不能进 `agent-deepagents`；归宿主 Distribution | 已由选项比较回答 |
| 跨重启 thread 恢复？ | langgraph-checkpoint-sqlite PyPI 3.1.3（2026-10-30，MIT，Trusted Publishing） | 用户已选：引入；strict msgpack 反序列化白名单默认启用 | 无——已定 |
| 记忆方案？ | langmem GitHub+PyPI（0.0.30，2025-10-27，约 13 个月无新版）；官方无 SQLite BaseStore（reference 页核实）；接缝：SupervisorSpec.store/tools 透传（supervisor.py:117-124） | **用户决定：v1 不做，后续讨论**。调研证据已在参照表留档，后续讨论不需重做研究 | 后续记忆讨论（候选独立 Feature） |
| 成熟项目划分？ | OpenClaw sandboxing docs；Khoj README；Letta README | 可信控制面+不可信执行面；沙箱默认关、后端可插拔；"work"参照=scheduled automations | 已验证 |
| 生产部署路径？ | langgraph-checkpoint-sqlite（轻量部署面） | v1=SQLite；checkpointer 可换 Postgres 实现；work 表迁移策略写 ADR；记忆接缝留位 | 无阻断——随记忆移出，Postgres-first 无 v1 用例 |

## Findings

- **Facts**：
  - `SupervisorSpec.store/checkpointer/tools/permissions/interrupt_on` 均为宿主注入点（supervisor.py:117-124）——装配包零改动即可满足本 Feature；
  - 委派控制器是进程内并发闸而非工作项系统（execution.py:76-142）；
  - 官方 `backend_kind` 分类无任何沙箱实现（backends.py:22-41）；
  - langgraph-checkpoint-sqlite 3.1.3：`SqliteSaver`/`AsyncSqliteSaver`，活跃维护，含 `LANGGRAPH_STRICT_MSGPACK` 安全开关；**仅 checkpointer，无 store**；
  - langmem 证据（留档备后续讨论）：MIT、LangChain 官方、原生 BaseStore、生产=AsyncPostgresStore（README 原文）；0.0.30（2025-10-27）后约 13 个月无新版、pre-1.0、与 langgraph 1.x 兼容性未验证。
- **Hypotheses**：OpenClaw 姿态（默认宿主执行+策略先行）适用于 v1 沙箱级别；stdlib `sqlite3` 单写者串行化足够 v1 work 存储。
- **Recommendations**：选项 A 第三版（无记忆）。
- **Unknowns**：无阻断 scope 的未决项；记忆方案留待用户后续讨论。

## Current directory tree

```text
spawn-join/  @ 4f5b79c（只列相关区域）
├── packages/core/{spawn-join-core,common,llm-provider}/   # 协议/契约层 [复用，不改]
├── packages/infra/llm-provider-langchain/                 # ModelCatalog + 凭据边界 [复用]
├── packages/infra/llm-channel/                            # 模型 Provider transport [不改]
├── packages/infra/llm-model-sync/                         # 手动同步，无调度 [不改]
├── packages/infra/agent-deepagents/                      # 装配层 [复用，不改公共 API]
│   ├── src/.../supervisor.py                             #   store/tools/checkpointer 透传 :117-124
│   ├── src/.../execution.py                              #   委派=进程内并发闸（非工作项）:76-142
│   └── src/.../backends.py                               #   backend_kind 仅分类 :22-41
├── docs/architecture/ + docs/decisions/                  # 治理与 ADR 根（agent 域下一编号 0015）
├── .specify/extensions/quality/quality-config.yml        # unprofiled_changed_paths: block
└── scripts/quality.ps1                                   # 包级质量门入口
```

## Current flow

```text
宿主构造 SupervisorSpec(models, backend, store, checkpointer, permissions, interrupt_on, tools)
  -> build_supervisor 校验 -> create_deep_agent（上游） -> SupervisorAssembly(graph, report, controller)
宿主 -> graph.ainvoke/astream
  -> DelegationPolicyMiddleware 拦 task 工具 -> FIFO/deadline/取消 -> 诊断事件
  -> interrupt -> Command(resume=...) 恢复
```

**缺口**（对照目标闭环）：无工作项存储/状态机；无 due 调度；无跨重启恢复；无审批持久化；无 CLI。记忆接缝（`store`/`memory` 透传）存在但不开发。

## Project history and external references

| Source | 版本/日期 | Read paths and evidence | Relevance / adopted | Rejected / constraints |
| --- | --- | --- | --- | --- |
| 本仓库 #36（`809ca37`） | — | git log 2026-11-21 | Distribution 有真实成本与退出先例 → 一次只加一个包 | — |
| 本仓库 ADR-0010:180-181 | Accepted | 已读 | 本需求命中"持久任务队列"触发条件；"第二个宿主"未出现 → 暂不拆 work/sandbox 包 | — |
| OpenClaw | MIT；2026-11-21 读 | README + docs/gateway/sandboxing | 可信控制面/不可信执行分离；沙箱默认关+后端可插拔+tool policy 先行；凭据入沙箱显式 opt-in | TS/pnpm 形态；channel 先行；常驻 Gateway 进程模型 |
| Khoj | **AGPL-3.0** | README | "work"产品形态参照（scheduled automations/newsletters） | **代码绝不复制**；RAG 方向超出 v1 |
| Letta | Apache-2.0 | README | memory-first 有状态 agent 概念（**留档备后续记忆讨论**） | server/SDK 形态；代码不复制 |
| langmem（langchain-ai/langmem） | 0.0.30，2025-10-27；MIT | GitHub README + PyPI | **留档备后续记忆讨论**：热路径记忆工具+后台管理器；原生 BaseStore；生产=AsyncPostgresStore | 约 13 个月未发新版（pre-1.0）；与 langgraph 1.x 兼容未验证；**v1 不采用** |
| langgraph-checkpoint-sqlite | 3.1.3，2026-10-30；MIT | PyPI + reference.langchain.com | **v1 采用**：SqliteSaver/AsyncSqliteSaver；strict msgpack 安全开关 | 仅 checkpointer，无 store |

- Search coverage：6 个外部页面 + 本仓库源码/历史，全部 2026-11-21 读取。
- External research: **performed**。
- Evidence gaps：无阻断 scope 的缺口。

## Options and candidate change tree

**选项 A（推荐，第三版）：新增宿主应用 Distribution `packages/apps/personal-assistant`，不含记忆。**
- 范围：工作项（stdlib `sqlite3`）+ 调度循环 + 装配接线（受限工作区 backend + 权限门禁）+ 审批持久化 + SQLite checkpointer + CLI + ADR-0015（含生产迁移接缝与**记忆接缝留位**）。
- 依赖（v1 新增第三方仅 1 个）：`langgraph-checkpoint-sqlite>=3.1.3,<4`；**不引 langmem**。
- 决定约束：ADR-0010 边界；Constitution III/V；`quality-config` profile 一次付清；依赖方向 `apps -> infra -> core`。
- 最强反例："无记忆的个人助理闭环价值有限"。回应：用户显式决定记忆后续讨论；本版先交付可验证的工作项/调度/审批/恢复骨架，记忆作为独立后续 Feature 时挂到现成接缝（`SupervisorSpec.store`/`memory` 透传）上，不需重构。
- 什么会改变推荐：用户重启记忆讨论且要求并入 v1 → 回到第二版方案；要求 Postgres-first → 范围重议。

**选项 B：不建包，examples 脚本验证。** 拒绝：产品无构建/测试/发布边界。

**选项 C：立即拆 work/sandbox 多包。** 拒绝：无第二消费者；ADR-0010 触发条件未满足。

### 候选变更树（选项 A，第三版）

```text
spawn-join/  @ 4f5b79c
├── packages/infra/agent-deepagents/                    [复用/不改] store/tools/checkpointer 透传即够
├── packages/apps/personal-assistant/                  [预计新增] 唯一新增宿主 Distribution
│   ├── pyproject.toml                                # deps: agent-deepagents、llm-provider-langchain、
│   │                                                 #   langgraph-checkpoint-sqlite>=3.1.3,<4
│   ├── src/spawn_join_personal_assistant/
│   │   ├── __init__.py / config.py                  # 显式导出；工作区根/DB 路径/model.yaml 引用
│   │   ├── work/                                     # stdlib sqlite3：工作项表、状态机、幂等键、仓储
│   │   ├── scheduler.py                              # asyncio 调度：due/并发/取消/重启恢复
│   │   ├── host.py                                   # 装配：backend+permissions+interrupt_on+checkpointer
│   │   ├── approvals.py                              # HITL 审批持久化与 resume
│   │   └── cli.py                                    # accept/due/run/report/approve
│   ├── examples/                                     # fake model 离线端到端示例
│   └── tests/                                        # work/scheduler/approvals/host 边界测试
├── docs/decisions/agent/0015-personal-assistant-host-boundary.md  [预计新增] Proposed ADR
│                                                      #   （含 SQLite→Postgres 迁移接缝 + 记忆接缝留位）
├── docs/architecture/{repository-map,package-boundaries}.md      [预计修改]
├── .specify/extensions/quality/quality-config.yml                [预计修改] 新 profile
├── scripts/quality.ps1                               [待确认] 包枚举是否需扩展
└── README.md（根）                                    [预计修改] 包选择表
```

## Scope, risks, and verification

- **Included（v1）**：单用户本地；工作项 CRUD+状态机+幂等键（stdlib `sqlite3`）；due 调度循环与重启恢复；装配接线（backend=受限工作区 + permissions + interrupt_on）；HITL 审批持久化；`langgraph-checkpoint-sqlite`（strict msgpack 默认启用）；CLI 入口；Proposed ADR-0015；治理文件同步。
- **Excluded（v1）**：**记忆全部形式（langmem、BaseStore、embeddings、记忆文件开发）——后续单独讨论**；多租户/授权/计费；IM 通道；Web UI；MCP Server；容器/远程沙箱；Postgres 实际部署（只写接缝文档）；cron 丰富语法。
- **Interfaces / compatibility / security**：不改现有七包公共契约；凭据走 `LLM_API_KEY`（ADR-0008）；checkpointer 反序列化默认白名单；新第三方依赖 1 个（langgraph-checkpoint-sqlite，MIT）。
- **Verification**：离线 tests/（fake model + tmpdir）：work 状态机/幂等/重启恢复、scheduler due/取消、approvals resume、checkpointer 恢复、越界写 deny/interrupt、CLI 冒烟；命令：`pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-personal-assistant`、`uv build packages/apps/personal-assistant --out-dir <temp>`、`uv lock --check / uv sync --locked --directory packages/apps/personal-assistant`、回归 `scripts/test-quality.ps1`。
- **风险**：文件 backend 非隔离（工作区根 + FilesystemPermission deny/interrupt + 默认不暴露 shell 工具）；`deepagents<0.8` 锁为长期约束；work DB 单文件单写者；SQLite checkpointer 文件属宿主数据目录（含状态数据，注意备份可见性）。
- **Decision blockers / questions**：仅剩范围批准（Q1' 部署形态已随记忆移出收敛为唯一合理解——SQLite 本地 + 接缝；若需 Postgres-first 请拒绝并说明）。

## Checkpoint record

- EXPLORATION_VERDICT: ready
- Evidence location: .specify/delivery/personal-assistant-20261121/exploration.md
- SCOPE_APPROVAL: pending

- 2026-11-21 第一版呈现（hash `ead5697f…`）：用户 Q2=工作区+权限门禁、Q3=CLI、Q4=sqlite checkpointer；Q5 reject（调整=记忆考虑 langmem + 生产部署）。runtime 已记录。
- 2026-11-21 第二版呈现（hash `26e3aae8…`，含 langmem+自建 SQLite store）：用户决定**记忆先不做、后续讨论**；Q5 reject。runtime 已记录。langmem/SQLite-store 证据留档于参照表。
- 本第三版 = 第二版减去记忆模块；范围收窄，无新增未决问题。

- 2026-11-21 第三版呈现（hash `15ffb490…`）：**用户批准**（runtime `decide --name scope --choice approve` 已记录）。
  - 批准范围：选项 A 第三版——`packages/apps/personal-assistant` 单宿主 Distribution（工作项/调度/装配/审批/CLI + `langgraph-checkpoint-sqlite`），沙箱=工作区+权限门禁，入口=CLI，记忆**移出 v1、后续单独讨论**；治理文件同步与 Proposed ADR-0015 随交付。
  - 已锁定决策：Q2 沙箱=工作区+权限门禁；Q3 入口=CLI；Q4 跨重启=sqlite checkpointer（strict msgpack 默认启用）；部署形态=单用户本地 SQLite + Postgres 迁移只写接缝。
  - 明确接受的非关键限制：参照研究未做 issue/PR 级深挖；langmem 等记忆证据留档供后续讨论，本 Feature 不使用。

FEATURE_DIR: specs/personal-assistant-host-20261121

## Plan gate 呈现快照（2026-11-21，Decision Propose 之后、plan gate 之前）

- 方法：SHA-256（`Get-FileHash -Algorithm SHA256`，按文件逐一；上方为呈现内容指纹，非整包目录哈希）。
- 输入清单与摘要：

| 呈现输入 | SHA-256 |
| --- | --- |
| `specs/personal-assistant-host-20261121/plan.md`（本 Feature 设计，AC-01..AC-10 + 合作计划） | `4ed9b3390b8c3064491fdc3dbf16c4e470a36745e460c72ccafd622a6d184cd8` |
| `specs/personal-assistant-host-20261121/spec.md`（已澄清需求，scope 第三版批准） | `a689e889f1367e5cb470810cbf0870ae0ccce1ca1aa3df81e243d45d458c76f6` |
| `docs/decisions/agent/0015-personal-assistant-host-boundary.md`（Proposed ADR 基线） | `5289376cd40d988eef335ad27d40b5271ca300b637ddf3aee4b65b5876b57fde` |
| `.specify/delivery/personal-assistant-20261121/exploration.md`（引用的治理/批准证据） | 呈现时以本文件当时内容为准（fingerprint 在 runtime present 记录） |
| `.specify/delivery/personal-assistant-20261121/decision-context.md`（引用的决策上下文） | `d4ff504949a1dae416588f5bf182ca03c9d3e0c9d03f2d4514ecfc24498ed58f` |

- 引用的治理策略/ADR：Constitution v1.0.0、ADR-0006/0008/0010/0011/0013、`package-boundaries.md`、`quality-config.yml`（AC 表逐行绑定）。
- Tasks 消费方在记录 plan-gate 选择前必须重算上表身份；输入变更则呈现失效，需重新呈现批准。

## Phase handoff

- **Receiving owner**: `speckit.specify`（scope gate 批准后）。
- **Required reading**: Constitution v1.0.0；ADR-0010；ADR-0008；`package-boundaries.md`；`agent-deepagents/README.md` 公共 API 与资源恢复节；`quality-config.yml`；本 run `decision-context.md`。
- **Input identity**: run `personal-assistant-20261121`；HEAD `4f5b79c`；第三版呈现的 scope gate 实际选择与接受的限制。
- **Expected return**: `specs/<feature-id>/spec.md` + 本 packet 追加 `FEATURE_DIR:` 行；记忆排除与后续讨论约定写入 spec 的非目标；范围 materially 扩张时回到 scope gate。
