# Evidence — Delivery Bundle v0.4.8 与 Codex 接入

## Identity and scope

- **feature_id**: `delivery-v048-upgrade`（Lightweight 安装升级，未创建 Feature）
- **phase_id**: `delivery-v048-upgrade`
- **route**: Lightweight
- **base_revision**: `53c741e2fee7bd37419ad0f8b496a1cb898d1c81`
- **head_revision**: `working-tree`
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: `2026-11-21`
- **result**: pass — 固定 Release 安装、Codex 生命周期、配置保留及项目针对性检查通过；真实模型与远端 CI 边界见下文
- **environment**: Windows、Specify CLI 1.2.3、工具环境 Python 3.13.5、Codex bundled PowerShell
- **changed_paths**: `.agents/skills/speckit-*/SKILL.md`（30 个新增入口）、`.specify/` 的 Catalog/registry/manifest/Workflow、AGENTS、仓库地图、安装说明、ADR-0004、Harness 文档与本 evidence

用户要求安装固定 v0.4.8 并处理 Codex 支持，随后授权创建 PR、监听 CI，成功后合并并收尾。
基线为干净的 `main`，工作分支 `codex/delivery-v048-codex`。本次未改 Python 包、锁文件、
公共 API 或运行时依赖；项目原有 OpenCode 默认集成保持。

## 来源与保留边界

- Release：[v0.4.8](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.4.8)，
  发布时间 `2026-11-20T14:04:26Z`，非草稿、非预发布，10 个发布资产均有 SHA-256 digest。
- 固定 checkout：`b98f7fa2c0df1e54e6f9de81f99a656f2b995ac8`；附注 Tag 对象
  `52844c6f02c619a70d1f8ec2e6cf393f0851794c`。
- 临时目录：`C:\Users\YanZh\AppData\Local\Temp\spawn-join-delivery-v048-20261121-141631`，
  含 `backup/`、`rehearsal/`、`upstream/`、`logs/` 和一次性脚本，不提交项目。
- 三类 Catalog 固定到 v0.4.8。全部组件/入口通过官方安装器生成，未手改 manifest/registry。
- 当前 CLI 实际为 1.2.3，满足 Bundle `>=1.2.3`，不同于旧 evidence 的 1.4.0 观察。
  Bug 从旧安装 1.0.2 调整为 Bundle pin / 当前 CLI 随附的 1.0.1；其余九个扩展和三条
  Workflow 均为 0.4.8，Bundle 共 13 个组件。
- 保护范围：`.specify/extensions.yml`、所有项目 `*-config.yml`、跟踪的
  `.specify/templates/**`、已有 `.agents/skills/**`、静态 PR 模板，共 165 个文件。
  目标前后 SHA-256 全部相同；演练副本经 Git 换行转换，按归一化文本比较也全部一致。
- 保留 Codex 核心 10 个 Skills，新增 30 个扩展 Skills（含 `speckit-sd` alias），另有
  原有 Fireworks，共 41 个技能目录。OpenCode 保留 40 个命令（39 个完整命令 + `sd`）。
  两宿主扩展入口均在各组件 `registered_commands` 登记；未复制用户级 `$sd` 门面。

## 实际命令与结果

除注明外在项目根执行，原始输出在临时 `logs/`。`upgrade.ps1` 顺序替换三类 Catalog，
再运行 `specify bundle update speckit-delivery`，每步检查退出码。

| 命令 / 检查 | 工作目录 | Exit | 结果 |
|---|---|---:|---|
| `git status --short --branch`、`git rev-parse HEAD` | project | 0 | 干净基线如上 |
| `specify version`、`gh release view v0.4.8` | project | 0 | CLI 1.2.3，Release/资产元数据如上 |
| `upgrade.ps1` | rehearsal / project | 0 | Bundle 0.4.8、13 组件安装完成 |
| `specify integration use codex`、`specify integration use opencode` | rehearsal / project | 0 | 两套入口重注册，最后恢复 OpenCode 默认 |
| 165 个保护文件核验 | rehearsal / project | 0 | 内容全部保留，目标逐字节哈希不变 |
| `verify-install.py` | project | 0 | 76 个安装负载与 Tag 归一化文本一致；3 个 Workflow README 不属安装负载 |
| 两宿主入口、alias 与归属 | project | 0 | 各 30 个扩展入口存在，alias/router 正文一致，router 接收 `$ARGUMENTS` |
| `specify integration status` | project | 0 | 无缺失/非法路径；已有定制提示：Codex 1、OpenCode 10、共享基础设施 7 |
| `python scripts/test_bundle_install.py --integration codex --specify <installed-specify>` | upstream Tag | 0 | 干净 Codex 项目安装、参数、资源/runtime、归属、更新/重装/移除和配置保留通过 |

`bundle update --integration codex` 在有活动集成的演练项目中仍使用活动 OpenCode；核对
CLI 原生契约后，改用 `integration use codex` / `use opencode` 重注册，不覆盖核心技能。
安装器提示共享脚本/模板已有定制时按原样保留，未使用 `--force`。

初版一次性核验脚本把 LF/CRLF 字节差异和无输入命令没有 `$ARGUMENTS` 误判为失败；
改为归一化负载比较、仅要求 router 参数后重跑通过，未修改发布负载或项目定制。

## 项目检查与 Standards Review

| 检查 | Exit | 结果 |
|---|---:|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 152 个文件、417 个本地链接目标通过 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors / 1 历史 freshness warning（v0.2.2 evidence，非本次新问题） |
| `readme_structure.py README.md --base HEAD --docs-root docs` | 0 | `README_STRUCTURE: pass` |
| `readme_structure.py README.en.md --base HEAD --docs-root docs` | 0 | `README_STRUCTURE: pass` |
| `git diff --check`、`git diff --cached --check` | 0 | 无空白错误；实际 staged 范围为 58 个文件，其中 30 个为生成 Skills |

Standards Review：实现者对实际 outgoing diff 做单独自审，核对安装器/项目拥有权、生成
入口与同一源的 alias、两宿主 registry、配置和核心定制保留、来源固定、文档版本/命令、
无关路径与供应链边界。未新增公共抽象、包依赖、Hook 或复制门面；未发现阻断问题。
这是实现者自审，未执行独立 Reviewer 或远端人工批准，不宣称 Ralph 三门凭证完整。
生成 Skills 的资源路径前缀和 Bug 命令占位符由安装器转换为 Codex 原生形式，属于预期
渲染差异；资源仍引用同一套 `.specify/extensions/`，没有添加第二份 runtime。

PR 正文落盘在临时根目录 `pull-request.md`（`PR_BODY_PATH`），绑定提交后的实际 HEAD；
可用 `gh pr create --base main --head codex/delivery-v048-codex --body-file <PR_BODY_PATH>`
复用正文。PR 创建、CI 与合并结果在 GitHub 对应 PR 保存，不预写成功结论。

## Limitations

- Codex 生命周期探针使用固定 Tag 和实际 CLI，不调用真实模型；不能证明 Codex CLI 认证、
  真实宿主交接、完整 SD/Ralph、取消恢复或真实模型端到端交付质量。
- `auto_execute_hooks: false`、`hooks: {}`、Slice 策略与项目权限边界保持。
- Python 包未变，本机未重复七包构建/类型/测试矩阵；PR 远端 Quality Gate 单独观察。
- 未启动 Delivery runtime run；本文件是 Harness 安装证据，不伪造任务 receipts、独立
  Reviewer 或 Doctor/Ralph 的通过结论。
