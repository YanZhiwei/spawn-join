# SpawnJoin Repository Map

> 本文件是仓库导航视图，不是项目治理原则。
> 包的真实名称、依赖和构建边界以对应 Distribution 的 `pyproject.toml` 为准；
> Feature 的具体影响路径以 `specs/<feature-id>/plan.md` 和 `tasks.md` 为准。

## 当前仓库结构

```text
spawn-join/
├── .github/workflows/             # GitHub Actions 质量检查；无发布或远端设置
├── .agents/
│   └── skills/                    # Spec Kit 与固定版本 Fireworks 技能
├── .codegraph/                    # 本机源码索引；只提交 .gitignore
├── .specify/                      # Spec Kit 基础设施
│   ├── integrations/              # Codex、Speckit 等集成清单
│   ├── memory/                    # 项目 Constitution
│   ├── scripts/                   # Spec Kit 辅助脚本
│   ├── templates/                 # Spec、Plan、Tasks 等模板
│   └── workflows/                 # 已安装的 Spec Kit workflow
├── docs/
│   ├── architecture/              # 仓库地图和包边界说明
│   ├── decisions/                 # 按领域分类的长期 ADR、模板和索引
│   └── development/               # 质量工具、技术图和运行说明
├── harness/                        # 阶段计划、上下文、评审和验证证据
│   ├── build/
│   ├── context/
│   ├── code_review/
│   ├── evidence/
│   └── build-log.md
├── packages/
│   ├── core/
│   │   ├── spawn-join-core/          # 独立 uv project、环境和锁文件
│   │   └── llm-provider/             # 独立 uv project、环境和锁文件
│   └── infra/
│       ├── llm-provider-langchain/   # 独立 uv project、环境和锁文件
│       └── spawn-join-observability/ # 独立 uv project、环境和锁文件
├── AGENTS.md                      # Agent 工作约定和治理入口
├── pyproject.toml                 # tool-only 配置，不是根级 Python/uv project
├── README.md                      # 面向使用者的项目概览
├── scripts/                       # PowerShell 质量入口及其故障回归
├── specs/                         # 本地交付工件；Git 忽略，不随仓库分发
│   ├── 001-harness-foundation/    # 历史工件，ADR-0002 取消跟踪，本地保留
│   └── 002-python-quality-gates/  # 当前 Feature
```

本地 `specs/` 包含 Harness Foundation 和 Python Quality Gates；`/specs/` 已加入 Git 忽略，
历史工件已按 [ADR-0002](../decisions/engineering/0002-untrack-historical-feature-artifacts.md)
取消跟踪但保留本机文件，未跟踪工件仅保留在本地，不代表任务已经完成。`harness/` 保存阶段约定及实际
记录；standalone 质量入口和 CI 配置已加入，但没有自动化 Spec Kit hook、Delivery 或发布。
远端 CI 和分支保护必须另有运行/配置证据，不把配置路径存在当作通过。

## 导航入口

| 主题 | 权威入口 |
|---|---|
| 首页分类导航与项目概览 | [`README.md`](../../README.md) |
| 项目原则和治理 | [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) |
| Agent 工作约定 | [`AGENTS.md`](../../AGENTS.md) |
| Package 职责和依赖方向 | [`package-boundaries.md`](package-boundaries.md) |
| 长期架构决策、分类和模板 | [`docs/decisions/README.md`](../decisions/README.md) |
| 项目级技术图技能和环境隔离 | [`technical-diagrams.md`](../development/technical-diagrams.md) |
| Feature 规范和任务 | `specs/<feature-id>/`（按需创建） |
| Harness 阶段记录和证据 | [`harness/README.md`](../../harness/README.md) |
| Spec Kit 模板、脚本和 workflow | [`.specify/`](../../.specify/) |
| Python 包元数据和构建配置 | 各 Distribution 的 `pyproject.toml` |
| 质量工具和运行命令 | [`quality-gates.md`](../development/quality-gates.md) |
| Python 源码关系和影响范围 | CodeGraph 索引 |

## 路径语义

- `packages/core` 和 `packages/infra` 是架构分组，不是 Python Distribution。
- 每个下层 Distribution 都拥有自己的 `pyproject.toml`、`src/` layout 和独立构建边界。
- Distribution 名称使用连字符，例如 `spawn-join-core`；Python import package 使用下划线，
  例如 `spawn_join_core`。
- `docs/architecture/` 只维护架构和导航说明，不记录 Feature 的临时任务状态。
- `docs/decisions/` 是唯一 ADR 根，按职责分类，保存长期理由与必要设计图，不替代 Feature 或实际证据。
- `.agents/skills/fireworks-tech-graph/` 保留固定提交的第三方技能及原始辅助脚本，不是领域源码或 Python Distribution。
- `harness/` 只维护阶段计划、材料性上下文、评审、证据和实际执行日志，不替代 Spec/Plan/Tasks。
- `.specify/` 维护 Spec Kit 自身的模板、脚本、集成和 workflow，不存放普通业务设计。
- `.codegraph/` 是本机开发辅助数据，不是 Python 包，也不是业务源码。
- 每个 Distribution 都是独立的 uv project，拥有自己的 `pyproject.toml`、`.venv` 和 `uv.lock`；仓库根目录不创建共享 uv workspace。
- 根 `pyproject.toml` 只包含 tool 表；开发依赖仍由四个 Distribution 各自锁定。
- `scripts/` 只存放开发治理 PowerShell 脚本，不承载 Python 领域源码。
- Python 构建产物不得进入版本控制，包括根目录或包目录下的 `build/`、`dist/`、`*.egg-info/`、缓存和临时报告；`harness/build/` 是应提交的治理文档目录。

## 更新规则

当发生以下变化时，必须更新本文件：

- 新增、删除或重命名顶层治理目录；
- 新增、删除或移动 Distribution；
- `packages/core` 或 `packages/infra` 的架构归属发生变化；
- `.specify/`、`docs/architecture/` 或 `harness/` 的职责发生变化；
- README 或 AGENTS 中的导航入口发生变化。

普通模块新增、类新增或同一 Distribution 内部文件移动，不需要把每个文件追加到本地图。
这类变更使用 CodeGraph、IDE 和 Feature 的计划文件导航。

更新本文件时，应同时检查：

1. 目标路径是否真实存在，或者是否明确标记为“Feature 时创建”；
2. 每个 Distribution 的 `pyproject.toml` 是否仍然与包名、源目录和依赖一致；
3. 本文件、README、AGENTS 和包边界文档之间是否出现重复或矛盾；
4. `git diff --check` 和相关文档链接检查是否通过。
