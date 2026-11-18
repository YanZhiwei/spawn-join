# Evidence — Delivery Bundle v0.4.7 upgrade

## Identity and scope

- **feature_id**: `delivery-v047-upgrade`（一次性 Lightweight 升级标识，未创建 Feature）
- **phase_id**: `delivery-v047-upgrade`
- **route**: Lightweight
- **base_revision**: `15f5c03028496abf122b6f5fc685f70496d295dd`
- **head_revision**: `working-tree`
- **working_directory**: `D:\Repos\spawn-join`
- **recorded_at**: `2026-11-18`
- **result**: pass — 固定 Release 安装、配置保留、模板不变、安装内容一致性和下述上游检查通过；项目检查与远端状态分别记录
- **environment**: Windows 10.0.26300、Specify CLI 1.4.0（其 Python 3.13.5）、PowerShell 7.7.0（Store 包，经 junction 调用）、Python Launcher `py -3` 在本机不可用

用户要求安装 v0.4.7。本 evidence 只覆盖安装与本地验证；未创建 PR，也不把安装成功描述成
原生交付完成。升级从干净工作区开始，此前 v0.4.6 安装、治理和 evidence 全部保留。

## Release 来源

- Release：[v0.4.7](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.4.7)
  （2026-11-16 发布，非草稿、非预发布，10 个资产均带 `sha256` digest）。
- 实际 checkout commit：`90487e2d16f356687f2873f9e78efc596d461116`（Tag 为附注标签，
  对象 `bb1f61dc5f5dbc27e23a24bf2c8085ea59dd17b8`）。
- 三类固定 Catalog 使用
  `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.7/catalogs/`
  下的 `extensions.json`、`workflows.json` 和 `bundles.json`。

本版不新增配置字段：`delivery`、`docs-sync` 的 `config-template.yml` 与 v0.4.6 逐字节相同。
安装面变化为：10 个 `extension.yml` 版本号、Delivery 的 `README.md`、
`commands/speckit.delivery.explore.md`、`templates/exploration.md`、
`templates/method-diagnose.md`、新增 `templates/focused-audits.md`、Review 的
`templates/reviewer.md`、Simplify 的 `commands/speckit.simplify.scan.md`，以及三条
Workflow。行为契约变化属于引导式 Prompt：Explore 区分目标/症状/手段并记录反证，
Diagnosis/Review/Simplify 质疑首选解释并连接不变量与受影响消费者。

## 备份、演练与项目归属

临时根目录：`C:\Users\YanZh\AppData\Local\Temp\spawn-join-delivery-v047-20261118`。
其中 `backup/` 保存升级前 `.specify`、`.opencode`、`.agents` 及静态 PR 模板；`rehearsal/`
是演练副本；`upstream/` 是固定 Tag checkout；日志在 `logs/`。临时脚本和日志不进入仓库。

安装前记录 165 个保护路径的 SHA-256：`.specify/extensions.yml`、全部项目 `*-config.yml`、
跟踪的 `.specify/templates/**`、`.agents/skills/**` 和 `.github/pull_request_template.md`。
演练与目标安装器执行后，165 个哈希均未改变，说明安装器没有覆盖项目配置或核心定制。

本次安装器拥有的改动为 Catalog、Bundle/extension/workflow registry、九个 Delivery 扩展、
生成的 OpenCode 命令和三条 Workflow。项目拥有的改动为 AGENTS.md、版本说明、ADR-0004
历史、Harness 中英文入口、本 evidence 和 build log。随包 PR 模板 v0.4.7 未变化，
`.github` 静态副本保持同一字节，未做同步写入。没有修改包源码、锁文件、公共 API、运行时
依赖、权限或 Hook 开关。

## 实际命令与结果

除注明外，命令在上述项目根运行。`upgrade.ps1` 顺序执行三组固定 Catalog remove/add，随后
执行 `specify bundle update speckit-delivery` 和 `specify bundle list --json`，检查每步退出码；
演练与目标使用同一脚本。

| 命令 / 检查 | 工作目录 | Exit | 结果 |
|---|---|---:|---|
| `git status --short --branch`、`git rev-parse HEAD` | project | 0 | 工作区干净，HEAD 与 `origin/main` 同为基准 |
| `specify version` | project | 0 | CLI 1.4.0（升级前已非文档记载的 1.2.3） |
| 固定 Tag checkout、`git rev-parse HEAD` | upstream | 0 | checkout commit 见上文 |
| `upgrade.ps1` | rehearsal | 0 | v0.4.7 Bundle 与 13 个组件登记成功 |
| 保护路径哈希（演练） | rehearsal | 0 | 165/165 未变 |
| 安装内容比对（演练） | rehearsal | 0 | 76 个文件一致；3 个 Workflow README 不在安装负载 |
| `upgrade.ps1` | project | 0 | 九个 Delivery 扩展和三个 Workflow 为 0.4.7，共 13 个组件 |
| 保护路径哈希（目标） | project | 0 | 165/165 未变 |
| 安装内容比对（目标） | project | 0 | 76 个文件一致；0 内容差异，3 个仓库文档未安装 |
| `specify extension list` | project | 0 | Bug 1.0.2，九个 Delivery 扩展 0.4.7，10 个扩展 |
| `specify workflow list` | project | 0 | 三条 Delivery Workflow 均为 0.4.7 |
| `specify integration status` | project | 1 | 32 个已有 managed files 定制提示；0 missing / invalid paths（预期 warning） |
| OpenCode 命令计数 | project | 0 | 39 个点号原生命令，另有 `sd.md` alias |
| `git diff --check` | project | 0 | 无空白错误 |
| README 结构守卫 | project | 0 | 见下方项目检查 |
| 项目 docs/governance 检查 | project | 0 | 见下方项目检查 |
| 上游 `test_delivery_runtime.py`（补充，非升级必需） | upstream | 0 | 37 项通过 |
| 上游 `validate_distribution.py`（补充，非升级必需） | upstream | 0 | Catalog、manifest、Workflow、Bundle 一致 |

