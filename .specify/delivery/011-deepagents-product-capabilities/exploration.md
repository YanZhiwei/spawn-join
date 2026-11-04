# Exploration and scope packet

## Request and investigation

- Request and desired outcome: 为 SpawnJoin 增加一个可独立分发的 DeepAgents 产品开发增强包，补齐实际产品中的 supervisor/子代理装配、模型用途绑定、中间件作用域、委派执行策略、运行诊断以及资源与恢复接缝。
- Delivery run / canonical packet path: 共享会话路由；未分配独立 `delivery_run`。本 Feature 的 canonical packet 为 `.specify/delivery/011-deepagents-product-capabilities/exploration.md`。
- Feature location / Bug slug: `specs/011-deepagents-product-capabilities/` / 不适用。
- Investigation: new capability。
- Provisional lane / recommended lane: Feature。新增 Distribution、公共 API、跨包运行时依赖、执行和恢复契约，必须经过 Spec、Plan、Tasks、质量门和 Standards Review。
- Baseline HEAD / relevant working-tree changes: `5e8eb7e4029d5a2ae4835e59ef3759c2abc26d82` on `main`。工作树已有此前 v0.3.2 Delivery 安装/治理升级的修改与 `harness/evidence/` 记录；没有本 Feature 的 Python 包或业务源码改动。
- Governing instructions / ADRs: `AGENTS.md`；`.specify/memory/constitution.md`；`docs/architecture/package-boundaries.md`；`docs/architecture/repository-map.md`；`docs/development/quality-gates.md`；ADR-0006 LangChain-first runtime；ADR-0008 model file/env boundary；Proposed ADR-0009 model metadata/sync boundary；当前 Delivery route/config/template。
- Tools / fallback / freshness limitations: 使用 SpawnJoin CodeGraph（索引在基线时为最新）分析现有包；使用 NovaClaw CodeGraph 读取参考实现；使用本地 `defuddle` 提取 Datawhale 社区教程；以 DeepAgents `0.7.32` 固定提交源码、PyPI 元数据和 LangChain 官方文档核对上游契约；使用 Git history、GitHub PR 只读状态和本地质量脚本。没有安装新依赖、运行下载代码、修改 NovaClaw 或调用真实模型。教程章节版本不一致，NovaClaw 测试证据只覆盖 `deepagents==0.7.7`，均不作为本 Feature 的通过证据。

## Findings

- Facts:
  - 当前仓库有五个独立 Distribution；`packages/infra/agent-deepagents/` 尚不存在。现有架构要求新 Distribution 使用独立 `pyproject.toml`、`src/` layout、`.venv`、`uv.lock`、测试和构建边界。
  - `spawn-join-llm-provider-langchain` 已拥有 `ChatModelConfig`、`create_chat_model`、`ModelCatalog`、`ModelSummary` 和 `load_model_catalog`，负责 `model.yaml`、`.env`/环境变量凭据边界以及返回 LangChain `BaseChatModel`。本 Feature 已确认将其作为显式运行时依赖；Agent 包不重复解析 YAML、读取密钥或调用 Provider SDK。
  - ADR-0006 要求应用直接使用 LangChain 原生消息和 `BaseChatModel`；ADR-0008 将文件模型配置与凭据解析固定在 LangChain 适配包。新包应在上层绑定模型用途，而不是改变这些边界。
  - DeepAgents `0.7.32`（MIT，Python `>=3.11,<4.0`）已提供模型—工具循环、声明式/compiled 子代理接入、Middleware 组合、文件 Backend、Checkpoint、interrupt 和 streaming。0.7 默认策略更薄，Todo 等能力需要显式选择；本包不能把教程旧默认值重新隐藏成隐式全局行为。
  - DeepAgents `0.7.32` 的默认 isolated 子代理与 beta fork 子代理具有不同的上下文/中间件继承语义；`CompiledSubAgent` 保持自身图和内部配置。新包应暴露和验证这些差异，而不是复制上游注册、排序或执行循环。
  - NovaClaw `lead-agent` 已证明真实产品需要子代理注册/工厂、任务超时、并发/排队/取消、错误可见性、调用上下文和持久化接线；这些是参考证据，不是可直接复制的 SpawnJoin API。
  - 当前 `spawn-join-observability` 仅有包级 docstring，不能作为已有观测后端；首版只能提供与 callbacks/原生流兼容的诊断接缝。
