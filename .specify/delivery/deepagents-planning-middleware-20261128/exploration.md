# 探索与范围包

## 请求与调查

- 请求与期望结果：在 `spawn-join-agent-deepagents` 中为“产品开发过程”补齐
  `planning/todo` 中间件的一等支持，让宿主可以用显式配置启用 LangChain
  `TodoListMiddleware` 的 `write_todos` 能力，而不是依赖模型专属 harness profile 或
  未文档化的原始 middleware 注入。
- Delivery run / 规范包路径：
  `deepagents-planning-middleware-20261128` /
  `.specify/delivery/deepagents-planning-middleware-20261128/exploration.md`。
- FEATURE_DIR: specs/012-deepagents-planning-middleware
- 功能位置 / Bug slug：`specs/012-deepagents-planning-middleware/`；本包不适用 Bug slug。
- 调查类型：现有能力扩展（现有包新增显式公共 seam，不是新 Distribution）。
- 暂定路线 / 推荐路线：Feature。新增公共 API、可观察的工具/提示行为、双语 README
  契约，并需要 Proposed ADR、测试和质量门。
- 基线 HEAD / 相关工作树改动：
  `87e809f2b8d405c19d9bced4bfda89d018fa430e`；规划开始时工作树干净。
- 治理说明 / ADR：`AGENTS.md`、Constitution、ADR-0010（Accepted）、
  ADR-0012（Accepted）、ADR-0014（Proposed）、ADR-0006/0008/0016、
  `.specify/extensions/delivery/delivery-config.yml`、`quality-config.yml`。
- 工具 / 回退 / 时效限制：使用 Git、源码文本检索和
  `packages/infra/agent-deepagents/.venv` 中已安装的 `deepagents 0.7.32` /
  `langchain 1.4.8` 读取真实默认栈与 `TodoListMiddleware` 签名。
  `codegraph` 不在 PATH，未使用 CodeGraph；使用文本检索替代。未调用真实模型，
  未运行网络请求。

### 结果与问题界定

- 观察到的症状：`create_deep_agent` 0.7.32 的默认栈没有 `write_todos`；只有
  `openai_codex` harness profile 显式添加 `TodoListMiddleware`。SpawnJoin 包也没有
  planning 配置入口或文档，因此“产品开发型”agent 默认不会规划多步任务。
- 期望结果：宿主可以显式开启 planning，并获得可测试、可报告的稳定装配行为；
  未配置时保持现有图与工具不变。
- 请求机制：在现有 `SupervisorSpec` 上增加 planning 配置，不新建包、
  不重写执行循环、不引入外部服务。
- 成功条件：配置 planning 后，supervisor 的 middleware 报告中出现
  `TodoListMiddleware`，图提供 `write_todos`；未配置时报告与现有测试完全一致。
- 已知偏好/约束：用户已选择“补 planning/todo 一等支持”；项目偏好
  opt-in、显式契约、双语 README、离线可测。

## 概念、边界与研究问题

| 术语 | 本请求中的含义 / 权威来源 | 歧义或排除含义 |
| --- | --- | --- |
| planning / todo | LangChain `TodoListMiddleware` 及其 `write_todos` 工具；DeepAgents 0.7.32 不默认安装 | 不是 SpawnJoin 自研的 PRD/需求/设计工作流；不是 `tasks.md` 队列 |
| 产品开发过程 | 使用该 agent 包构建产品时的多步任务规划与进度跟踪能力 | 不包含需求收集、设计评审、测试编排等领域中间件 |
| 一等支持 | 公开配置类型、校验、装配逻辑、报告/文档和测试均属于包契约 | 不是默认对所有宿主强制开启 |

- 领域边界：`spawn-join-agent-deepagents` 只拥有 planning 配置到
  `TodoListMiddleware` 的接线、校验和报告；LangChain 拥有工具与状态实现；
  宿主拥有模型、任务语义、持久化和 UI。

