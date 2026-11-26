# Evidence — ADR 生命周期收口 (Lightweight)

## Identity and scope

- **route**: Lightweight（只更新 ADR 记录、决策索引与文档状态；无产品源码、公共契约或运行时行为变化）
- **feature_id**: 不适用（独立治理收口，不是新的 Feature/Bugfix run）
- **phase_id**: `adr-lifecycle-closure`
- **base_revision**: `79425090f442506663c0024bde02c62f1f5c7ea6`
- **head_revision**: `working-tree (7942509 plus uncommitted worktree)`
- **working_directory**: `D:\Repos\spawn-join`
- **recorded_at**: 2026-11-26
- **environment**: Windows；PowerShell 7.6.10；uv 0.13.10（winget 用户级安装）；`UV_PYTHON=3.13`；Git for Windows
- **result**: pass
- **lane**: lightweight
- **decision_record**: 用户于 2026-11-26 明确选择接受 ADR-0011、ADR-0012、ADR-0016；ADR-0009、ADR-0014 经独立六维 Review 后均判定 `blocked`，保持 `Proposed`
- **delivery_run**: `adr-lifecycle-closure-20261126`

## Why Lightweight

本次只修改长期决策记录、决策索引和安装说明中的状态描述，不改变任何 Distribution、公共 API、
测试、依赖或运行时行为。没有创建新的 Feature 工件；范围限于文档事实与维护者已明确记录的
ADR 接受决定。

## Changed paths

- `docs/decisions/engineering/0011-common-helper-package.md`：`Proposed` → `Accepted`，记录接受人和日期。
- `docs/decisions/agent/0012-deepagents-official-p0.md`：`Proposed` → `Accepted`，记录接受人和日期。
- `docs/decisions/engineering/0016-desktop-first-service-ready-packages.md`：`Proposed` → `Accepted`；
  修正“尚未实现任何包、适配器或迁移”的过时描述，改为 `agent-work` 已交付、`personal-assistant`
  已迁移，并明确服务端适配器仍未实现。
- `docs/decisions/llm-provider/0009-model-metadata-and-sync.md`：保留 `Proposed`；修正过时实现描述，
  并记录 2026-11-26 独立 Review 的 `blocked` 结论（F1–F5）。
- `docs/decisions/agent/0014-deepagents-p1-capabilities.md`：保留 `Proposed`；记录独立 Review 的
  `blocked` 结论（F1–F3 等），并更新对 ADR-0012 已接受状态的引用。
- `docs/decisions/README.md`：同步 ADR-0011、ADR-0012、ADR-0016 的索引状态。
- `docs/development/spec-kit-delivery.md`：更新 ADR-0016 已接受的说明。
- `.specify/delivery/adr-lifecycle-closure-20261126/evidence.md`：本记录。
- `.specify/delivery/adr-lifecycle-closure-20261126/reviews/adr-0009-review.md`：ADR-0009 独立 Review 报告。
- `.specify/delivery/adr-lifecycle-closure-20261126/reviews/adr-0014-review.md`：ADR-0014 独立 Review 报告。
- `harness/build-log.md`：登记本次治理变更。

## Verification

| Actual command/check | Working directory | Exit | Result |
|---|---|---:|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | `D:\Repos\spawn-join` | 0 | 207 个共享 Markdown、0 个本地 Feature 文档、1041 个本地链接通过 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | `D:\Repos\spawn-join` | 0 | 0 error、3 条既有历史时效 warning；9 个 Distribution 的覆盖清单一致 |
| `git diff --check` | `D:\Repos\spawn-join` | 0 | 无空白错误 |
| `delivery_runtime.py init --run adr-lifecycle-closure-20261126 --lane lightweight --json` | `D:\Repos\spawn-join` | 0 | `status: active`，`phase: intake`，`blockers: []` |

说明：`governance` 首次运行时因 PATH 中没有 `uv` 而被阻断；安装 uv 后使用
`UV_PYTHON=3.13` 重跑，避免 uv 默认选择 Python 3.15 导致 `pyyaml` 本地编译失败。
后续两项检查均在最终工作区内容上执行。

## Decision evidence

- ADR-0011：接受依据为已合并实现、独立六维 Review、PR #47 的远端 CI；具体历史见
  `.specify/delivery/common-foundation-20261107/evidence.md`。
- ADR-0012：接受依据为 P0 独立六维 Review；4 个阻塞项在合并前修复。
- ADR-0016：接受的是“桌面优先、服务端可替换”的长期策略；实现证据为
  `.specify/delivery/agent-work-desktop-20261122/slices.md` 与
  `.specify/delivery/agent-work-main-integration-20261123/evidence.md`（PR #93–#98）。
- ADR-0009、ADR-0014：实现均已存在；2026-11-26 的独立六维 Review 均判定 `blocked`，
  因此保持 `Proposed`。ADR-0009 的 blocker 是上游/`model.yaml` 校验错误未转换为稳定错误与
  退出码（F1），另有 dry-run 副作用、缓存路径、渠道差异和依赖声明不一致（F2–F5）。
  ADR-0014 的 blocker 是原生 rubric beta gate 只覆盖 supervisor 作用域（F1），另有
  `tool_count` 读取错误（F2）和 `SupervisorSpec` 位置参数兼容性破坏（F3）。

## Independent reviews

| ADR | Verdict | Report |
|---|---|---|
| ADR-0009 | `blocked` / keep Proposed | `.specify/delivery/adr-lifecycle-closure-20261126/reviews/adr-0009-review.md` |
| ADR-0014 | `blocked` / keep Proposed | `.specify/delivery/adr-lifecycle-closure-20261126/reviews/adr-0014-review.md` |

两位 reviewer 均为独立只读子代理，在 HEAD `7942509` 上执行；未修改任何 tracked 文件。
Review 实际运行了 ADR-0009 相关的 34 + 115 + 58 个测试和 ADR-0014 相关的 45 + 48 个测试，
均通过；失败点来自契约矛盾、未覆盖路径和 1 个 blocker 级别的错误处理/gate 缺口。

## Limitations

- ADR-0009 与 ADR-0014 的独立 Review 结论均为 `blocked`；两者保持 `Proposed`，修复 blocker/major
  发现并复评后才能接受。修复工作不在本次 Lightweight 范围内。
- 两份独立 Review 只运行了目标测试，没有在 `7942509` 上执行完整包质量门、隔离安装、docs/governance
  或远端 CI；这些检查需在后续 Bugfix/复评时补齐。
- ADR-0012 的接受引用历史 P0 独立 Review，本次没有重新审查产品代码。
- ADR-0016 只验证了桌面默认档的实现与迁移；服务端 Postgres/MQ 适配器、多租户和 Temporal
  集成仍未实现，接受策略不代表这些能力已完成。
- `governance` 的 3 条 warning 均为既有历史证据时效问题
  （`delivery-v022-upgrade.md`、`engineering-governance-integration.md`、
  `pr-delivery-evidence-publication.md`），与本次改动无关。
- 本机仍缺 `specify`、`gh`、`node`、`codegraph`；本次是纯文档/决策改动，未运行包测试、
  构建或远端 CI。
- 本次未提交、未 push、未创建或合并 PR；这些动作需要单独授权。
