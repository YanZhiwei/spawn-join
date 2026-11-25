# AGENTS.md 与项目宪法的职责分工验证

- **delivery_run**: agents-constitution-boundary-20261125
- **lane**: lightweight
- **evidence_path**: .specify/delivery/agents-constitution-boundary-20261125/evidence.md
- **feature_id**: agents-constitution-boundary-20261125
- **phase_id**: lightweight-verification
- **base_revision**: 2b57b86b16278bee16ab80981129455e751b8fce
- **head_revision**: 2b57b86b16278bee16ab80981129455e751b8fce
- **reviewed_head**: 2b57b86b16278bee16ab80981129455e751b8fce
- **merge_base**: 2b57b86b16278bee16ab80981129455e751b8fce
- **original_pr_head**: pending
- **pull_request**: pending
- **content_fingerprint**: a6e9b0a9f402e5ced683fbaf7333623e59e2d9853fd0f2b31031bb34002a330d
- **requirements_fingerprint**: ae292b78bad5b87725bd349eedd2ea01999febb392b4ea3c6f48cc2f8d21ca0c
- **method_identity**: builtin
- **working_directory**: D:/Repos/Github/spawn-join
- **recorded_at**: 2026-11-25T14:10:31+08:00
- **observed_at**: 2026-11-25T14:10:31+08:00
- **result**: pass

## 范围与输入

已跟踪的工作区改动为 [AGENTS.md](../../../AGENTS.md)，从 457 行缩至 133 行。现行权限、公开契约的迁移条件与资源保护要求均有独立复审记录。宪法依旧为 v1.0.0，其原始字节 SHA256 为 `6f98a7926636e9092ec6f9f3aeafe35fa5b741c431f12cebb2ae45fac125f63f`。

本机另修复 Git 忽略的历史计划 `specs/016-deepagents-mcp-config/plan.md` 第 5 行。它现在链接同目录的 `spec.md` 与 `research.md`，保留原运行名称。研究记录明确说明复用了同一运行的 Explore 证据。逆向复原这一行后，整个文件与改前 SHA256 相符。

| 文件 | 变更类型 | 复核时的原始字节 SHA256 |
|---|---|---|
| `AGENTS.md` | 已跟踪，工作区修改 | `e78949ef57d3abbc05fa8b83e3abe3ee01f2e30e4033d1eff6d979b0e00c7b5e` |
| 历史计划 | 本机忽略文件，仅修正文档引用 | `c78be7251395a8fcceda0623885ab3335d891b51a7a5eeffbc0a53082281fe99` |
| 同目录研究记录 | 链接目标 | `3a38dd7a79e001de13c18e8e7287b5c928fc7bf644adb08925e1481342ff7e01` |

同一运行的 `runtime/input-review.json` 记录 Git 模式、实际内容及暂存状态，另显式绑定历史计划、规格和研究记录。需求摘要采用 `runtime/historical-link/requirements.json` 的 18 个来源，用排序的紧凑 UTF-8 JSON 对路径及原始 SHA256 的映射再次取 SHA256。

## 实际验证

| 仓库根目录下的命令 | 退出码 | 结果 |
|---|---:|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 167 份文档、491 个本地链接目标。此前同一历史计划的断链在工作区可复现。 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 个错误、1 条已有的证据时效告警。 |
| `git diff --check` | 0 | 共享差异的空白检查通过。 |
| `git diff --cached --quiet` | 0 | 暂存区为空。 |

本机环境为 Windows，PowerShell 7.6.9。两项质量检查均记录实际目录、命令、退出码、配置、起止时间和相同的起止输入摘要。运行目录 `runtime/historical-link/` 中的 `docs.json` 与 `governance.json` 分别为 `06ec1ea01f70f75bd29720bf9ead903548b6b864ca0361becead3278d1535dca`、`af0137cf25d3b83108ef97cd1d98cf117de0f766e8af8d76adccb50f9a06d50e`。

Quality、Standards、独立 Review 均通过。维护者已接受本次评审并授权完成本地交接。六个维度覆盖需求、可读性、架构、正确性、安全与兼容性、验证有效性。首轮发现的外部写入授权与公开契约迁移条件已分别修订并复核。独立 Review 记录 SHA256 为 `625c56ec7becea90c6af73d6f45e35e44bff6e5cdc006ebb967d326b4ef6eaa5`。

## Limitations

本节记录 2026-11-25T14:10:31+08:00、`reviewed_head=2b57b86b16278bee16ab80981129455e751b8fce` 的本地状态。治理告警来自 `harness/evidence/delivery-v022-upgrade.md`，该旧证据比本次 HEAD 落后 76 次提交。历史 Spec 受仓库 Git 忽略策略管理，其单行修正仅存在于本机。此次范围为文档，未运行 Python 包矩阵或远端 CI。复核时改动未暂存、未提交，尚无对应 PR。
