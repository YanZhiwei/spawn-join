# Evidence — Delivery Bundle v0.4.6 upgrade

## Identity and scope

- **feature_id**: `delivery-v046-upgrade`（一次性 Lightweight 升级标识，未创建 Feature）
- **phase_id**: `delivery-v046-upgrade`
- **route**: Lightweight
- **base_revision**: `02e3d913fd6fbc740a57ddaa23f34cde1048877f`
- **head_revision**: `working-tree`
- **working_directory**: `C:\Users\YanZh\.local\share\opencode\worktree\86e56b\quick-forest`
- **recorded_at**: `2026-11-09`
- **result**: pass — 固定 Release 安装、配置保留、模板不变、源码一致性和下述上游检查通过；项目检查、评审及远端状态分别记录
- **environment**: Windows、Specify CLI 1.2.3（其 Python 3.13.5）、PowerShell 7、Python Launcher `py -3`

用户要求安装 v0.4.6，并在完成后创建 PR、CI 成功后按 SD 流程完成合并。本 evidence 只覆盖
安装与本地验证；PR、CI 和合并结果由对应 Delivery run 另行记录，不把安装成功描述成原生
交付完成。升级从干净工作区的 detached `HEAD` 开始，此前 v0.4.5 安装、治理和 evidence 全部保留。

## Release 来源

- Release：[v0.4.6](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.4.6)。
- 实际 checkout commit：`6e251cd34c22b81b0d05710bfa943a075a8126d6`。
- 三类固定 Catalog 使用
  `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.6/catalogs/`
  下的 `extensions.json`、`workflows.json` 和 `bundles.json`。

本版只更新 Docs Sync：新增确定性的项目 README 结构守卫
`scripts/readme_structure.py`、索引式 `templates/project-readme.md`，以及 `project_readme`、
`readme_paths`、`readme_max_lines`、`readme_sections`、`readme_docs_root` 配置。三条 Lane
的 `package-readme` 节点在 Review 前要求结构结论，Review Fix 在修复后重新校验。默认
`project_readme: auto`，已有项目只报告不阻断；本版不增加 runtime 字段或自动调度器。

## 备份、演练与项目归属

临时根目录：`C:\Users\YanZh\AppData\Local\Temp\spawn-join-delivery-v046-20261109`。
其中 `backup/` 保存升级前 `.specify`、`.opencode`、`.agents` 及静态 PR 模板；`rehearsal/`
是演练副本，`upstream/` 是固定 Tag checkout。临时脚本和日志不进入仓库。

安装前记录 165 个保护路径的 SHA-256：`.specify/extensions.yml`、全部项目 `*-config.yml`、
跟踪的 `.specify/templates/**`、`.agents/skills/**` 和 `.github/pull_request_template.md`。
演练与目标安装器执行后，165 个哈希均未改变，说明安装器没有覆盖项目配置或核心定制。

本次安装器拥有的改动为 Catalog、Bundle/extension/workflow registry、九个 Delivery 扩展、
生成的 OpenCode 命令和三条 Workflow。项目拥有的改动为 Docs Sync 配置中的
`project_readme: auto`、当前版本说明、ADR-0004 历史、Harness 中英文入口、本 evidence 和
build log。随包 PR 模板 v0.4.6 未变化，`.github` 静态副本保持同一字节，未做同步写入。
没有修改包源码、锁文件、公共 API、运行时依赖、权限或 Hook 开关。

## 实际命令与结果

除注明外，命令在上述项目根运行。`upgrade.ps1` 顺序执行三组固定 Catalog remove/add，随后
执行 `specify bundle update speckit-delivery` 和 `specify bundle list --json`，检查每步退出码。

| 命令 / 检查 | 工作目录 | Exit | 结果 |
|---|---|---:|---|
| `git status --short --branch`、`git rev-parse HEAD` | project | 0 | 工作区干净，HEAD 与 `origin/main` 同为基准 |
| `specify version`、Bundle/Catalog listings | project | 0 | CLI 1.2.3；升级前 Bundle/Catalog 为 v0.4.5 |
| 固定 Tag clone、`git rev-parse HEAD` | upstream | 0 | checkout commit 见上文 |
| `upgrade.ps1` | rehearsal | 0 | v0.4.6 Bundle 与 13 个组件登记成功 |
| `verify-protected.ps1`（演练） | rehearsal | 0 | 165/165 保护路径未变 |
| `upgrade.ps1` | project | 0 | 九个 Delivery 扩展和三个 Workflow 为 0.4.6，Bug 为 1.0.1，共 13 个组件 |
| `verify-protected.ps1`（目标） | project | 0 | 165/165 保护路径未变 |
| `verify-install.ps1` | project | 0 | 75 个已安装扩展/Workflow 文件与固定 Tag 内容一致；0 内容差异 |
| `specify extension list` / `specify workflow list` | project | 0 | 10 个扩展、3 个 Delivery Workflow 版本符合预期 |
| `specify integration status` | project | 0 | 32 个已有 managed files 定制提示；0 missing / invalid paths |
| `py -3 scripts/readme_structure.py README.md --base HEAD --docs-root docs` | project | 0 | `README_STRUCTURE: pass`，8 个既有章节 |
| `py -3 scripts/test_delivery_runtime.py` | upstream | 0 | 37 项测试通过 |
| Specify tool Python：`scripts/validate_distribution.py` | upstream | 0 | Catalog、manifest、Workflow、Bundle 一致 |
| Specify tool Python：`scripts/test_validate_distribution.py` | upstream | 0 | 73 项测试通过 |
| Specify tool Python：`scripts/test_docs_readme_structure.py` | upstream | 0 | 11 项测试通过 |

上游源码另含三条 Workflow 目录的 `README.md`，安装负载不包含这些仓库文档，因此未出现在
75 个内容一致文件的比对中；这不是缺失的生成命令或模板。上游检查使用
`C:\Users\YanZh\AppData\Roaming\uv\tools\specify-cli\Scripts\python.exe`，采用 fixture，
不是真实项目 Ralph 或模型行为效果验证。

## 失败尝试与纠正

- 首次 `verify-install.ps1` 把 PowerShell 函数调用误写成命令式参数，导致每个文件都被判为
  内容不同（`matched=0 mismatches=80`）。改为先取归一化文本再比较后，结果为 75 个一致、
  0 个内容差异；未修改项目文件来规避该失败。
- 比对遍历包含上游测试生成的 `__pycache__`，已排除缓存目录；未删除上游测试证据。
- Windows 检出同时存在 LF/CRLF；一致性比较归一化换行，只用于内容核对，不声称字节顺序
  相同。`.github` 静态模板另用同一归一化比较确认与随包模板一致。

## Limitations（验证边界与限制）

安装/Catalog、165 个保护路径保留、75 个上游文件一致、静态模板不变和上游 37/73/11 项检查
已通过。PR 创建、远端 CI 和 SD 合并流程在对应 Delivery run 中另行执行和取证，不继承本
evidence 的结论。未改包，因此未重跑六个 Distribution 的构建/类型/pytest 矩阵。安装未验证
真实模型 eval、Ralph 或远端 CI。Doctor 仍是 Agent Prompt，本次没有运行 Doctor。

## Rollback

以备份为保留依据，使用固定 v0.4.5 Catalog/Bundle 的原生更新路径回退，并删除 v0.4.6 新增
的 `docs-sync/scripts/` 与 `docs-sync/templates/project-readme.md`。项目配置中的
`project_readme` 可同时移除。不手改 registry、manifest 或生成命令掩盖版本漂移。
