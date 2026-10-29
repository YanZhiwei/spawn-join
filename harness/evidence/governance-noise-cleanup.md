# Evidence — Governance noise cleanup (Lightweight)

## Identity and scope

- **route**: Lightweight（治理检查与历史记录元数据，无运行时行为变化）
- **feature_id**: 不适用（独立治理改动）
- **phase_id**: `governance-noise-cleanup`
- **task_id**: 不适用（无 Ralph receipt）
- **base_revision**: `dab15fe2b7d3f3c1108ad32a3a671e65d80e0642`
- **head_revision**: `working-tree (dab15fe plus uncommitted worktree)`
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-29
- **environment**: Windows；PowerShell 7；Python 3.13.5（验证用解释器）
- **result**: pass

## Changed paths

- `scripts/check-governance.ps1`：支持 `- superseded_by: <仓库内证据路径>`；目标不存在时
  报错，存在时只抑制该记录的 freshness warning，不改变其他校验。
- `scripts/test-governance.ps1`：新增“superseded evidence 抑制 warning”和“缺失目标报错”
  两个场景（21 → 23）。
- 四份 `phase-01-*` evidence：指向覆盖同一关注点的较新记录，保留原始结论与 head。
- `docs/development/quality-gates.md`：说明 `superseded_by` 语义与场景数。
- 本机 `.specify/feature.json`（Git 忽略，未提交）：移除指向已完成 Feature 006 的陈旧指针。

## Verification

| Actual command/check | Exit | Result |
|---|---:|---|
| `scripts/test-governance.ps1` | 0 | 23 scenarios |
| `scripts/quality.ps1 -Check governance` | 0 | 0 error；warning 由 5 降到 1（当前交付记录，落后 1 个提交） |
| `scripts/quality.ps1 -Check static` | 0 | 0 failing check |
| `scripts/test-static.ps1` | 0 | 3 scenarios |
| `scripts/quality.ps1 -Check docs` | 0 | 63 files / 167 targets |
| `git diff --check` | 0 | 无空白错误 |

## Limitations

- 剩余 1 条 warning 是当前 `delivery-release-installation.md` 落后于 HEAD；它记录的是当前
  安装状态，不应标记 superseded，应在合并后按既有做法重新锚定。
- 本次只改治理脚本、文档与 evidence 元数据，未重跑四包构建/安装矩阵；PR CI 会执行完整检查。
- `feature.json` 是机器本地状态，删除后由下一次 Feature 切换重新生成；不进入 Git。
