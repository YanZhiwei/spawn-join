# Harness Build Log

> 本文件是实际执行进度和观察到的验证结果，不是未来工作的计划。
> 条目按时间追加；如果早期记录有错误，追加更正，不静默删除失败尝试。

## 2026-10-26 — Harness Foundation

**Status**: Complete for the documentation-first foundation slice

**Feature**: `001-harness-foundation`

**Branch**: `main`

**Base revision**: `ac959f696c4af5a902e2dc596e8a6ebd0af2792f`

**Head revision**: `ac959f696c4af5a902e2dc596e8a6ebd0af2792f`

**Working directory**: `D:\Repos\Github\spawn-join`

### Scope

- 建立 Harness 的职责入口和子目录说明；
- 建立 Feature Spec、Plan、Tasks、Research 和 Quickstart；
- 更新仓库地图、包边界、README 和 AGENTS 的导航；
- 不修改 Python 源码、包依赖、CI、hook 执行器、分支、提交、推送或外部系统。

### Pre-existing Worktree State

本 Feature 开始前工作区已经包含未提交的 README、AGENTS、`.agents/`、`.codegraph/`、
`.specify/` 和 `docs/` 变化。因为本次 Feature 也更新了其中的部分文档，当前 `HEAD` 与
工作树之间的完整 diff 不能单独归因于本 Feature；收口前必须按实际 changed paths 重新
确认范围。

### Observed Actions

- Spec Kit 初始化脚本创建了 `specs/001-harness-foundation/spec.md` 和活动 Feature 指针；
- 生成了本 Feature 的 Spec、Plan、Tasks、Research、Quickstart 和质量清单；
- 创建了 `harness/` 及其 build、context、code review、evidence 说明文件；
- 没有创建 `.specify/extensions.yml`，因此没有执行 Spec Kit 扩展 hook。

### Feature-owned Paths

本 Feature 触及的治理和交付路径为：

- `AGENTS.md`
- `README.md`
- `docs/architecture/package-boundaries.md`
- `docs/architecture/repository-map.md`
- `harness/README.md`
- `harness/build/README.md`
- `harness/context/README.md`
- `harness/code_review/README.md`
- `harness/evidence/README.md`
- `harness/build-log.md`
- `specs/001-harness-foundation/`

### Verification

- Markdown 本地链接检查：`PASS`，检查 16 个 Markdown 文件；
- 任务格式检查：`PASS`，19 个任务，ID 连续，均包含状态、ID 和目标路径；
- `git diff --check`：`PASS`；Git 仅输出 `README.md` 的 LF/CRLF 提示，没有 diff 错误；
- 尾随空格检查：`PASS`，变更文档未发现尾随空格；
- Harness、Feature 和架构目录检查：`PASS`，目标目录均存在；
- 过期基线检查：`PASS`，AGENTS 不再声称 Constitution 未完成或 `.specify/` 不存在；
- Python 构建、类型检查和测试：`not-run`，本 Feature 只修改文档和治理记录。

### Environment Note

PowerShell 启动配置在命令开始前输出了若干与仓库无关的 `Import-Clixml` 诊断；上述目标
检查仍返回成功状态，诊断未被计入 Harness 验证结果。

### Limitations and Blockers

- 当前 Harness 仍然是文档约定，尚未被 hook 或独立校验脚本自动强制执行；
- 当前仓库仍没有统一的 Ruff、Pyright/mypy、pytest、pre-commit 或 CI quality profile；
- 工作区不是干净基线，不能仅凭本条目声明完整 Feature diff 已独立收口；`.agents/`、
  `.codegraph/`、`.specify/` 和部分文档变化在本 Feature 开始前已经存在。

## 2026-10-26 — Harness Foundation 收口范围重新确认

**Status**: Complete（证据重新锚定与状态修正；无行为变化）

**Route**: Lightweight（文档修正，不创建新 Feature Spec）

**Feature**: `001-harness-foundation`

**Branch**: `main`

**Base revision**: `bd497d72e928f596e79cdbe5b1466eba4c75ec39`

**Working directory**: `D:\Repos\Github\spawn-join`

### Purpose

上一条目把 Feature 证据锚定在 `ac959f6` 的工作树状态，且记录了基线不干净的警告。实际
收口提交 `bd497d7` 产生后，按 `AGENTS.md` 第 8 节"新提交产生后旧 evidence 必须重新确认
范围"的要求补做范围确认；同时修正 `specs/001-harness-foundation/spec.md` 仍为 `Draft`
的过期状态。

### Scope Re-confirmation against bd497d7

`bd497d7`（`chore: establish SDD governance and independent uv projects`）共包含 62 个
文件，按归属分类核对：

- 16 个文件与上一条目声明的 Feature-owned 路径一一对应（`AGENTS.md`、`README.md`、
  两个架构文档、`harness/` 下 6 个文件、`specs/001-harness-foundation/` 下 6 个工件），
  无缺失、无多余；
- 其余 46 个文件在 Feature 声明范围之外：`.agents/skills/`（17）、`.specify/` 初始化
  工件（20）、`.codegraph/.gitignore`（1）、根 `.gitignore`（1）、`packages/`（7，四个
  Distribution 的 `pyproject.toml` 增量与 `uv.lock`）。其中 `.agents/`、`.specify/`、
  `.codegraph/`、README、AGENTS 和 docs 的变化与上一条目 "Pre-existing Worktree State"
  的记录一致；`packages/` 与根 `.gitignore` 未被上一条目显式枚举，属于提交标题所述
  "independent uv projects" 部分，此归因限制维持原记录，不做追溯改写。

### Changes in This Entry

- `specs/001-harness-foundation/spec.md`：`Status` 由 `Draft` 更新为 `Implemented`，
  与 `tasks.md` 19/19 任务完成状态对齐；
- `harness/build-log.md`：追加本条目。

### Verification

- `git show --name-only --format= bd497d7` 分类统计：实际执行，62 = 16 + 17 + 20 + 1 + 1 + 7，
  结果如上；
- `git status --short --branch`（本条目开始前）：工作区干净，`main` @ `bd497d7`；
- Markdown 本地链接检查（quickstart 脚本，`-NoProfile`）：`PASS`；该清单覆盖 9 个导航
  文件，本条目修改的两个文件不在清单内，且本次修改未新增或删除链接；