- Hypotheses:
  - 新包可以在不改动 Core、协议包和模型工厂的情况下，为不同宿主统一表达一次 Agent 装配和执行策略；需在 Plan 阶段用实际 `0.7.32` 离线图执行验证。
  - 委派期限、并发上限和取消清理若直接包装上游 task 调用，可能与 LangGraph 原生取消/中断边界冲突；需先确定策略的拥有者和最低可验证语义，不能凭 NovaClaw 行为直接移植。
  - 装配报告可以解释“未注册/未入选/未调用/调用失败”，但其事件字段是否成为长期公共契约需由 Clarify/Plan 决定。
- Recommendations:
  - 新增 `spawn-join-agent-deepagents`，import package 为 `spawn_join_agent_deepagents`，运行时显式依赖 `deepagents>=0.7.32,<0.8` 与 `spawn-join-llm-provider-langchain`，保留原生 `BaseChatModel` 注入入口以支持宿主已有模型和离线测试。
  - 以六项产品能力为首版范围：子代理接入与本轮装配、模型用途绑定、中间件组合、委派执行策略、诊断/观测接缝、资源与恢复集成。详细文件和类型不在探索阶段冻结。
  - 复用 DeepAgents/LangChain/LangGraph 原生执行、重试/fallback、调用限制、Checkpoint、interrupt 和 streaming；库只拥有接线、校验、策略和诊断，不拥有租户、授权、计费、UI、MCP Server、数据库或沙箱。
- Unknowns:
  - Clarify 已确定模型用途只能通过显式 `inherit_from` 继承、委派使用宿主注入或显式创建的有界 FIFO 控制器、诊断使用结构化报告加可选同步/异步回调、资源由宿主拥有透传、fork 仅显式实验开关；这些不再是范围未决项。
  - 仍需在 Plan 中确定具体公共类型/函数名、Middleware 作用域表示、回调异常处理、Checkpoint/`thread_id` 边界校验细节，以及是否需要 Proposed ADR。
  - 0.7.32 实际离线图执行、独立 wheel 安装和新包质量 profile 尚无证据，必须由 Plan/Tasks 补齐。

## Current directory tree

```text
spawn-join/
├── packages/
│   ├── core/
│   │   ├── spawn-join-core/                 # Core 配置、异常、基础类型
│   │   └── llm-provider/                    # 框架无关 LLM 协议与错误
│   └── infra/
│       ├── llm-provider-langchain/          # 模型文件、凭据边界、BaseChatModel 工厂
│       ├── llm-model-sync/                  # 手动元数据同步
│       └── spawn-join-observability/        # 当前为骨架
├── scripts/                                # 质量、治理、静态分析入口
├── .github/workflows/quality.yml           # 当前五包质量矩阵
├── docs/architecture/                      # 包边界与仓库地图
├── docs/decisions/llm-provider/            # ADR-0006/0008/0009
├── .specify/                               # Spec Kit、Delivery、质量配置
└── harness/                                # 阶段记录与实际证据
```

## Current flow

```text
宿主应用配置/本轮资源
  -> spawn-join-llm-provider-langchain.ModelCatalog 或 BaseChatModel 注入
  -> 宿主提供业务工具、SubAgent/CompiledSubAgent、Middleware、Backend/Store/Checkpointer
  -> [拟新增] SpawnJoin Agent 装配与策略校验
  -> DeepAgents create_deep_agent / 原生 LangGraph 图
  -> 宿主调用 ainvoke/astream，并拥有会话身份、资源生命周期、UI/事件展示和外部副作用
```

模型文件和凭据仍由 `spawn-join-llm-provider-langchain` 负责；Agent 包只把已创建模型绑定到用途并报告缺失/冲突。MCP Session、数据库/沙箱连接和持久化 Store 不由同步图工厂暗中创建或关闭。

## Project history and external references

