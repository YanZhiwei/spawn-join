# 最终 PR 共享验收记录的恢复与门禁验证

- feature_id: pr-delivery-evidence-publication
- phase_id: governance-regression
- base_revision: 2b57b86b16278bee16ab80981129455e751b8fce
- head_revision: 6928289b105c0475f3d5a16145f0d4eac8a7138c
- working_directory: `%TEMP%/spawn-join-pr-evidence-20261125`（独立 Git 工作树的仓库根目录）
- recorded_at: 2026-11-25T20:42:50+08:00
- result: pass

本次修复将最终 PR 的证据检查接入[质量工作流](../../.github/workflows/quality.yml)，并恢复 [#98 的最终集成记录](../../.specify/delivery/agent-work-main-integration-20261123/evidence.md)。本记录对应本次治理修复的实施提交。

## #98 恢复依据

原集成工作树中未跟踪的 `evidence.md` 的 SHA-256 为 `242234a0122e044887268b62620755edc37b6b48e2628a00b23533c40f556c4b`。原审查报告与收据的 SHA-256 分别为 `ebb87bbe54416fe7c9df4bc23526c0cb1e59759d029d9129ec9a22a2f2907bf8`、`746f3d1ad5cba361747e0443d760b05f63f702631eae8cf67194d34d13e2a5c5`，与 [PR #98](https://github.com/YanZhiwei/spawn-join/pull/98) 的交接信息吻合。审查提交、实际 PR head 和 squash 提交指向同一棵 Git 树 `3c5e15dd4b828913addfe9f2441de1d96978bf07`。

旧记录的观测时间比 GitHub 合并时间早约 21 秒。根据 2026-11-25T10:07:40Z 的 GitHub 回读，用已安装的原生 Close 刷新当前结果块，得到 `delivered`、`published-content-equivalent` 和 `diff-equivalent`。重复调用报告 `changed: false`。发布分支上的文件按 LF 归一化后，结果块结束标志以下的全部历史正文与原件相同。

## 发布分支验证

以下检查在 Windows 上的独立分支 `codex/pr-evidence-gate` 运行。实施提交的完整 Git 树为 `00ac946d195b1bdafc694673ab1b588c5979fa99`。独立复核核对了这棵树的 12 个变更文件，检查了原生与历史证据格式、分支清单、模板与 CI 入口、依赖完整性，以及合并后对历史正文的保护。未发现发布阻断。

| 场景或命令 | 退出码 | 结果 |
| --- | --- | --- |
| 对 #98 的真实 base `d78ecdc33b15c941317d1fb8f25f18155236da9b` 和 PR head `b0116edc09b997c7c6c94beaf6e805e987942ebc` 输入新版最终 PR 声明 | 1（预期） | 尽管本地已经恢复原件，门禁仍准确报告历史 PR 的 Git 树中缺少该文件。 |
| `pwsh -NoProfile -File scripts/test-pr-evidence.ps1` | 0 | 45 个场景通过，包括单 PR、中间层、最终层、代码变动后的复审、只追加证据的发布提交，以及原生 `close-record` 对归档和 squash 结果的验证。 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` 和 `-Check governance` | 0 | 文档检查通过。治理为 0 错误，有 1 条既有的 `delivery-v022-upgrade.md` 时效告警。 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` 和 `pwsh -NoProfile -File scripts/test-static.ps1` | 0 | 工作流与 PowerShell 静态分析通过，3 个静态回归场景通过。 |
| `pwsh -NoProfile -File scripts/test-governance.ps1` 和 `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | 按发布分支实际包含的门禁，分别通过 26 个治理回归、20 个质量门回归。 |
| `git diff --cached --check` | 0 | 实施树通过 Git 空白检查。 |

## Limitations

本地验证针对治理改动。GitHub 的跨平台包矩阵结果由本 PR 的 Checks 提供。首层分支清单与批准分组的一致性由维护者复核。#98 原件覆盖 #93–#98 的最终 `lightweight` 集成验收，更早的原 Feature 部分任务回执仍缺失。
