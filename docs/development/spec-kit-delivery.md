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
| Delivery、Decision、Ralph、Review、Simplify、Evidence、Quality、Docs Sync、Diagram | `speckit-delivery` Bundle v0.1.2 |
| Bug | Specify CLI 1.2.3 随附的 1.0.1 |
| Feature / Bugfix / Lightweight Workflow | `speckit-delivery` Bundle v0.1.2 |

当前项目使用 **Bundle v0.1.2**，Bundle 记录拥有 10 个扩展和 3 个 Workflow，共 13 个组件。
v0.1.0 的逐组件安装只作为历史 bootstrap；v0.1.1 修复了 Workflow Catalog 的 requirements
不一致；v0.1.2 增加 Diagram 扩展与 `speckit.delivery.context`，并在 Feature 的 `plan`、
Bugfix 的 `assess` 之前加入非阻塞的代码上下文步骤。

发布入口：[v0.1.2](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.1.2)。
安装取舍见 [ADR-0004](../decisions/engineering/0004-release-managed-delivery-installation.md)。
实际命令、版本和限制见 [安装 evidence](../../harness/evidence/delivery-release-installation.md)。

## 首次接入已有项目

从仓库根目录执行。先备份现有配置与定制内容；这些命令用于**尚未安装交付组件**的项目，
已经安装时先检查清单和差异，不机械重跑或添加 `--force`。不要对现有项目执行 `specify init --force`。

```powershell
specify version
specify integration install opencode --script ps
specify integration use opencode

$base = 'https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.1.2/catalogs'
specify extension catalog add "$base/extensions.json" --name speckit-delivery --install-allowed
specify workflow catalog add "$base/workflows.json" --name speckit-delivery
specify bundle catalog add "$base/bundles.json" --id speckit-delivery --policy install-allowed
specify bundle install speckit-delivery --version 0.1.2
```

Bundle 会安装 `bug`、九个 Delivery 扩展（含 Diagram）以及三条 Workflow。Catalog 的安装信任
只授权已审阅的固定来源，不授权发布、云服务访问或外传仓库内容。安装器对已有共享文件和
定制模板的保留提示是预期现象，不用强制重初始化消除。

### 从 v0.1.0 逐组件安装迁移

先备份配置与核心定制，然后使用 `--keep-config` 移除旧组件，再安装 v0.1.2 Bundle：

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

随后删除旧 Catalog、加入 v0.1.2 Catalog，并执行上面的 `bundle install`。迁移后必须检查：
`bundle list --json` 为 0.1.2、13 个组件；项目 `*-config.yml` 哈希不变；核心任务技能和
`tasks-template.md` 不被覆盖；`auto_execute_hooks: false` 保持。

### 从 v0.1.1 升级

已由 Bundle 管理的项目不需要逐个移除组件，使用 Bundle 自身的更新路径。先用
`specify workflow catalog list` 确认旧来源的索引，再更新三类 Catalog：

```powershell
$base = 'https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.1.2/catalogs'
specify extension catalog remove speckit-delivery
specify extension catalog add "$base/extensions.json" --name speckit-delivery --install-allowed
specify workflow catalog remove 0
specify workflow catalog add "$base/workflows.json" --name speckit-delivery
specify bundle catalog remove speckit-delivery
specify bundle catalog add "$base/bundles.json" --id speckit-delivery --policy install-allowed
specify bundle update speckit-delivery
```

升级后检查：`bundle list --json` 为 0.1.2、13 个组件；`*-config.yml` 哈希不变；
`auto_execute_hooks: false`；OpenCode 原生命令从 31 个增加到 33 个（新增
`speckit.diagram.render` 和 `speckit.delivery.context`）。`bundle update` 会重新安装
三条 Workflow，因此新步骤随 Bundle 生效。

## 项目配置

- [Delivery](../../.specify/extensions/delivery/delivery-config.yml)：上游字段及项目安全设置。
  未显式写入 `code_context` 时按 `auto` 处理：Feature 在 `plan` 前、Bugfix 在 `assess` 前
  可使用本地 `.codegraph/` 生成上下文；没有索引时降级为部分结果，不阻塞交付。
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

运行环境要求见 [质量门前置条件](quality-gates.md#prerequisites)。本次所有 Profile 命令在
显式提供临时 PSScriptAnalyzer 1.25.0 模块路径后通过；默认本机环境仍缺该模块，因此
Doctor 的默认环境结果是 blocked，而非安装失败或已具备无人值守执行条件。
可在当前会话提供经验证的模块路径，或经维护者确认按质量门说明安装；不将临时路径写成
项目配置或永久修改用户环境。

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
一致、所有 Workflow 命令在当前宿主可解析、质量命令实际可运行、语义标准有 owner/mechanism。
Doctor 是 Agent Prompt，不是 PATH 可执行文件。安装器生成的命令由 OpenCode 自动重载；
旧技能的当前会话缓存不代表新入口缺失。当前项目应发现 33 个点号原生命令（23 个扩展命令
+ 10 个核心命令）。

升级前先在临时项目验证新 Release 和 Bundle，检查组件差异、项目配置与定制保留；经确认
后才更新固定 Catalog/Tag，并使用 Bundle 升级或 `--keep-config` 迁移方式。不要编辑生成命令、
安装器 manifest 或 Bundle record 来掩盖漂移。
`.specify/extensions/.cache/`、`.backup/` 与锁文件不提交；安装 registry、manifest、配置和
生成命令保留以便项目级追溯。Vendor Prompt/README 的上游相对链接不属于项目文档链接门，
保留原样，不伪称其经过本项目文档验证。

本次实际验证及限制见 [安装 evidence](../../harness/evidence/delivery-release-installation.md)。