| Source / repository | Issue / PR / commit / version | Read paths and evidence | Relevance / adopted idea | Rejected parts / constraints / scope impact |
| --- | --- | --- | --- | --- |
| SpawnJoin | `468ee7f`, ADR-0006 Accepted | `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md`, `packages/core/llm-provider`, `packages/infra/llm-provider-langchain` | 复用 LangChain 原生消息/模型，协议包保持框架无关 | 不在 Agent 包定义第二套消息、Provider 或 LLM wrapper |
| SpawnJoin | `1958071`, ADR-0008 Accepted | `docs/decisions/llm-provider/0008-model-file-and-env-boundary.md`, 现有 `model_file/` API | 显式复用 ModelCatalog 和凭据边界 | 不重复 YAML、`.env`、密钥解析，不把密钥放入诊断 |
| SpawnJoin | `5e8eb7e`, ADR-0009 Proposed | `docs/decisions/llm-provider/0009-model-metadata-and-sync.md`, PR #31 | 保持模型同步与运行时模型创建分离 | 不让 Agent 包拥有元数据同步副作用 |
| NovaTech/NovaClaw | `30a0bb4f5077ed4eed805f25d9060bb0b48b839f`, `deepagents==0.7.7` 环境 | `backend/packages/lead-agent/`, `lead-agent-contract/`, `services/app-api/agents/subagents/` 及 57 项离线测试 | 借鉴真实产品中的注册/工厂、调用上下文、期限/并发/取消、错误可见性和资源接线问题 | 不复制租户、授权、计费、业务 Delegate、数据库和应用 API；旧版本测试不替代 0.7.32 验证 |
| langchain-ai/deepagents | `0.7.32`, fixed commit `e85c6b98087861512d2c5240305e16cfac68a746` | PyPI metadata、`graph.py`、subagent/middleware 源码、官方 DeepAgents 文档 | 复用原生装配、子代理、Middleware、Checkpoint、interrupt 和 streaming 契约 | 不重写执行循环；beta fork 语义必须显式标注，不将其伪装为稳定隔离模式 |
| Datawhale China | 教程章节；各章版本为 0.7.1/0.7.10/0.7.15 | `https://datawhalechina.github.io/deepagents-in-action/` 的子代理、Memory、HITL、MCP、streaming 章节 | 辅助理解真实产品生命周期、恢复、MCP Session 和流消费陷阱 | 这是社区教程，不是 SDK 权威；版本差异不作为 0.7.32 事实，模板 Web/SSE/前端不纳入包 |

- Search coverage: 已检查相关本地 ADR、包边界、仓库历史、NovaClaw lead-agent 调用链、DeepAgents 0.7.32 固定源码和官方/社区文档；未创建 Issue/PR、未运行下载代码。
- External research: performed。参考实现和 SDK 版本均记录了固定版本/提交；没有把外部目录结构直接复制为 SpawnJoin 设计。
- Evidence gaps: 尚无本包代码、0.7.32 离线执行测试、构建/隔离 wheel 证据或最终质量 profile；这些必须进入 Plan/Tasks。当前 docs quality 仍被历史断链阻塞，Delivery Doctor 还发现历史 PR #31 的 active evidence 和旧模板路径问题；不把它们误报为本 Feature 已解决。

## Options and candidate change tree

最小但不足的选项是只提供 `create_supervisor()` 别名；它无法表达产品中的模型用途、期限/取消和诊断，不能满足请求。过宽的选项是把 MCP、数据库、沙箱、观测 SDK、Web/SSE 和租户策略一并纳入，会制造错误的资源拥有者和额外发布依赖。推荐中等选项如下：

