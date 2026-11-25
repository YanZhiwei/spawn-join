# 工程治理改动的整合验证

- feature_id: engineering-governance-integration
- phase_id: publication-verification
- base_revision: 5e223ab835f8880d9c79f5a5f5f8b0aae792e9f6
- head_revision: 11380328efd1f63f1569c8c3281dc5c0156c346f
- working_directory: `%TEMP%/sj-governance-20261125`（Windows 独立 Git 工作树）
- recorded_at: 2026-11-25T21:03:11+08:00
- result: pass

这次单 PR 汇总已完成的仓库治理改动。验收对象是 `11380328efd1f63f1569c8c3281dc5c0156c346f` 相对 #99 合并提交的完整实施差异，共 13 个文件，Git 树为 `e44cdc95f3eb51ece5fa75b30b34fb8ce84e47fc`。采用 `git diff --no-ext-diff --no-renames --binary --full-index <base> <head> --` 获得的原始字节 SHA-256 为 `3a41fe8fed86977ec0c15d3e060dba175703ff103bd2baf78a7e957d105ff515`。

## 公开交付的内容

- 根指南从 457 行缩为 133 行。Agent 从指南找到工作入口、授权条件和验证方法。面向全部贡献者的原则继续由 v1.0.0 宪法维护。指南原运行的本地交接时间、审查提交、两项已解决发现和历史 Spec 修正均保存在[当时的验收快照](../../.specify/delivery/agents-constitution-boundary-20261125/evidence.md)。
- `quality.ps1` 与 `check-governance.ps1` 共用 Markdown 检查。默认检查可提交的共享文档和锚点。传入 `-FeatureDir` 后，另查选中目录的文档，governance 还核对其 Spec 和 Tasks。Git 忽略的本地 Spec 可继续用于开发。用法见[质量门说明](../../docs/development/quality-gates.md#local-entry-point)。
- governance 从包 manifest 读取 Distribution 名称，对照 GitHub Actions 矩阵、Spec Kit 包级质量配置、PowerShell 的 `-Package` 参数和包描述表。遗漏、冗余和重名都有具体来源。
- 已从 GitHub 核对 #82 的 PR head `b3f60525ef4b869b7b8b4a2d0a4db8be614ee0a9`、合并提交 `5739be137b3a95caa7507f2db6f48e32fc6d5d57` 及时间 `2026-11-21T15:58:57Z`。两者的完整树同为 `550438defed56dd0545e870ab470704dafde3907`。新增 Close 信息保留原验证正文的全部字节。ADR-0016 在索引和正文中仍为 `Proposed`。[#82 的交付档案](../../.specify/delivery/desktop-first-package-policy-20261121/evidence.md) · [ADR-0016](../../docs/decisions/engineering/0016-desktop-first-service-ready-packages.md)

## 实际验证

以下检查从上述工作树的仓库根目录运行，使用同一份实施内容。PowerShell 脚本均用 `pwsh -NoProfile -File` 调用。

| 检查 | 退出码 | 观察结果 |
| --- | --- | --- |
| `scripts/quality.ps1 -Check docs` | 0 | 201 份共享 Markdown，0 份本地 Feature 文档，检查了 1028 个本地链接。 |
| `scripts/quality.ps1 -Check governance` | 0 | 9 个 Distribution 的名称核对通过，0 个错误。两条历史时效提醒见下文。 |
| `scripts/quality.ps1 -Check docs -FeatureDir specs/016-deepagents-mcp-config`，以及同目录的 `-Check governance` | 0 | 201 份共享 Markdown、9 份本地文档，检查了 1037 个链接。 历史 `plan.md` 的 SHA-256 为 `c78be7251395a8fcceda0623885ab3335d891b51a7a5eeffbc0a53082281fe99`。 |
| `scripts/quality.ps1 -Check static` 与 `scripts/test-static.ps1` | 0 | 工作流和 PowerShell 静态检查通过，3 个静态回归场景通过。 |
| `scripts/test-governance.ps1`、`scripts/test-quality.ps1`、`scripts/test-pr-evidence.ps1` | 0 | 分别通过 43、26、45 个回归场景。 |
| `git diff --check`（完整发布差异） | 0 | Git 空白检查通过。 |

独立评审按需求、代码质量、架构、正确性、安全与兼容性、测试有效性核对实际实施树。六个维度全部通过。已逐项复核指南中的外部写入授权和公共契约迁移要求（`G-AUTH-01`、`G-MIG-01`），两项均已解决。

## 限制

两条 Harness 时效告警分别来自早期 `delivery-v022-upgrade.md` 和 #99 的 `pr-delivery-evidence-publication.md`。#99 经 squash 合并，原审查提交不在新 `main` 的祖先链上。已核实 #99 的最终 PR head `6463037` 与合并提交 `5e223ab` 的完整文件树相同，实施提交 `6928289` 至合并结果只相差当次验收文件和 build-log 条目。[#99 合并记录](https://github.com/YanZhiwei/spawn-join/pull/99)

历史 Feature 的 9 个 Markdown 文件仅供本机显式检查，公开检出可以直接运行默认检查。GitHub 跨平台包矩阵和最终 `Quality Gate` 的结果由本发布 PR 的 Checks 记录。