- `git diff --check`：`PASS`；Git 仅输出两个变更文件（`harness/build-log.md`、
  `specs/001-harness-foundation/spec.md`）的 LF/CRLF 提示，没有尾随空格或 diff 错误；
- 本条目未修改 Python 源码、依赖、CI、hook 或任何外部系统状态。

### Limitations

- 本条目与 `spec.md` 状态修正在撰写时尚未提交；提交后需按同一规则再次确认 `HEAD`；
- `.specify/feature.json` 是本机活动 Feature 指针（已被 `.specify/.gitignore` 排除），
  由 Spec Kit 工具管理，本条目不修改；
- 混合提交的逐文件归因（Feature 内/外）无法仅凭提交本身重建，维持上一条目的记录。

## 2026-10-26 — Python Quality Gates

**Status**: Implemented and locally verified；远端 CI / Ruleset 未执行

**Route**: Feature，用户批准的人工 Spec/Plan/Tasks；没有运行 Ralph 或自动收口提交

**Feature**: `002-python-quality-gates`

**Base/head**: `bd497d72e928f596e79cdbe5b1466eba4c75ec39` + 未提交工作树

**Working directory**: `D:\Repos\Github\spawn-join`

### Observed implementation

- 新增 tool-only 根配置；四包独立 dev group/lock，未改变运行时依赖或公共 API。
- 新增 Black/isort、Ruff lint、Pyright strict、pytest、文档、构建和隔离安装检查入口。
- 新增 20 个现有包契约测试和 9 场景门禁回归；零测试不能通过。
- 新增 12 组合 GitHub Actions 配置及固定名称 `Quality Gate`；没有配置远端 Ruleset。
- 同步运行说明、架构/Harness 导航和测试生成规范；只删除 Core 多余末尾空行。
- 保留本条目前全部历史内容和用户 Foundation spec 状态修正；不提交、不推送、不改分支。

### Observed verification and limitations

- `pwsh -NoProfile -File scripts/quality.ps1`：退出 0，Windows Python 3.13.5，四包完整检查通过。
- 同一入口在隔离副本中使用 Python 3.11.13：退出 0，四包完整检查通过，真实环境未切换。
- 使用 CI 固定 uv 0.13.5 重跑完整入口及回归：均退出 0；未升级全局 uv。
- `pwsh -NoProfile -File scripts/test-quality.ps1`：退出 0；8 种故障被实际拒绝。
- workflow/config 补充静态检查和汇总脚本 16 种状态组合：退出 0；不是 GitHub 运行结果。
- CodeGraph sync/affected：退出 0；没有据此跳过全包测试。
- 全部变更文本空白检查通过；源树 build/dist 未增加，已清理本次生成的已知 setuptools 元数据。
- 原有 README、hardlink/copy、LF/CRLF 警告仍记录；全局 Python alias 问题未改动。
- Linux、Python 3.14、远端 CI、Ruleset、Delivery/hook/Ralph、发布和安全扫描均未执行。

详细命令、退出码、环境、失败尝试、37 路径范围及复核说明：
[Evidence](evidence/phase-01-python-quality-gates.md)；
[Review](code_review/review-phase-01-python-quality-gates.md)。新提交或实现范围变化后须重新确认。

## 2026-10-26 — ADR and project-local diagram skill (Lightweight)

- 按用户授权设置唯一 `docs/decisions/` 根、领域/子领域分类、全局编号和显式 ADR 关联，
  增加模板与首条工程治理决策；不改变 Feature 的 Spec/Plan/Tasks 执行要求。
- 安装固定提交的 Fireworks 1.2.0 到 `.agents/skills/fireworks-tech-graph/`，139 个上游
  文件逐字节校验一致，保留 MIT 许可证、引用和测试，另加本地来源说明。
- 用户后续要求忽略 Specs：根 `.gitignore` 加 `/specs/`，不删除现有文件、不取消已有
  跟踪；将长期文档中指向被忽略 002 工件的链接改为明确的本地路径及共享说明入口。
- 上游针对性测试 35 项：33 通过、2 个 Windows 路径/换行断言失败；未修改上游实现。
  实际 SVG 验证、生成、结构检查和离线 HTML 导出通过；PNG/GIF 因渲染依赖缺失 blocked。
- 不新增业务依赖，不创建根级环境，不提交、推送、发布或调用收费 API。此前质量门验证
  不自动覆盖本次新范围；本次命令、限制和保留性复核单独记录。

详细范围、基准 HEAD、命令、退出码和残余限制：
[ADR/技能 evidence](evidence/adr-and-project-diagram-skill.md)。

## 2026-10-27 — 修复 CI governance 步骤退出码（Bugfix）

**Status**: Fixed and locally verified；远端 CI 待推送后确认

**Route**: Bugfix；GitHub 已有两次可复现失败，未创建 Feature Spec

**Base revision**: `0e2b10ea176ca9411fa8a7bcb5f34a27a28d1e4f`

**Head revision**: `0e2b10e` 加未提交工作树

**Working directory**: `D:\Repos\Github\spawn-join`

### Observed defect

push `3b0aaf9` 与 `0e2b10e` 的 Quality 运行中，12 个 packages 任务全部通过，但
`governance` 的 `Test gate failure paths` 在 9/9 场景 PASS 后仍以 exit 1 结束，且没有
错误文本。根因是最后一个断言故意运行失败门禁，留下 `$LASTEXITCODE=1`；GitHub 对
`pwsh` 步骤追加 `exit $LASTEXITCODE`，成功路径没有显式退出码。直接 `-File` 运行不
追加该检查，因此历史本机结果 0 掩盖了该缺陷。

### Changes in this entry

- `scripts/test-quality.ps1`：`finally` 清理后显式 `exit 0`，并注释失败原因；
- 新增 `harness/evidence/ci-governance-exit-code.md`；
- 本条目。未改断言、`quality.ps1`、workflow、Python 源码或依赖。

### Verification

- runner 等价包装（dot-source + `exit $LASTEXITCODE`）复现：修复前 exit 1，
  9 个场景全部 PASS；修复后同一包装 exit 0；