```text
spawn-join/
├── packages/infra/agent-deepagents/        [new] 新 Distribution；六项产品增强能力
│   ├── pyproject.toml、uv.lock、README.md、LICENSE
│   ├── src/spawn_join_agent_deepagents/    [new] 少量显式公共 API
│   │   ├── supervisor.py                   [new] supervisor/图装配与装配报告
│   │   ├── subagents.py                    [new] 声明式与 compiled 接入校验
│   │   ├── model_bindings.py               [new] 用途到模型的绑定；复用 ModelCatalog
│   │   ├── middleware.py                   [new] 作用域与组合配置
│   │   ├── execution.py                    [new] deadline、并发、排队、取消策略
│   │   └── diagnostics.py                  [new] 诊断和原生 callbacks/stream 接缝
│   └── tests/                              [new] 离线装配/委派/错误/恢复/公共 API
├── packages/infra/llm-provider-langchain/  [reuse] 模型创建和凭据；本轮不重复实现
├── packages/core/llm-provider/             [no-change] 保持框架无关
├── packages/infra/spawn-join-observability/[reuse cautiously] 仅在 Plan 证明真实复用后接入
├── scripts/quality.ps1、test-quality.ps1   [modify] 注册新 Distribution
├── .specify/extensions/quality/quality-config.yml [modify] 新包质量 profile
├── .github/workflows/quality.yml           [modify] 新包 CI 矩阵
├── docs/architecture/package-boundaries.md [modify] 新包边界和依赖方向
├── docs/architecture/repository-map.md     [modify] 新 Distribution 导航
└── docs/decisions/agent/                   [uncertain] 仅在长期约束需要且经 Decision Propose 后新增
```

## Scope, risks, and verification

- Included / excluded scope: 首版包含子代理接入与本轮装配、用途模型绑定、中间件组合/作用域、委派期限/并发/取消策略、诊断/观测接缝、资源与恢复集成契约，以及独立 Distribution 的文档、质量和 CI 接入。排除 DeepAgents 执行循环重写、Provider SDK、第二套模型配置、MCP/数据库/沙箱/远程服务、租户授权/计费/UI/产物台账和自动发布。
- Interfaces, compatibility, migrations, security: 新包为新增发布面，无既有消费者迁移；运行时版本范围拟为 `deepagents>=0.7.32,<0.8`，并显式依赖 `spawn-join-llm-provider-langchain`。模型对象注入保留原生 `BaseChatModel`。诊断不得包含 API key、完整私有 URL、提示词中的未经脱敏用户数据或内部凭据。所有宿主资源的创建/关闭责任必须显式。
- Verification: 新包独立 `uv lock --check`、`uv sync --locked`、Black/isort/Ruff/Pyright strict/pytest、wheel+sdist、干净环境 `pip check`/隔离导入；离线模型覆盖声明式与 compiled 子代理、不同模型绑定、中间件作用域、缺配置、重复名、失败、timeout、cancel、interrupt/checkpoint 恢复；更新质量 profile、CI 矩阵、README 和架构文档。
- Defect handoff: 不适用；这是新能力，不把 NovaClaw 的历史问题描述为 SpawnJoin 缺陷。
- Decision blockers / questions: Clarify 已冻结模型显式继承、显式有界委派控制器、宿主资源拥有透传、结构化报告加回调诊断和 fork 实验开关；Plan 仍需据此形成精确公共类型、Middleware 作用域、回调异常处理、恢复边界和验证路径。历史 Delivery Doctor/documentation blockers remain external to scope and must be resolved or explicitly carried as delivery blockers before final handoff。

## Checkpoint record

- EXPLORATION_VERDICT: ready
- Evidence location: `.specify/delivery/011-deepagents-product-capabilities/exploration.md`
- SCOPE_APPROVAL: approved
- CLARIFICATION_STATUS: complete after five answered questions.
- CLARIFICATION_APPROVAL: approved by user on 2026-11-04 ("批准进入 Plan"); the approved clarifications are the five answers recorded in `specs/011-deepagents-product-capabilities/spec.md` under `## Clarifications`. This approval does not approve the not-yet-presented Plan, public interfaces, ADR, or Tasks.
- Approval record: 用户在共享会话中以“可以”确认了此前提出的六项首版产品能力范围，并随后确认模型相关能力显式依赖 `spawn-join-llm-provider-langchain`。该批准只覆盖探索范围，不覆盖尚未呈现的详细接口、Plan、ADR 或 Tasks。
- Accepted non-critical limitations: Datawhale 教程版本不统一；NovaClaw 0.7.7 测试不可替代 0.7.32 运行证据；当前 observability 包不是现成后端。这些限制已转为后续验证或宿主责任，不阻塞本次范围决定。

## Plan checkpoint record

