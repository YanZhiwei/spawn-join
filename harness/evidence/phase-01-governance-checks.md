# Evidence — Phase 01 Governance Checks

## Identity and scope

- **feature_id**: `003-governance-checks`
- **phase_id**: `phase-01-governance-checks`
- **task_id**: T001–T007
- **base_revision**: `c5ad5763dcf00139e629746a9847f9824bb98ebf`
- **head_revision**: `8d9c59c7b3fd961d0b319c1a9628b4a87312fcac`（PR #6 合并提交；PR #2 squash 为 `83628ac`）
- **reconfirmed_at**: 2026-10-27
- **working_directory**: `D:\Repos\Github\spawn-join`
- **superseded_by**: `harness/evidence/package-metadata-and-license.md`
- **recorded_at**: 2026-10-27
- **environment**: Windows；PowerShell 7.6.9；git 2.55.0.windows.3；uv 0.7.13；Node 22.17.0
- **result**: pass (本地结构门禁、回归和全量质量门；远端 CI 已由 PR #1 与 main 运行确认)

## Changed paths

- 新增 `scripts/check-governance.ps1`、`scripts/test-governance.ps1`；
- `scripts/quality.ps1`：增加 `governance` 检查并纳入无 Package 的 `all`；
- `.github/workflows/quality.yml`：governance job 增加结构检查和失败回归，checkout 使用完整历史；
- `docs/development/quality-gates.md`、`harness/README.md`、`harness/evidence/README.md`、
  `AGENTS.md`、`README.md`：检查范围、命令和限制同步；
- `harness/evidence/adr-and-project-diagram-skill.md`、`harness/evidence/ci-governance-exit-code.md`、
  `harness/evidence/untrack-historical-specs.md`：只补机器可读元数据，不改既有结论；
- 本 evidence、`harness/code_review/review-phase-01-governance-checks.md` 和 `harness/build-log.md`。

本地 `specs/003-governance-checks/` 是 Git 忽略的 Feature 工件，不随仓库分发。

## Observed commands

| Command | Exit | Observed result |
|---|---|---|
| `pwsh -NoProfile -File scripts/check-governance.ps1` | 0 | 0 error，1 warning（phase-01 head 落后 6 个提交） |
| `pwsh -NoProfile -File scripts/test-governance.ps1` | 0 | 9 个场景：1 个合法结构 + 8 个拒绝 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 与直接脚本一致 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 41 个 Markdown / 105 个本地目标 |
| `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | 原有 9 场景无回归 |
| `pwsh -NoProfile -File scripts/quality.ps1` | 0 | 四包格式/lint/类型/测试/构建 + 文档 + 治理 |
| pwsh 7 AST 解析三个脚本 | 0 | 0 parse error |
| 干净克隆 + 未提交改动副本（15 个 overlay 文件），`-Check docs` | 0 | 26 文件 / 90 目标；无 `specs/` |
| 同一副本，`-Check governance` | 0 | 0 error，1 warning；Spec/Tasks 检查按设计跳过 |

## Failed attempts and corrections

- 首次实现使用 `$(Compare-Object ...).Count` 与 `$( ... | Sort-Object -Unique).Count`，
  在 StrictMode 下遇到标量对象没有 `Count`；改为 `@(...)` 后通过。
- 首次本地链接检查把目录链接（`packages/core/spawn-join-core/`、`.specify/`）误判为
  local-only；Git 对目录路径和尾斜杠的 `check-ignore` 语义不稳定。修正为：目录只校验存在，
  文件才检查忽略状态，并跳过第三方 `.agents/skills/` 文档。
- 干净副本第一次没有 Git 历史，导致所有 base/head SHA 被判为不存在；改用完整克隆后通过。
  该现象也促成 shallow clone 处理：缺失修订在浅克隆中降为 warning，CI governance job
  显式 `fetch-depth: 0`。

## Remote confirmation and follow-up

- PR [#1](https://github.com/YanZhiwei/spawn-join/pull/1) 已合并为 `475ab4c`；
- PR 运行 `40525168443`：14/14 success，governance `0 error / 1 warning`、9 场景通过；
- main 推送运行 `40525841365`：14/14 success，governance 实际执行并输出 9 场景通过；
- PR [#2](https://github.com/YanZhiwei/spawn-join/pull/2) 以 squash 合并为 `83628ac`，
  main 运行 `40528549959` 为 14/14 success；分支提交不是 main 祖先，本证据按合并提交锚定；
- 合并后修复 freshness 误报：提交 `03dcfc4`；`scripts/test-governance.ps1` 扩为 11 场景，
  当前仓库 `check-governance.ps1` 为 `0 error / 0 warning`；详见 build-log 同日条目；
- Ruleset `main` 已加入 required `Quality Gate`；临时 PR [#3](https://github.com/YanZhiwei/spawn-join/pull/3)
  注入 trailing whitespace 后 14/14 失败、`mergeStateStatus=BLOCKED`，验证后已关闭；
- PR [#6](https://github.com/YanZhiwei/spawn-join/pull/6) 以 squash 合并为 `8d9c59c`，
  PR 运行 `40534650197` 与 main 运行 `40535092200` 均 14/14 success。

## Limitations and blockers

- 治理检查只验证结构和索引一致性；evidence 语义是否覆盖改动、freshness 是否仍有效
  仍需人工评审。
- `phase-01-python-quality-gates` 已按 PR #2 的 squash 提交 `83628ac` 重新锚定。
- 远端 CI 已由 PR #1、PR #2 和 main 运行确认；Ruleset 已配置 required `Quality Gate`，
  并用临时失败 PR #3 验证 `BLOCKED`。
- 本 evidence 随 PR 更新；新提交产生后按 freshness 规则确认。