- `pwsh -NoProfile -File scripts/test-quality.ps1`：exit 0；
- `pwsh -NoProfile -File scripts/quality.ps1 -Check docs`：exit 0；
- 未残留 `spawn join gate fixture *` 临时目录。

### Limitations

- 本地未运行 Linux pwsh；远端 ubuntu job 需推送后复跑确认。
- 未提交、未推送、未修改远端 Ruleset；本条目绑定未提交工作树，提交后须重新确认。
- 旧证据仍锚定 `bd497d7`，`0e2b10e` 仍无独立记录；均不在本次范围内。

## 2026-10-27 — 远端 CI 确认（fix 4c69609）

- 修复提交 `4c69609667a482e27271ee5a63633c6d0e17fec4`（父 `0e2b10e`）已推送 `origin/main`；
- Quality 运行 `40515982522` 结论 `success`：12 个 packages 矩阵、
  `Governance and gate regression` 和 `Quality Gate` 共 14/14 job 成功；
- 上一条目"远端 CI 待推送后确认"的状态由本条目关闭；
- 本条目为 docs-only 追加，其自身提交的 CI 结果不在此处声称。

## 2026-10-27 — Governance Checks（Feature 003）

**Status**: Implemented and locally verified；远端 CI 待推送后确认

**Route**: Feature（新增治理门禁、CI 步骤和回归）

**Feature**: `003-governance-checks`（本地工件，Git 忽略）

**Base revision**: `c5ad5763dcf00139e629746a9847f9824bb98ebf`

**Head revision**: `c5ad576` 加未提交工作树

**Working directory**: `D:\Repos\Github\spawn-join`

### Observed implementation

- 新增 `scripts/check-governance.ps1`：evidence 必填字段/结果词表、build-log 引用、
  ADR 索引与状态、Spec/Tasks 一致性、被跟踪文档的 local-only 文件链接；
  freshness 只告警；浅克隆缺少历史时降级为 warning。
- 新增 `scripts/test-governance.ps1`：1 个合法结构 + 8 个拒绝场景（共 9 个）。
- `scripts/quality.ps1` 增加 `-Check governance`，无 Package 的 `all` 纳入治理检查；
  包级矩阵任务不重复执行仓库级检查。
- CI governance job 增加结构检查与失败回归，checkout 使用 `fetch-depth: 0`。
- 同步 `docs/development/quality-gates.md`、`harness/README.md`、`harness/evidence/README.md`、
  `AGENTS.md`、`README.md`。
- 三条旧 evidence 只补 `base_revision`/`head_revision`/`recorded_at`/`result` 元数据，
  不改变既有结论。

### Verification

- `scripts/check-governance.ps1`：0 error，1 warning（phase-01 落后 HEAD 6 个提交）；
- `scripts/test-governance.ps1`：9 场景全部按预期；原 `test-quality.ps1` 9 场景无回归；
- `scripts/quality.ps1`：四包完整检查 + 文档 + 治理，exit 0；
- 干净克隆（无 `specs/`）中 docs 与 governance 均 exit 0；
- 失败尝试（StrictMode Count、目录链接误判、浅克隆历史）已在 evidence 中保留。

### Limitations

- freshness 语义仍由人工判断；`phase-01` 欠账留待优先级 2；
- 未提交、未推送；远端 CI 与分支保护未确认；
- 本条目和 evidence 绑定未提交工作树，提交后需重新锚定。

详细命令、失败尝试和残余限制：
[Evidence](evidence/phase-01-governance-checks.md)；
[Review](code_review/review-phase-01-governance-checks.md)。

## 2026-10-27 — 修复 freshness 告警误报（Bugfix）

**Status**: Fixed and locally verified

**Route**: Bugfix（纯文档跟进被误报为证据过期）

**Base revision**: `475ab4ceb257c4a66da607ca7834fde0986fdd41`

**Head revision**: `03dcfc4` 加未提交工作树

### Observed defect

把 evidence 的 head 更新到当前提交后，任何后续 docs-only 提交都会产生
`head_revision is N commit(s) behind HEAD`。这会让刚清理完的证据在随手改文档后
再次告警，削弱 freshness 信号。新增 fixture 先失败：`docs-only follow-up` 场景
在 exit 0 的同时输出 WARN，测试按预期拒绝。

### Changes in this entry

- `scripts/check-governance.ps1`：只在落后且期间改动非文档路径
  （`packages/`、`scripts/`、`.github/`、根配置文件等）时告警；
- `scripts/test-governance.ps1`：新增“纯文档跟进不告警”和“非文档变更告警”两个场景（9→11）；
- `docs/development/quality-gates.md`、`harness/evidence/README.md`、`harness/README.md`
  同步 freshness 语义。

### Verification

- 修复前 fixture：docs-only 场景失败（出现 WARN）；
- 修复后 `scripts/test-governance.ps1`：11 场景全部通过；
- `scripts/check-governance.ps1`：0 error / 0 warning；
- `scripts/quality.ps1`：exit 0。

### Limitations

- 只按路径类别判断，不判断改动语义；人工评审仍然必须。
- 未提交；本条目绑定未提交工作树，提交后按规则重新确认。

## 2026-10-27 — Evidence 再锚定与追溯记录（Lightweight）

**Status**: Complete

**Route**: Lightweight（只更新治理记录，无运行时行为）

**Base revision**: `475ab4ceb257c4a66da607ca7834fde0986fdd41`

**Head revision**: `03dcfc4` 加未提交工作树

### Changes in this entry

- `harness/evidence/phase-01-python-quality-gates.md`：head 更新到合并提交 `475ab4c`，
  新增 reconfirmation 段；原始 `bd497d7` 绑定保留在正文，不改原命令与结论；
- `harness/evidence/phase-01-governance-checks.md`：记录 PR #1、main 运行
  `40525841365` 的远端确认，以及 freshness 修复后的 11 场景；
- `0e2b10e` README 重写补记：该提交只改 `README.md` 与 `repository-map.md`；
  Quality 运行 `40351563312` 的 `Check documents` 步骤成功，governance 失败是
  `test-quality.ps1` 退出码缺陷（已由 `4c69609` 修复），与文档内容无关；
