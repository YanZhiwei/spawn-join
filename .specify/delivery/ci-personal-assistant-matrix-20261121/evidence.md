# Delivery Evidence — CI 矩阵补齐个人助理包

## Lane and scope

- **feature_id**: `ci-personal-assistant-matrix-20261121`
- **phase_id**: `lightweight-close`
- **lane**: Lightweight
- **base_revision**: `c2de6aed93c563c8830d45936425389f7c04294a`
- **head_revision**: `working-tree (c2de6ae plus uncommitted worktree)`
- **working_directory**: `D:\Repos\spawn-join`
- **recorded_at**: 2026-11-21
- **result**: pass

## Why Lightweight

本次只补 CI 矩阵条目并同步当前状态文档的计数，不改变产品行为、公共 API、依赖、
持久化或安全边界；新条目复用一个已经存在且能通过的包级 quality profile。

## Problem and evidence

- `.github/workflows/quality.yml` 的 `matrix.package` 只列 7 个 Distribution；
  `grep personal-assistant .github/workflows/*.yml` 为 0 命中。
- `.specify/extensions/quality/quality-config.yml` 已有 `spawn-join-personal-assistant`
  profile（match `packages/apps/personal-assistant/**`）。
- 因此该包在 PR 上不会被构建、测试或隔离安装，`Quality Gate` 仍可能为绿——这与
  “每个 Distribution 独立质量边界”的项目契约不一致。
- 当前状态文档仍写“七个保留包 / 21 组合”，已落后于第 8 个包落地的事实。

## Changed paths

- `.github/workflows/quality.yml`：`matrix.package` 增加 `spawn-join-personal-assistant`，
  矩阵从 7×3 变为 8×3（24 组合）。
- `docs/development/quality-gates.md`：包数量、矩阵组合数与 CI 覆盖表述由七个/21 更新为
  八个/24，并说明 `apps` 分组同样使用独立锁文件、质量 Profile、隔离安装和 CI 矩阵。
- `docs/development/spec-kit-delivery.md`：Quality Profile 计数由“七个保留包…十个 Profile”
  更新为“八个保留包…十一个 Profile”。
- `AGENTS.md`：当前配置基线快照更新为 2026-11-21、八个保留包（`core` 3、`infra` 4、
  `apps` 1），并改为“所有保留包（含 `apps` 分组）已具备……CI 矩阵”。
- `.specify/delivery/ci-personal-assistant-matrix-20261121/evidence.md`：本记录。
- `harness/build-log.md`：登记本次 Lightweight 变更。

## Verification

| Actual command/check | Exit | Result |
|---|---:|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-personal-assistant` | 0 | `uv lock --check` / `uv sync --locked`、Black/isort、Ruff、Pyright strict、60 用例、构建、隔离安装 + `pip check` + 隔离导入全部通过 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | 0 | 0 failing check（含 workflow 静态分析） |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 76 files / 372 local targets |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 error / 1 历史 freshness warning（`delivery-v022-upgrade.md`，既有） |
| `git diff --check` | 0 | 无空白错误 |

## Review

- 独立只读审查：由不同上下文的只读子代理执行，仅读取工作区 diff、未获得写权限；不冒充人工评审。
- 发现 1 个 MINOR：`harness/build-log.md` 写成“远端矩阵由 PR CI 实测”，与 evidence 中
  “远端尚未执行”矛盾；已改为“将由 PR CI 实测”并复跑文档检查。
- NIT 已确认不在本次范围：`readme-dual-audience-20261121` 的 2 个未跟踪正文文件不纳入本次
  提交；Linux/Python 3.14 新组合只能由远端 CI 验证，保持为已声明残余风险。
- `QUALITY_VERDICT: pass`（以上命令实际执行）。
- `STANDARDS_VERDICT: pass`：CI 与文档分别属于 `project-automation` 与
  `governance-and-documentation` 的既有拥有者，未扩大到产品源码、依赖或公共契约。
- `REVIEW_VERDICT: pass`（独立只读审查，MINOR 已修复）。

## Limitations and follow-up

- 远端 24 作业矩阵必须在 push 后由 PR CI 实测；本次本地只验证了新矩阵条目所使用的命令。
- 未新增依赖、未修改 Action 的固定 SHA、未改质量 Profile 或根工具配置。
- 历史 evidence 中的“七个包”是当时快照，按 freshness 规则保留原文，不回写。