- Recorded at: 2026-11-04, after `speckit.decision.propose` established the Proposed ADR baseline and before the Plan gate.
- Plan path: `specs/011-deepagents-product-capabilities/plan.md`.
- Clarified requirements path: `specs/011-deepagents-product-capabilities/spec.md` (five answers under `## Clarifications`).
- Proposed ADR baseline: `docs/decisions/agent/0010-deepagents-product-boundary.md` (Status: Proposed; not Accepted).
- Fingerprint method: SHA-256 over raw file bytes for every input; manifest line format `<repository-relative-path-with-forward-slashes><TAB><lowercase-file-sha256>`, paths sorted ordinally; composite digest is SHA-256 of the UTF-8 manifest bytes including the final newline.
- Composite SHA-256: `7f58094554c233cae2309d97ea984211ebabc8749a7d95218e604e33e1886f8e`.
- Input manifest:

| Path | SHA-256 |
|---|---|
| `.specify/delivery/011-deepagents-product-capabilities/decision-context.md` | `2bcfc7b08724f287b11fa84affa2ddadf822fed1ca49f9910b14df80ae8b0c60` |
| `.specify/memory/constitution.md` | `6f98a7926636e9092ec6f9f3aeafe35fa5b741c431f12cebb2ae45fac125f63f` |
| `AGENTS.md` | `e0ad64d02d0469c4a3ae23ecad9f8e791e528cdf800b90e81a19238de6b556f4` |
| `docs/architecture/package-boundaries.md` | `be322f13836c464355074a2ded0094919b990a359c2a2f796a480fa106c4946f` |
| `docs/architecture/repository-map.md` | `6c8b3c2030a1303eb0594ceafe27f3ffdc835eef4201e42742ca97f0edbaf1c6` |
| `docs/decisions/agent/0010-deepagents-product-boundary.md` | `15c61d48ab5cce68d9dfae5e1ae5577cb9d4330c4c529c0070d8f661b6d7e26c` |
| `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` | `b692b65ee300656ccddfeaadd59cfe86fbbfde7e19493644a32513b2b6fffb29` |
| `docs/decisions/llm-provider/0008-model-file-and-env-boundary.md` | `c9b6abdac1e4f9abb7622390973e9b7540cd008e320f870b67f465b13b198096` |
| `docs/decisions/llm-provider/0009-model-metadata-and-sync.md` | `31cbb5a8cb219d58444de83eef75f447d33ef325ad8439ca1e80dd3e8c3cb492` |
| `docs/decisions/README.md` | `4f73d0f1e557e61f5b40c7e2c18bd459dd344649ca16f05689a28fa8ef36d50c` |
| `docs/development/quality-gates.md` | `a6d8bcb2341dbdfe4e5ef014df8fbee51d12d7d73db52e36e9ceda0a12d7f44c` |
| `specs/011-deepagents-product-capabilities/contracts/public-api.md` | `cdb747cf34ce1ebb87846466f45162e77dedf354dc0fa8fa7544a293a4f552bc` |
| `specs/011-deepagents-product-capabilities/data-model.md` | `3591ae531a39f29d7fcb614d2d9a3fcaa3b8fff3eaf3e4bcb7eb26803a6cfa26` |
| `specs/011-deepagents-product-capabilities/plan.md` | `e771d6c1f2176dd3311119cb8039e83b130a570a39532f38a93b9777dd716789` |
| `specs/011-deepagents-product-capabilities/quickstart.md` | `d31e5eb7717ac5d0ba6bb010eabd02cedd5ac5948092175bfda661c27e78dbea` |
| `specs/011-deepagents-product-capabilities/research.md` | `689e96776e3fcca607b4a5a7f833e250941a878feec794ca57055f5ecd53debc` |
| `specs/011-deepagents-product-capabilities/spec.md` | `639480e8b6e70b002ffeb9d68dbebca106001624aa20bbb298b9355866293056` |

- Presented scope differences: `SUMMARIZATION` is explicitly required by default; governed delegation is async-only with an explicit sync error. No material scope expansion.
- PLAN_APPROVAL: **approved** by the user on 2026-11-04 ("批准进入 Tasks") against the unchanged composite fingerprint `7f58094554c233cae2309d97ea984211ebabc8749a7d95218e604e33e1886f8e`. This approves the presented Plan/public API contract/Proposed ADR-0010 baseline only; it does not approve implementation, Tasks execution, the ADR status, or a later changed design. Any change to the listed inputs requires a refreshed presentation and fingerprint before implementation.