- 本次不创建 Feature Spec；`specs/003` 仍为本地工件。

### Verification

- `scripts/quality.ps1`：exit 0（四包 + 文档 + 治理）；
- `scripts/test-quality.ps1`：9 场景通过；
- `scripts/test-governance.ps1`：11 场景通过；
- `scripts/quality.ps1 -Check docs`：41 文件 / 105 目标；
- `scripts/check-governance.ps1`：0 error / 0 warning；
- 远端：PR 运行 `40525168443` 与 main 运行 `40525841365` 均 14/14 success。

### Limitations

- `0e2b10e` 没有当时的本机原始日志，只能依据远端步骤结果做追溯记录；
- Ruleset / 分支保护仍未配置；
- 本条目提交后已本地重跑 `check-governance.ps1`（0/0）；远端 CI 待 PR 确认；
- 上一条 Bugfix 的验证已在 `03dcfc4` 重跑并通过，其“未提交”限制由本条关闭。

## 2026-10-27 — Ruleset 强制力验证与证据再锚定（Lightweight）

**Status**: Complete

**Route**: Lightweight（远端设置与记录更新，无代码行为）

**Base revision**: `83628acb287a0c3cf74e92530d...`（PR #2 squash 合并）

**Head revision**: `83628ac` 加未提交工作树

### Changes in this entry

- 通过 `PUT /repos/YanZhiwei/spawn-join/rulesets/25965550` 把 `Quality Gate` 加入
  `required_status_checks`；`strict_required_status_checks_policy=true`，`bypass_actors` 为空；
  PR、线性历史、禁止删除和 force push 保持不变；
- 临时 PR #3 在 `README.md` 注入尾随空白：14/14 检查失败，`mergeStateStatus=BLOCKED`；
  验证后已关闭并删除分支，不合入；
- PR #2 以 squash 合并为 `83628ac`；`phase-01-python-quality-gates` 与
  `phase-01-governance-checks` 的 head 重新锚定到该提交；
- 更新 `docs/development/quality-gates.md`、`README.md`、`AGENTS.md`、`harness/README.md`
  中“远端分支保护未配置”的过期表述。

### Verification

- Ruleset API 返回 `required_status_checks=[{context:"Quality Gate"}]`，
  `current_user_can_bypass=never`；
- PR #3：`mergeStateStatus=BLOCKED`，14/14 失败，随后关闭；
- main 运行 `40528549959`：14/14 success；
- `scripts/check-governance.ps1`：0 error / 0 warning；
- `scripts/quality.ps1 -Check docs`：41 文件 / 105 目标；
- 本条目经 PR 更新，远端 CI 待该 PR 验证。

### Limitations

- required check 依赖 `Quality Gate` 这个 job 名称；重命名 job 必须同步 Ruleset。
- 临时失败 PR 只验证“失败无法合并”，不验证管理员绕过（`bypass_actors` 为空）。
- `strict_required_status_checks_policy=true` 要求 PR 分支与 main 同步。

## 2026-10-27 — Static Analysis（Feature 004）

**Status**: Implemented and locally verified；远端 CI 待 PR

**Route**: Feature（新增静态分析入口、CI 步骤和回归）

**Feature**: `004-static-analysis`（本地工件，Git 忽略）

**Base revision**: `2a895da32f5634f9bdbddb9ad0afe2d4fa81ac91`

**Head revision**: `ba8993d1a3d8fe9c6fd760da704ea59a2745677d`

**Working directory**: `D:\Repos\Github\spawn-join`

### Observed implementation

- 新增 `scripts/check-static.ps1`：actionlint 1.7.12（经 `actionlint-py==1.7.12.25` + `uvx`）
  与 PSScriptAnalyzer 1.25.0；高信号规则集见 `scripts/PSScriptAnalyzerSettings.psd1`；
- 新增 `scripts/test-static.ps1`：合法、坏 workflow、`Invoke-Expression` 三个场景；
- `quality.ps1` 增加 `-Check static`；无 Package 的 `all` 纳入；
- CI governance job 安装固定 PSScriptAnalyzer 并执行静态检查与回归；
- `Assert-GovernanceResult` 改名为 `Test-GovernanceResult`，满足 approved verbs；
- 同步质量门、README 和 AGENTS 的工具/命令/限制说明。

### Verification

- `scripts/check-static.ps1`：actionlint 与 PSScriptAnalyzer 均 0 finding；
- `scripts/test-static.ps1`：3 场景全部按预期；
- `quality.ps1`：四包 + 文档 + 治理 + 静态分析 exit 0；
- 治理检查 0 error / 0 warning，11 场景无回归；
- 干净克隆（无 `specs/`）中 static 与 governance 均 exit 0；
- 失败尝试（actionlint flag、fixture 缺 Git、非 approved verb）已记录在 evidence。

### Limitations

- 静态分析不验证运行时行为；第三方技能脚本不扫描；
- PSScriptAnalyzer 需安装，缺失时明确失败；
- 远端 CI 未运行；本条目绑定实现提交 `ba8993d`。

详细命令与残余限制：
[Evidence](evidence/phase-01-static-analysis.md)；
[Review](code_review/review-phase-01-static-analysis.md)。

## 2026-10-27 — Delivery Enablement（Feature 005）

**Status**: Implemented and locally verified；远端 CI 待 PR

**Route**: Feature（启用 Delivery 配置与 Ralph 协议边界）

**Feature**: `005-delivery-enablement`（本地工件，Git 忽略）

**Base revision**: `48fb3a73b48b366c1958171217ff0494be907843`

**Head revision**: `9fab77dcf4b3d8916f5a5497c1f8c43eb2a2080b`

**Working directory**: `D:\Repos\Github\spawn-join`

### Observed implementation

- 新增 `.specify/extensions/delivery/delivery-config.yml`：ephemeral artifacts、context/ADR、
  验证入口、docs sync、Ralph `ralph/` 分支、无并行 Worker、不自动 push/merge、
  `RALPH_TASK_GATE: PASS`；
