# SpawnJoin

SpawnJoin 是一个面向多个私有 Python 项目的基础设施组件单仓库（monorepo）。仓库中的每个包目录都是一个可以独立构建、测试、版本化和发布的 Python Distribution。

`SpawnJoin` 取自并发与运行时语境中的两个开发概念：`spawn` 表示创建执行单元，`join` 表示等待执行单元完成。这个名字表达项目对完整执行生命周期的关注：从初始化、运行和观测，到完成、回收与清理。

当前采用的核心原则是：

- **Monorepo + 独立 Package + 私有包分发**：所有基础设施组件在同一个仓库维护，但保持独立的包边界。
- **Core 保持小而稳定**：`spawn-join-core` 只承载跨领域的公共规则、配置机制、异常、类型和基础协议。
- **领域抽象归属领域包**：LLM 等领域自己的抽象接口放在对应的领域包中，不把所有接口集中到 `spawn-join-core`。
- **单向依赖**：业务应用依赖基础设施包，基础设施包可以依赖 Core；Core 不反向依赖任何领域包。
- **按需扩展**：在出现真实的跨组件复用之前，不预先增加 `utils.py`、`constants.py`、`helpers.py` 等通用收纳模块。

当前仓库暂不包含 `spawn-join-database` 和 `spawn-join-agent`，后续根据真实需求单独规划。

## 目录结构

```text
spawn-join/
├── packages/
│   ├── core/
│   │   ├── spawn-join-core/
│   │   │   ├── pyproject.toml
│   │   │   └── src/
│   │   │       └── spawn_join_core/
│   │   │           ├── __init__.py
│   │   │           ├── config.py
│   │   │           ├── exceptions.py
│   │   │           ├── protocols.py
│   │   │           └── types.py
│   │   │
│   │   └── llm-provider/
│   │       ├── pyproject.toml
│   │       └── src/
│   │           └── spawn_join_llm_provider/
│   │               ├── __init__.py
│   │               └── abstractions/
│   │                   └── __init__.py
│   │
│   └── infra/
│       ├── llm-provider-langchain/
│       │   ├── pyproject.toml
│       │   └── src/
│       │       └── spawn_join_llm_provider_langchain/
│       │           ├── __init__.py
│       │           └── providers/
│       │               ├── __init__.py
│       │               ├── azure_openai/
│       │               │   └── __init__.py
│       │               └── deepseek/
│       │                   └── __init__.py
│       │
│       └── spawn-join-observability/
│           ├── pyproject.toml
│           └── src/
│               └── spawn_join_observability/
│                   └── __init__.py
│
└── README.md
```

`packages/core` 和 `packages/infra` 是仓库内的架构分组，不是额外的 Python Distribution。包目录可以使用清晰的领域名称，例如 `llm-provider`；真正可独立构建和发布的名称由各目录的 `pyproject.toml` 定义，并统一使用 `spawn-join-*` 命名空间。

这里的包名和 Python 导入名遵循不同的命名规则：

- Distribution 名称使用连字符，例如 `spawn-join-llm-provider`。
- Python 导入模块使用下划线，例如 `spawn_join_llm_provider`。

## Package 职责

| Distribution | Python 模块 | 所在分组 | 职责 |
|---|---|---|---|
| `spawn-join-core` | `spawn_join_core` | `core` | 公共配置机制、异常、类型和跨领域基础协议 |
| `spawn-join-llm-provider` | `spawn_join_llm_provider` | `core` | 与框架无关的 LLM 协议和领域抽象 |
| `spawn-join-llm-provider-langchain` | `spawn_join_llm_provider_langchain` | `infra` | LangChain 适配层，以及内部 Provider 实现 |
| `spawn-join-observability` | `spawn_join_observability` | `infra` | 日志、追踪、指标等可观测性能力 |

当前只创建包边界和最小源码骨架，具体领域能力会在真实需求出现后再加入对应包。`abstractions` 表示领域接口或协议，`implementations` / `providers` 表示具体实现。

`packages/core` 是架构分组，不等于 `spawn-join-core`。因此，`packages/core/llm-provider` 虽然位于 `core` 分组，但仍然是独立的 LLM 领域 Distribution；它不应把 LLM 领域接口全部塞进 `spawn-join-core`。

## 依赖方向

```text
业务应用
    ├── spawn-join-llm-provider-langchain ────────────┐
    │       ├── spawn-join-llm-provider ──────────────┤
    │       └── langchain-core                     │
    └── spawn-join-observability ─────────────────────┘
                                                  ▼
                                            spawn-join-core
```

