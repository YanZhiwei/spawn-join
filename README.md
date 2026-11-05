# SpawnJoin

[简体中文](#中文) | [English](#english)

## 中文

SpawnJoin 是一个面向多个私有 Python 项目的基础设施组件单仓库（monorepo）。每个包都是
可以独立构建、测试、版本化和发布的 Python Distribution，不使用根级共享 uv 环境。

`spawn` 表示创建执行单元，`join` 表示等待执行单元完成。项目关注完整生命周期：从初始化、
运行和观测，到完成、回收与清理；工程协作采用 **SDD 规范驱动开发 + Harness 工程治理**。

### 导航

| 分类 | 内容 |
|---|---|
| [项目与架构](#项目与架构) | 项目原则、包边界与仓库地图 |
| [SDD 与 Harness 工程治理](#sdd-与-harness-工程治理) | 交付路由、工件职责、执行证据与长期决策 |
| [本地开发与质量验证](#本地开发与质量验证) | 独立 uv 环境、测试、类型、格式和构建 |
| [工具与技能](#工具与技能) | CodeGraph 源码导航、项目级技术图技能 |
| [包分发与演进](#包分发与演进) | Git 安装、私有分发与扩展边界 |
| [当前状态](#当前状态) | 已有基础、能力边界与尚未启用的自动化 |

### 项目与架构

- **独立 Package**：各 Distribution 拥有自己的 `pyproject.toml`、`uv.lock`、`.venv/`
  和 `tests/`，保留独立安装、构建与发布边界。
- **Core 小而稳定**：只承载跨领域稳定规则；LLM 等领域的协议留在对应领域包。
- **依赖单向**：业务应用组合基础设施包；框架与 Provider SDK 留在适配层，不泄漏回协议或 Core。
- **按需扩展**：只有真实、稳定的复用需求才提取公共能力，不预建万能工具模块或未来包。
- **公共 API 显式导出**：源码使用 `src/` layout，通过各包 `__init__.py` 定义公共入口。

`packages/core` 和 `packages/infra` 是架构分组，不是额外的 Distribution。Distribution
名称使用连字符，Python import package 使用下划线。五个保留包的职责和依赖方向以
[包边界说明](docs/architecture/package-boundaries.md)为准，实际元数据以各包的
`pyproject.toml` 为准。

完整目录结构只维护在[仓库地图](docs/architecture/repository-map.md)，首页不复制完整树。
当前已实现 LLM channel/options 契约、LangChain 模型工厂和 DeepAgents 产品装配；
Core 仍为骨架，尚不包含 `spawn-join-database`。

### SDD 与 Harness 工程治理

**SDD（Spec-Driven Development）** 明确“做什么、为什么做、怎样验收”；
**Harness** 记录“在什么范围和上下文中执行、如何审查、实际验证了什么”。二者互补，
不是两套任务系统，也不等于已经启用了自动化 Agent 编排。

#### 按风险选择交付路由

| 路由 | 适用范围 | 执行要求 |
|---|---|---|
| Lightweight | 文档、机械性或行为保持不变的窄范围改动 | 锁定范围，保留针对性验证；不制造空的 Feature 工件 |
| Bugfix | 可复现、边界明确的缺陷 | 先建立失败证据，再修复与回归 |
| Feature | 新增行为、公共 API、跨包边界、持久化、安全或架构决策 | 先完成 Spec / Plan / Tasks，再按任务实现和审查 |

Feature 的基本链路是：

```text
需求澄清 → Spec → Plan / 必要的 ADR → Tasks → Slice 计划/Gate → 增量实现 → 验证与审查 → 交接
```

`tasks.md` 是 Feature 的唯一执行队列；`slices.md` 只提供可独立评审/合并的边界，不得增删或
重排任务。Harness 阶段计划不能另建一份任务系统。
当前入口是 CLI 管理的 OpenCode 原生命令
[`/speckit.delivery.route`](.opencode/commands/speckit.delivery.route.md)。已通过固定 Release
安装 Delivery Bundle v0.4.2（10 个扩展和三条 Workflow，共 13 个组件），保留 Codex 核心技能；
不再使用拷贝式 sd 门面。v0.3.0 新增 `speckit.delivery.close`，v0.3.1 增加包 README 节点，
v0.4.2 增加逐任务关闭 transport 与 publication group 规划。安装方式、迁移步骤和配置见
[Delivery 安装说明](docs/development/spec-kit-delivery.md)。
安装不等于 Ralph 已运行；提交、推送和合并仍需用户授权，缺少能力时报告 blocked。
详细执行契约以 [AGENTS.md](AGENTS.md) 和
[Constitution](.specify/memory/constitution.md) 为准。

#### 分清工件职责

| 层次 | 权威位置 | 负责的内容 |
|---|---|---|
| 原则与协作契约 | [Constitution](.specify/memory/constitution.md)、[AGENTS.md](AGENTS.md) | 项目原则、交付路线与稳定边界 |
| Feature 交付工件 | 本地 `specs/<feature-id>/` | Spec 定义需求，Plan 定义方案，Tasks 管理执行队列 |
| 阶段执行与证据 | [harness/](harness/README.md) | 批准范围、材料性上下文、评审、实际命令与结果 |
| 长期架构知识 | [架构说明](docs/architecture/repository-map.md)、[ADR](docs/decisions/README.md) | 当前系统视图、关键设计理由及长期约束 |

`/specs/` 已加入 Git 忽略，Feature 工件只在本地；历史工件已按
[ADR-0002](docs/decisions/engineering/0002-untrack-historical-feature-artifacts.md)
取消跟踪并保留本机文件。
收口前应将稳定设计提炼到 ADR/架构说明，将有效验证保存到证据层，不能只留在忽略目录。

#### Harness 工程化治理

Harness 将计划、观察和结论分开保存：

- [build/](harness/build/README.md)：阶段批准范围、实施计划与人工审批边界。
- [context/](harness/context/README.md)：影响范围、接口、设计和风险的材料性上下文。
- [code_review/](harness/code_review/README.md)：评审发现、修复状态与复核结果。
- [evidence/](harness/evidence/README.md)：实际命令、工作目录、环境、退出码、revision 和限制。
- [build-log.md](harness/build-log.md)：追加式记录实际执行进度，不把计划写成已完成结果。

治理时分别判断 **Quality Gate**（格式、lint、类型、测试和构建等机械检查）、
**Standards Review**（DRY、职责、公共 API 和依赖方向等标准审查）与 **Evidence**
（结果是否绑定当前变更范围与 revision）。测试通过不能代替架构审查；未执行或 blocked
不能算 pass，提交或范围变化后旧证据需要重新确认。

长期决策统一放在 `docs/decisions/`，按领域/子领域分类、全局编号并通过链接表达依赖或替代。
ADR 可以包含必要设计和图表，但不替代正式契约、测试或任务；Accepted 只代表决策获批，
不表示已经实现或验证。模板与状态规则见[决策入口](docs/decisions/README.md)。

### 模型元数据同步

`model.yaml` 的 `metadata_ref` / `metadata_source` 可以关联价格、能力、模态、上下文和
生命周期元数据。同步是手动操作，不会修改 `model.yaml`，也不会自动注册模型：

```powershell
uv sync --locked --directory packages/infra/llm-model-sync
uv run --project packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --check
uv run --project packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --apply
```

快照默认写在 `model.yaml` 同目录的 `model-metadata.json`；运行时通过
`ModelCatalog.from_file(..., metadata_file=...)` 显式读取。使用、失败保护、回滚和新增
同步源的说明见
[`spawn-join-llm-model-sync`](packages/infra/llm-model-sync/README.md)。

### DeepAgents 产品装配

`spawn-join-agent-deepagents` 提供 DeepAgents supervisor 装配、显式模型用途、Middleware
作用域、受控委派、诊断和恢复接缝。它返回原生 LangGraph 图，宿主继续拥有模型、工具、
Store、Checkpointer、MCP/沙箱和业务权限。

```powershell
uv sync --locked --directory packages/infra/agent-deepagents
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents
```

公共契约、离线示例和限制见
[`spawn-join-agent-deepagents`](packages/infra/agent-deepagents/README.md)。

### 本地开发与质量验证

#### 独立环境与日常运行

每个 Distribution 都是独立的 uv project，拥有自己的虚拟环境和锁文件。使用
[uv](https://docs.astral.sh/uv/) 时，应在目标包目录执行 `uv sync`，不要在仓库根目录创建共享
`.venv`。从仓库根目录分别初始化需要开发的包：

```bash
uv sync --directory packages/core/spawn-join-core
uv sync --directory packages/core/llm-provider
uv sync --directory packages/infra/llm-provider-langchain
uv sync --directory packages/infra/llm-model-sync
uv sync --directory packages/infra/agent-deepagents
```

每条命令只管理对应 Distribution 的环境：

- `.venv/` 位于对应 Distribution 目录下，不提交到 Git；
- `uv.lock` 位于对应 Distribution 目录下，提交到 Git；
- `uv sync` 会按该包的 `pyproject.toml` 创建或更新环境；
- 包间开发依赖通过各自 `pyproject.toml` 中的 `[tool.uv.sources]` 指向本仓库的兄弟包。

只同步本次开发涉及的包即可。在对应包环境中运行命令时，使用 `uv run`，例如：

```bash
uv run --directory packages/core/llm-provider python -c "import spawn_join_llm_provider"
```

构建并隔离验证单个 Distribution（输出位于临时目录）：

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core -Check build
```

替换 Distribution 名可检查其他包；测试始终以包为边界独立执行。

#### 统一质量门禁

```powershell
pwsh -NoProfile -File scripts/quality.ps1
pwsh -NoProfile -File scripts/test-quality.ps1
```

需要 PowerShell 7、uv、Python >=3.11、Node 22+。Black/isort 统一格式，Ruff 做 lint，
Pyright 做严格类型检查，pytest 验证包契约，另外执行文档、构建和隔离安装检查。
根 `pyproject.toml` 只保存共享工具配置，不是根级 uv project；工具依赖仍在各包 dev group。
命令、修复格式、CI 矩阵和分支保护说明见
[`docs/development/quality-gates.md`](docs/development/quality-gates.md)。

GitHub Actions 配置见 [quality.yml](.github/workflows/quality.yml)，覆盖五个保留包和跨平台矩阵，
并设置 `Quality Gate` 汇总检查。Ruleset `main` 已启用 PR、线性历史和 required `Quality Gate`；
失败 PR 的实际拦截已用临时 PR 验证。

### 工具与技能

#### CodeGraph 源码导航

本项目已启用 CodeGraph，用于在修改 Python 源码前定位文件、符号、调用路径和受影响测试。CodeGraph 的索引是本机生成的开发辅助数据，不属于 Python Distribution，也不应作为业务代码提交。

从仓库根目录运行；首次使用时先执行 `codegraph init`，已有索引则检查状态：

```bash
codegraph status
codegraph files
codegraph explore "<symbol or code question>"
codegraph node <symbol-or-file>
codegraph callers <symbol>
codegraph callees <symbol>
codegraph impact <symbol>
codegraph affected "<file>"
codegraph sync
```

将占位符替换为实际符号或路径。修改前理解边界，修改后同步索引、分析影响，再运行相关测试。
索引损坏或需完全重建时使用 `codegraph index`；CodeGraph 的关系证据不能代替类型、测试或构建。

`.codegraph/.gitignore` 会忽略本机数据库、日志、daemon 状态和 socket 等临时文件；只保留 `.gitignore` 本身作为项目约定。若索引状态显示过期或缺失，应先同步或初始化，不要把本机生成的数据库文件复制到其他环境。

#### 项目级技能与技术图

项目级 Agent 能力放在 `.agents/skills/`，包括 Spec Kit 入口和固定版本的
[Fireworks Tech Graph](.agents/skills/fireworks-tech-graph/SKILL.md)。技能是开发工具，
不是 Python Distribution，也不进入业务包运行时依赖。

Fireworks 从描述生成 SVG 技术图，可按需导出 PNG，不需要图像模型 API Key。
SVG 是可维护主产物；图中必须区分当前实现与目标设计，并核对箭头关系、事实来源和最终视觉效果。
辅助脚本与各保留包环境隔离；安装技能不代表渲染依赖齐全，也不授权付费 API、发布或外传源码。
使用方式、Windows 命令和环境限制见[技术图说明](docs/development/technical-diagrams.md)。

### 包分发与演进

#### Git URL

适合早期开发或快速复用时，可以从私有 Git 仓库安装指定 tag，并通过 `subdirectory` 指向具体包：

```bash
uv pip install "spawn-join-llm-provider-langchain @ git+https://github.com/<your-org>/spawn-join.git@v0.1.0#subdirectory=packages/infra/llm-provider-langchain"
```

使用 Git URL 时，需要确保对应仓库的认证方式已经配置完成，并且目标包可以独立构建。

#### 私有 Package Registry

当多个项目持续依赖这些组件，并需要版本锁定、自动构建和发布时，可采用支持 Python 的
私有 Package Registry；具体服务与发布流水线另行规划。业务项目只声明所需包及版本范围，例如：

```toml
[project]
dependencies = [
    "spawn-join-core>=0.1.0,<0.2.0",
    "spawn-join-llm-provider>=0.1.0,<0.2.0",
]
```

每个包独立维护版本号，推荐遵循语义化版本（SemVer），避免无关领域包因为共享仓库而被迫同步升级。

#### 演进规则

- 只有至少两个组件存在稳定、真实的复用需求时，才考虑把能力提升到 Core。
- 如果能力依赖 Redis、Azure OpenAI、SQLAlchemy 等第三方库，优先放入相应领域包，而不是 Core。
- 新增实现时，放入对应领域的既有模块或经 Plan 批准的新模块；不要为形式预建空的
  `implementations/` 或 `providers/` 目录。
- 每个包都应能独立安装、测试、构建和发布。
- 公共 API 通过包的 `__init__.py` 明确导出；内部实现不要无意中成为公共契约。

### 当前状态

| 类别 | 当前边界 |
|---|---|
| 领域包 | 五个保留的独立 Distribution；LLM 包已实现 channel/options 契约、LangChain 模型工厂、手动元数据同步和 DeepAgents 产品装配；Core 仍为骨架 |
| SDD 基础 | 已有 Constitution、Spec Kit 模板/脚本和 Bundle v0.4.2 管理的 Delivery 原生命令（含 close/evidence 收口、逐任务关闭 transport 与包 README 节点）；Feature 工件本地化 |
| Harness 治理 | 已有阶段计划、上下文、评审、证据与执行日志约定，以及结构/索引门禁；不是自动执行引擎 |
| 开发质量 | 已配置 Black/isort、Ruff、Pyright、pytest、actionlint、PSScriptAnalyzer、构建/安装验证和 GitHub Actions |
| 长期知识与绘图 | 已有 ADR 分类、模板与项目级 Fireworks；渲染能力取决于本机依赖 |
| 尚未配置 | 自动化 Spec Kit/Harness hook 与发布流水线 |

### 许可证

本仓库及其五个保留 Distribution 为专有软件，保留所有权利。未经版权持有人书面许可，不得使用、
复制、修改、发布、分发、再许可或销售。详见 [LICENSE](LICENSE)。

实际命令、环境和验证限制以 [Harness evidence](harness/evidence/README.md) 中对应记录为准；
不以配置存在或某次本机成功代替当前 revision 的验证。Fireworks 已知兼容性与渲染依赖限制见
[技能验证记录](harness/evidence/adr-and-project-diagram-skill.md)。

许可证见 [LICENSE](LICENSE)。

## English

SpawnJoin is a monorepo of infrastructure components for multiple private Python projects. Each
package is an independently buildable, testable, versionable, and publishable Python Distribution;
there is no root shared uv environment.

`spawn` means creating an execution unit and `join` means waiting for it to finish. The project covers
the full lifecycle from initialization, execution, and observation through completion, reclamation,
and cleanup. Engineering collaboration uses **SDD (spec-driven development) plus Harness governance**.

### Navigation

| Category | Content |
|---|---|
| [Project and architecture](#project-and-architecture) | principles, package boundaries, repository map |
| [SDD and Harness governance](#sdd-and-harness-governance) | delivery routes, artifact ownership, execution evidence, durable decisions |
| [Local development and quality](#local-development-and-quality) | independent uv environments, tests, types, formatting, builds |
| [Tools and skills](#tools-and-skills) | CodeGraph source navigation, project diagram skill |
| [Distribution and evolution](#distribution-and-evolution) | Git installs, private distribution, extension boundaries |
| [Current status](#current-status) | existing foundations, limits, disabled automation |

### Project and architecture

- **Independent packages**: each Distribution owns its `pyproject.toml`, `uv.lock`, `.venv/`, and
  `tests/`, preserving independent install, build, and release boundaries.
- **Small, stable Core**: only cross-domain stable rules; domain protocols stay in domain packages.
- **One-way dependencies**: applications compose infrastructure packages; framework and Provider SDKs
  stay in adapters and never leak back into protocols or Core.
- **Extend on demand**: extract shared capabilities only after a real, stable reuse need; do not
  pre-build generic utility modules or future packages.
- **Explicit public API**: source uses `src/` layout and each package's `__init__.py` defines public
  entry points.

`packages/core` and `packages/infra` are architecture groups, not additional Distributions.
Distribution names use hyphens and Python import packages use underscores. The five retained packages'
responsibilities and dependency directions are authoritative in
[package boundaries](docs/architecture/package-boundaries.md); actual metadata is authoritative in
each `pyproject.toml`.

The full directory structure is maintained only in the
[repository map](docs/architecture/repository-map.md); this page does not copy the whole tree. Current
implementations include LLM channel/options contracts, the LangChain model factory, and DeepAgents
product assembly; Core is still a scaffold, and `spawn-join-database` does not exist.

### SDD and Harness governance

**SDD** defines what to build, why, and how acceptance is judged; **Harness** records the scope,
context, review, and actual verification. They are complementary, not two task systems, and do not
mean automated Agent orchestration is enabled.

#### Choose a delivery route by risk

| Route | Applies to | Execution requirement |
|---|---|---|
| Lightweight | documentation, mechanical, or behavior-preserving narrow changes | lock scope and keep targeted verification; do not manufacture empty Feature artifacts |
| Bugfix | reproducible, clearly bounded defects | establish failing evidence before fixing and regression |
| Feature | new behavior, public API, cross-package boundaries, persistence, security, or architecture decisions | complete Spec / Plan / Tasks before implementation and review |

The Feature path is:

```text
clarification -> Spec -> Plan / necessary ADRs -> Tasks -> Slice plan/gate -> incremental implementation -> verification and review -> handoff
```

`tasks.md` is the Feature's sole execution queue; `slices.md` only provides independently reviewable
boundaries and must not add, remove, or reorder tasks. Harness phase plans cannot create a second task
system. The current entry point is the CLI-managed OpenCode native command
[`/speckit.delivery.route`](.opencode/commands/speckit.delivery.route.md). Delivery Bundle v0.4.2 is
installed from a fixed Release (10 extensions and three workflows, 13 components), while Codex core
skills are retained; the copied `sd` facade is no longer used. The installed `sd` alias and
`/speckit.delivery.route` share the same contract. v0.3.0 added `speckit.delivery.close`, v0.3.1 added
the package README node, and v0.4.2 adds per-task closure transport and publication-group planning.
See [Delivery installation](docs/development/spec-kit-delivery.md) for installation, migration, and
configuration. Installation does not mean Ralph has run; commits, pushes, and merges still require
user authorization, and missing capabilities must be reported as blocked. The detailed execution
contract is [AGENTS.md](AGENTS.md) and the [Constitution](.specify/memory/constitution.md).

#### Know what each artifact owns

| Layer | Authoritative location | Responsibility |
|---|---|---|
| Principles and collaboration contract | [Constitution](.specify/memory/constitution.md), [AGENTS.md](AGENTS.md) | project principles, delivery routes, stable boundaries |
| Feature delivery artifacts | local `specs/<feature-id>/` | Spec defines requirements, Plan defines design, Tasks manages the execution queue |
| Phase execution and evidence | [harness/](harness/README.md) | approved scope, material context, review, actual commands and results |
| Durable architecture knowledge | [architecture](docs/architecture/repository-map.md), [ADRs](docs/decisions/README.md) | current system view, key design rationale, long-term constraints |

`/specs/` is Git-ignored, so Feature artifacts exist only locally; historical artifacts were untracked
under [ADR-0002](docs/decisions/engineering/0002-untrack-historical-feature-artifacts.md) and retained
locally. Before closing, distill durable design into ADRs/architecture docs and valid verification into
evidence; do not leave it only in ignored directories.

#### Harness engineering governance

Harness separates plans, observations, and conclusions:

- [build/](harness/build/README.md): approved phase scope, implementation plan, and human approval boundaries.
- [context/](harness/context/README.md): material context affecting scope, interfaces, design, and risk.
- [code_review/](harness/code_review/README.md): review findings, fix status, and re-review results.
- [evidence/](harness/evidence/README.md): actual commands, working directory, environment, exit codes, revision, and limitations.
- [build-log.md](harness/build-log.md): append-only actual progress; never write plans as completed results.

Governance separately judges **Quality Gate** (mechanical checks such as formatting, lint, types, tests,
and builds), **Standards Review** (DRY, ownership, public API, dependency direction), and **Evidence**
(whether results are bound to the current scope and revision). Passing tests do not replace architecture
review; unexecuted or blocked checks are not passes, and old evidence must be reconfirmed after a commit
or scope change.

Durable decisions live under `docs/decisions/`, classified by domain/subdomain, globally numbered, and
linked to express dependency or replacement. ADRs may include necessary design and diagrams but do not
replace formal contracts, tests, or tasks; Accepted means the decision was approved, not implemented or
verified. See the [decision index](docs/decisions/README.md) for templates and status rules.

### Model metadata synchronization

`metadata_ref` / `metadata_source` in `model.yaml` can associate pricing, capabilities, modalities,
context, and lifecycle metadata. Synchronization is manual, never edits `model.yaml`, and never registers
models automatically:

```powershell
uv sync --locked --directory packages/infra/llm-model-sync
uv run --project packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --check
uv run --project packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --apply
```

The snapshot defaults to `model-metadata.json` beside `model.yaml`; runtime reads it explicitly through
`ModelCatalog.from_file(..., metadata_file=...)`. See
[`spawn-join-llm-model-sync`](packages/infra/llm-model-sync/README.md) for usage, failure protection,
rollback, and adding sources.

### DeepAgents product assembly

`spawn-join-agent-deepagents` provides DeepAgents supervisor assembly, explicit model purposes,
Middleware scopes, governed delegation, diagnostics, and recovery seams. It returns a native LangGraph
graph; the host retains ownership of models, tools, Store, Checkpointer, MCP/sandbox, and business
permissions.

```powershell
uv sync --locked --directory packages/infra/agent-deepagents
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents
```

See [`spawn-join-agent-deepagents`](packages/infra/agent-deepagents/README.md) for public contracts,
offline examples, and limitations.

### Local development and quality

#### Independent environments and daily work

Each Distribution is an independent uv project with its own virtual environment and lockfile. With
[uv](https://docs.astral.sh/uv/), run `uv sync` in the target package directory; do not create a shared
root `.venv`. From the repository root, initialize the package you need:

```bash
uv sync --directory packages/core/spawn-join-core
uv sync --directory packages/core/llm-provider
uv sync --directory packages/infra/llm-provider-langchain
uv sync --directory packages/infra/llm-model-sync
uv sync --directory packages/infra/agent-deepagents
```

Each command manages only its Distribution's environment:

- `.venv/` lives in the Distribution directory and is not committed;
- `uv.lock` lives in the Distribution directory and is committed;
- `uv sync` creates or updates the environment from that package's `pyproject.toml`;
- inter-package development dependencies point to sibling packages through each `pyproject.toml`'s `[tool.uv.sources]`.

Synchronize only the packages involved in the current work. Run commands in the package environment
with `uv run`, for example:

```bash
uv run --directory packages/core/llm-provider python -c "import spawn_join_llm_provider"
```

Build and verify one Distribution in an isolated temporary output:

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core -Check build
```

Replace the Distribution name for other packages; tests always run independently per package.

#### Unified quality gates

```powershell
pwsh -NoProfile -File scripts/quality.ps1
pwsh -NoProfile -File scripts/test-quality.ps1
```

Requires PowerShell 7, uv, Python >=3.11, and Node 22+. Black/isort format, Ruff lints, Pyright performs
strict type checking, pytest verifies package contracts, and documentation, build, and isolated install
checks also run. The root `pyproject.toml` stores shared tool configuration only and is not a root uv
project; tool dependencies remain in each package dev group. See
[`docs/development/quality-gates.md`](docs/development/quality-gates.md) for commands, formatting fixes,
the CI matrix, and branch protection.

GitHub Actions is configured in [quality.yml](.github/workflows/quality.yml), covering the five retained
packages and the cross-platform matrix, with a `Quality Gate` aggregate check. The `main` Ruleset enables
PRs, linear history, and the required `Quality Gate`; actual blocking was verified with a temporary PR.

### Tools and skills

#### CodeGraph source navigation

CodeGraph is enabled for locating files, symbols, call paths, and affected tests before changing Python
source. Its index is locally generated development data, not a Python Distribution, and must not be
committed as business code.

Run from the repository root; initialize on first use, or check status when an index exists:

```bash
codegraph status
codegraph files
codegraph explore "<symbol or code question>"
codegraph node <symbol-or-file>
codegraph callers <symbol>
codegraph callees <symbol>
codegraph impact <symbol>
codegraph affected "<file>"
codegraph sync
```

Replace placeholders with real symbols or paths. Understand boundaries before editing; after editing,
sync the index, analyze impact, and run relevant tests. Use `codegraph index` to rebuild a corrupt index;
CodeGraph relationship evidence does not replace type checks, tests, or builds.

`.codegraph/.gitignore` ignores local databases, logs, daemon state, sockets, and similar temporary files;
only `.gitignore` itself is retained as a project convention. If the index is stale or missing, sync or
initialize it; do not copy locally generated database files to other environments.

#### Project skills and technical diagrams

Project-level Agent capabilities live under `.agents/skills/`, including Spec Kit entries and a fixed
version of [Fireworks Tech Graph](.agents/skills/fireworks-tech-graph/SKILL.md). Skills are development
tools, not Python Distributions, and do not enter business package runtime dependencies.

Fireworks generates SVG technical diagrams from descriptions and can export PNG on demand without an image
model API key. SVG is the maintainable primary artifact; diagrams must distinguish current implementation
from target design and verify arrow relationships, evidence sources, and final visual quality. Helper
scripts are isolated from each retained package environment; installing the skill does not mean rendering
dependencies are complete and does not authorize paid APIs, publication, or source disclosure. See
[technical diagrams](docs/development/technical-diagrams.md) for usage, Windows commands, and limits.

### Distribution and evolution

#### Git URL

For early development or quick reuse, install a specific tag from a private Git repository and point
`subdirectory` at the package:

```bash
uv pip install "spawn-join-llm-provider-langchain @ git+https://github.com/<your-org>/spawn-join.git@v0.1.0#subdirectory=packages/infra/llm-provider-langchain"
```

Ensure the repository authentication is configured and the target package can build independently.

#### Private package registry

When multiple projects continuously depend on these components and need version pinning, automated builds,
and releases, use a Python-capable private package registry; the specific service and release pipeline are
planned separately. Business projects declare only the required packages and version ranges, for example:

```toml
[project]
dependencies = [
    "spawn-join-core>=0.1.0,<0.2.0",
    "spawn-join-llm-provider>=0.1.0,<0.2.0",
]
```

Each package maintains its own version; semantic versioning (SemVer) is recommended so unrelated domain
packages are not forced to upgrade together merely because they share a repository.

#### Evolution rules

- Extract capabilities into Core only after at least two components have a stable, real reuse need.
- If a capability depends on third-party libraries such as Redis, Azure OpenAI, or SQLAlchemy, prefer the relevant domain package over Core.
- Put new implementations in existing domain modules or modules approved by a Plan; do not pre-build empty `implementations/` or `providers/` directories.
- Every package must be independently installable, testable, buildable, and publishable.
- Export public APIs explicitly through each package's `__init__.py`; internal implementation must not become a public contract unintentionally.

### Current status

| Category | Current boundary |
|---|---|
| Domain packages | five retained independent Distributions; LLM packages implement channel/options contracts, the LangChain model factory, manual metadata sync, and DeepAgents product assembly; Core is still a scaffold |
| SDD foundation | Constitution, Spec Kit templates/scripts, and Bundle v0.4.2-managed native Delivery commands (including close/evidence closure and the package README node); Feature artifacts remain local |
| Harness governance | phase plans, context, review, evidence, execution logs, and structural/index gates; not an automatic execution engine |
| Development quality | Black/isort, Ruff, Pyright, pytest, actionlint, PSScriptAnalyzer, build/install verification, and GitHub Actions |
| Durable knowledge and diagrams | ADR classification/templates and project-level Fireworks; rendering depends on local dependencies |
| Not configured | automated Spec Kit/Harness hooks and a release pipeline |

### License

This repository and its five retained Distributions are proprietary software. All rights reserved.
Without written permission from the copyright holder, you may not use, copy, modify, publish,
distribute, sublicense, or sell them. See [LICENSE](LICENSE).

Actual commands, environments, and verification limitations are authoritative in the corresponding
[Harness evidence](harness/evidence/README.md) records; configuration presence or one local success does
not replace verification of the current revision. Known Fireworks compatibility and rendering dependency
limits are recorded in the [skill verification record](harness/evidence/adr-and-project-diagram-skill.md).

See the repository [LICENSE](LICENSE).
