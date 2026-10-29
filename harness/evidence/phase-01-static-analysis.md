# Evidence — Phase 01 Static Analysis

## Identity and scope

- **feature_id**: `004-static-analysis`
- **phase_id**: `phase-01-static-analysis`
- **task_id**: T001–T007
- **base_revision**: `2a895da32f5634f9bdbddb9ad0afe2d4fa81ac91`
- **head_revision**: `8d9c59c7b3fd961d0b319c1a9628b4a87312fcac`（PR #6 合并后再次锚定；PR #5 squash 为 `48fb3a7`）
- **reconfirmed_at**: 2026-10-27
- **working_directory**: `D:\Repos\Github\spawn-join`
- **superseded_by**: `harness/evidence/package-metadata-and-license.md`
- **recorded_at**: 2026-10-27
- **environment**: Windows；PowerShell 7.6.9；uv 0.7.13；actionlint 1.7.12；
  PSScriptAnalyzer 1.25.0（本地经临时模块路径，CI 由固定版本安装）
- **result**: pass (本地静态分析、回归和全量门禁；远端 CI 由 PR #5 与 main 运行确认)

## Changed paths

- 新增 `scripts/check-static.ps1`、`scripts/test-static.ps1`、
  `scripts/PSScriptAnalyzerSettings.psd1`；
- `scripts/quality.ps1`：增加 `static` 检查，无 Package 的 `all` 纳入；
- `scripts/test-governance.ps1`：`Assert-GovernanceResult` 改名为
  `Test-GovernanceResult`，满足 approved verbs 规则；
- `.github/workflows/quality.yml`：安装 PSScriptAnalyzer 并执行静态检查和回归；
- `docs/development/quality-gates.md`、`README.md`、`AGENTS.md`：工具、命令、限制同步；
- 本 evidence、`harness/code_review/review-phase-01-static-analysis.md` 和
  `harness/build-log.md`。

`specs/004-static-analysis/` 是 Git 忽略的本地 Feature 工件，不随仓库分发。

## Observed commands

| Command | Exit | Observed result |
|---|---|---|
| `scripts/check-static.ps1` | 0 | actionlint 0 问题；PSScriptAnalyzer 0 finding |
| `scripts/test-static.ps1` | 0 | 3 场景：合法、坏 workflow、`Invoke-Expression` 被拒绝 |
| `quality.ps1 -Check static` | 0 | 与直接脚本一致 |
| `quality.ps1 -Check governance` | 0 | 0 error / 0 warning |
| `quality.ps1 -Check docs` | 0 | 46 文件 / 111 目标 |
| `test-governance.ps1` | 0 | 11 场景 |
| `quality.ps1`（全量） | 0 | 四包 + 文档 + 治理 + 静态分析 |
| 干净克隆 + 未提交改动副本，`-Check static` / `-Check governance` | 0 each | 无 `specs/`；工具经 PSModulePath 提供 |
| pwsh 7 AST 解析五个脚本 | 0 | 0 parse error |

## Failed attempts and corrections

- actionlint 使用 `-color=never` 报参数解析错误；实际 flag 是 `-no-color`，已修正。
- 静态 fixture 没有 Git 仓库时 actionlint 报 “no project was found”；fixture 增加
  `git init` 后通过。
- `Assert-GovernanceResult` 使用非 approved verb；PSScriptAnalyzer 规则命中后改名为
  `Test-GovernanceResult`，行为不变。
- 本地 PSScriptAnalyzer 通过 `Save-Module` 到临时目录并加入 `PSModulePath`，未永久安装；
  CI 使用固定版本安装。

## Limitations and blockers

- 静态分析只覆盖 workflow 语法/表达式和 PowerShell 高信号规则，不验证运行时行为。
- `.agents/skills/` 第三方脚本不在扫描范围；未启用 shellcheck/pyflakes 集成。
- PSScriptAnalyzer 需要预先安装；缺失时门禁失败并给出安装命令，不静默跳过。
- 远端 CI：PR 运行 `40532695952` 与 main 运行 `40533177300` 均 14/14 success。
- 本 evidence 绑定实现提交 `9fab77d`；PR #5 squash 后已重新确认，后续纯文档提交不触发
  freshness warning。

## Reconfirmation — 2026-10-27

PR #5 以 squash 合并为 `48fb3a7`；其 PR 运行 `40532695952`、main 运行 `40533177300`
均 14/14 success。Feature 005 修改治理脚本后，在 `9fab77d` 重新执行；PR #6 又以 squash
合并为 `8d9c59c`，静态分析在合并后的 main 再次确认为 0 finding。

- `scripts/quality.ps1 -Check static`：exit 0，actionlint/PSScriptAnalyzer 0 finding；
- `scripts/quality.ps1 -Check governance`：0 error / 0 warning；
- `scripts/quality.ps1 -Check docs`：50 文件 / 120 目标。

原静态分析命令、3 个场景和工具版本保持不变；本次只重新确认实现仍通过。
