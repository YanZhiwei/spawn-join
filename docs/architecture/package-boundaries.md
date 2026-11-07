# SpawnJoin Package Boundaries

> 本文件维护包的职责、依赖方向和公共边界。
> 每个 Distribution 的名称、版本、依赖和构建配置以对应的 `pyproject.toml` 为最终来源。

## Package Map

| Distribution | Import package | 路径 | 分组 | 允许承担的职责 |
|---|---|---|---|---|
| `spawn-join-core` | `spawn_join_core` | [`packages/core/spawn-join-core`](../../packages/core/spawn-join-core/) | `core` | 跨领域稳定的配置机制、异常、类型和基础协议 |
| `spawn-join-common` | `spawn_join_common` | [`packages/core/common`](../../packages/core/common/) | `core` | 按功能组织的跨领域公共辅助实现；严格读取与可选 Pydantic 异常转换 |
| `spawn-join-llm-provider` | `spawn_join_llm_provider` | [`packages/core/llm-provider`](../../packages/core/llm-provider/) | `core` | 与框架无关的 LLM 协议选项、渠道契约和稳定错误 |
| `spawn-join-llm-provider-langchain` | `spawn_join_llm_provider_langchain` | [`packages/infra/llm-provider-langchain`](../../packages/infra/llm-provider-langchain/) | `infra` | LangChain 模型工厂、协议选项映射和配置校验 |
| `spawn-join-llm-model-sync` | `spawn_join_llm_model_sync` | [`packages/infra/llm-model-sync`](../../packages/infra/llm-model-sync/) | `infra` | 手动模型元数据同步、源注册和确定性快照生成 |
| `spawn-join-agent-deepagents` | `spawn_join_agent_deepagents` | [`packages/infra/agent-deepagents`](../../packages/infra/agent-deepagents/) | `infra` | DeepAgents 产品装配、模型用途绑定、Middleware 作用域、受控委派、诊断和恢复边界 |

当前 LLM 包已实现渠道/选项契约、LangChain 模型工厂和手动元数据同步；agent 包负责
DeepAgents 产品装配、执行策略和诊断接缝。新增模块前，先确认它属于哪个 Distribution、
由哪个包拥有，以及是否真的需要形成跨组件复用。

## Dependency Direction

```text
业务应用
    ├── spawn-join-common（默认标准库能力；validation extra -> pydantic）
    ├── LangChain BaseMessage / BaseChatModel
    ├── spawn-join-llm-provider-langchain
    │       ├── spawn-join-llm-provider
    │       ├── spawn-join-common[validation]
    │       ├── langchain-core
    │       ├── langchain-openai
    │       ├── langchain-anthropic
    │       └── pydantic
    ├── spawn-join-llm-model-sync
    │       ├── spawn-join-llm-provider
    │       ├── spawn-join-common
    │       ├── platformdirs
    │       └── PyYAML
    └── spawn-join-agent-deepagents
            ├── deepagents
            ├── langchain
            ├── langchain-core
            ├── langgraph
            └── spawn-join-llm-provider-langchain

spawn-join-llm-provider ──> spawn-join-core
                     ├──> spawn-join-common[validation]
                     └──> pydantic
spawn-join-llm-provider-langchain ──> spawn-join-llm-provider
                                 └──> spawn-join-common[validation]
spawn-join-llm-model-sync ──> spawn-join-llm-provider
                         └──> spawn-join-common
```

必须保持以下方向：

1. `spawn-join-core` 不得依赖其他 SpawnJoin 领域包，也不应因一个小工具引入第三方依赖。
2. `spawn-join-llm-provider` 可以依赖 Core、Common 和通用校验库 Pydantic，但不得
   依赖 LangChain 或具体 Provider SDK。
3. `spawn-join-llm-provider-langchain` 负责 LangChain 模型工厂、协议选项映射和配置校验，
   不能把框架类型泄漏回协议包。应用层直接使用 LangChain 消息和 `BaseChatModel`。
4. `spawn-join-llm-model-sync` 的运行时依赖只允许 `spawn-join-llm-provider`、
   `spawn-join-common` 和通用工具；
   不得运行时依赖 LangChain 适配包。完整 `model.yaml` 解析仍由适配包负责，同步工具只
   读取元数据投影。
5. `spawn-join-agent-deepagents` 负责 DeepAgents 产品装配、模型用途绑定、Middleware 作用域、
   受控委派、诊断和恢复接缝；它依赖 `deepagents`、LangChain、`langgraph` 和模型适配包，
   不得被 Core、协议包或模型包反向依赖。
6. 业务应用可以组合多个领域包，但包之间的相互依赖必须有明确的领域理由。
7. `spawn-join-common` 不依赖其他 SpawnJoin 包；默认零第三方运行时依赖，Pydantic 能力
   通过 `validation` extra 显式安装。它拥有公共辅助实现，Core 保留稳定契约；领域异常、
   schema、null 策略和错误文案由调用方拥有。

## Independent uv Projects