- 新增 `.specify/delivery/README.md`：evidence/receipt 路径与模板；
- 新增 ADR-0003，记录“启用配置与协议、保留人工远端授权”的取舍；
- `check-governance.ps1` 增加 Delivery 安全设置与引用路径校验；
- `test-governance.ps1` 增加不安全 `auto_push` 场景（12 场景）；
- 更新 README、AGENTS、Harness 和质量门中 Delivery/hook 的表述。

### Verification

- `check-governance.ps1`：0 error / 0 warning；配置 8 条引用路径全部存在；
- `test-governance.ps1`：12 场景通过；
- `quality.ps1`：四包 + 文档 + 治理 + 静态分析 exit 0；
- `-Check docs`：52 文件 / 123 目标；
- AST 解析：0 parse error。

### Limitations

- 未运行完整 Ralph 循环；首次实际交付仍需用户逐步授权；
- hook 未安装，不自动 push/merge/发布；
- 配置 schema 由项目维护，检查器只验证安全关键项；
- 远端 CI 未运行；本条目绑定 `9fab77d`。

详细命令与残余限制：
[Evidence](evidence/phase-01-delivery-enablement.md)；
[Review](code_review/review-phase-01-delivery-enablement.md)。

## 2026-10-27 — 首次 Delivery 试点：Lightweight 证据再锚定

**Status**: Complete

**Route**: Lightweight（首次通过新启用的 Delivery 路由执行）

**Base revision**: `8d9c59c7b3fd961d0b319c1a9628b4a87312fcac`（PR #6 squash）

**Head revision**: `8d9c59c` 加未提交工作树

### Lane announcement

- lane: Lightweight；artifact policy: ephemeral；integration: OpenCode；
- 验证入口：`scripts/quality.ps1`、`-Check governance/docs/static`；
- 不创建 Spec/Plan/Tasks，不运行 Ralph 循环。

### Changes in this entry

- 四份 phase evidence 的 head 再锚定到 `8d9c59c`；补 PR #6 与 main 运行确认；
- 新增 `.specify/delivery/lightweight-evidence-reanchor/evidence.md`（Delivery 证据格式）；
- 本条目。

### Verification

- `check-governance.ps1`：0 error / 0 warning；
- `quality.ps1`：四包 + 文档 + 治理 + 静态分析 exit 0；
- `-Check docs`：52 文件 / 124 目标；`-Check static`：0 finding。

### Finding

两份 evidence 曾使用截断 SHA（`83628ac...`），现有检查器只校验 40 位，freshness 被静默
跳过。本次已改为完整 SHA；把“截断 SHA 应失败”作为后续 Bugfix，不在 Lightweight 中扩大范围。

### Limitations

- 未实际运行 Ralph 分支/receipt/task gate；
- Delivery 仍为手动路由，不自动 push/merge。

详细证据：
[Delivery evidence](../.specify/delivery/lightweight-evidence-reanchor/evidence.md)。

## 2026-10-27 — 取消跟踪历史 specs/001（Lightweight）

**Status**: Implemented and locally verified；远端 CI 待提交后确认

**Route**: Lightweight（治理/分发规则，无运行时行为；按 ADR-0002 执行）

**Base revision**: `99f69078b6957e401c5f079890e3bccb2c7ee8d7`

**Head revision**: `99f6907` 加未提交工作树

### Changes in this entry

- `git rm --cached -r specs/001-harness-foundation`：6 个文件移出索引，本地文件保留；
- 新增 ADR-0002 并更新 `docs/decisions/` 索引与 ADR-0001 的关联/修订记录；
- 更新 `harness/README.md`、`docs/architecture/repository-map.md`、`README.md`、
  `AGENTS.md`、`.gitignore` 中“已跟踪文件继续跟踪”的过期表述；
- 新增 `harness/evidence/untrack-historical-specs.md` 与本条目。未修改 002、Python 源码或远端设置。

### Verification

- `git ls-files specs` 为空；本地 001 仍有 6 个文件；`git check-ignore` 命中 `/specs/`；
- 本机 `scripts/quality.ps1 -Check docs`：36 文件 / 99 目标，exit 0；
- 干净检出模拟（230 文件、无 `specs/`）：24 文件 / 87 目标，exit 0；
- 初次模拟因 `harness/README.md` 残留 001 链接失败，移除后重跑通过；失败尝试保留在此。

### Limitations

- 未提交、未推送；本条目绑定未提交工作树，提交后需重新确认；
- 001 仅取消跟踪，内容仍在本机与历史提交中；002 仍为本地工件；
- 远端 CI 与分支保护状态不变，本次不扩展处理。

## 2026-10-28 — Release Delivery 安装迁移

**Status**: Installed；最终质量验证进行中，未创建提交

**Route**: Feature（安装器自举迁移，人工按本地任务队列推进，不运行 Ralph）

**Base/head**: `fdd0c072186ef3cea7f4b3261acd1d82b358ef56` + 本次未提交变更

- 按用户要求移除项目 sd/speckit-delivery 拷贝门面，采用固定 Release 组件安装。
- 隔离验证发现 Bundle 在 CLI 1.2.3/0.16.4 的两条失败路径；不降级全局 CLI、不改发布文件。
- 原生组件安装已在隔离项目和目标仓库成功：八个 Release v0.1.0 扩展、Bug 1.0.1、三条 Tag 固定 Workflow。
- 默认 OpenCode，保留 Codex、项目任务定制、Specs 本地化和远端授权边界；Hook 自动执行关闭。
- 九个 Release 资产哈希及八个扩展的 41 文件逐字节核对通过；全部 Workflow 命令可解析。
- 先复现后修正 quoted gate 和 Vendor Markdown 链接边界，治理回归扩为 16 场景并通过。

实际命令、退出码、环境与限制见 [安装 evidence](evidence/delivery-release-installation.md)。
最终质量/Standards/Doctor 结果待后续实际执行后追加，不提前声明完整交付或 Ralph 完成。

## 2026-10-28 — Release 安装验证结果确认

**Status**: Release 组件安装与声明环境下的本地验证通过；默认环境 readiness / 提交收口仍有边界

- 六个 Profile 的十条精确命令全部 exit 0；最终 `pwsh -NoProfile -File scripts/quality.ps1`
  也已实际执行并 exit 0。四包 20 测试、构建/隔离安装、文档、治理和静态检查通过；
  门禁/治理/静态回归分别 9/16/3 场景通过。