约束如下：

1. `spawn-join-core` 不得依赖任何其他 SpawnJoin 领域包。
2. `spawn-join-llm-provider` 可以依赖 `spawn-join-core`，但不得依赖 LangChain 或具体 Provider SDK。
3. `spawn-join-llm-provider-langchain` 依赖 `spawn-join-llm-provider` 和 `langchain-core`，并负责 LangChain 相关实现。
4. 领域包可以依赖 `spawn-join-core`，但不应为了复用某个小工具而引入另一个无关领域包。
5. LLM 等领域的抽象应留在自己的包中，避免 Core 成为所有接口的集中地。
6. 业务应用可以组合多个领域包，但包之间的相互依赖必须有明确的领域理由。

`spawn-join-llm-provider-langchain` 内部的 Azure OpenAI、DeepSeek 等实现暂时共享一个适配包。只有当某个 Provider 需要独立版本、依赖、测试或维护周期时，才考虑拆分为独立 Distribution，例如 `spawn-join-llm-provider-openai`。

## 本地开发

每个包都有自己的 `pyproject.toml`，可以独立构建和安装。使用 [uv](https://docs.astral.sh/uv/) 管理虚拟环境和 Python 包。首次开发时先创建虚拟环境，再安装 Core 和需要的领域包：

```bash
uv venv
uv pip install --editable packages/core/spawn-join-core
uv pip install --editable packages/core/llm-provider
uv pip install --editable packages/infra/llm-provider-langchain
uv pip install --editable packages/infra/spawn-join-observability
```

如果只开发 LLM 协议或 LangChain 适配层，可以按需安装：

```bash
uv venv
uv pip install --editable packages/core/spawn-join-core
uv pip install --editable packages/core/llm-provider
uv pip install --editable packages/infra/llm-provider-langchain
```

构建单个 Distribution：

```bash
uv build packages/core/spawn-join-core
uv build packages/core/llm-provider
uv build packages/infra/llm-provider-langchain
uv build packages/infra/spawn-join-observability
```

将 `packages/core/spawn-join-core` 替换为其他包目录，即可分别构建对应组件。后续增加测试后，测试也应以包为边界单独执行。

## 私有包分发

### Git URL

适合早期开发或快速复用时，可以从私有 Git 仓库安装指定 tag，并通过 `subdirectory` 指向具体包：

```bash
uv pip install "spawn-join-llm-provider-langchain @ git+https://github.com/<your-org>/spawn-join.git@v0.1.0#subdirectory=packages/infra/llm-provider-langchain"
```

使用 Git URL 时，需要确保对应仓库的认证方式已经配置完成，并且目标包可以独立构建。

### 私有 Package Registry

当多个项目持续依赖这些组件，并且需要版本锁定、自动构建和发布时，建议使用 GitHub Packages、Azure Artifacts 或其他私有 Python Package Registry。业务项目只声明所需包及版本范围，例如：

```toml
[project]
dependencies = [
    "spawn-join-core>=0.1.0,<0.2.0",
    "spawn-join-llm-provider>=0.1.0,<0.2.0",
]
```

每个包独立维护版本号，推荐遵循语义化版本（SemVer），避免无关领域包因为共享仓库而被迫同步升级。

## 演进规则

- 只有至少两个组件存在稳定、真实的复用需求时，才考虑把能力提升到 Core。
- 如果能力依赖 Redis、Azure OpenAI、SQLAlchemy 等第三方库，优先放入相应领域包，而不是 Core。
- 新增实现时，放入对应领域的 `implementations/` 或 `providers/`，不要直接堆到包根目录。
- 每个包都应能独立安装、测试、构建和发布。
- 公共 API 通过包的 `__init__.py` 明确导出；内部实现不要无意中成为公共契约。

## 当前状态

本次初始化完成了：

- monorepo 的 `packages/` 布局；
- `core` 和 `infra` 两个架构分组；
- 四个独立 Distribution 的 `pyproject.toml`；
- `src` layout 和对应的 Python 导入包；
- `spawn-join-core` 与领域协议包的边界；
- Core、LLM Provider 的领域内部分层；
- 与框架无关的 LLM 协议包；
- LangChain LLM 适配包及其内部 Provider 命名空间；
- Observability 的最小可扩展骨架；
- 本 README 中的职责、依赖、安装和分发约定。

当前尚未实现具体的模型或可观测性业务能力，也尚未添加测试、CI 和发布流水线。Provider 的具体 SDK 依赖和调用实现将在协议稳定后加入 `spawn-join-llm-provider-langchain`。
