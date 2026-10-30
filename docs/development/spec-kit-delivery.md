# Spec Kit Delivery：Release 安装与维护

## 当前入口与归属

- 当前 CLI：Specify 1.2.3；默认集成 OpenCode，保留 Codex 核心技能。
- OpenCode 使用项目原生命令 `/speckit.delivery.route`、`/speckit.delivery.doctor`。
- 命令由 CLI 安装到 `.opencode/commands/`；不要使用本机旧的连字符包装命令或 `$sd` 判断项目状态。
- 已移除本项目 `.agents/skills/sd/`、`.agents/skills/speckit-delivery/` 手工拷贝；
  核心 Spec Kit 技能与 Fireworks 不属于该清理范围。
- 用户级共享技能未删除，避免影响其他项目。项目入口读取本项目安装的命令，不转发到旧全局技能。

组件与原生命令由安装器管理；`*-config.yml` 由项目管理。核心任务技能和模板有测试要求
定制，升级不得强制覆盖。原生通用 Prompt 中的可选测试表述不削弱 Constitution 的风险相关测试要求。

## 固定版本与实际安装方式

| 组件 | 来源/版本 |
|---|---|
| Delivery、Decision、Ralph、Review、Simplify、Evidence、Quality、Docs Sync、Diagram | `speckit-delivery` Bundle v0.2.1 |
| Bug | Specify CLI 1.2.3 随附的 1.0.1 |
| Feature / Bugfix / Lightweight Workflow | `speckit-delivery` Bundle v0.2.1 |

当前项目使用 **Bundle v0.2.1**，Bundle 记录拥有 10 个扩展和 3 个 Workflow，共 13 个组件。
v0.1.0 的逐组件安装只作为历史 bootstrap；v0.1.1 修复了 Workflow Catalog 的 requirements
不一致；v0.1.2 增加 Diagram 扩展与 `speckit.delivery.context`；v0.1.3 增加范围取证与有界
修复复审；v0.1.4 修正 Doctor 对共享 Reviewer 模板的路径引用。v0.2.0 增加
`speckit.delivery.slice`、`templates/slices.md`、Feature 的 `slice`/`slice-gate`，以及
`pr_slicing`、Slice 预算、`stack_provider` 和 `merge_policy`。v0.2.1 让
`speckit.delivery.handoff` 把正文写入 `.specify/delivery/<run>/pull-request.md` 或
`pull-request-<slice>.md`，输出 `PR_BODY_PATH` 和 `gh pr create --body-file` 提示；安装
静态 PR 模板仍是显式 opt-in，不会覆盖项目已有模板。这些仍是引导式契约，不是新增机器强制
执行的语义状态引擎。

发布入口：[v0.2.1](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.2.1)。
安装取舍见 [ADR-0004](../decisions/engineering/0004-release-managed-delivery-installation.md)。
本次升级命令与限制见 [v0.2.1 evidence](../../harness/evidence/delivery-v021-upgrade.md)；
早期安装见 [历史 evidence](../../harness/evidence/delivery-release-installation.md)。

## 首次接入已有项目

从仓库根目录执行。先备份现有配置与定制内容；这些命令用于**尚未安装交付组件**的项目，
已经安装时先检查清单和差异，不机械重跑或添加 `--force`。不要对现有项目执行
`specify init --force`。

```powershell
specify version
specify integration install opencode --script ps
specify integration use opencode

$base = 'https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.2.1/catalogs'
specify extension catalog add "$base/extensions.json" --name speckit-delivery --install-allowed
specify workflow catalog add "$base/workflows.json" --name speckit-delivery
specify bundle catalog add "$base/bundles.json" --id speckit-delivery --policy install-allowed
specify bundle install speckit-delivery --version 0.2.1
```

Bundle 会安装 `bug`、九个 Delivery 扩展（含 Diagram）以及三条 Workflow。Catalog 的安装信任
只授权已审阅的固定来源，不授权发布、云服务访问或外传仓库内容。安装器对已有共享文件和
定制模板的保留提示是预期现象，不用强制重初始化消除。

### 从 v0.1.0 逐组件安装迁移

先备份配置与核心定制，然后使用 `--keep-config` 移除旧组件，再安装 v0.2.1 Bundle：

```powershell
foreach ($extension in @('bug','decision','delivery','docs-sync','evidence','quality','ralph','review','simplify')) {
    specify extension remove $extension --keep-config --force
    if ($LASTEXITCODE -ne 0) { throw "Extension removal failed: $extension" }
}
foreach ($workflow in @('feature-delivery','bugfix-delivery','lightweight-delivery')) {
    specify workflow remove $workflow
    if ($LASTEXITCODE -ne 0) { throw "Workflow removal failed: $workflow" }
}
```

