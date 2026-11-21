# Delivery Evidence — 桌面优先、服务端可替换策略（ADR-0016）

## Lane and scope

- **feature_id**: `desktop-first-package-policy-20261121`
- **phase_id**: `lightweight-close`
- **lane**: Lightweight
- **base_revision**: `e7dde80c2a9389ab588016059d1385e1bd74c754`
- **head_revision**: `working-tree (e7dde80 plus uncommitted worktree)`
- **working_directory**: `D:\Repos\spawn-join`
- **recorded_at**: 2026-11-21
- **result**: pass
- **status**: in-progress（PR 待创建/合并）

## Why Lightweight

本次只新增一条 Proposed 架构决策（ADR-0016）、决策索引行和 AGENTS 架构约束，不创建包、
不改产品代码、不改变运行时行为；对应 Feature 的实现尚未开始。

## Changed paths

- `docs/decisions/engineering/0016-desktop-first-service-ready-packages.md`：新增 ADR-0016
  （桌面档默认、契约可移植、namespace 接缝、依赖分层、Temporal/Celery 定位）。
- `docs/decisions/README.md`：决策索引增加 ADR-0016，状态 `Proposed`。
- `AGENTS.md`：§1.2 增加第 12 条可复用运行时包约束，并链接 ADR-0016。
- `.specify/delivery/desktop-first-package-policy-20261121/evidence.md`：本记录。
- `harness/build-log.md`：登记本次治理变更。

## Verification

| Actual command/check | Exit | Result |
|---|---:|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 77 files / 380 local targets |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 error / 1 历史 freshness warning（`delivery-v022-upgrade.md`，既有） |
| `git diff --check` | 0 | 无空白错误 |

## Review

- 独立只读审查：由不同上下文的只读子代理执行，仅读取工作区 diff、无写权限；不冒充维护者批准。
- 发现 4 个 MINOR 并已处理：ADR-0015 所有权迁移的前置条件与同步修订说明、第二消费者/产品决策
  门槛、AGENTS“进程生命周期”措辞过宽、本记录的审查状态；1 个 NIT（索引 domain 与 ADR 子领域
  显示差异）保留为展示层差异。
- `QUALITY_VERDICT: pass`（docs 77 files / 380 targets；governance 0 error / 1 历史 warning）。
- `STANDARDS_VERDICT: pass`：决策属于 engineering 分类与跨包架构边界，未越权创建包或修改
  产品契约；与 ADR-0010/0015、Constitution III 的复用与副作用所有权不冲突。
- `REVIEW_VERDICT: pass`（独立只读审查，MINOR 修复后复跑文档与治理检查）。

## Limitations and follow-up

- ADR-0016 保持 `Proposed`；转为 `Accepted` 需要维护者批准且在后续 Feature 的 reviewed HEAD
  上完成实现验证。
- 本次不创建 `spawn-join-agent-work`，不新增适配器，不改 `personal-assistant` 行为。
- 未运行包构建/测试矩阵；本次无源码变更。
- 后续 Feature 需要在 Plan 中落实：适配器契约、SQLite schema、ZeroMQ 拓扑、依赖/许可证结论、
  S1–S3 切片与验证命令。
