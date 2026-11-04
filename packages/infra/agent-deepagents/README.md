# spawn-join-agent-deepagents

`spawn-join-agent-deepagents` 是 SpawnJoin 的 DeepAgents 产品装配包。它把实际产品中反复出现的
Agent 接线问题收敛成可测试的公共契约，同时保留 DeepAgents、LangChain 和 LangGraph 的原生
执行、Checkpoint、interrupt、resume 和 streaming 能力。

## 状态与兼容性

- 版本与稳定性：`0.1.0`，preview；`0.x` 期间公共 API 仍可能按文档化变更调整。
- 运行时：Python `>=3.11`；DeepAgents `0.7.x`；LangChain/LangGraph 1.x。
- 发布状态：当前仅支持仓库内本地开发，尚未发布到 PyPI 或私有 Registry。

## 提供的能力

- 从显式模型用途构建 supervisor，返回原生 LangGraph 图和不可变装配报告；
- 声明式与 compiled 子代理；compiled 子代理保留自己的图、模型和内部中间件；
- supervisor、workers、per-subagent override 三种 Middleware 作用域；
- 显式 async-first 委派控制器：并发上限、有界 FIFO、deadline、取消和失败语义；
- 可选同步/异步诊断回调，以及脱敏的装配/生命周期记录；
- 宿主拥有 Store、Backend、Checkpointer、MCP Session、沙箱和业务工具；
- 独立 wheel/sdist、`py.typed`、包级测试、质量 profile 和 CI 矩阵。

## 安装

从仓库根目录使用该 Distribution 自己的环境：

```powershell
uv lock --check --directory packages/infra/agent-deepagents
uv sync --locked --directory packages/infra/agent-deepagents
```

运行时依赖：

- `deepagents>=0.7.32,<0.8`
- `langchain>=1.4.7,<2.0`
- `langchain-core>=1.7.0,<2.0`
- `langgraph>=1.2,<2`
- `spawn-join-llm-provider-langchain>=0.1.0,<0.2.0`

本包不重复解析 `model.yaml`、`.env` 或 Provider SDK；配置模型由
[`spawn-join-llm-provider-langchain`](../llm-provider-langchain/README.md) 创建。

## 快速开始

宿主可以直接注入已有的 `BaseChatModel`，也可以传入 `ModelCatalog`：

```python
from langchain_core.messages import HumanMessage
from spawn_join_llm_provider_langchain import ModelCatalog

from spawn_join_agent_deepagents import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    SubAgentDefinition,
    SupervisorSpec,
    build_supervisor,
)

catalog = ModelCatalog.from_file("model.yaml")
models = ModelBindings(
    catalog=catalog,
    bindings=(
        ModelBinding(ModelPurpose.SUPERVISOR, catalog="coordinator"),
        ModelBinding(ModelPurpose.WORKER, catalog="worker"),
        ModelBinding(
            ModelPurpose.SUMMARIZATION,
            inherit_from=ModelPurpose.SUPERVISOR,
        ),
    ),
)

assembly = build_supervisor(
    SupervisorSpec(
        models=models,
        name="coordinator",
        subagents=(
            SubAgentDefinition(
                name="researcher",
                description="Research a bounded question and return findings.",
                system_prompt="Return a concise, source-grounded result.",
            ),
        ),
    )
)

result = await assembly.graph.ainvoke(
    {"messages": [HumanMessage(content="Research the topic.")]}
)
print(assembly.report)
```

装配只读取配置并创建图，不会执行图、打开外部连接或关闭宿主资源。运行 `ainvoke`/`astream`
时，使用宿主自己的模型、工具、Store、Checkpointer 和业务资源。

离线、无密钥的完整示例：

- [`examples/basic_supervisor.py`](examples/basic_supervisor.py)
- [`examples/governed_delegation.py`](examples/governed_delegation.py)

```powershell
uv run --locked --directory packages/infra/agent-deepagents python examples/basic_supervisor.py
uv run --locked --directory packages/infra/agent-deepagents python examples/governed_delegation.py
```

## 模型用途

| 用途 | 规则 |
|---|---|
| `SUPERVISOR` | 必须直接绑定；不能继承 |
| `WORKER` | 声明式子代理使用；可显式 `inherit_from` |
| `SUMMARIZATION` | 默认必须绑定；可显式 `inherit_from` |

