# Evidence — Delivery Bundle v0.4.9 发布与安装

## Identity and scope

- **feature_id**: `delivery-v049-upgrade`（Lightweight 安装维护，未创建 Feature）
- **phase_id**: `delivery-v049-upgrade`
- **base_revision**: `c7fe16d91d07812d854512f6b4719608fcba379b`
- **head_revision**: `working-tree`
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: `2026-11-21`
- **result**: pass — 正式 Release 发布、固定版本安装、定制保留与规划路径准入验证通过；项目机械检查另见下方实测记录
- **environment**: Windows；Specify CLI 1.2.3（其 Python 为 3.13.5）；核验脚本使用 Python 3.14.5；PowerShell 7
- **changed_paths**: 安装器拥有的 `.specify/` Catalog、Bundle record、registry、manifest、Workflow 与 Delivery runtime/契约；Codex/OpenCode 路由及 alias；AGENTS、安装说明、ADR-0004、Harness 双语说明、build-log 与本 evidence

用户明确授权合并上游 PR、发布新版本并安装到当前项目。本次在已有 MCP 规划变更的
`main` 工作区执行，未重置、隐藏或提交这些变更；本记录不是 MCP Feature 执行凭证。

## 上游合并与 Release 来源

- [上游 PR #29](https://github.com/YanZhiwei/speckit-delivery/pull/29) 在 14/14 检查通过后
  squash 合并；合并提交为 `94837b03772ee632e62eca29dd751355e0497229`。
- 通过原有 [Release distribution](https://github.com/YanZhiwei/speckit-delivery/actions/runs/44903044440)
  发布，输入 `version=0.4.9`、`ref=94837b03772ee632e62eca29dd751355e0497229`。
  Workflow 固定同一源码 SHA，六宿主 Windows/Linux 安装矩阵及最终构建/发布任务全部成功。
- 正式 [v0.4.9 Release](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.4.9)
  发布于 `2026-11-21T12:20:03Z`，不是 Draft/Prerelease。注解 Tag 解引用为上述合并提交。
- 下载全部 10 个 ZIP，逐个验证 GitHub Release 资产提供的 SHA-256 digest 和文件大小，全部匹配。
  原始发布元数据与资产校验结果保留于本机临时目录，不把生成 ZIP 提交到项目。

## 备份、演练与保留边界

- 临时根目录：`C:\Users\YanZh\AppData\Local\Temp\spawn-join-delivery-v049-20261121-xx_nya4f`，
  包含 `backup/`、`rehearsal/`、`artifacts/`、`logs/` 和一次性维护脚本。
- 先复制跟踪内容、原有未提交文档、完整 `.specify/`、`.agents/`、`.opencode/` 和本地 `specs/`，
  再在独立副本执行正式 Catalog/Bundle 升级；演练通过后才更新目标。
- 1,461 个受保护文件包括项目扩展配置、核心模板/脚本/Skills、固定 Fireworks、静态 PR 模板、
  既有 Specs、Delivery 运行记录、Feature 指针和三个已有 MCP 规划文档。
  演练和目标的安装器执行前后逐字节 SHA-256 全部相同。
- 不使用 `--force`。安装器保留共享定制；原先 18 个 managed-file modification 提示仍存在，
  0 missing、0 invalid manifest paths；这些是已保留的定制，不是缺失入口。
- 后续项目版本文档同步单独执行：`AGENTS.md` 仅将当前 Bundle 声明由 v0.4.8 改为 v0.4.9。
  这不是安装器覆盖；既有审批中的旧输入哈希保留，不伪造新的批准快照。

## 实际命令与安装结果

除注明外从项目根执行，一次性脚本在临时根目录；日志位于其 `logs/`。

| 命令 / 核验 | 工作目录 | Exit | 实际结果 |
| --- | --- | ---: | --- |
| `gh pr merge 29 --squash --match-head-commit 00c3c823…` | upstream | 0 | PR 已合并为 94837b0 |
| `gh workflow run release.yml --ref main -f version=0.4.9 -f ref=94837b0…` | upstream | 0 | 正式发布 run 成功 |
| `git rev-parse v0.4.9^{}` / Release digest 验证 | upstream / temp | 0 | 固定源码及 10 个资产均匹配 |
| `prepare.py` / `verify-preserved.py` | project / temp | 0 | 原始备份及演练副本，1,461 个文件匹配 |
| `upgrade.ps1` | rehearsal / project | 0 | 三类 Catalog 固定为 v0.4.9，原生 `bundle update` 成功 |
| `specify integration use codex` / `use opencode` | rehearsal / project | 0 | 重注册两套入口，恢复 OpenCode 默认 |
| `verify-install.py` | rehearsal / project | 0 | Bundle 0.4.9，共 13 组件；Bug 1.0.1，其余自有扩展/Workflow 0.4.9 |
| 固定 Tag 负载比较 | rehearsal / project | 0 | 76 个安装文件归一化文本与发布源码相同；3 个 Workflow README 不属于安装负载 |
| 注册入口、router 参数及 alias | rehearsal / project | 0 | 每个宿主 30 个扩展入口；router/alias 正文一致，参数输入保留 |
| `specify integration status` | project | 0 | OpenCode 默认，Codex/OpenCode 均已安装，0 missing/invalid |
| `mcp-probe.py` | project | 0 | 实际安装 helper 接纳原运行的三个规划路径；原始 state.json 逐字节保留 |

### MCP 原运行与审批新鲜度

运行 `mcp-loose-coupling-20261121` 保持 `planning`，scope/design 审批历史及原生状态未改写。
安装器执行完成时，原设计快照 21 个输入哈希全部不变；真实已安装的 v0.4.9 helper 对
ADR-0015、ADR 索引和包边界文档均返回 `decision/adr=true`，不再重现 GOV-01 路径拒绝。

随后 AGENTS 版本声明属于项目文档同步，会改变这一治理输入的哈希。保留原 presentation、
审批及 blocked Analyze 作为历史；本次不重签旧审批、不创建检查点或任务凭证。继续 MCP
时必须按当前安装、文档和真实内容重新核对 Doctor/Analyze 与审批新鲜度，再进入执行/切片门。
MCP Spec、Plan、Tasks、ADR-0015 内容和任务状态均未修改。

## 项目机械检查

| 检查 | Exit | 实际结果 |
| --- | ---: | --- |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors / 1 原有 freshness warning：v0.2.2 evidence 落后 51 commits |
| `check-upgrade-docs.ps1`（临时一次性脚本，按项目同一规则检查本次文档范围） | 0 | 7 份升级文档、132 个本地链接目标通过，尾随空白与 `git diff --check` 通过 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 1 | 全局检查被原有 `specs/016-deepagents-mcp-config/tasks.md` 尾随空白阻断 |
| 同一全局 docs 命令在未升级备份执行 | 1 | 同一 Tasks 文件、同一尾随空白错误，证明不是升级引入 |
| `readme_structure.py README.md --base HEAD --docs-root docs` | 1 | 原有新 ADR-0015 未直接登记首页索引 |
| 同一结构检查对 `README.en.md` 执行 | 1 | 同一 ADR 索引问题；`project_readme: auto` 报告，不代表安装失败 |
| `git diff --cached --name-only` | 0 | 暂存区为空；未提交当前项目变更 |
| 原运行 `delivery_runtime.py status --run mcp-loose-coupling-20261121 --json` | 0 | 运行可加载，仍为 planning、scope/design 历史保留，没有 pending task/checkpoint |

Tasks 与 ADR-0015 文件逐字节等于升级前备份。保留已生成的 MCP 工件，不为掩盖全局
检查结果改写 Task 队列或审批输入；这些问题留在 MCP 后续规划/文档阶段处理。本次升级的
7 份文档范围单独通过，不宣称全局 docs 或 README structure 已通过。

安装器执行后 1,461 个原保护文件全部不变；项目版本文档同步后为 1,460 个不变，唯一
差异为 AGENTS 的 v0.4.8 → v0.4.9 声明，已按准确文本替换单独核验。原 runtime 状态、
审批文件、Spec/Plan/Tasks 和三个 MCP 文档保持原字节。本记录不替代完整 Quality、Standards
或独立 Review 凭证。

## Limitations

- 未执行真实模型 Workflow、MCP 会话、Ralph 或产品任务；本记录不证明这些能力已完成。
- Python 包和锁文件未改变，未在本机重复七包构建、类型和测试矩阵；上游发布完整验证另有固定 SHA 的 CI 记录。
- 未为当前项目创建提交、push 或 PR；当前工作区保留安装改动及之前的 MCP 规划变更。
- 未执行独立 Reviewer 或全量目标项目 Quality Gate，不宣称 native 三门或 MCP Analyze 已通过。
- `auto_execute_hooks: false`、`hooks: {}`、串行执行及原有权限边界保持不变。
