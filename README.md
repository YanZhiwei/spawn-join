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
├── .agents/
│   └── skills/
├── .codegraph/                      # 本机源码索引
├── .specify/                        # Spec Kit 基础设施
├── docs/
│   └── architecture/               # 仓库地图和包边界
├── harness/                        # 阶段计划、上下文、评审和验证证据
├── packages/
│   ├── core/
│   │   ├── spawn-join-core/
│   │   └── llm-provider/
│   └── infra/
│       ├── llm-provider-langchain/
│       └── spawn-join-observability/
├── specs/<feature-id>/              # Feature 路由时创建的 SDD 工件
├── AGENTS.md
└── README.md
```

完整且易变的仓库地图维护在 [`docs/architecture/repository-map.md`](docs/architecture/repository-map.md)。
包职责、依赖方向和公共边界维护在
[`docs/architecture/package-boundaries.md`](docs/architecture/package-boundaries.md)。
Harness 的阶段记录和证据约定维护在 [`harness/README.md`](harness/README.md)。
不要在 README、AGENTS 和架构文档中维护多份完整目录树。

`packages/core` 和 `packages/infra` 是架构分组，不是额外的 Python Distribution。每个包目录
可以独立构建和安装，真实的 Distribution 名称和依赖由对应目录的 `pyproject.toml` 定义。
包名和 Python 导入名遵循不同的命名规则：

- Distribution 名称使用连字符，例如 `spawn-join-llm-provider`。
- Python 导入模块使用下划线，例如 `spawn_join_llm_provider`。

当前只创建包边界和最小源码骨架，具体领域能力会在真实需求出现后再加入对应包。

## 本地开发

每个 Distribution 都是独立的 uv project，拥有自己的虚拟环境和锁文件。使用
[uv](https://docs.astral.sh/uv/) 时，应在目标包目录执行 `uv sync`，不要在仓库根目录创建共享
`.venv`。从仓库根目录分别初始化需要开发的包：

```bash
uv sync --directory packages/core/spawn-join-core
uv sync --directory packages/core/llm-provider
uv sync --directory packages/infra/llm-provider-langchain
uv sync --directory packages/infra/spawn-join-observability
```

每条命令只管理对应 Distribution 的环境：

- `.venv/` 位于对应 Distribution 目录下，不提交到 Git；
- `uv.lock` 位于对应 Distribution 目录下，提交到 Git；
- `uv sync` 会按该包的 `pyproject.toml` 创建或更新环境；
- 包间开发依赖通过各自 `pyproject.toml` 中的 `[tool.uv.sources]` 指向本仓库的兄弟包。

如果只开发 LLM 协议或 LangChain 适配层，可以按需同步：

```bash
uv sync --directory packages/core/spawn-join-core
uv sync --directory packages/core/llm-provider
uv sync --directory packages/infra/llm-provider-langchain
```

在包目录中运行命令时，使用 `uv run`，例如：

```bash
uv run --directory packages/core/llm-provider python -c "import spawn_join_llm_provider"
```

构建单个 Distribution：

```bash
uv build packages/core/spawn-join-core
uv build packages/core/llm-provider
uv build packages/infra/llm-provider-langchain
uv build packages/infra/spawn-join-observability
```

将 `packages/core/spawn-join-core` 替换为其他包目录，即可分别构建对应组件。后续增加测试后，测试也应以包为边界单独执行。

## 代码导航与 CodeGraph

本项目已启用 CodeGraph，用于在修改 Python 源码前定位文件、符号、调用路径和受影响测试。CodeGraph 的索引是本机生成的开发辅助数据，不属于 Python Distribution，也不应作为业务代码提交。

首次在新环境使用时，从仓库根目录初始化索引：

```bash
codegraph init
```

检查当前索引状态：

```bash
codegraph status
```

源码发生变化后，优先执行增量同步；索引损坏、解析器升级或需要完全重建时，再执行全量索引：

```bash
codegraph sync
codegraph index
```

常用导航命令：

```bash
# 查看索引中的项目文件结构
codegraph files

# 按符号或代码术语搜索
codegraph query <symbol-or-term>

# 查看相关源码和调用路径
codegraph explore "<symbol or code question>"

# 查看单个符号，或读取文件并查看其依赖关系
codegraph node <symbol-or-file>

# 查看调用方、被调用方和变更影响
codegraph callers <symbol>
codegraph callees <symbol>
codegraph impact <symbol>

# 根据变更文件查找受影响的测试
codegraph affected "<file>"
```

推荐的源码变更顺序是：

1. `codegraph status`，确认索引是否为最新。
2. 使用 `codegraph explore`、`codegraph node`、`codegraph callers` 和 `codegraph callees` 理解目标模块及其调用关系。
3. 完成小步修改后执行 `codegraph sync`。
4. 使用 `codegraph impact` 或 `codegraph affected` 检查影响范围，再运行与包边界匹配的测试和构建验证。

`.codegraph/.gitignore` 会忽略本机数据库、日志、daemon 状态和 socket 等临时文件；只保留 `.gitignore` 本身作为项目约定。若索引状态显示过期或缺失，应先同步或初始化，不要把本机生成的数据库文件复制到其他环境。

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
