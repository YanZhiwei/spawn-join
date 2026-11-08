# Exploration: DeepAgents 官方 P0 能力补齐

- Delivery run: `deepagents-p0-capabilities-20261108`
- Lane: Feature
- Base: `7dbc714` (`origin/main`)
- Branch: `feat/012-deepagents-official-p0`
- Date: 2026-11-08

## Request

在 `spawn-join-agent-deepagents` 中新增上一轮分析确认的 P0 三项：

1. `AsyncSubAgent` 一等公民支持；
2. Memory / Skills 配置化与报告；
3. Harness / Provider Profile 注册、校验与报告。

## Evidence

- 当前实现：`packages/infra/agent-deepagents/src/spawn_join_agent_deepagents/`
  - `supervisor.py` 已透传 `backend/store/checkpointer/interrupt_on/skills/memory/cache`。
  - `subagents.py` 只支持 `SubAgentDefinition | CompiledSubAgentDefinition`。
  - `models.py` 只有 `SUPERVISOR/WORKER/SUMMARIZATION`。
- 上游锁文件：`deepagents 0.7.32`（`packages/infra/agent-deepagents/uv.lock`）。
- 上游源码核对（`D:/Repos/Github/spawn-join/packages/infra/agent-deepagents/.venv`）：
  - `create_deep_agent(subagents=...)` 通过 `graph_id` 识别 `AsyncSubAgent` 并自动装配
    `AsyncSubAgentMiddleware`；
  - `MemoryMiddleware`、`SkillsMiddleware` 是一等能力；
  - `HarnessProfile`/`ProviderProfile` 为 beta，注册后才被 `create_deep_agent` 读取。
- 本地规划：`specs/011-deepagents-product-capabilities/` 的 v1 明确把 remote async workers、
  MCP/sandbox/UI 等列为非目标；本次是 v1 之后的新增官方能力范围。

## Current tree (relevant)

```text
packages/infra/agent-deepagents/
├── src/spawn_join_agent_deepagents/
│   ├── supervisor.py      # SupervisorSpec / build_supervisor
│   ├── subagents.py       # declarative / compiled
│   ├── models.py          # model purposes
│   ├── middleware.py      # reserved names / scopes
│   ├── diagnostics.py     # AssemblyReport / lifecycle events
│   └── recovery.py
└── tests/
```

## Candidate change tree

```text
packages/infra/agent-deepagents/
├── src/spawn_join_agent_deepagents/
│   ├── subagents.py              # + AsyncSubAgentDefinition, SubAgentKind.ASYNC
│   ├── context_sources.py        # + MemoryConfiguration, SkillsConfiguration
│   ├── profiles.py               # + Harness/Provider profile bindings
│   ├── supervisor.py             # + wiring, gating, report
│   ├── diagnostics.py            # + ContextReport, ProfileReport, async warnings
│   └── __init__.py               # + public exports
└── tests/
    ├── test_async_subagents.py
    ├── test_context_sources.py
    ├── test_profiles.py
    └── test_upstream_contract.py # + 0.7.32 contract assertions
```

## Scope approved

用户输入 `新增p0三项`，明确批准上一轮列出的 P0-1/P0-2/P0-3：

- P0-1：异步子代理定义、beta opt-in、报告与错误语义；
- P0-2：Memory/Skills 配置对象、校验、`add_cache_control` 透传与报告；
- P0-3：Harness/Provider Profile 注册封装、保留名冲突校验、报告。

不包含 P1/P2（Rubric、Backend 工厂、HITL helper、Streaming 适配、异步诊断）。

## Alternatives

1. 让宿主直接使用上游 `AsyncSubAgent`/`MemoryMiddleware`/`register_harness_profile`，包不做代码。
   否决：无法统一校验、报告和 beta 开关，且 `SupervisorSpec.subagents` 对未知形态会
   抛出 `AttributeError` 而不是稳定配置错误。
2. 只在 README 记录上游用法。
   否决：用户明确要求“新增 P0 三项”，需要可测试的公共契约。
3. 新增独立 Distribution。
   否决：属于同一 Agent 装配边界，拆包没有复用收益。

## Risks

- `AsyncSubAgent` 与 `ProviderProfile` 均为 beta；必须显式 opt-in，不能进入稳定默认承诺。
- Harness/Provider profile 的注册是上游进程级注册表副作用；包只能校验保留名并记录本次
  run 注册的 key，不能完整内省最终图。
- Memory/Skills 的 source 可能是虚拟 backend 路径，装配期只做形状校验，不读取文件。
- 新增公共 API 属于 Feature；不提交、不推送、不创建 PR，等待单独授权。

## Excluded

- MCP Server、数据库、沙箱实现、Web/SSE 适配器、生产观测后端；
- 租户/授权/计费、UI、自动发布；
- P1/P2 能力（Rubric、Backend 工厂、HITL、streaming）。

## Research limitations

- 未联网核对官方在线文档；以上游已安装 `0.7.32` 源码与锁文件为准。
- 未在干净环境重新 `uv sync`；实现后以包级质量门结果为准。

## Verdict

`EXPLORATION_VERDICT: ready`
`SCOPE_APPROVAL: approved by user "新增p0三项" (2026-11-08)`