- 不允许隐式回退到 supervisor、Catalog 默认模型或另一个用途；
- 同一用途只解析一个模型实例，并在所有消费者中复用；
- 继承必须显式声明；循环、缺失、未知 Catalog 条目和创建失败都会在装配前报错；
- compiled 子代理拥有自己的模型，本包不检查或替换。

`SUMMARIZATION` 默认必填，因为 DeepAgents 的默认栈始终包含 summarization。生成的
`SummarizationMiddleware` 会原位替换默认实例，而不是追加重复实例。

## 子代理

- `SubAgentDefinition`：声明式 worker，支持 `tools`、`middleware`、`interrupt_on`、
  `response_format`、`skills`、`permissions` 和上下文模式；
- `CompiledSubAgentDefinition`：宿主提供的 runnable，保留自己的图、模型和内部中间件；
- 名称在两种形态之间必须唯一；
- `tools=None` 表示沿用上游工具继承，`tools=()` 表示显式不提供额外工具；
- `mode="fork"` 是 DeepAgents beta，只能通过
  `SupervisorSpec(allow_experimental_fork=True)` 显式开启，且不进入稳定兼容承诺。

## Middleware 作用域

```python
from spawn_join_agent_deepagents import MiddlewareConfiguration

middleware = MiddlewareConfiguration(
    supervisor=(supervisor_audit,),
    workers=(worker_rate_limit,),
    worker_overrides={"researcher": (research_trace,)},
)
```

有效顺序：定义级 middleware、全局 worker middleware、命名 override、生成的
summarization middleware。compiled 子代理不接收任何注入。

- 同一作用域内重复 `.name` 会被拒绝；
- `"SummarizationMiddleware"` 和包内部 middleware 名称保留；
- 上游 `.name` 替换语义原样保留，包不实现第二套 registry；
- assembly report 记录实际生效的名称和作用域。

## 委派

```python
from spawn_join_agent_deepagents import (
    DelegationConfiguration,
    DelegationPolicy,
)

delegation = DelegationConfiguration(
    policy=DelegationPolicy(
        max_concurrency=4,
        max_queue=16,
        deadline_seconds=120,
    )
)
```

- 控制器由宿主注入或显式创建，可跨同一事件循环内的运行复用，不使用进程全局状态；
- 有界 FIFO 队列；超过 `max_queue` 立即返回 `DelegationQueueFullError`；
- `deadline_seconds` 覆盖排队和执行；到期抛出 `DelegationTimeoutError` 并清理槽位；
- 父任务取消会清理排队/活动状态并传播 `asyncio.CancelledError`；
- worker 失败保留原始异常；超时、取消和失败在诊断中可区分；
- **委派策略只支持异步执行**。配置策略后使用 `invoke`/`stream` 会在 `task` 调用明确抛出
  `UnsupportedSyncDelegationError`，不会伪装可抢占的同步 deadline。未配置策略时同步执行保持原生行为。

## 诊断

```python
from spawn_join_agent_deepagents import DiagnosticsConfig

def on_event(event):
    print(event.event_type, event.subagent_name, event.outcome)

diagnostics = DiagnosticsConfig(sync_callback=on_event)
```

- 装配报告不可变且只包含安全标签；
- 生命周期记录区分 selected、queued、started、completed、failed、timed_out、cancelled、
  interrupted、rejected；
- 相关性来自原生 `tool_call_id`、`run_id` 和可选的 `thread_id`；
- 失败只记录稳定的错误类别/类名，不记录异常消息；
- 同步执行调用同步回调；异步执行先调用同步回调，再 await 异步回调；
- 只配置异步回调但使用同步执行时，不伪造事件循环，装配报告记录 warning；
- 回调异常会传播；宿主负责日志、追踪、UI、持久化和背压。

## 资源与恢复

```python
from spawn_join_agent_deepagents import RecoveryContext

config = RecoveryContext(thread_id="conversation-1").to_graph_config()
```

- Store、Backend、Checkpointer、MCP Session、沙箱和业务工具由宿主创建、保持有效并关闭；
- 本包只校验 `interrupt_on` 需要 checkpointer、`thread_id` 非空，并透传原生 LangGraph 语义；
- 恢复使用原生 `Command(resume=...)` 和同一 `thread_id`；
- 本包不创建或关闭宿主资源，不承诺 exactly-once 副作用；
- 调用方应使用 `to_graph_config()` 生成 native config，或自行提供等价的 `configurable.thread_id`。

