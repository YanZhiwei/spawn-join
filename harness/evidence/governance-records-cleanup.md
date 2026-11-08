# Evidence — Governance records cleanup (Lightweight)

## Identity and scope

- **route**: Lightweight（只补交付记录与治理元数据，无产品源码或运行时行为变化）
- **feature_id**: 不适用（独立治理改动，非 Feature run）
- **phase_id**: `governance-records-cleanup`
- **base_revision**: `7dbc714e8d575ae326da81c92eca7459807a241d`
- **head_revision**: `working-tree (7dbc714 plus uncommitted worktree)`
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-11-08
- **environment**: Windows；PowerShell 7；Git for Windows
- **result**: pass

## Changed paths

- `.specify/delivery/readme-governance-package-retirement-20261105/`：把此前只存在本地的
  已交付 run 持久工件纳入 Git（evidence/exploration/decision-context/slices/PR body/verdicts），
  `runtime/` 运行日志仍保留本地。
- `.specify/delivery/common-foundation-20261107/`：同上，纳入已交付 Feature 014 的
  evidence/exploration/slices/PR body；`runtime/` 保持本地。
- `readme-governance.../evidence.md`：在 Current delivery outcome 块补 `head_revision`
  （合并修订 `02c14ccc…`，与既有 `merged_revision`/`effective_head` 一致），修复治理检查
  的 “missing field: head_revision”。
- `harness/build-log.md`：登记本次清理。

## Verification

| Actual command/check | Exit | Result |
|---|---:|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 error；保留 1 条历史 freshness warning（`delivery-v022-upgrade.md`） |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 138 files / 393 local targets |
| `git diff --check` | 0 | 无空白错误 |

## Limitations

- 本次不修改任何产品源码、manifest、锁文件、CI 或质量 Profile，因此不重跑包构建/测试矩阵；
  PR CI 仍会执行完整检查。
- `runtime/` 下的运行日志、脚本和原生回执继续只保留本地，符合 Delivery 运行工作区与持久
  evidence 分离的约定。
- 本克隆的 `.git/info/exclude` 按 ephemeral 策略显式排除了两个 run 的 `exploration.md`、
  `decision-context.md`、`slices.md`、`pull-request*.md` 和 verdicts 等规划/工作区工件；
  本次不 `-f` 强制加入，只提交 `evidence.md`（及 common 的 `pull-request.md`，该路径未被
  排除）。因此全新 clone 中 `evidence.md` 对上述本地规划文件的引用不可解析，属于项目
  artifact policy 的既有取舍，不是本次新增行为。
- `harness/evidence/delivery-v022-upgrade.md` 的历史 freshness warning 属于既有记录，
  不在本次范围，未重新锚定。
- ADR-0009 与 ADR-0011（engineering）仍为 Proposed；转为 Accepted 属于决策人批准动作，
  不在本次机械治理清理中代作决定。