| 问题 / 受影响决策 | 证据与来源身份 | 结论 / 冲突证据 | 剩余缺口、影响与下一所有者 |
| --- | --- | --- | --- |
| 0.7.32 默认栈是否包含 planning？ | `deepagents 0.7.32` `graph.py` 默认栈：Filesystem、SubAgent、Summarization、PatchToolCalls；无 TodoList 导入 | 不包含。docstring 仍提 planning，但实现已变薄 | 与上游文档措辞有差异，按实际源码和离线图测试为准 |
| 谁提供 `write_todos`？ | `langchain 1.4.8` `langchain.agents.middleware.TodoListMiddleware` | LangChain 提供稳定 middleware；Codex profile 只是显式采用 | 需在图构建测试中证明工具确实出现 |
| 宿主现在能否注入？ | `MiddlewareConfiguration` 接受任意 `AgentMiddleware`，保留名不含 `TodoListMiddleware` | 可以，但无配置类型、无文档、无冲突校验、无报告语义 | 一等支持应补这些缺口，而不是复制 middleware |
| 默认开启是否安全？ | ADR-0014 的不变量：未配置时行为完全不变；0.7 默认更薄是刻意选择 | 默认开启会改变所有现有图的工具与提示，风险高 | 推荐 opt-in；是否默认开启由 scope/plan 审批决定 |
| worker 是否也需要 planning？ | `SubAgentMiddleware` 为声明式 worker 建立独立图；现有 `workers` middleware 逐 worker 注入 | 技术上可行，但会让每个 worker 额外产生 todo 状态与工具 | 首版推荐 supervisor-only，worker 通过显式原始 middleware 扩展 |
| 是否新增 ADR？ | ADR-0014 的先例：新的公共 seam 需要 Proposed ADR | 需要 Proposed ADR-0019，不修改已 Accepted 的 ADR-0010 | Decision Propose 阶段正式建立 |

## 发现

- 事实：
  - `packages/infra/agent-deepagents/src/spawn_join_agent_deepagents/supervisor.py`
    的 `_supervisor_middleware` 依次加入错误归一、用户 supervisor middleware、
    summarization、memory、rubric、诊断和委派策略；没有 planning。
  - `middleware/scopes.py` 的保留名只有 summarization、delegation、diagnostics、
    llm error normalization；`TodoListMiddleware` 不在其中。
  - `deepagents 0.7.32` 的 `create_deep_agent` 默认栈没有 `TodoListMiddleware`；
    `openai_codex` harness profile 单独添加。
  - `langchain 1.4.8` 的 `TodoListMiddleware` 是稳定公开类，构造参数为
    `system_prompt` 与 `tool_description`，`.name == "TodoListMiddleware"`，
    工具为 `write_todos`。
  - 包内已有 `RubricConfiguration`、`MemoryConfiguration`、`SkillsConfiguration`
    等“配置对象 → 原生 middleware”的先例，可复用同一模式。
- 假设：
  - 新增 `PlanningConfiguration` 并在 `SupervisorSpec.planning` 显式传入时追加
    `TodoListMiddleware`，可以在不改变现有默认行为的前提下满足产品开发型 agent。
  - 通过 `assembly.report.middleware.supervisor_names` 或新增小型 planning 报告字段
    可以让宿主确认启用状态；具体字段应在 Plan 中按最小公共面决定。
- 建议：
  - 采用 opt-in：`planning: PlanningConfiguration | None = None`；默认不追加任何
    middleware，保持现有测试和调用方行为不变。
  - 首版只作用于 supervisor；worker 需要时继续使用现有 `MiddlewareConfiguration`
    或声明式 `SubAgentDefinition.middleware`。
  - 提供 `system_prompt` / `tool_description` 可选覆盖，并在启用时禁止同一作用域
    再注入同名 `TodoListMiddleware`，避免双实例与隐式顺序竞争。
  - 增加 Proposed ADR-0019，记录 planning seam、默认关闭、作用域和报告边界。
- 未知项：
  - 是否需要在 `AssemblyReport` 增加 planning 专用字段，还是只依赖 middleware 报告；
    这是 Plan 的设计选择，不是范围阻塞。
  - 是否需要 worker 级 planning；首版明确排除，后续按真实消费者再扩展。

## 当前目录树

```text
spawn-join/
├── packages/infra/agent-deepagents/
│   ├── src/spawn_join_agent_deepagents/
│   │   ├── supervisor.py              # SupervisorSpec、build_supervisor、middleware 装配
│   │   ├── middleware/scopes.py       # 作用域、保留名、报告
│   │   ├── middleware/__init__.py     # middleware 子包导出
│   │   ├── diagnostics.py             # AssemblyReport 与诊断
│   │   ├── rubric.py                  # 配置对象 → 原生 middleware 的先例
│   │   └── __init__.py                # 公共 API 导出
│   ├── tests/
│   │   ├── test_middleware.py         # 作用域/保留名/装配顺序
│   │   ├── test_supervisor.py         # 图构建与报告
│   │   └── conftest.py                # fake model / 离线图夹具
│   ├── README.md                      # 简体中文公共契约
│   └── README.en.md                   # 英文公共契约
├── docs/decisions/agent/
│   ├── 0010-deepagents-product-boundary.md   # Accepted 边界
│   └── 0014-deepagents-p1-capabilities.md    # Proposed 公共 seam 先例
└── .specify/delivery/
    └── deepagents-planning-middleware-20261128/
        ├── decision-context.md
        └── exploration.md
```