- 验证环境通过进程级 `PSModulePath` 提供固定 PSScriptAnalyzer 1.25.0，不做全局安装。
  默认本机环境仍缺该模块，因此 Doctor 明确为 blocked，不将临时成功误报成无人值守就绪。
- OpenCode 服务 API 已发现本项目全部 31 个原生命令；三个 Workflow 与固定 Tag 逐字节一致。
- 无本地 Specs 的 tracked checkout 模拟通过 docs/governance 和 cached diff 检查；
  source build/dist/egg-info 与根级环境/锁无残留，目标索引未暂存，HEAD 未改变。
- Standards Review 对本次安装实现给出 pass；ADR-0004 保持 Proposed，Tasks 和任务提交收口未关闭。
- 未执行 Bundle/Ralph 循环、远端 CI、推送、合并或发布。

结果与失败尝试：[安装 evidence](evidence/delivery-release-installation.md)；
范围审查：[Standards Review](code_review/review-delivery-release-installation.md)。

## 2026-10-28 — SDD/Harness 再审计与双仓库修复

**Status**: analyzed and locally verified；未提交、未推送

**Route**: Bugfix/治理修复（先复现失败，再收紧检查与分发契约）

**Base/head**: `fdd0c072186ef3cea7f4b3261acd1d82b358ef56` + 当前未提交工作树

- SpawnJoin：`check-governance.ps1` 新增 `.specify/delivery` evidence 校验、截断 revision
  拒绝、`artifact_policy`/ADR 目录安全校验和 `auto_execute_hooks` 拒绝；回归扩为 20 场景。
- 历史 evidence 的截断 head 改为明确的 `working-tree (...)`，不改变原结论；轻量证据
  补齐 `phase_id`。
- Quality Profile 增加共享 `pyproject.toml` Profile，避免根工具配置重复触发四包全量检查；
  当前共七个 Profile。
- `speckit-delivery`：对齐三个 Workflow Catalog 的 `requires`，新增分发契约校验、契约回归
  和真实 Bundle 安装回归；Bundle 最低 CLI 改为 1.2.3，更新发布/验证 Workflow 与文档。
- 本地 Bundle 回归以 CLI 1.2.3 从本地 release-shaped Catalog 安装 12 个组件成功；
  v0.1.0 固定 Tag 仍含旧 Catalog，必须新 Release 后复核，不能把源码验证当作已发布修复。
- 未运行完整 Ralph、远端 CI、推送、合并或发布；默认本机静态工具仍缺 PSScriptAnalyzer。

命令与限制：[安装 evidence](evidence/delivery-release-installation.md)；
上游结果：`D:\Repos\Github\speckit-delivery` 的
`scripts/validate_distribution.py`、`scripts/test_validate_distribution.py`、
`scripts/test_bundle_install.py`。新提交产生后需重新确认本条目和旧 evidence。

## 2026-10-28 — 迁移到 v0.1.1 Bundle

**Status**: Bundle 安装与本地验证通过；未提交、未推送

**Route**: Feature 006 后续迁移（发布后从逐组件安装切换到 Bundle）

**Base/head**: `fdd0c072186ef3cea7f4b3261acd1d82b358ef56` + 当前未提交工作树

- 先验证已发布 v0.1.1：Tag 指向 `27b2e73`，9 个资产 SHA-256 匹配，公开 Catalog
  均为 0.1.1；干净项目 Bundle 安装 12 个组件成功。
- 备份项目配置后，以 `--keep-config` 移除 v0.1.0 组件和三条 Workflow，更新 Catalog 到
  v0.1.1，安装 Bundle `0.1.1`；`bundle list` 显示 12 个贡献组件。
- 六个扩展配置、核心任务技能和 `tasks-template.md` 哈希保持不变；
  `auto_execute_hooks: false`、空 hooks 和授权边界保持不变。
- OpenCode 发现 31 个原生命令；“Bug” 保持 CLI 随附 1.0.1。
- 完整 `quality.ps1`、9 个门禁场景、20 个治理场景和 3 个静态场景全部通过；
  默认环境仍缺 PSScriptAnalyzer 1.25.0，Doctor 保持 blocked。
- 未运行完整 Ralph 循环，未提交、推送、合并或发布 SpawnJoin 变更。

验证记录：[安装 evidence](evidence/delivery-release-installation.md)；
范围审查：[Standards Review](code_review/review-delivery-release-installation.md)。

## 2026-10-28 — v0.1.1 Bundle 交付收口

**Status**: Complete；PR #8 已合并，main Quality 14/14

**Route**: Feature 006 收口（文档、ADR 状态和证据再锚定，无运行时行为变化）

**Base/head**: `2b8b70db080096a5d12ee399409e3cd4c40dfa2f` 加本次收口提交

- PR #8 已合并为 `2b8b70db080096a5d12ee399409e3cd4c40dfa2f`；Quality 运行
  `40699123377` 的 14/14 job 全部成功。
- ADR-0004 由 Proposed 改为 Accepted，索引同步；Feature 006 状态改为 Implemented，
  T001–T009 全部完成。
- Harness evidence 的 head 再锚定到合并提交，评审 RI-007 关闭，并记录收口结果。
- 未运行真实 Ralph 循环；默认环境仍缺 PSScriptAnalyzer 1.25.0。

验证记录：[安装 evidence](evidence/delivery-release-installation.md)；
范围审查：[Standards Review](code_review/review-delivery-release-installation.md)。

## 2026-10-28 — 升级到 Delivery Bundle v0.1.2

**Status**: 本机升级与验证通过；未提交、未推送

**Route**: Lightweight 依赖升级（分发组件版本更新，无业务源码变化）

**Base/head**: `06f6303b597ce01a707164762f55369706b13063` 加当前工作树

- 先核对 v0.1.2 Release：10 个资产（9 个扩展 + Bundle），三类 Catalog 均固定到 `v0.1.2`。
- 在隔离 fixture 验证 0.1.1 → 0.1.2 的 `bundle update`，随后对目标仓库执行同一步骤；
  新增 Diagram 扩展，三条 Workflow 重新安装。