## 项目检查

本机 PowerShell 7 的 `WindowsApps` 别名不可执行（见“环境偏差”），改用其版本化目录的
junction 后，项目脚本在 PowerShell 7.7.0 下执行；`py -3` 不可用，Python 脚本改用 Specify
工具链 Python。

| 检查 | 结果 |
|---|---|
| `readme_structure.py README.md --base HEAD --docs-root docs` | `README_STRUCTURE: pass`，8 个既有章节 |
| `quality.ps1 -Check governance` | exit 0，0 errors / 1 历史 warning（v0.4.2 evidence 的 freshness，非本次改动） |
| `quality.ps1 -Check docs` | exit 0，69 个文件、347 个本地链接目标通过 |

升级未改 Python 包、脚本、CI 或质量 Profile，因此不运行包矩阵、`-Check static` 或回归
套件；这些由后续 PR 的远端 `Quality Gate` 覆盖，不是本次安装验证的前提。

## 上游补充检查

固定 Tag checkout 的回归结果（补充信息，不属于升级必需项）：

| 检查 | 结果 |
|---|---|
| `test_delivery_runtime.py` | 37 项通过 |
| `validate_distribution.py` | Catalog、manifest、Workflow 和 Bundle 一致 |

上游源码另含三条 Workflow 目录的 `README.md`，安装负载不包含这些仓库文档，因此未出现在
76 个一致文件的比对中；这不是缺失的生成命令或模板。

## 环境偏差与失败尝试

- **PowerShell 7 无法 spawn**：会话中途开始，`WindowsApps` 下的 `pwsh.exe` 别名与包内
  重定向路径均返回 `拒绝访问 (os error 5)`；重启 OpenCode 后仍复现。本机实际安装的是 Store
  版 PowerShell 7.7.0，其版本化目录
  `C:\Program Files\WindowsApps\Microsoft.PowerShell_7.7.0.0_x64__8wekyb3d8bbwe\pwsh.exe`
  可直接执行。为继续安装，新建用户级 junction
  `%LOCALAPPDATA%\Programs\pwsh7` 指向该目录，并把用户级 `opencode.jsonc` 的 `shell`
  指回 `pwsh7\pwsh.exe`；项目脚本随后在 PowerShell 7.7.0 下执行。这是本机工具环境修复，
  不是仓库配置。
- **网络代理**：`raw.githubusercontent.com` 直连出现 `WinError 10054`/读取超时；本机 WinINET
  代理为 `127.0.0.1:3213`，但 Python 请求未继承。安装命令显式设置 `HTTP(S)_PROXY` 后成功。
  未修改系统代理或仓库网络配置。
- **Bug 扩展版本提示**：Bundle pin 为 `1.0.1`，CLI 1.4.0 随包 `1.0.2`，安装器提示使用更新的
  补丁版并在 `installed_versions` 记录 `1.0.2`；`required_components` 仍为 pin 值。
- **CLI 版本漂移**：文档原记载 CLI 1.2.3，现场为 1.4.0；`spec-kit-core` Catalog 仍指向
  `github/spec-kit/v1.2.3`。本次只更正文档事实，未改动该 Catalog。
- 演练首次哈希比对误用 `git ls-files`，在无 `.git` 的副本中只得到 10 个路径；改为先生成
  165 条路径清单再逐条哈希后，演练与目标结果一致。未修改仓库文件来规避该失败。

## Limitations（验证边界与限制）

安装/Catalog、165 个保护路径保留、76 个上游文件一致、静态模板不变和上游回归已通过。
未创建 PR，也未运行远端 CI、Doctor、Ralph 或完整交付循环。未改包，因此未重跑七个
Distribution 的构建/类型/pytest 矩阵。安装未验证真实模型 eval 或行为评估场景 54–59 的实际
效果。本机 PowerShell 7 的别名路径不可执行，已用版本化目录 junction 恢复；`py -3` 不可用
属于环境限制，已用 Specify 工具链 Python 执行并记录。

## Rollback

以备份为保留依据，使用固定 v0.4.6 Catalog/Bundle 的原生更新路径回退；v0.4.7 新增的
`delivery/templates/focused-audits.md` 随扩展回退删除。项目文档与 evidence 回退到
`base_revision`。不手改 registry、manifest 或生成命令掩盖版本漂移。