随后删除旧 Catalog、加入 v0.2.1 Catalog，并执行上面的 `bundle install`。迁移后必须检查：
`bundle list --json` 为 0.2.1、13 个组件；项目 `*-config.yml` 哈希不变；核心任务技能和
`tasks-template.md` 不被覆盖；`auto_execute_hooks: false` 保持。

### 从 v0.1.x Bundle 升级

已由 Bundle 管理的项目不需要逐个移除组件，使用 Bundle 自身的更新路径。先用
`specify workflow catalog list` 确认旧来源的索引，再更新三类 Catalog：

```powershell
$base = 'https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.2.1/catalogs'
specify extension catalog remove speckit-delivery
specify extension catalog add "$base/extensions.json" --name speckit-delivery --install-allowed
specify workflow catalog remove 0
specify workflow catalog add "$base/workflows.json" --name speckit-delivery
specify bundle catalog remove speckit-delivery
specify bundle catalog add "$base/bundles.json" --id speckit-delivery --policy install-allowed
specify bundle update speckit-delivery
```

升级后检查：`bundle list --json` 为 0.2.1、13 个组件；`*-config.yml` 哈希不变；
`auto_execute_hooks: false`；OpenCode 原生命令为 36 个（相对 v0.1.4 新增
`speckit.delivery.slice`，Delivery 扩展命令由 8 个增加到 9 个）。`bundle update` 会重新
安装三条 Workflow，因此 Feature 的新 `slice`/`slice-gate` 随 Bundle 生效。不能只更新
薄门面或单条命令。

v0.1.4 → v0.2.1 的配置差异需要项目明确处理，而不是让安装器代填：v0.2.0 新增
`pr_slicing`、`slice_warn_files`、`slice_warn_lines`、`slice_requires_approval`、
`stack_provider` 和 `merge_policy`；v0.2.1 新增 `install_pull_request_template`。本项目
保持单 PR 路径，设置 `pr_slicing: "off"`、`stack_provider: manual`、`use_queue: false`，
并因仓库 Ruleset 要求线性历史而把 `final` 设为 `squash`。这是对现有策略的显式记录，
不是安装器覆盖项目配置。

直接 Workflow 现要求唯一、安全的单段 `delivery_run`；Bugfix 另需规范化的 `bug_slug`。
恢复时沿用相同标识和 `.specify/delivery/<delivery_run>/` 本地记录，不通过换 ID 重置修复预算：

```powershell
specify workflow run feature-delivery --input delivery_run=audit-trail-01 --input spec="增加审计轨迹"
specify workflow run bugfix-delivery --input delivery_run=retry-fix-01 --input bug_slug=duplicate-retry --input report="重试重复通知"
specify workflow run lightweight-delivery --input delivery_run=docs-fix-01 --input change="修正文档标题"
```

这些是用法示例，本次升级未运行 Workflow。项目 `max_review_fix_rounds: 2` 保持不变，
低于上游三槽上限；任务关闭需要当前快照的 Quality、Standards 与独立 Review 三门证据。
Feature 在 `tasks.md` 之后增加 Slice 计划与 Slice Gate；`tasks.md` 仍是唯一执行队列，
`slices.md` 只记录可独立评审/合并的边界，不得增删或重排任务。

## 项目配置

- [Delivery](../../.specify/extensions/delivery/delivery-config.yml)：上游字段及项目安全设置。
  `pr_slicing: "off"` 保持单 PR；`slice_requires_approval: true` 保留 Slice Gate 的快速
  确认；`stack_provider: manual`、`use_queue: false` 不声称本仓库具备原生 Stacked PR
  或 Merge Queue。`merge_policy.final: squash` 与仓库 required linear history 一致；
  启用 integration 交付前必须重新评审该策略。PR 模板默认使用 SD 包内
  `templates/pull-request.md`：`pull_request_template` 指向该安装文件，
  `install_pull_request_template: true` 记录已显式批准；`.github/pull_request_template.md`
  是该模板的项目副本，供 GitHub UI 使用，后续升级若模板变化需显式刷新。Handoff 仍通过
  `PR_BODY_PATH` 和 `--body-file` 提交每次变更的正文。未显式写入 `code_context` 时按
  `auto` 处理；本项目显式设为 `auto`，Feature 在 `plan` 前、Bugfix 在 `assess` 前可使用
  本地 `.codegraph/` 生成上下文；没有索引时降级为部分结果，不阻塞交付。
