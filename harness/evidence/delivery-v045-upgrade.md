# Evidence — Delivery Bundle v0.4.5 upgrade

## Identity and scope

- **feature_id**: `delivery-v045-upgrade`（一次性 Lightweight 升级标识，未创建 Feature）
- **phase_id**: `delivery-v045-upgrade`
- **route**: Lightweight
- **base_revision**: `e292f0e3b746fec266e71dca142fc20356841978`
- **head_revision**: `working-tree`
- **working_directory**: `C:\Users\YanZh\.local\share\opencode\worktree\86e56b\mighty-harbor`
- **recorded_at**: `2026-11-07`
- **result**: pass — 固定 Release 安装、配置保留、模板同步、源码一致性和下述上游检查通过；项目检查、评审及远端状态分别记录
- **environment**: Windows、Specify CLI 1.2.3（其 Python 3.13.5）、PowerShell 7、Python Launcher `py -3`

升级从已有未提交变更的工作区开始，HEAD 为上述基准、当时处于 detached HEAD。此前的
v0.4.4 安装、治理优化及历史 evidence 全部保留。用户先要求安装 v0.4.5，并明确要求升级后
创建 PR；安装本身与后续 PR 收口分别取证，不把安装成功描述成原生交付完成。

## Release 来源

- Release：[v0.4.5](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.4.5)。
- Tag object：`8e39711962740dc05b91cbe46a193a210cb72ec0`。
- 实际 checkout commit：`2e1e67f0201182efcefc7247c9274feb73824d81`。
- GitHub Release API 报告的 Bundle 资产摘要：
  `sha256:9c5d4b2936300c832175d52cfe9154d44032e450c3eaabfa714d64eba89f741b`。
  这是 API 报告值，不冒充独立下载后的原始 ZIP 哈希验证。
- 三类固定 Catalog 使用
  `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.5/catalogs/`
  下的 `extensions.json`、`workflows.json` 和 `bundles.json`。

本版更新精简 Handoff/PR 正文，补充审查身份、验证缺口、人工评审重点和有来源的本地 AI
Review/Repair 历史；按适用条件展开 UI 前后证据、Bugfix 修复历程、Slice、发布和迁移说明。
Evidence 新说明性文字使用项目/请求语言，机器字段及历史记录保持原样。本版未增加 runtime
字段或自动调度器；新增行为 eval 输入不等于真实模型对比已经执行。

## 备份、演练与项目归属

临时根目录：
`C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-delivery-v045-20261107`。
其中 `backup/` 保存升级前 `.specify`、`.opencode`、`.agents` 及静态 PR 模板；
`rehearsal/` 是演练副本，`upstream/` 是固定 Tag checkout。临时脚本和日志不进入仓库。

安装前记录 165 个保护路径的 SHA-256：`.specify/extensions.yml`、全部项目 `*-config.yml`、
跟踪的 `.specify/templates/**`、`.agents/skills/**` 和 `.github/pull_request_template.md`。
演练与目标安装器执行后、显式同步静态模板之前，165 个哈希均未改变。最终 164 个项目配置、
核心模板/技能路径继续保持；第 165 个静态模板按项目已选择随包模板的策略有意同步。

同步前已对照旧模板和新的随包模板，确认差异为 v0.4.5 的实际内容更新。同步后的 `.github`
静态模板与 `.specify/extensions/delivery/templates/pull-request.md` 内容一致；LF/CRLF
转换只在文本一致性检查时归一化，不用于声称旧模板字节未改变。

本次安装器拥有的改动为 Catalog、Bundle/extension/workflow registry、九个 Delivery 扩展、
生成的 OpenCode 命令和三条 Workflow。项目拥有的配套改动为当前版本说明、ADR-0004 历史、
Harness 中英文入口、静态 PR 模板、本 evidence 和 build log。没有强制覆盖核心定制，
没有修改包源码、锁文件、公共 API、运行时依赖、权限或 Hook 开关。

## 实际命令与结果

除注明外，命令在上述项目根运行。`upgrade.ps1` 顺序执行三组固定 Catalog remove/add，
随后执行 `specify bundle update speckit-delivery` 和 `specify bundle list --json`，检查每步退出码。

