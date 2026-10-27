# SpawnJoin

SpawnJoin 是一个面向多个私有 Python 项目的基础设施组件单仓库（monorepo）。每个包都是
可以独立构建、测试、版本化和发布的 Python Distribution，不使用根级共享 uv 环境。

`spawn` 表示创建执行单元，`join` 表示等待执行单元完成。项目关注完整生命周期：从初始化、
运行和观测，到完成、回收与清理；工程协作采用 **SDD 规范驱动开发 + Harness 工程治理**。

## 导航

| 分类 | 内容 |
|---|---|
| [项目与架构](#项目与架构) | 项目原则、包边界与仓库地图 |
| [SDD 与 Harness 工程治理](#sdd-与-harness-工程治理) | 交付路由、工件职责、执行证据与长期决策 |
| [本地开发与质量验证](#本地开发与质量验证) | 独立 uv 环境、测试、类型、格式和构建 |
| [工具与技能](#工具与技能) | CodeGraph 源码导航、项目级技术图技能 |
| [包分发与演进](#包分发与演进) | Git 安装、私有分发与扩展边界 |
| [当前状态](#当前状态) | 已有基础、能力边界与尚未启用的自动化 |

## 项目与架构

- **独立 Package**：各 Distribution 拥有自己的 `pyproject.toml`、`uv.lock`、`.venv/`
  和 `tests/`，保留独立安装、构建与发布边界。
- **Core 小而稳定**：只承载跨领域稳定规则；LLM 等领域的协议留在对应领域包。
- **依赖单向**：业务应用组合基础设施包；框架与 Provider SDK 留在适配层，不泄漏回协议或 Core。
- **按需扩展**：只有真实、稳定的复用需求才提取公共能力，不预建万能工具模块或未来包。
- **公共 API 显式导出**：源码使用 `src/` layout，通过各包 `__init__.py` 定义公共入口。

`packages/core` 和 `packages/infra` 是架构分组，不是额外的 Distribution。Distribution
名称使用连字符，Python import package 使用下划线。四包职责和依赖方向以
[包边界说明](docs/architecture/package-boundaries.md)为准，实际元数据以各包的
`pyproject.toml` 为准。

完整目录结构只维护在[仓库地图](docs/architecture/repository-map.md)，首页不复制完整树。
当前领域代码仍是最小骨架；尚不包含 `spawn-join-database` 或 `spawn-join-agent`。

## SDD 与 Harness 工程治理

**SDD（Spec-Driven Development）** 明确“做什么、为什么做、怎样验收”；
**Harness** 记录“在什么范围和上下文中执行、如何审查、实际验证了什么”。二者互补，
不是两套任务系统，也不等于已经启用了自动化 Agent 编排。

### 按风险选择交付路由

| 路由 | 适用范围 | 执行要求 |
|---|---|---|
| Lightweight | 文档、机械性或行为保持不变的窄范围改动 | 锁定范围，保留针对性验证；不制造空的 Feature 工件 |
| Bugfix | 可复现、边界明确的缺陷 | 先建立失败证据，再修复与回归 |
| Feature | 新增行为、公共 API、跨包边界、持久化、安全或架构决策 | 先完成 Spec / Plan / Tasks，再按任务实现和审查 |

Feature 的基本链路是：

```text
需求澄清 → Spec → Plan / 必要的 ADR → Tasks → 增量实现 → 验证与审查 → 交接
```

`tasks.md` 是 Feature 的唯一执行队列；Harness 阶段计划不能另建一份任务系统。
项目级人工入口见 [sd](.agents/skills/sd/SKILL.md) 与
[speckit-delivery](.agents/skills/speckit-delivery/SKILL.md)。入口存在不表示完整 Delivery
已配置；缺少配置或执行能力时必须报告未配置/blocked，不伪装成自动化流程已完成。
详细执行契约以 [AGENTS.md](AGENTS.md) 和
[Constitution](.specify/memory/constitution.md) 为准。

### 分清工件职责

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

### Harness 工程化治理

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

## 本地开发与质量验证

### 独立环境与日常运行

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

只同步本次开发涉及的包即可。在对应包环境中运行命令时，使用 `uv run`，例如：

```bash
uv run --directory packages/core/llm-provider python -c "import spawn_join_llm_provider"
```

构建并隔离验证单个 Distribution（输出位于临时目录）：

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core -Check build
```

替换 Distribution 名可检查其他包；测试始终以包为边界独立执行。

### 统一质量门禁

```powershell
pwsh -NoProfile -File scripts/quality.ps1
pwsh -NoProfile -File scripts/test-quality.ps1
```

需要 PowerShell 7、uv、Python >=3.11、Node 22+。Black/isort 统一格式，Ruff 做 lint，
Pyright 做严格类型检查，pytest 验证包契约，另外执行文档、构建和隔离安装检查。
根 `pyproject.toml` 只保存共享工具配置，不是根级 uv project；工具依赖仍在各包 dev group。
命令、修复格式、CI 矩阵和分支保护说明见
[`docs/development/quality-gates.md`](docs/development/quality-gates.md)。

GitHub Actions 配置见 [quality.yml](.github/workflows/quality.yml)，覆盖四包和跨平台矩阵，
并设置 `Quality Gate` 汇总检查。Ruleset `main` 已启用 PR、线性历史和 required `Quality Gate`；
失败 PR 的实际拦截已用临时 PR 验证。

## 工具与技能

### CodeGraph 源码导航

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

### 项目级技能与技术图

项目级 Agent 能力放在 `.agents/skills/`，包括 Spec Kit 入口和固定版本的
[Fireworks Tech Graph](.agents/skills/fireworks-tech-graph/SKILL.md)。技能是开发工具，
不是 Python Distribution，也不进入业务包运行时依赖。

Fireworks 从描述生成 SVG 技术图，可按需导出 PNG，不需要图像模型 API Key。
SVG 是可维护主产物；图中必须区分当前实现与目标设计，并核对箭头关系、事实来源和最终视觉效果。
辅助脚本与四包环境隔离；安装技能不代表渲染依赖齐全，也不授权付费 API、发布或外传源码。
使用方式、Windows 命令和环境限制见[技术图说明](docs/development/technical-diagrams.md)。

## 包分发与演进

### Git URL

适合早期开发或快速复用时，可以从私有 Git 仓库安装指定 tag，并通过 `subdirectory` 指向具体包：

```bash
uv pip install "spawn-join-llm-provider-langchain @ git+https://github.com/<your-org>/spawn-join.git@v0.1.0#subdirectory=packages/infra/llm-provider-langchain"
```

使用 Git URL 时，需要确保对应仓库的认证方式已经配置完成，并且目标包可以独立构建。

### 私有 Package Registry

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

### 演进规则

- 只有至少两个组件存在稳定、真实的复用需求时，才考虑把能力提升到 Core。
- 如果能力依赖 Redis、Azure OpenAI、SQLAlchemy 等第三方库，优先放入相应领域包，而不是 Core。
- 新增实现时，放入对应领域的 `implementations/` 或 `providers/`，不要直接堆到包根目录。
- 每个包都应能独立安装、测试、构建和发布。
- 公共 API 通过包的 `__init__.py` 明确导出；内部实现不要无意中成为公共契约。

## 当前状态

| 类别 | 当前边界 |
|---|---|
| 领域包 | 四个独立 Distribution、最小源码骨架与包级边界测试；尚无具体模型或可观测性业务实现 |
| SDD 基础 | 已有 Constitution、Spec Kit 模板/脚本及人工技能入口；Feature 工件按需在本地创建 |
| Harness 治理 | 已有阶段计划、上下文、评审、证据与执行日志约定，以及结构/索引门禁；不是自动执行引擎 |
| 开发质量 | 已配置 Black/isort、Ruff、Pyright、pytest、构建/安装验证和 GitHub Actions |
| 长期知识与绘图 | 已有 ADR 分类、模板与项目级 Fireworks；渲染能力取决于本机依赖 |
| 尚未配置 | 完整 Delivery/Ralph 编排、自动化 Spec Kit/Harness hook 与发布流水线 |

实际命令、环境和验证限制以 [Harness evidence](harness/evidence/README.md) 中对应记录为准；
不以配置存在或某次本机成功代替当前 revision 的验证。Fireworks 已知兼容性与渲染依赖限制见
[技能验证记录](harness/evidence/adr-and-project-diagram-skill.md)。
