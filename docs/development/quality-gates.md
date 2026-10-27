# Python Quality Gates

本文件拥有质量工具、命令、失败终态和 CI 的运行说明。业务行为和架构/DRY 审查仍由
Spec、Plan、Tasks 和人工 Standards Review 负责；机械检查不能代替审批或标准审查。

## Tools and ownership

| Check | Owner | Failure condition |
|---|---|---|
| 代码排版 | Black，88 列，Python 3.11 目标 | `--check` 发现需要重新格式化 |
| import 分组/排序 | isort，Black profile，88 列 | `--check-only` 发现差异 |
| 错误和复杂度 | Ruff E4/E7/E9/F/B/UP/T20/C90 | 任何启用规则违反；复杂度上限 10 |
| 类型 | Pyright strict，Python 3.11 / All | 类型诊断导致非零退出 |
| 契约测试 | pytest，各包 `tests/` | 失败、收集错误或零测试（pytest exit 5） |
| 包产物 | uv build、隔离 wheel 安装、pip check、isolated import | 任一步失败或缺少 wheel/sdist |
| 文档 | PowerShell 本地目标/尾随空白检查、Git diff 检查 | 文件缺失、本地链接缺失或空白错误 |
| 治理记录 | `check-governance.ps1`：evidence 元数据、build-log 引用、ADR 索引、Spec/Tasks、本地-only 链接 | 结构不一致、未索引 ADR、状态矛盾或链接到被忽略路径 |
| 静态分析 | actionlint 1.7.12（`uvx actionlint-py==1.7.12.25`）、PSScriptAnalyzer 1.25.0 | workflow 语法/表达式错误，或 PowerShell 高信号规则违反 |

根 [`pyproject.toml`](../../pyproject.toml) **只包含 tool 表**，不是 Python project 或 uv
workspace，不得向其加入 project/build-system/dependency-groups。Black 与 isort 不和
Ruff formatter/I 规则混用；CI 不运行自动修复。

Black、isort、Ruff、Pyright、pytest 的版本范围归各包的 dev group 所有，实际版本归各自
uv.lock 所有。运行时依赖未增加；工具不会进入 wheel 的 Requires-Dist。

## Prerequisites

- PowerShell 7（`pwsh`）、Git、uv >=0.7.13；CI 固定 uv 0.13.5。
- 可用的 Python >=3.11；CI 显式覆盖 3.11 和 3.14。本机无需全局 `python` 命令。
- Node 22+：Pyright wrapper 使用已有 Node；入口拒绝缺失或旧版本，不隐式安装 Node。
- 静态分析：`uvx` 自动使用固定 `actionlint-py==1.7.12.25`；PSScriptAnalyzer 需预先安装：
  `Install-Module PSScriptAnalyzer -RequiredVersion 1.25.0 -Scope CurrentUser -Force`。
- 首次依赖同步、隔离构建及安装需要公开包索引网络，无真实服务、密钥或私有凭据。

## Local entry point

从仓库根目录运行：

```powershell
pwsh -NoProfile -File scripts/quality.ps1
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core -Check format
pwsh -NoProfile -File scripts/quality.ps1 -Check lint
pwsh -NoProfile -File scripts/quality.ps1 -Check type
pwsh -NoProfile -File scripts/quality.ps1 -Check test
pwsh -NoProfile -File scripts/quality.ps1 -Check build
pwsh -NoProfile -File scripts/quality.ps1 -Check docs
pwsh -NoProfile -File scripts/quality.ps1 -Check governance
pwsh -NoProfile -File scripts/quality.ps1 -Check static
pwsh -NoProfile -File scripts/test-quality.ps1
pwsh -NoProfile -File scripts/test-governance.ps1
pwsh -NoProfile -File scripts/test-static.ps1
```

Package 是四个真实 Distribution 名称之一，省略则检查全部。`all` 包含文档、治理、静态分析和包检查；
指定 Package 的包级任务不重复执行仓库级检查。只指定其他 Check 时不宣称其他门禁通过。
工具缺失、锁不一致、安装失败都不会被跳过。

每个包先执行 `uv lock --check` 和 `uv sync --locked`，随后使用该包环境中的工具。
所有工具显式引用根配置；类型检查显式绑定该包解释器。若要验证指定的已安装 Python，
可设置 `UV_PYTHON`（例如 `3.11`）再运行入口，不会自动回退到其他版本。