## 当前流程

```text
宿主构建 SupervisorSpec(models, middleware, ...)
  -> build_supervisor
     -> _supervisor_middleware:
          LLM 错误归一
          -> spec.middleware.supervisor
          -> 生成的 SummarizationMiddleware
          -> Memory / Rubric / diagnostics / delegation
     -> create_deep_agent
        -> 上游默认栈:
             Filesystem, SubAgent, Summarization, PatchToolCalls
        -> 用户 middleware 按 .name 合并
  -> 宿主调用 graph.ainvoke/astream
```

当前没有路径添加 `write_todos`；宿主必须注入原始 `TodoListMiddleware`，
且没有包级校验或 planning 报告。

## 项目历史与外部参考

| 来源 / 仓库 | Issue / PR / commit / 版本 | 读取路径与证据 | 相关性 / 采纳点 | 拒绝部分 / 约束 / 范围影响 |
| --- | --- | --- | --- | --- |
| SpawnJoin | `87e809f` | `packages/infra/agent-deepagents/` 源码、测试、README | 复用现有配置对象 + 原生 middleware 模式 | 不新建包、不复制执行循环 |
| SpawnJoin | ADR-0010 Accepted | `docs/decisions/agent/0010-deepagents-product-boundary.md` | 边界允许 middleware 装配 seam | 不改变资源所有权和上游替换语义 |
| SpawnJoin | ADR-0014 Proposed | `docs/decisions/agent/0014-deepagents-p1-capabilities.md` | 新公共 seam 记录为 Proposed ADR；未配置时行为不变 | 不把 planning 标记为 beta；LangChain 类是稳定 API |
| langchain-ai/deepagents | `0.7.32` | 安装环境 `deepagents/graph.py`、`profiles/harness/_openai_codex.py` | 默认薄栈；Codex profile 显式添加 planning | 不依赖模型 profile 伪装成产品能力 |
| langchain-ai/langchain | `1.4.8` | `langchain.agents.middleware.TodoListMiddleware` 签名与 `.name` | 直接复用稳定 middleware | 不重新实现 todo 状态或工具 |

- 检索覆盖：检索了包源码、测试、README、ADR-0010/0012/0014、质量配置、
  Delivery 配置，以及安装环境中的 DeepAgents 0.7.32 默认栈和 Codex profile。
- 外部研究：未新增网络研究；以上游已安装固定版本源码为准。
- 证据缺口：未运行真实模型；`write_todos` 的实际模型行为不在自动化范围。
  CodeGraph 不可用，使用源码检索替代；这些不阻塞范围决定。

## 方案与候选变更树

1. **仅文档说明宿主自行注入原始 `TodoListMiddleware`** — 最小，但没有配置类型、
   校验、报告和回归测试，不能满足“一等支持”。
2. **新增 `PlanningConfiguration` + `SupervisorSpec.planning`（推荐）** — 复用
   LangChain 原生 middleware，新增公开配置、校验、装配、文档和测试；默认关闭，
   不改变现有行为。
3. **默认开启 planning，并同时注入所有 worker** — 开箱即用，但会改变所有现有图的
   工具/提示和 token 行为，且 worker 规划语义未经验证；超出本次有界范围。

推荐选项 2。首版 supervisor-only；worker 级 planning 留给真实消费者和独立变更。

```text
spawn-join/
├── packages/infra/agent-deepagents/
│   ├── src/spawn_join_agent_deepagents/
│   │   ├── planning.py                     [预计新增] PlanningConfiguration 与校验
│   │   ├── supervisor.py                   [预计修改] SupervisorSpec.planning 与装配
│   │   ├── __init__.py                     [预计修改] 导出 PlanningConfiguration
│   │   ├── middleware/scopes.py            [预计修改] 冲突/保留名说明（按设计）
│   │   └── diagnostics.py                  [待确认] 是否新增 PlanningReport
│   ├── tests/
│   │   ├── test_planning.py                [预计新增] 配置校验与冲突
│   │   ├── test_middleware.py              [预计修改] 启用/未启用装配断言
│   │   └── test_supervisor.py              [预计修改] 图/报告断言
│   ├── README.md                           [预计修改] 中文使用与限制
│   └── README.en.md                        [预计修改] 英文对齐
├── docs/decisions/agent/
│   └── 0019-deepagents-planning-middleware.md  [预计新增] Proposed ADR
└── .specify/delivery/deepagents-planning-middleware-20261128/
    └── exploration.md                      [本文件]
```