每个 Distribution 都是独立的 uv project，不使用仓库根目录共享环境或根级 uv workspace：

| Distribution | 开发环境 | 锁文件 | 本地开发依赖 |
|---|---|---|---|
| `spawn-join-core` | `packages/core/spawn-join-core/.venv/` | `packages/core/spawn-join-core/uv.lock` | 无 SpawnJoin 包依赖 |
| `spawn-join-common` | `packages/core/common/.venv/` | `packages/core/common/uv.lock` | 无 SpawnJoin 包依赖；可选 `validation` |
| `spawn-join-llm-provider` | `packages/core/llm-provider/.venv/` | `packages/core/llm-provider/uv.lock` | `spawn-join-core` 的相对路径源 |
| `spawn-join-llm-provider-langchain` | `packages/infra/llm-provider-langchain/.venv/` | `packages/infra/llm-provider-langchain/uv.lock` | `spawn-join-llm-provider` 的相对路径源 |
| `spawn-join-llm-model-sync` | `packages/infra/llm-model-sync/.venv/` | `packages/infra/llm-model-sync/uv.lock` | `spawn-join-llm-provider`、`spawn-join-llm-provider-langchain` 的相对路径源 |
| `spawn-join-agent-deepagents` | `packages/infra/agent-deepagents/.venv/` | `packages/infra/agent-deepagents/uv.lock` | `spawn-join-llm-provider-langchain` 的相对路径源 |

包间的发布依赖仍然写在 `[project].dependencies` 中；仅开发期的本地路径解析写在对应
`pyproject.toml` 的 `[tool.uv.sources]` 中。这样既保留 Distribution 的发布元数据，
又允许每个包在自己的环境中以 editable 方式开发。

六个保留包的 `uv.lock` 应提交到 Git；各包的 `.venv/`、`build/`、`dist/` 和 `*.egg-info/`
属于本机或构建产物，不应提交。

共享质量策略放在根 tool-only `pyproject.toml`，不创建根级 Python project 或共享环境。
Black/isort/Ruff/Pyright/pytest 只加入每包 dev group，不进入发布运行时依赖。
检查命令和隔离 wheel 安装说明见 [质量门说明](../development/quality-gates.md)。

## Source Layout and Public Surface

- 每个 Distribution 必须使用 `src/` layout，并拥有独立的 `pyproject.toml`。
- 测试以 Distribution 为边界放在对应包的 `tests/` 目录。
- 公共 API 通过包的 `__init__.py` 显式导出；内部模块、测试辅助函数和临时兼容层不得
  因为可导入就自动成为公共契约。
- 与框架无关的领域抽象留在领域包；LangChain、Provider SDK、Redis、数据库等外部
  适配和副作用留在对应的 infra 或适配器包。
- 模型文件（`model.yaml`）与环境变量/`.env` 解析属于
  `spawn-join-llm-provider-langchain`；协议包只保留配置类型和校验，不读取文件。
- 模型元数据契约、快照文档解析和覆盖合并属于 `spawn-join-llm-provider`；
  手动同步、源注册、缓存和 CLI 副作用属于 `spawn-join-llm-model-sync`。
- DeepAgents supervisor 装配、模型用途绑定、Middleware 作用域、受控委派、诊断和恢复接缝
  属于 `spawn-join-agent-deepagents`；它通过 `spawn-join-llm-provider-langchain` 创建配置
  模型，不读取 `model.yaml` 或凭据，也不创建或关闭宿主资源。
- LLM 消息、工具调用、流式块和 usage 使用 LangChain 原生类型；协议包不重复定义
  消息、请求/响应或流式事件。
- 网络、文件、数据库、缓存、线程和任务等副作用必须有明确拥有者；Core 和协议层应
  保持尽可能纯粹、可替换和可测试。

## Extension and Extraction Rules

- 只有至少两个组件存在稳定、真实的复用需求时，才考虑把契约提升到 Core，或把领域无关的
  辅助实现放入 Common；单领域规则继续留在原包。
- Common 内按职责组织功能，当前提供 `FieldReader` 与可选的 `validation.validate_with`。
  时间转换、序列化等新能力有具体契约和调用者时再加入，不创建空模块。
- 如果能力依赖第三方库，优先放入相应领域或 infra 包；明确通用的依赖可以作为 Common
  的可选 extra。Core 保持零第三方运行时依赖。
- 不要预先创建没有明确拥有者的 `utils.py`、`helpers.py`、`constants.py` 或万能基类。
- 未来的 Provider 集成暂时共享 `spawn-join-llm-provider-langchain` 适配包。只有当某个
  Provider 需要独立版本、依赖、测试或维护周期时，才考虑拆分为独立 Distribution。

## Change Review

当新增、移动或拆分包时，Plan 或 Review 必须说明：

1. 新边界解决的真实复用或维护问题；
2. 新增依赖的方向和理由；
3. 公共 API、版本和安装方式是否改变；
4. 需要新增或迁移的测试、构建和文档；
5. 是否需要同步更新 [`repository-map.md`](repository-map.md)、README 和 AGENTS。