| 命令 / 检查 | 工作目录 | Exit | 结果 |
|---|---|---:|---|
| `git status --short --branch`、`git rev-parse HEAD` | project | 0 | HEAD 为基准，保留已有未提交升级/治理变更 |
| `specify version`、Bundle/Catalog listings | project | 0 | CLI 1.2.3；升级前 Bundle/Catalog 为 v0.4.4 |
| Release API、`git ls-remote`、固定 Tag clone | project | 0 | Tag/commit 和公开来源见上文 |
| `upgrade.ps1` | rehearsal | 0 | v0.4.5 Bundle 与 13 个组件登记成功 |
| `snapshot.ps1 -Project <rehearsal> -Verify`（模板同步前） | rehearsal | 0 | 165 个保护路径未变 |
| `verify-install.ps1 -Project <rehearsal>`（模板同步后） | rehearsal | 0 | 73 个上游扩展/Workflow 文件、组件版本、39 个命令、sd alias 和静态模板一致 |
| `specify integration status` | rehearsal | 0 | 32 个已有 managed files 定制提示；0 missing / invalid paths |
| `py -3 scripts/test_delivery_runtime.py` | upstream | 0 | 37 项测试通过 |
| Specify tool Python：`scripts/validate_distribution.py` | upstream | 0 | Catalog、manifest、Workflow、Bundle 一致 |
| Specify tool Python：`scripts/test_validate_distribution.py` | upstream | 0 | 67 项测试通过 |
| `upgrade.ps1` | project | 0 | 九个 Delivery 扩展和三个 Workflow 为 0.4.5，Bug 为 1.0.1，共 13 个组件 |
| `snapshot.ps1 -Project <project> -Verify`（模板同步前） | project | 0 | 165 个保护路径未变 |
| 显式 `Copy-Item` 随包 PR 模板到 `.github/pull_request_template.md` | project | 成功 | 模板文本已同步；随后用独立内容比较确认，未只依赖 shell 的旧退出码 |
| `verify-install.ps1 -Project <project>`（模板同步后） | project | 0 | 73 个上游文件、13 个版本、39 个命令、sd alias 和 PR 模板一致 |
| `specify integration status` | project | 0 | 保留相同的 32 个定制文件；0 missing / invalid paths |

上游分发检查使用 `C:\Users\YanZh\AppData\Roaming\uv\tools\specify-cli\Scripts\python.exe`。
原生 runtime 测试和分发回归采用 fixture，不是真实项目 Ralph 或模型行为效果验证。

## 失败尝试与纠正

- 演练副本最初未复制 `.github` 目录，模板保护检查因文件不存在失败；补建临时目录并复制
  原模板后，165 个保护哈希检查通过。未修改目标源码来规避此失败。
- 随后的模板比较识别了真实 v0.4.4→v0.4.5 差异；审阅后显式同步，再比较通过。
- shallow clone 无 `HEAD~1`，历史 diff 查询失败，未把浅克隆的根提交统计当成本版增量。
  最终安装一致性依据固定 Tag 的实际文件内容。
- 一次只读统计误用 PowerShell `Measure-Object -Property Count` 失败，不影响安装；最终以
  Git changed paths 和实际内容比较确认范围。
- PR 准备的首次治理检查 exit=1：本文件的中文限制标题未被现有脚本识别。保留中文正文，
  将标题补为 `Limitations` 后重新运行；初次失败的原始日志/blocked receipt 保留在同一 run。

## Limitations（验证边界与限制）

安装/Catalog、164 个定制路径保留、静态模板同步和上游 37/67 项检查已通过。项目文档、
治理与静态检查及最终独立 PR Review 由随后同一 PR run 重新执行/记录，不继承旧 HEAD 的
通过结论。历史 `delivery-v022-upgrade.md` freshness warning 单独披露，不改写旧记录。

未改包，因此未重跑五包构建/类型/pytest 矩阵。安装未验证真实模型 eval、Ralph 或远端 CI。
已有 PR run `delivery-v044-governance-context-20261107` 仅建立了身份和 execution phase，
此前 reviewer 调用被中断、没有结果；延续该 run 完成 PR 检查，不伪造此前独立评审或任务门禁。

## Rollback

以备份为保留依据，使用固定 v0.4.4 Catalog/Bundle 的原生更新路径回退；若决定同时回退
PR 模板，再恢复备份中的项目静态副本。不手改 registry、manifest 或生成命令掩盖版本漂移。
后续 PR 的实际 head、远端 CI 和未合并状态在其自己的验证快照中记录，不提前声明交付。