## 范围、风险与验证

- 包含 / 排除范围：
  - 包含：opt-in planning 配置、`TodoListMiddleware` 装配、可选 prompt/description
    覆盖、同名冲突校验、supervisor 装配报告可见性、双语 README、ADR-0019 Proposed、
    包级测试和质量检查。
  - 排除：默认开启、worker 级 planning、领域工作流（需求/设计/测试/评审）、
    新 Distribution、持久化/队列/UI、真实模型行为验证、修改 DeepAgents 默认栈。
- 接口、兼容性、迁移、安全：
  - 新增公共类型和 `SupervisorSpec` 字段均有默认值；未配置时行为不变。
  - 不新增运行时依赖：`TodoListMiddleware` 来自现有 `langchain` 依赖。
  - 不读取密钥、不记录 prompt/tool 描述到报告；只记录启用状态和名称。
  - 同名冲突在装配前以 `MiddlewareConfigurationError` 失败，避免双实例。
- 验证：
  - `uv lock --check` / `uv sync --locked`（包目录）。
  - `pytest` 覆盖：配置校验、默认关闭时 middleware 名称不变、启用后
    `TodoListMiddleware` 出现在 supervisor 栈、同名冲突失败、可选覆盖传递、
    必要时 worker 排除。
  - `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents`
    覆盖格式、lint、严格类型、测试、构建和隔离安装。
  - `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` 与 README 双语链接检查。
- 缺陷交接：不适用；这是能力扩展，不是缺陷修复。
- 决策阻塞 / 问题：无范围级阻塞。Plan 需决定是否增加 `PlanningReport`，以及
  worker 级 planning 是否保持显式排除；两项都不改变已展示范围。

## 检查点记录

- EXPLORATION_VERDICT: ready
- 证据位置：
  `.specify/delivery/deepagents-planning-middleware-20261128/exploration.md`
- SCOPE_APPROVAL: 用户于 2026-11-28 批准；批准范围为仅 supervisor 的 opt-in
  planning 配置、默认关闭、可选 prompt/tool-description 覆盖、冲突校验、测试、
  双语 README 更新和 Proposed ADR-0019。worker 级 planning 与默认开启明确排除。

## Delivery Doctor

- SD_DOCTOR_VERDICT: pass
- Run root/runtime root 存在；Delivery 0.5.0 组件、Decision、Ralph、Review、
  Simplify、Evidence、Quality、Docs Sync、Bug 和 Diagram 已安装。
- Feature/Bugfix/Lightweight workflow 均为 0.5.0，并引用已安装命令，包括
  Slice → Analyze → combined gate → approval writer → checkpoint → Ralph。
- 质量 profile `spawn-join-agent-deepagents` 存在，指向
  `scripts/quality.ps1 -Package spawn-join-agent-deepagents`；docs/governance profile
  覆盖 README 和 ADR 变更。
- 切片策略：`auto`、manual stack provider、需要切片批准、slice/final squash、
  merge sync。
- `pull_request_template` 存在于 `.github/pull_request_template.md`。
- 当前 run 尚未有 Evidence，这在 Evidence 阶段之前允许。
- 无关的 legacy run `006`、`008`、`009`、`010` 报告缺少 legacy Evidence 身份；
  这些是维护发现，不是本 run 的阻塞。

## Plan 检查点记录

- 记录时间：2026-11-28，Decision Propose 建立 Proposed ADR-0019 基线之后、
  Plan Gate 之前。
- Plan 路径：`specs/012-deepagents-planning-middleware/plan.md`。
- 澄清需求路径：`specs/012-deepagents-planning-middleware/spec.md`
  （无待批准澄清；`CLARIFY_VERDICT: ready`）。
- Proposed ADR 基线：`docs/decisions/agent/0019-deepagents-planning-middleware.md`
  （Status: Proposed；非 Accepted）。
- 指纹方法：对每个输入原始字节计算 SHA-256；manifest 行格式为
  `<仓库相对路径，正斜杠><TAB><小写文件 SHA-256>`，路径按序数排序；
  复合摘要为 UTF-8 manifest 字节（含末尾换行）的 SHA-256。
- 复合 SHA-256：`7096ffa46c4b27134ee597141995dfd530b0c73ba4b6f009c6c547d623c000f9`。
- 输入 manifest：