- Bundle 记录 13 个组件；六个扩展配置、核心任务技能和任务模板哈希不变；
  `auto_execute_hooks: false`、空 hooks 保持；`extensions.yml` 仅新增 `diagram`。
- OpenCode 原生命令由 31 增加到 33；Feature 与 Bugfix 新增非阻塞的
  `speckit.delivery.context` 步骤，Diagram 提供 `speckit.diagram.render`。
- 默认环境仍缺 PSScriptAnalyzer 1.25.0；未运行真实 Ralph 循环，未推送或发布。

验证记录：[安装 evidence](evidence/delivery-release-installation.md)；
安装步骤：[Delivery 安装说明](../docs/development/spec-kit-delivery.md)。

## 2026-10-28 — 包元数据、许可证与 PR 模板

**Status**: 本机验证通过；未提交、未推送

**Route**: Lightweight（元数据与治理，无运行时行为变化）

**Base/head**: `0f67f44eb5fb7bd76f85ac9ce2b701dd15e3cbf1` 加当前工作树

- 根 `LICENSE` 与四个包的 `LICENSE`/`README.md` 补齐；四个 `pyproject.toml` 增加
  `readme`、`license`、`license-files`、`authors`、`[project.urls]`，构建后端提升到
  `setuptools>=77`。
- 构建不再出现 `sdist: standard file not found`；wheel 带 `License-Expression` 和
  `License-File`，sdist 包含 README 与 LICENSE。
- 新增中文 PR 模板；治理 Profile 覆盖 `LICENSE` 与根模板，避免这两类路径成为 unprofiled。
- 四个 `uv lock --check` 与完整 `quality.ps1` 通过；未发布、未创建 Tag。

验证记录：[元数据 evidence](evidence/package-metadata-and-license.md)。

## 2026-10-28 — 治理链接检查覆盖未跟踪文档

**Status**: 本机验证通过；未推送

**Route**: Bugfix（CI 暴露的检查范围缺陷）

**Base/head**: `1eeb1f0` 加当前工作树

- 红证据：PR #11 的 governance job 因新包 README 的坏链接失败
  （`missing link target: ../infra/llm-provider-langchain/`）。
- 根因：`check-governance.ps1` 的链接扫描只枚举 `git ls-files`，未暂存的新文档被跳过。
- 修复：链接扫描同时枚举 `git ls-files --others --exclude-standard`，并在
  `test-governance.ps1` 增加“未跟踪 Markdown 坏链接”场景。
- 验证：21 个治理场景、静态检查与静态回归通过；真实仓库的未跟踪坏链接探针 exit 1，
  删除后 exit 0。
- 未重跑四包完整 gate（本次仅改脚本与文档）；PR CI 会重新执行全部检查。

验证记录：[元数据 evidence](evidence/package-metadata-and-license.md)。

## 2026-10-29 — 治理噪音清理

**Status**: 本机验证通过；未提交、未推送

**Route**: Lightweight（治理检查与历史 evidence 元数据，无运行时行为变化）

**Base/head**: `dab15fe2b7d3f3c1108ad32a3a671e65d80e0642` 加当前工作树

- `check-governance.ps1` 新增 `superseded_by`：历史 evidence 可指向更新记录，目标必须存在；
  该字段只抑制 freshness warning，不删除旧记录或改写结论。
- 四份 `phase-01-*` evidence 标记为 superseded，指向覆盖同一关注点的较新记录；
  `test-governance.ps1` 增加两个对应场景（21 → 23）。
- governance warning 由 5 条降到 1 条：剩余一条是当前交付记录落后于 HEAD，应在合并后
  重新锚定，而不是标记 superseded。
- 删除机器本地的 `.specify/feature.json` 陈旧指针（Git 忽略，不提交）。
- 验证：23 个治理场景、静态检查、静态回归、文档检查与 `git diff --check` 通过。

验证记录：[治理清理 evidence](evidence/governance-noise-cleanup.md)。

## 2026-10-29 — v0.1.2 安装 evidence 再锚定

**Status**: 已验证；未提交、未推送

**Route**: Lightweight（证据再锚定，无行为变化）

**Base/head**: `00d9c402bb2325c3b8f007ece5564312397ac77e` 加当前工作树

- 在 `00d9c40` 重新核对安装状态：Bundle `0.1.2`、13 个组件、33 个原生命令。
- 5 个扩展配置、核心任务技能和任务模板保持不变；`quality-config.yml` 与
  `extensions.yml` 的变化分别是 PR #11 的治理 Profile 扩展和 PR #10 的 `diagram` 登记。
- 完整 `quality.ps1` 通过；main Quality 运行 `40802098059` 为 14/14。
- 本次只改 evidence 与 build-log；合并后 freshness warning 应为 0。

验证记录：[安装 evidence](evidence/delivery-release-installation.md)。

## 2026-10-29 — Delivery Bundle v0.1.3 升级

**Status**: 已安装；安装一致性、文档与治理检查通过，Doctor blocked；未提交、未推送

**Route**: Lightweight（固定 Release 开发工具升级，不新增 Python 行为或 Feature 工件）

**Base/head**: `881dcfeb4885c044d39071660606775509d64165` 加当前工作树

- 校验 10 个 Release ZIP 的 SHA-256，先在本地临时副本升级，再更新当前仓库三类固定
  Catalog 并执行 `specify bundle update speckit-delivery`；13 个组件版本一致。
- 14 个受保护配置/定制文件未变；自动 Hook 关闭；未运行 Workflow、Ralph 或远端写入。
- 53 个非项目配置的扩展文件与发布 ZIP 字节一致；活跃 OpenCode 识别 35 条原生命令。
- 23 个治理回归场景通过。默认静态检查实际失败：缺 PSScriptAnalyzer 1.25.0；
  发布版 Doctor 的 Reviewer 路径也有上游缺陷，保留原样并报告，不虚报就绪。
- 文档检查 65 文件 / 175 目标通过；治理 0 错误 / 0 告警；`git diff --check` 通过。
- 同步当前版本、Workflow 新输入和三门快照证据要求，历史安装记录保留。

验证记录：[v0.1.3 升级 evidence](evidence/delivery-v013-upgrade.md)。

## 2026-10-29 — Delivery Bundle v0.1.4 升级

