# 决策上下文

- 模式：discover（pre-spec）
- 路线：feature
- Delivery run：`deepagents-planning-middleware-20261128`
- 决策上下文路径：`.specify/delivery/deepagents-planning-middleware-20261128/decision-context.md`
- 基线提交：`87e809f2b8d405c19d9bced4bfda89d018fa430e`

## 生效约束

| 来源 | 状态 | 与本请求相关的约束 |
| --- | --- | --- |
| `docs/decisions/agent/0010-deepagents-product-boundary.md` | Accepted | `spawn-join-agent-deepagents` 拥有产品装配、模型用途、中间件作用域、受控委派、诊断和资源透传。不得重写 DeepAgents 执行循环；中间件按 `.name` 替换仍由上游拥有。 |
| `docs/decisions/agent/0014-deepagents-p1-capabilities.md` | Proposed | beta seam 必须显式 opt-in；新增公共报告字段只使用稳定标签，不得泄漏提示或凭据；未配置时行为必须不变。 |
| `docs/decisions/agent/0012-deepagents-official-p0.md` | Accepted | 包消费官方 DeepAgents/LangChain 中间件，不重新实现。 |
| `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` | Accepted | 使用原生 LangChain 消息/模型和原生中间件契约。 |
| `docs/decisions/llm-provider/0008-model-file-and-env-boundary.md` | Accepted | Agent 包不得解析模型 YAML 或凭据。 |
| `docs/decisions/engineering/0016-desktop-first-service-ready-packages.md` | Accepted | 默认实现必须无需外部服务运行；本功能不增加运行时服务依赖。 |
| `.specify/memory/constitution.md` | 生效 | 公共契约需要显式测试、精确类型和文档化所有权。 |
| `packages/infra/agent-deepagents/README.md` | 当前契约 | 中间件作用域、保留名和 opt-in 能力文档属于包公共面。 |

## 相关当前行为

- 已安装的 `deepagents==0.7.32` 在 `create_deep_agent` 中构建默认栈：
  `FilesystemMiddleware`、可选 `SubAgentMiddleware`、`SummarizationMiddleware`
  和 `PatchToolCallsMiddleware`；默认不添加 `TodoListMiddleware`
  （`site-packages/deepagents/graph.py`）。
- 只有 Codex harness profile 显式添加 `TodoListMiddleware`
  （`site-packages/deepagents/profiles/harness/_openai_codex.py`），因此上游 planning
  是模型 profile 专属能力，不是通用产品能力。
- `langchain==1.4.8` 导出稳定的 `TodoListMiddleware`
  （`langchain.agents.middleware`）；其 `.name` 为 `TodoListMiddleware`，提供
  `write_todos` 工具。
- `spawn-join-agent-deepagents` 当前公开 `MiddlewareConfiguration` 的
  supervisor/workers/override 作用域，但没有 planning 配置、没有
  `TodoListMiddleware` 引用，也没有 planning 文档。宿主可以通过
  `MiddlewareConfiguration` 注入原始 `TodoListMiddleware`，但该路径未文档化、
  未测试，也不在装配报告中表达。

## 冲突与待决事项

- 与 ADR-0010 不冲突：planning 是 DeepAgents/LangChain 中间件加产品配置 seam，
  不是执行循环重写。
- Plan 需要决定：
  1. planning 是 opt-in（`planning: PlanningConfiguration | None = None`）还是默认开启。
     默认开启会改变所有现有图的工具/提示，违反“未配置行为不变”的先例。
  2. 首版作用域仅 supervisor 还是也包含声明式 worker。
  3. 是否在 `AssemblyReport` 增加小型 `PlanningReport`，还是复用现有
     `middleware.supervisor_names`/`warnings`。
  4. 新公共 seam 是否需要 Proposed ADR-0019（参照 ADR-0014 先例，预计需要）。
- 证据缺口：仓库没有产品开发工作流包；本请求仅限现有 agent 包的 planning 中间件
  seam，不是需求到评审的工作流引擎。
