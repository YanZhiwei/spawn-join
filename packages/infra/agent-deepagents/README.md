# spawn-join-agent-deepagents

[简体中文](README.md) | [English](README.en.md)

`spawn-join-agent-deepagents` 是 SpawnJoin 的 DeepAgents 产品装配包。它把实际产品中反复出现的
Agent 接线问题收敛成可测试的公共契约，同时保留 DeepAgents、LangChain 和 LangGraph 的原生
执行、Checkpoint、interrupt、resume 和 streaming 能力。

**目录**

- [状态与兼容性](#状态与兼容性)
- [提供的能力](#提供的能力)
- [安装](#安装)
- [快速开始](#快速开始)
  - [1. 先运行完整离线示例](#1-先运行完整离线示例)
  - [2. 连接自己的模型服务](#2-连接自己的模型服务)
- [模型用途](#模型用途)
- [子代理](#子代理)
  - [AsyncSubAgent（远程子代理）](#asyncsubagent远程子代理)
  - [AsyncSubAgent 字段说明](#asyncsubagent-字段说明)
  - [远程执行流程](#远程执行流程)
  - [本地与远程子代理对比](#本地与远程子代理对比)
- [Middleware 作用域](#middleware-作用域)
- [Memory、Skills 与 Profile](#memoryskills-与-profile)
  - [完整可运行示例](#完整可运行示例)
- [委派](#委派)
- [诊断](#诊断)
- [资源与恢复](#资源与恢复)
- [公共 API](#公共-api)
- [错误与失败行为](#错误与失败行为)
- [兼容性与限制](#兼容性与限制)
- [开发与验证](#开发与验证)
- [发布与版本](#发布与版本)
- [维护与贡献](#维护与贡献)
- [相关文档](#相关文档)
- [许可证](#许可证)

## 状态与兼容性

- 版本与稳定性：`0.1.0`，preview；`0.x` 期间公共 API 仍可能按文档化变更调整。
- 运行时：Python `>=3.11`；DeepAgents `0.7.x`；LangChain/LangGraph 1.x。
- 发布状态：当前仅支持仓库内本地开发，尚未发布到 PyPI 或私有 Registry。

## 提供的能力

- 从显式模型用途构建 supervisor，返回原生 LangGraph 图和不可变装配报告；
- 声明式、compiled 和远程 async 子代理；compiled/async 子代理保留自己的执行边界；
- supervisor、workers、per-subagent override 三种 Middleware 作用域；
- Memory/Skills 配置对象，支持 memory cache-control 选择；
- 上游 Harness/Provider profile 的显式注册、保留名校验和报告；
- 显式 async-first 委派控制器：并发上限、有界 FIFO、deadline、取消和失败语义；
- 可选同步/异步诊断回调，以及脱敏的装配/生命周期记录；
- 宿主拥有 Store、Checkpointer、MCP Session、沙箱、业务工具和宿主提供的 Backend；
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

### 1. 先运行完整离线示例

从仓库根目录执行，无需模型文件或密钥：

```powershell
uv run --locked --directory packages/infra/agent-deepagents python examples/basic_supervisor.py
uv run --locked --directory packages/infra/agent-deepagents python examples/governed_delegation.py
uv run --locked --directory packages/infra/agent-deepagents python examples/p0_capabilities.py
```

完整源码：[基础 supervisor](examples/basic_supervisor.py)、[受控委派](examples/governed_delegation.py)、
[官方 P0 能力](examples/p0_capabilities.py)。
它们使用同目录的 [`fake_model.py`](examples/fake_model.py) 提供确定性离线响应；请在仓库中
运行这些文件，而不是单独复制其中一个文件。第一个示例输出装配报告、worker 的
`research result` 和最终的 `The supervisor's final answer.`；第二个还输出 `Events:`
生命周期列表；第三个输出 `Context`、`Profiles`、`Subagents` 分区和同样的最终回答。
报告的完整 repr 不是稳定输出契约。

### 2. 连接自己的模型服务

宿主可以直接注入已有的 `BaseChatModel`，也可以传入 `ModelCatalog`。下面是完整的
Catalog 集成：在仓库根目录保存 `model.yaml`，把示例 endpoint 和 model 替换成服务实际值，
并在进程环境中设置 `LLM_API_KEY`（两个用途共享该凭据）：

```yaml
schema_version: 1
default: coordinator
models:
  coordinator:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: your-supervisor-model
    api_key_env: LLM_API_KEY
  worker:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: your-worker-model
    api_key_env: LLM_API_KEY
```

模型需要支持工具调用。将下面代码保存为仓库根目录的 `supervisor_demo.py`，执行
`uv run --locked --project packages/infra/agent-deepagents python supervisor_demo.py`。
执行图会将提示词发送给所配置的服务；回复内容由服务决定。

```python
import asyncio

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

async def main() -> None:
    catalog = ModelCatalog.from_file("model.yaml", env_file=None)
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
    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
```

装配只读取配置并创建图，不会执行图、打开外部连接或关闭宿主资源。运行 `ainvoke`/`astream`
时，使用宿主自己的模型、工具、Store、Checkpointer 和业务资源。

后续章节的配置片段用于组合到 `SupervisorSpec`，不是独立程序。
委派与诊断如何接入装配和执行，见上面的完整受控委派示例。

## 模型用途

| 用途 | 规则 |
|---|---|
| `SUPERVISOR` | 必须直接绑定；不能继承 |
| `WORKER` | 声明式子代理和默认受控的 `general-purpose` 使用；可显式 `inherit_from`；默认需要绑定 |
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
- `AsyncSubAgentDefinition`：远程 Agent Protocol 子代理，按原生 `graph_id`/`url`/
  `headers`/`webhook` 透传；必须显式设置
  `SupervisorSpec(allow_experimental_async_subagents=True)`，`mode="fork"` 还需
  `allow_experimental_fork=True`，且只支持异步执行路径；
- 名称在三种形态之间必须唯一；
- `tools=None` 表示沿用上游工具继承，`tools=()` 表示显式不提供额外工具；
- 默认情况下，如果没有声明 `general-purpose`，包会注入一个受控的 `general-purpose`：
  使用 `WORKER` 模型和 `workers` middleware，并出现在装配报告中；
- `SupervisorSpec(control_default_subagent=False)` 保留上游 supervisor-owned 的
  `general-purpose`；报告将其标记为 `upstream_default`，并警告 `WORKER` 和 worker
  middleware 不适用。若模型 harness profile 禁用了该默认子代理，报告条目表示上游默认约定，
  最终以实际图为准；
- `mode="fork"` 是 DeepAgents beta，只能通过
  `SupervisorSpec(allow_experimental_fork=True)` 显式开启，且不进入稳定兼容承诺。

### AsyncSubAgent（远程子代理）

`AsyncSubAgentDefinition` 不是“在本进程再建一个 agent”，而是登记一个运行在远程
Agent Protocol 服务上的子代理。远程服务拥有自己的模型、工具和运行环境；本包只负责校验
声明、转换成 DeepAgents 原生 `AsyncSubAgent`，并在装配报告中说明它。

#### Agent Protocol 是什么

Agent Protocol 是一套面向 Agent 服务的 HTTP 接口约定：客户端可以查询 assistant/graph、
创建 thread、启动 run、查询状态和结果。LangGraph Platform 实现了它；自托管服务也可以用
FastAPI 等实现同样的接口。DeepAgents 的 `AsyncSubAgentMiddleware` 通过 `langgraph_sdk`
调用这些接口，所以：

- `url` 是“远程服务地址”；
- `graph_id` 是“远程服务上的哪个 agent/graph/assistant”。

#### AsyncSubAgent 字段说明

| 字段 | 必填 | 默认 | 大白话 |
| --- | --- | --- | --- |
| `name` | 是 | 无 | 本地给这个远程代理起的名字，supervisor 用它选人 |
| `description` | 是 | 无 | 告诉模型“它适合干什么”，模型靠它决定是否派活 |
| `graph_id` | 是 | 无 | 远程服务上的 graph/assistant ID，相当于“找哪个团队” |
| `url` | 否 | SDK 默认地址 | Agent Protocol 服务地址；省略时使用 LangGraph SDK 默认端点或本地 ASGI transport |
| `headers` | 否 | 无 | 调远程服务时附加的 HTTP headers，通常放认证信息；不会进入报告 |
| `webhook` | 否 | 无 | 远程 run 结束时回调的 URL，供宿主自行接收完成通知 |
| `update_strategy` | 否 | `"interrupt"` | 运行中再发跟进消息：`interrupt` 打断当前 run，`enqueue` 排队等当前 run 结束 |
| `notify_parent` | 否 | 上游默认 `True` | 远程任务完成时是否允许唤醒当前 agent；应用自己用 webhook 交付时可设为 `False` |
| `mode` | 否 | `"isolated"` | `isolated` 使用独立上下文；`fork` 复制父对话历史（beta，需要远程侧配置匹配） |

最小写法只需要前三个字段：

```python
AsyncSubAgentDefinition(
    name="remote-researcher",
    description="Research a bounded question on the remote deployment.",
    graph_id="research_agent",
)
```

真实部署通常还会带地址和认证头（密钥必须来自宿主环境，不要硬编码）：

```python
AsyncSubAgentDefinition(
    name="remote-researcher",
    description="Research a bounded question on the remote deployment.",
    graph_id="research_agent",
    url="https://my-deployment.langsmith.dev",
    headers={"Authorization": f"Bearer {token_from_host}"},
    update_strategy="enqueue",
    notify_parent=False,
    webhook="https://my-app.example.com/agent-events",
)
```

#### 远程执行流程

1. `build_supervisor` 只做校验和转换，**不连接远程服务**。
2. `create_deep_agent` 看到 `graph_id` 后自动安装 `AsyncSubAgentMiddleware`。
3. supervisor 模型会多出一组异步任务工具：`start_async_task`、`check_async_task`、
   `update_async_task`、`cancel_async_task`、`list_async_tasks`。
4. 模型调用 `start_async_task`，立刻拿到 `task_id`，然后可以继续做别的事。
5. 远程服务在自己的进程里执行真正的 agent。
6. 模型之后可以查状态/取结果，或者依赖 webhook / `notify_parent` 接收完成通知。
7. 这条路径要求 `ainvoke` / `astream` 异步执行；远程服务必须实现 Agent Protocol。

这也是它和普通子代理最大的区别：普通子代理是“派活并等结果”，async 子代理是
“先拿工单号，稍后查进度”。

#### 本地与远程子代理对比

| | `SubAgentDefinition` | `AsyncSubAgentDefinition` |
| --- | --- | --- |
| 模型在哪 | 当前进程 | 远程服务 |
| 是否等结果 | 等 | 先拿 `task_id`，稍后查 |
| 包是否注入 Middleware | 会 | 不会 |
| 报告中的模型来源 | `purpose:worker` 等 | `remote:<graph_id>` |
| 是否需要远程服务 | 不需要 | 需要 Agent Protocol 服务 |
| beta 开关 | `fork` 才需要 | `allow_experimental_async_subagents=True` |

注意：`examples/p0_capabilities.py` 里的 `url="https://example.invalid"` 只是展示字段，
示例并不会调用远程子代理，因此不会联网，也不会因为地址不可达而失败。

## Middleware 作用域

下面的 `supervisor_audit`、`worker_rate_limit`、`research_trace` 是宿主提供的
LangChain middleware 实例；构造后通过 `SupervisorSpec(middleware=middleware, ...)` 接入。

```python
from spawn_join_agent_deepagents import MiddlewareConfiguration

middleware = MiddlewareConfiguration(
    supervisor=(supervisor_audit,),
    workers=(worker_rate_limit,),
    worker_overrides={"researcher": (research_trace,)},
)
```

请求顺序：定义级 middleware、全局 worker middleware、命名 override、生成的
summarization middleware。DeepAgents 会按 `.name` 原位替换默认 summarization，因此最终
base-stack 位置由上游决定；报告记录请求名称和 `replaced_defaults`，不声称 summarization 一定最后执行。
compiled 子代理不接收任何注入。

- 同一作用域内重复 `.name` 会被拒绝；
- `"SummarizationMiddleware"` 和包内部 middleware 名称保留；
- 上游 `.name` 替换语义原样保留，包不实现第二套 registry；
- assembly report 记录实际生效的名称和作用域。

## Memory、Skills 与 Profile

```python
from spawn_join_agent_deepagents import (
    HarnessProfileBinding,
    MemoryConfiguration,
    ProfilesConfiguration,
    SkillsConfiguration,
)
from deepagents import HarnessProfile

spec = SupervisorSpec(
    models=models,
    memory=MemoryConfiguration(sources=("AGENTS.md",), add_cache_control=False),
    skills=SkillsConfiguration(sources=("skills",)),
    profiles=ProfilesConfiguration(
        harness=(
            HarnessProfileBinding(
                "openai:gpt-5.4",
                HarnessProfile(system_prompt_suffix="Be concise."),
            ),
        )
    ),
    allow_experimental_profiles=True,
)
```

- `MemoryConfiguration` / `SkillsConfiguration` 拒绝空、空白和重复 source；装配期不读取
  source，宿主或虚拟 Backend 负责实际内容。
- `add_cache_control=True`（默认）继续由上游创建 `MemoryMiddleware`；`False` 时本包自己创建
  同名实例并向上游传 `memory=None`，因此没有可替换的上游默认实例，fork 子代理也不会继承
  这份 memory。
- `ProfilesConfiguration` 在 `create_deep_agent` 前调用上游
  `register_harness_profile` / `register_provider_profile`；这是 beta 的进程级注册表，
  必须显式开启 `allow_experimental_profiles=True`。Provider profile 只影响上游从字符串
  构造模型的路径；本包始终传 `BaseChatModel`，所以对已解析实例不生效。
- profile 的 `excluded_middleware` 不得包含本包保留名
  （`SummarizationMiddleware`、`spawn_join_delegation_policy`、`spawn_join_diagnostics`）。
- 装配报告的 `context` 只记录 source 数量和管理方式，`profiles` 只记录注册 key；
  不记录路径、URL、headers 或凭据。

### 完整可运行示例

下面的脚本与 [`examples/p0_capabilities.py`](examples/p0_capabilities.py) 一致：用临时
`FilesystemBackend` 提供 memory/skills 文件，用 fake model 离线执行，同时声明一个不会被
调用的远程 async 子代理。运行：

```powershell
uv run --locked --directory packages/infra/agent-deepagents python examples/p0_capabilities.py
```

```python
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any, cast

from deepagents import HarnessProfile
from deepagents.backends import FilesystemBackend
from fake_model import FakeChatModel
from langchain_core.messages import AIMessage, HumanMessage

from spawn_join_agent_deepagents import (
    AsyncSubAgentDefinition,
    HarnessProfileBinding,
    MemoryConfiguration,
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    ProfilesConfiguration,
    SkillsConfiguration,
    SubAgentDefinition,
    SupervisorSpec,
    build_supervisor,
)


def _task_call() -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "task",
                "args": {
                    "description": "Research the topic.",
                    "subagent_type": "researcher",
                },
                "id": "call-researcher",
                "type": "tool_call",
            }
        ],
    )


async def main() -> None:
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root)
        (root / "AGENTS.md").write_text(
            "# Agent memory\n\nReturn concise answers.\n",
            encoding="utf-8",
        )
        skill = root / "skills" / "web-research"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\n"
            "name: web-research\n"
            "description: Research a bounded question.\n"
            "---\n\n"
            "Use the available research tools and cite the result.\n",
            encoding="utf-8",
        )

        supervisor = FakeChatModel(
            responses=[
                _task_call(),
                AIMessage(content="The supervisor's final answer."),
            ]
        )
        worker = FakeChatModel(responses=[AIMessage(content="research result")])
        models = ModelBindings(
            catalog=None,
            bindings=(
                ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor),
                ModelBinding(ModelPurpose.WORKER, model=worker),
                ModelBinding(
                    ModelPurpose.SUMMARIZATION,
                    inherit_from=ModelPurpose.SUPERVISOR,
                ),
            ),
        )

        assembly = build_supervisor(
            SupervisorSpec(
                models=models,
                backend=FilesystemBackend(root_dir=root),
                memory=MemoryConfiguration(
                    sources=("/AGENTS.md",),
                    add_cache_control=False,
                ),
                skills=SkillsConfiguration(sources=("/skills",)),
                profiles=ProfilesConfiguration(
                    harness=(
                        HarnessProfileBinding(
                            "example:fake-model",
                            HarnessProfile(system_prompt_suffix="Be concise."),
                        ),
                    )
                ),
                allow_experimental_profiles=True,
                subagents=(
                    SubAgentDefinition(
                        name="researcher",
                        description="Research a bounded question.",
                        system_prompt="Return a concise result.",
                    ),
                    AsyncSubAgentDefinition(
                        name="remote-researcher",
                        description="A remote Agent Protocol worker.",
                        graph_id="research_agent",
                        url="https://example.invalid",
                    ),
                ),
                allow_experimental_async_subagents=True,
                name="coordinator",
            )
        )

        result = cast(
            dict[str, Any],
            await assembly.graph.ainvoke(
                {"messages": [HumanMessage(content="Start the research.")]}
            ),
        )

        print("Report:", assembly.report)
        print("Context:", assembly.report.context)
        print("Profiles:", assembly.report.profiles)
        print("Subagents:", [(item.name, item.kind) for item in assembly.report.subagents])
        for message in cast(list[Any], result["messages"]):
            print(type(message).__name__, getattr(message, "content", ""))


if __name__ == "__main__":
    asyncio.run(main())
```

要点：

- `MemoryConfiguration(add_cache_control=False)` 走包自己创建 `MemoryMiddleware` 的路径；
  `FilesystemBackend` 由宿主提供，示例退出时由 `TemporaryDirectory` 清理。
- `SkillsConfiguration(sources=("/skills",))` 指向包含 `web-research/SKILL.md` 的目录；
  缺少有效 frontmatter 的文件会被上游跳过并记录 warning。
- `AsyncSubAgentDefinition` 只参与装配和报告；示例不会调用远程子代理，因此没有网络依赖。
- `ProfilesConfiguration` 注册的 harness profile 是 beta 进程级状态；示例 key 不会匹配
  fake model，所以只用于展示注册、校验和报告，不改变离线输出。

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
from spawn_join_agent_deepagents import DiagnosticEvent, DiagnosticsConfig

def on_event(event: DiagnosticEvent) -> None:
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

- Store、Checkpointer、MCP Session、沙箱、业务工具和宿主提供的 Backend 由宿主创建、保持有效并关闭；
- 宿主省略 `backend` 时，包会创建一个无外部关闭路径的内存 `StateBackend`，报告为 `default_state`；
- 本包校验显式 `interrupt_on`、声明式子代理 `interrupt_on` 和
  `FilesystemPermission(mode="interrupt")` 都需要 checkpointer，并透传原生 LangGraph 语义；
- 恢复使用原生 `Command(resume=...)` 和同一 `thread_id`；
- 本包不创建或关闭宿主资源，不承诺 exactly-once 副作用；
- 调用方应使用 `to_graph_config()` 生成 native config，或自行提供等价的 `configurable.thread_id`。

## 公共 API

公共导出由 `spawn_join_agent_deepagents.__all__` 定义，主要包括：

- `build_supervisor`、`SupervisorSpec`、`SupervisorAssembly`；
- `ModelPurpose`、`ModelBinding`、`ModelBindings`、`ResolvedModelBindings`；
- `SubAgentDefinition`、`CompiledSubAgentDefinition`、`AsyncSubAgentDefinition`、
  `SubAgentKind`（含 `UPSTREAM_DEFAULT`、`ASYNC`）、`SubAgentMode`；
- `MemoryConfiguration`、`SkillsConfiguration`；
- `ProfilesConfiguration`、`HarnessProfileBinding`、`ProviderProfileBinding`；
- `MiddlewareConfiguration`、`MiddlewareScopeReport`；
- `DelegationPolicy`、`DelegationController`、`DelegationConfiguration`；
- `DiagnosticsConfig`、`DiagnosticCallback`、`AsyncDiagnosticCallback`、`DiagnosticEvent`、
  `DiagnosticEventType`、`AssemblyReport`、`SubagentReport`、`DelegationReport`、
  `ResourceReport`、`ContextReport`、`ProfileReport`；
- `RecoveryContext`；
- 稳定错误类型（`AgentConfigurationError` 及其子类，包括 `ContextConfigurationError`、
  `ProfileConfigurationError`）。

内部模块不会因为可导入就自动成为公共契约。

## 错误与失败行为

- `AgentConfigurationError` 是装配期配置错误基类；模型、子代理、Middleware、恢复、Memory/
  Skills 和 Profile 各有稳定子类，便于调用方区分失败类别。
- 配置错误在 `create_deep_agent` 前抛出，不会返回半配置图；上游装配/注册异常保留 `__cause__`。
- async 子代理和 profile 注册未显式开启 beta 开关时，在装配前失败。
- 未知子代理形态、空白 `graph_id`、重复 key 或 profile 排除保留 Middleware 名都会得到
  稳定配置错误，而不是上游 `AttributeError` 或静默忽略。
- 委派队列满、deadline、父级取消、worker 失败和中断具有可区分语义；worker 原始异常
  不会被转换为成功结果。
- 诊断回调异常会传播，不会被静默吞掉；异步回调只在异步执行中 await。

## 兼容性与限制

- Python `>=3.11`；
- DeepAgents `>=0.7.32,<0.8`；升级到 0.8 需要单独的兼容验证；
- `fork` 子代理是 beta，不包含在稳定兼容承诺中；
- async 子代理是 beta，依赖远程 Agent Protocol 服务和异步执行路径；
- Harness/Provider profile 是上游 beta，注册为进程级副作用；
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