**Status**: 已安装；安装一致性通过；Doctor 环境阻塞仍在；未提交、未推送

**Route**: Lightweight（上游补丁版本升级，不新增 Python 行为或 Feature 工件）

**Base/head**: `881dcfeb4885c044d39071660606775509d64165` 加当前工作树

- v0.1.4 修复 v0.1.3 的 Doctor Reviewer 模板路径缺陷；命令面、配置、六维评审、
  快照和修复预算均未变。
- 校验 10 个 Release ZIP 的 SHA-256；在含 v0.1.3 未提交状态的工作树副本中先升级，
  再对目标执行 `bundle update`；13 个组件一致，原生命令仍为 35 条。
- 14 个受保护配置/定制文件未变；53 个非配置扩展文件与发布 ZIP 字节一致；三条 Workflow
  与 v0.1.4 Tag 字节一致；生成的 Doctor 已指向 Review 模板。
- 默认环境仍缺 PSScriptAnalyzer 1.25.0，静态检查保持 blocked，不因补丁升级放宽。

验证记录：[v0.1.4 升级 evidence](evidence/delivery-v014-upgrade.md)。

## 2026-10-29 — v0.1.4 升级合并与证据再锚定

**Status**: 已验证；合并后证据已锚定到 main

**Route**: Lightweight（证据再锚定，无行为或工具变化）

**Base/head**: `881dcfeb4885c044d39071660606775509d64165` → `bae306c1573a205a582778a57eaf607d871d1a39`

- PR #14 以 Squash 合并为 `bae306c`，main 历史只保留一个升级提交。
- main 的 Quality 运行 `40849963307` 完成 14/14：治理与门禁回归、12 个包/平台矩阵
  和 required `Quality Gate` 均成功。
- v0.1.4 evidence 的 `head_revision` 由分支提交改为合并提交；分支 SHA 不再是祖先，
  不能作为当前证据。
- 本次只改 `harness/` 文档；重新执行文档与治理检查后保持 0 错误、0 告警。
- 远端 CI 通过不等于 Doctor 就绪：默认环境仍缺 PSScriptAnalyzer 1.25.0。

验证记录：[v0.1.4 升级 evidence](evidence/delivery-v014-upgrade.md)。

## 2026-10-30 — Delivery Bundle v0.2.1 升级

**Status**: 已安装；安装一致性与针对性检查通过；未提交、未推送

**Route**: Lightweight（上游 minor 版本升级，不新增 Python 行为或 Feature 工件）

**Base/head**: `9cdb10a334acf9100ae822f7220cb67fa7a25650` → `306bc1b31f3baf36d094f74fdffa5c20eedd0e1a`

- v0.2.0 增加 Slice 计划/Slice Gate、`slices.md` 和合并策略；v0.2.1 让 Handoff 把正文
  写入本地 `PR_BODY_PATH`，并保持静态 PR 模板安装为显式 opt-in。
- 校验 10 个 Release ZIP 的 SHA-256；先在隔离副本升级，再对目标执行 `bundle update`；
  13 个组件一致，原生命令由 35 增加到 36，三条 Workflow 与 v0.2.1 Tag 字节一致。
- 安装器保留 14 个受保护配置/定制文件；项目随后显式更新 `delivery-config.yml`：
  `pr_slicing: "off"`、`stack_provider: manual`、`use_queue: false`、`final: squash`，
  以匹配现有单 PR 和 required linear history；既有 `.github/pull_request_template.md`
  保留，`install_pull_request_template: false`。
- 55 个非配置扩展文件与发布 ZIP 字节一致；Doctor 继续指向 Review 模板；Handoff 包含
  `PR_BODY_PATH`、`PR_CREATE_HINT: gh pr create` 和 `--body-file`。
- 文档、治理和静态检查通过；完整四包质量矩阵、门禁回归 9 场景、治理回归 23 场景、
  静态回归 3 场景通过。Workflow、独立 Review 和 Doctor Agent 运行未执行，保留为限制。
- PR 模板改为默认使用 SD v0.2.1 仓库自带的中文 `.github/pull_request_template.md`：
  项目保存同名副本并由 `pull_request_template` 指向它；扩展包的英文 fallback 未使用，
  `install_pull_request_template: false`，旧项目模板保留在 Git 历史中。
- 未创建提交、推送、合并或发布；`specify integration status` 仍提示 32 个项目自有
  核心技能/模板修改，未使用 `--force` 消除。

验证记录：[v0.2.1 升级 evidence](evidence/delivery-v021-upgrade.md)。

## 2026-10-30 — Delivery Bundle v0.2.2 升级

**Status**: 已安装；安装一致性与针对性检查通过；已通过 PR #17 squash 合并（`353af49`）

**Route**: Lightweight（上游补丁版本升级，只改 PR 模板兜底）

**Base/head**: `9cdb10a334acf9100ae822f7220cb67fa7a25650` → `353af49cf9db6014b7af0437a3f9dc0dd651437c`

- v0.2.2 只把 Delivery 随包 `templates/pull-request.md` 兜底模板改为中文；命令面、
  Workflow 输入、六维 Review、快照和修复预算均与 v0.2.1 一致。
- 校验 10 个 Release ZIP 的 SHA-256；先在隔离副本升级，再对目标执行 `bundle update`；
  13 个组件一致，原生命令仍为 36 条，55 个非配置扩展文件和三条 Workflow 与 Tag 字节一致。
- 安装器保留 14 个受保护配置/定制文件；项目配置改为指向随包中文模板，并把同一字节写入
  `.github/pull_request_template.md`，`install_pull_request_template: true`。
- 文档、治理、静态、完整四包质量矩阵、门禁回归 9 场景、治理回归 23 场景、静态回归
  3 场景通过。Workflow、独立 Review 和 Doctor Agent 运行未执行，保留为限制。
- v0.2.1 evidence 标记为 superseded；旧项目模板保留在 Git 历史中。
- 已创建提交并推送到 PR 分支；未合并或发布；`specify integration status` 仍提示 32 个项目
  自有核心技能/模板修改，未使用 `--force` 消除。

验证记录：[v0.2.2 升级 evidence](evidence/delivery-v022-upgrade.md)。