- [Diagram](../../.specify/extensions/diagram/diagram-config.yml)：默认 `format: mermaid`、
  `renderer: auto`；未安装渲染器时保持 Mermaid，不自动下载或初始化任何工具。
- [Quality](../../.specify/extensions/quality/quality-config.yml)：共享工具配置、四包、自动化、
  治理文档共七个 Profile。包级 `quality` 命令组合格式、lint、类型、测试和隔离构建；
  根 `pyproject.toml` 单独映射一次全量门禁，不创建根级 uv 环境。
- [Decision](../../.specify/extensions/decision/decision-config.yml)：唯一 ADR 根 `docs/decisions/`。
- [Ralph](../../.specify/extensions/ralph/ralph-config.yml)：Specs 为 ephemeral、单任务串行。
- [Docs Sync](../../.specify/extensions/docs-sync/docs-sync-config.yml)：手工维护权威文档并执行链接检查；
  当前没有生成投影，因此不虚构 generator 或 publication manifest。
- [扩展设置](../../.specify/extensions.yml)：`auto_execute_hooks: false`，`hooks: {}`。

Specs 仍只在本地。安装不授权执行 Ralph、创建任务提交、push、merge 或发布。原生 Ralph
需要干净工作区及独立的任务关闭证据；本次安装验证不等于完整交付循环通过。

## 验证与升级

运行环境要求见 [质量门前置条件](quality-gates.md#prerequisites)。历史 v0.1.2 完整验证曾
显式提供临时 PSScriptAnalyzer 1.25.0 模块路径；本次升级未沿用该环境或旧结果。本次会话
中 PSScriptAnalyzer 可用，`quality.ps1 -Check static`、完整四包 `quality.ps1` 矩阵和
`test-quality.ps1` 门禁回归均实际通过。Doctor 仍是 Agent Prompt，本次未独立运行；安装
一致性、配置、命令闭包和 Handoff 契约通过直接检查确认，不把安装验证表述为完整交付循环
通过。

```powershell
specify integration status
specify extension list
specify workflow list
specify bundle list --json
pwsh -NoProfile -File scripts/quality.ps1
pwsh -NoProfile -File scripts/test-quality.ps1
pwsh -NoProfile -File scripts/test-governance.ps1
pwsh -NoProfile -File scripts/test-static.ps1
git diff --check
```

另外按 `/speckit.delivery.doctor` 的只读契约核对：配置可解析、Bundle/扩展/Workflow 版本
一致、Feature 包含 Slice 命令/模板/Gate 且 Ralph、Review、Handoff 消费 `slices.md`、所有
Workflow 命令在当前宿主可解析、质量命令实际可运行、语义标准有 owner/mechanism。Doctor
还检查 `pr_slicing`/Slice 预算/`merge_policy`、PR 模板配置，以及 Handoff 是否写出真实
`PR_BODY_PATH` 并给出 `gh pr create --body-file` 提示。Doctor 是 Agent Prompt，不是 PATH
可执行文件。安装器生成的命令由 OpenCode 自动重载；旧技能的当前会话缓存不代表新入口缺失。
当前项目已发现 36 个点号原生命令（26 个扩展命令 + 10 个核心命令）。

升级后应确认生成的 Doctor 指向
[Review 扩展模板](../../.specify/extensions/review/templates/reviewer.md)，而不是
`.specify/extensions/delivery/templates/reviewer.md`。v0.1.3 曾把该共享模板误指向
Delivery 扩展，产生错误的就绪阻塞；v0.1.4 已在上游修复，v0.2.1 保持该路径。安装包仍
保持发布原样，不创建重复模板或手工篡改生成命令。若仍看到旧路径，说明安装未真正刷新到
当前版本。

升级前先在临时项目验证新 Release 和 Bundle，检查组件差异、项目配置与定制保留；经确认
后才更新固定 Catalog/Tag，并使用 Bundle 升级或 `--keep-config` 迁移方式。不要编辑生成命令、
安装器 manifest 或 Bundle record 来掩盖漂移。
`.specify/extensions/.cache/`、`.specify/workflows/.cache/`、`.backup/` 与锁文件不提交；
安装 registry、manifest、配置和生成命令保留以便项目级追溯。Vendor Prompt/README 的上游
相对链接不属于项目文档链接门，保留原样，不伪称其经过本项目文档验证。

本次实际验证及限制见 [v0.2.1 evidence](../../harness/evidence/delivery-v021-upgrade.md)。
