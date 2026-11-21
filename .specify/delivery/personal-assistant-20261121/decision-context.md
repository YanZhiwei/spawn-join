# Decision Context — personal-assistant-20261121

- LANE: feature
- DELIVERY_RUN: personal-assistant-20261121
- DECISION_CONTEXT_PATH: .specify/delivery/personal-assistant-20261121/decision-context.md
- Mode: discover（spec 之前的发现模式；只给术语与约束，不选方案）
- Baseline HEAD: 4f5b79c（main，工作区干净）
- 读取日期: 2026-11-21

## Active constraints（已读，状态已知）

| 来源 | 状态 | 对本工作（personal assistant）的约束 |
|---|---|---|
| Constitution I–V | 活跃 | 可读性优先；对象有边界；DRY 需 ≥2 处稳定复用才提升抽象；行为改动先定不变量与测试；KISS/YAGNI，推测性风险须用户批准才扩大范围 |
| Constitution: Architecture constraints | 活跃 | src/ layout、`__init__.py` 显式导出、依赖单向、副作用必须有拥有者、密钥/凭据不入库不入日志 |
| [ADR-0006](../../../docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md) | Accepted | LangChain-first：应用直接使用 `BaseChatModel`/`BaseMessage`，协议包保持框架无关 |
| [ADR-0008](../../../docs/decisions/llm-provider/0008-model-file-and-env-boundary.md) | Accepted | `model.yaml` 解析与凭据边界在 `spawn-join-llm-provider-langchain`；agent 包不读密钥；新宿主应用同样不得自建第二套凭据解析 |
| [ADR-0009](../../../docs/decisions/llm-provider/0009-model-metadata-and-sync.md) | Proposed | 模型同步是手动 CLI，明确"不实现定时任务/后台调度"——仓库内没有任何调度器先例 |
| [ADR-0010](../../../docs/decisions/agent/0010-deepagents-product-boundary.md) | Accepted | `spawn-join-agent-deepagents` 只做装配：Store/Checkpointer/MCP/沙箱/Backend 由宿主创建与关闭；重新评估触发条件明确包含"真实的跨进程委派或持久任务队列需求"与"第二个宿主需要 lifecycle adapter" |
| [ADR-0012](../../../docs/decisions/agent/0012-deepagents-official-p0.md) | Proposed | P0 接线边界；不实现 MCP Server、数据库、沙箱、UI、租户/授权/计费 |
| [ADR-0014](../../../docs/decisions/agent/0014-deepagents-p1-capabilities.md) | Proposed | P1 能力公共边界；`backend_kind` 输出 `sandbox`/`local_shell` 等稳定标签（仅分类，不实现） |
| [ADR-0013](../../../docs/decisions/llm-provider/0013-channel-runtime-and-credentials.md) | Accepted | `spawn-join-llm-channel` 是模型 Provider transport（openai/anthropic），**不是**用户消息通道（微信/Telegram/Slack） |
| [ADR-0011](../../../docs/decisions/engineering/0011-common-helper-package.md) | Proposed | Common 默认零第三方运行时依赖；新包不应把通用辅助塞回 Common |
| [ADR-0001/0002/0003/0004/0007](../../../docs/decisions/README.md) | Accepted | 交付工件与长期设计分离；specs/ 本地忽略；Slice 交付默认启用；PR 线性历史 squash |
| `quality-config.yml`（`.specify/extensions/quality/`） | 活跃 | `unprofiled_changed_paths: block`——**任何新 Distribution 路径必须同时新增 quality profile，否则质量门直接 blocked** |
| `package-boundaries.md` | 活跃 | 依赖方向表允许"业务应用组合多个领域/infra 包"；Core/协议包不得反向依赖 |

## Conflicts with the proposed work

- 无直接冲突。关键点是 **ADR-0010 刻意把 work（持久任务队列）与 sandbox 排除在 agent 装配包之外**（"不把租户、授权、计费、产物台账、UI/事件协议、MCP Server、数据库或沙箱实现放入本包"）。因此新能力必须落在**新的拥有者**（宿主应用 Distribution 或独立包），把 work/sandbox 塞进 `spawn-join-agent-deepagents` 会直接违反 Accepted ADR。
- 无 superseded 历史约束影响本工作。

## Open decisions the plan must resolve

1. 新能力拥有者与分组：`packages/apps/personal-assistant`（新增 `apps` 分组）vs `packages/infra/` 下复用分组 vs 暂不建包（详见 exploration.md 选项比较）。
2. 持久化介质与并发边界：stdlib `sqlite3`（零新依赖，配串行化访问）vs `aiosqlite`（第三方）；thread 级恢复是否引入 `langgraph-checkpoint-sqlite`（第三方）。
3. sandbox 级别 v1：受限文件工作区 + `FilesystemPermission` 门禁 vs 子进程隔离 vs 上游 `LangSmithSandbox`（外部托管服务依赖）。
4. 记忆方案：工作区内 memory 文件 + Store 桥 vs 独立 memory 存储。
5. Proposed ADR 编号与分类：`agent/` 域，下一可用编号 **0015**。