脚本输出实际命令及 `exit_code`；终态为 0 或失败 1。它不生成提交或自动宣称阶段完成。
依赖同步会更新忽略的包级环境/元数据/缓存；“只读检查”指不自动重写源码和锁文件。

### Explicitly fixing formatting

下面是会修改文件的人工命令，不属于 CI 检查：

```powershell
uv run --locked --directory packages/core/spawn-join-core isort --settings-path ../../../pyproject.toml src tests
uv run --locked --directory packages/core/spawn-join-core black --config ../../../pyproject.toml src tests
```

先 isort 再 Black。替换包目录可处理其他 Distribution；`uv --directory` 会改变工具工作目录，
因此工具参数应相对于包目录，或者使用绝对路径。

## Artifact isolation

构建目标及其本仓库上游包时先复制源码到唯一临时 staging，排除环境、缓存和旧构建产物，
再用 `uv build --no-sources` 构建。不会在真实包目录中新建 build/dist 目录。
第三方运行时依赖从目标包的锁导出；本仓库包显式排除，改为安装本次构建的 wheel。
全新 venv 中执行 `uv pip check` 和 `python -I` 导入，避免 editable 安装掩盖包缺失问题。

临时目录父路径默认使用系统临时目录；本机可设置 `SPAWN_JOIN_TEMP_DIR` 为已存在路径。
成功或失败都会在 finally 中删除本次创建的唯一子目录，不清理整个父目录或用户源树。
包级 README 缺失的 setuptools 警告是现有元数据问题，不在本 Feature 顺便修复。

## CI and merge protection

[`quality.yml`](../../.github/workflows/quality.yml) 对所有 PR、main push 和手动运行启用：

- 四个包 × Linux/Python 3.11、Linux/Python 3.14、Windows/Python 3.11，共 12 组合；
- 独立 governance job 执行文档和门禁故障回归；
- 最后固定名称 `Quality Gate`，只有 packages 和 governance 都为 success 才成功；
- 无路径过滤，避免只改文档时 required check 永远 pending；
- contents:read、checkout 不持久化凭据、Action 固定 SHA、明确超时、取消过期运行；
- 不使用 pull_request_target，不发布、不部署、不修改 GitHub 设置。

**Merge protection**: 仓库 Ruleset `main` 已启用 PR、线性历史、禁止删除和 force push，
并把 `Quality Gate` 设为 required status check；`strict_required_status_checks_policy=true`，
合并前分支必须与 main 同步。配置已由 API 核对；临时失败 PR #3 的 `mergeStateStatus`
为 `BLOCKED`，验证后已关闭。

## Regression and limitations

`scripts/test-quality.ps1` 在路径含空格的临时 Git fixture 中运行真实工具：一个全流程成功，
以及 Black、isort、Ruff、类型、失败测试、wheel 导入失败、零测试、坏链接八种拒绝场景。
`scripts/test-governance.ps1` 用独立 fixture 覆盖 11 个治理场景（合法结构、缺字段、非法
状态词、未索引 ADR、本地-only 链接、evidence 未进 build-log、缺失 build-log、状态矛盾、
重复任务 ID、纯文档跟进不告警、非文档变更告警）。
`scripts/test-static.ps1` 覆盖 3 个静态分析场景（合法结构、坏 workflow、`Invoke-Expression`）。
检查探针内容没有被格式检查重写，也不产生根级环境/锁/构建目录。

- 现有 20 个 pytest 用例只覆盖当前骨架的导入、身份和运行时依赖边界，不是业务覆盖率。
- 文档检查验证简单 Markdown 本地目标存在，不验证网页内容、所有 Markdown 语法或锚点。
- 治理检查验证结构和索引一致性；evidence 的语义是否覆盖改动、freshness 是否仍有效
  仍需人工评审（落后且期间有非文档路径变更时产生 warning；纯文档追加不告警）。
- 静态分析只覆盖 workflow 语法/表达式和 PowerShell 高信号规则，不验证运行时行为；
  `.agents/skills/` 的第三方脚本不在扫描范围。
- 本期不安装 pre-commit、coverage 百分比门槛、漏洞扫描或发布流水线。
- Standalone 质量入口/CI 不是 Spec Kit hook；Delivery/Ralph 仍未配置。
- 增加依赖、接口或目录后，必须同步测试、脚本中的本地构建依赖映射、文档和实际证据。

本地 Feature 为 `specs/002-python-quality-gates/`（Git 忽略，不保证存在于干净检出）。
可共享的实施与验证记录见
[Harness evidence](../../harness/evidence/phase-01-python-quality-gates.md)。