| 路径 | SHA-256 |
|---|---|
| `.specify/delivery/deepagents-planning-middleware-20261128/code-context.md` | `f4c73158152313db5fe49ac877a64b77e67c8d6104996bb7c038f749ec2dfc4b` |
| `.specify/delivery/deepagents-planning-middleware-20261128/decision-context.md` | `3a82ad1e9dae7479e6f405363cb23757c7a20a198bf3c6382a77ea457271a158` |
| `.specify/memory/constitution.md` | `945401879b4ec63691da47fb68efe7a3f2520cd0bb12802f979f27c313bc155f` |
| `AGENTS.md` | `ffc35330e928ae2fe9d4cb92aea0c42ef9f703406e94a814dca99bcfed80ce21` |
| `docs/architecture/package-boundaries.md` | `c567466c8d544b3c5633f0367aa793016b71e0f92a769072b7a941e4b102dd34` |
| `docs/architecture/repository-map.md` | `756383679463bb2759db5c7e6adc64dc871b93cc2ab6f3e2b98574b7f5253a02` |
| `docs/decisions/README.md` | `3700c2d92eae18e0982867de25524f0a90c5e4c4c83461911d6003acf2cc820b` |
| `docs/decisions/agent/0010-deepagents-product-boundary.md` | `9fb2d69b96e43a4e6eefb77fcc0c29d9c9edcbf1fbdae86ff12153711ada9059` |
| `docs/decisions/agent/0012-deepagents-official-p0.md` | `0f04dfcf76349ecdd530e5f3d45a823ee96d4eaf573f206d9011c54b0b9d2321` |
| `docs/decisions/agent/0014-deepagents-p1-capabilities.md` | `f9006e3cd5d9c2c3a632e90c5a740023b5abb38ca28864b2150d89161c63e918` |
| `docs/decisions/agent/0019-deepagents-planning-middleware.md` | `4d1b0d0ed464e04f6a5e64d2e3916a8638f5f8c8c6f824252e295b9ef4dc6652` |
| `docs/decisions/engineering/0016-desktop-first-service-ready-packages.md` | `172fa79755e201f2d37e635e6aa0bbe532bfd6837cac4e86fecba389aed4390b` |
| `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` | `b692b65ee300656ccddfeaadd59cfe86fbbfde7e19493644a32513b2b6fffb29` |
| `docs/decisions/llm-provider/0008-model-file-and-env-boundary.md` | `c9b6abdac1e4f9abb7622390973e9b7540cd008e320f870b67f465b13b198096` |
| `docs/development/quality-gates.md` | `f06e01161418f4a9dce6cc5f1ece2f9768b47de1075a86efcd06d32f52f3643f` |
| `specs/012-deepagents-planning-middleware/contracts/public-api.md` | `e4f21dd5c47bb102859e1682060406d621bf28961925a72ce7380b4521fc75bd` |
| `specs/012-deepagents-planning-middleware/data-model.md` | `63666ace62b1502b1511daa3c3d206816845b2262ce2694674d65e47db4f4c74` |
| `specs/012-deepagents-planning-middleware/plan.md` | `d6a4075eb6c7ee46eebaa7c04e12f69f0705c58d1ce9842ed6023cd41974a7d1` |
| `specs/012-deepagents-planning-middleware/quickstart.md` | `1b65aaf63e8ec715c54baf7920be2305e202ea7b32ca55ddd045677582fa71d0` |
| `specs/012-deepagents-planning-middleware/research.md` | `d7aacef96183a777575e603e765ebae42280c24d2318cd13051795538affd5ee` |
| `specs/012-deepagents-planning-middleware/spec.md` | `ec1d60e3d3eef0368e4a9d788488f7c7863596d5310b82901264cdc88bdb33d6` |

- 展示的范围差异：无。设计通过复用
  `MiddlewareScopeReport.supervisor_names` 解决唯一开放选择；不新增
  `PlanningReport`。
- 语言说明：2026-11-28 用户要求 spec 工件使用中文。上述指纹对应中文翻译后的
  同义内容；语义、范围和设计未变化，原设计批准继续适用。
- PLAN_APPROVAL: **已批准**，用户于 2026-11-28（“批准设计”）针对当时展示的
  Plan、公共 API 契约、架构约束、协作计划和 Proposed ADR-0019 基线；中文翻译
  不改变语义。该批准不覆盖实现、ADR 状态或远程发布。
- SLICE_APPROVAL: 用户于 2026-11-28（“批准执行”）批准 S1 为单个 standalone
  切片、single 执行/发布模式、squash 到 `main`；发布仍需单独授权。