## 公共 API

公共导出由 `spawn_join_agent_deepagents.__all__` 定义，主要包括：

- `build_supervisor`、`SupervisorSpec`、`SupervisorAssembly`；
- `ModelPurpose`、`ModelBinding`、`ModelBindings`、`ResolvedModelBindings`；
- `SubAgentDefinition`、`CompiledSubAgentDefinition`、`SubAgentKind`、`SubAgentMode`；
- `MiddlewareConfiguration`、`MiddlewareScopeReport`；
- `DelegationPolicy`、`DelegationController`、`DelegationConfiguration`；
- `DiagnosticsConfig`、`DiagnosticCallback`、`AsyncDiagnosticCallback`、`DiagnosticEvent`、
  `DiagnosticEventType`、`AssemblyReport`、`SubagentReport`、`DelegationReport`、`ResourceReport`；
- `RecoveryContext`；
- 稳定错误类型（`AgentConfigurationError` 及其子类）。

内部模块不会因为可导入就自动成为公共契约。

## 错误与失败行为

- `AgentConfigurationError` 是装配期配置错误基类；模型、子代理、Middleware、恢复和委派
  各有稳定子类，便于调用方区分失败类别。
- 配置错误在 `create_deep_agent` 前抛出，不会返回半配置图；上游装配异常保留 `__cause__`。
- 委派队列满、deadline、父级取消、worker 失败和中断具有可区分语义；worker 原始异常
  不会被转换为成功结果。
- 诊断回调异常会传播，不会被静默吞掉；异步回调只在异步执行中 await。

## 兼容性与限制

- Python `>=3.11`；
- DeepAgents `>=0.7.32,<0.8`；升级到 0.8 需要单独的兼容验证；
- `fork` 子代理是 beta，不包含在稳定兼容承诺中；
- 受控委派仅异步；同步策略明确报错；
- 不实现 MCP Server、数据库、沙箱、Web/SSE、生产观测后端、租户/授权/计费、产物台账或 UI；
- 不提供自动 PR、发布或后台调度。

## 开发与验证

```powershell
uv lock --check --directory packages/infra/agent-deepagents
uv sync --locked --directory packages/infra/agent-deepagents
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents
```

- 布局：`src/spawn_join_agent_deepagents/` 是运行时源码，`tests/` 是离线测试，
  `examples/` 是可执行示例；包内自带 `uv.lock`、`py.typed` 和 `LICENSE`。
- 必需工具：uv `>=0.7.13`、PowerShell 7、Git、Node.js 22+（Pyright 包装器），以及包
  dev group 中的 Black/isort/Ruff/Pyright/pytest。
- 包级质量门执行 Black/isort、Ruff、Pyright strict、pytest、wheel/sdist、隔离安装、
  `pip check` 和隔离导入。离线测试不读取真实密钥、不连接外部服务。

## 发布与版本

本包使用独立版本号和独立 wheel/sdist，不随其他 Distribution 隐式发布。当前版本为
`0.1.0`，尚未发布；发布必须经过仓库质量门、独立评审和单独的发布授权。公共 API 的
破坏性变更应更新版本、文档和兼容性说明，并重新运行包级与仓库级门禁。

## 维护与贡献

本包由 SpawnJoin 仓库维护者拥有；变更遵循 `AGENTS.md`、[包边界](../../../docs/architecture/package-boundaries.md)
和 [ADR-0010](../../../docs/decisions/agent/0010-deepagents-product-boundary.md)。新能力或公共
契约变更走 Feature 交付路由；缺陷走 Bugfix；纯文档或机械改动走 Lightweight。提交前必须
提供与当前 diff 绑定的质量、标准和评审证据。

## 相关文档

- [ADR-0010：DeepAgents 产品边界](../../../docs/decisions/agent/0010-deepagents-product-boundary.md)
- [包边界](../../../docs/architecture/package-boundaries.md)
- [仓库地图](../../../docs/architecture/repository-map.md)
- [质量门说明](../../../docs/development/quality-gates.md)

## 许可证

本包为专有软件，保留所有权利。详见 [LICENSE](LICENSE)。