## Verified external references（2026-11-21 补做）

- **OpenClaw**（github.com/openclaw/openclaw，MIT，约 395k stars，读 README + docs.openclaw.ai/gateway/sandboxing）：Gateway（可信控制面）常驻宿主、**仅工具执行**按配置进入沙箱后端（Docker/Podman/SSH/OpenShell/Crabbox 可插拔）；sandboxing 默认关闭；tool allow/deny policy 先于 sandbox 规则生效；凭据注入沙箱是显式 opt-in 并带审计告警；`sandbox list/explain/recreate` 生命周期 CLI。许可：MIT。
- **Khoj**（github.com/khoj-ai/khoj，**AGPL-3.0**）：个人 AI second brain；scheduled automations/newsletters 即"work/调度"能力的参照形态。约束：AGPL 代码**绝不复制**，只借鉴概念。
- **Letta**（github.com/letta-ai/letta，Apache-2.0，f.k.a. MemGPT）：memory-first 有状态 agent 平台；活跃源码已迁至 letta-code（npm/TS）。约束：代码不复制。
- **langmem**（github.com/langchain-ai/langmem + PyPI，MIT，**0.0.30，2025-10-27 发布**）：LangChain 官方记忆框架；热路径记忆工具（`create_manage_memory_tool`/`create_search_memory_tool`）+ 后台记忆管理器；原生对接 LangGraph `BaseStore`；README 明确 InMemoryStore 重启即丢、生产用 AsyncPostgresStore。**风险事实：最新版距今约 13 个月未更新，pre-1.0**；与 langgraph 1.x 兼容性未验证（Plan 首任务兼容 spike）。
- **langgraph-checkpoint-sqlite**（PyPI 3.1.3，2026-10-30，MIT，Trusted Publishing）：`SqliteSaver`/`AsyncSqliteSaver`；`LANGGRAPH_STRICT_MSGPACK` 反序列化白名单安全开关；活跃维护。**核实：该包只含 checkpointer，官方无 SQLite `BaseStore` 实现**（reference.langchain.com 确认）。
- pi（earendil-works/pi）仅在 OpenClaw README 被提及，本会话未读，不作为证据。

## 新增 open decisions（第三轮收敛后）

1. ~~记忆方案~~ → **用户已决定：v1 不做任何记忆开发（langmem/BaseStore/嵌入/记忆文件），后续单独讨论**；langmem 与 SQLite-store 调研证据已在 exploration.md 参照表留档，后续讨论不需重做研究。
2. 部署形态 → 随记忆移出收敛为唯一合理解：v1 单用户本地 + SQLite（work 表 + checkpointer），Postgres 迁移只写接缝文档（ADR-0015）。
3. embeddings 语义检索 → 随记忆一并移出 v1。

## Missing evidence

- 无阻断 scope 决策的缺口。剩余限制：未对参照项目做 issue/PR 级深挖（scope 决策不需要）；langmem 兼容性验证不再属于本 Feature（记忆移出后无此依赖）。

## Resolve 结论（2026-11-21，planning 阶段）

- 冲突检查：无 scope 级 ADR 冲突。ADR-0010 把 work/sandbox/数据库排除在 `agent-deepagents` 之外——本 Feature 的新宿主 Distribution 正是该排除项的预期归宿，设计未违反任何 Accepted 决策；"持久任务队列"重评触发条件（ADR-0010:180）由本 Feature 满足。
- 依赖声明核对：ADR-0006/0008 的 LangChain-first 与凭据边界由 `ModelCatalog` 消费路径满足；ADR-0013 channel 语义不受影响（本 Feature 无用户消息通道）；ADR-0011 Common 不引入新依赖；`quality-config.yml` 的 `unprofiled_changed_paths: block` 要求新包 profile 随首切片落地。
- 规划期必须解决的开放决策（进入 plan.md，非用户决策）：
  1. work 表 SQLite schema 与状态机字段；
  2. checkpointer 同步/异步选择（调度循环为 asyncio，倾向 `AsyncSqliteSaver`；plan 定）；
  3. `packages/apps` 新分组的治理文件更新面（repository-map / package-boundaries / quality-config / 根 README）；
  4. Proposed ADR-0015 编号与分类（`agent/` 域，0015）。
- 输入绑定：`specs/personal-assistant-host-20261121/spec.md`（scope 已批准）为规划输入；clarify 已记录 `ready`/`needs_approval=false`。
