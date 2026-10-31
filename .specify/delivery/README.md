# Delivery Evidence and Run Workspace

本目录保存 Delivery 运行的持久证据与按策略保留的运行工作区；配置在
[`../extensions/delivery/delivery-config.yml`](../extensions/delivery/delivery-config.yml)。

## 边界

- Spec 工件按 ADR-0002 保持本地（`specs/` 忽略）；这里的证据必须自包含，不依赖
  本地 Spec 才能理解。
- 每个运行使用 `.specify/delivery/<delivery_run>/`。
- `evidence.md` 始终是持久记录：`feature_id`、`phase_id`、`base_revision`、`head_revision`、
  `working_directory`、`recorded_at`、`result`、limitations，并在 PR 结果确定后由
  `speckit.delivery.close` 写入 `status`、`pull_request`、`outcome_recorded_at` 和
  `merged_revision`（`delivered`），或 `superseded_by` 与 `reason`（`superseded`）。
- 运行工作区（`exploration.md`、`decision-context.md`、`slices.md`、`task-verdicts.yml`、
  `receipts/`、`reviews/`、`pull-request*.md`）受 `artifact_policy` 约束；本项目为
  `ephemeral`，工作区不是长期权威记录。`merged` 运行不删除已交付证据；`abandoned` 与
  `superseded` 运行按 close 契约只保留 `evidence.md`。
- 安装、升级、bootstrap 或手工治理记录不是 delivery run；权威记录放在
  [`harness/evidence/`](../../harness/evidence/)，不在本目录维护第二份副本。
- 每个通过 gate 的任务写一个 receipt：`receipts/<task-id>.md`。
- 不自动 push、merge、发布或修改远端设置；这些动作仍需用户明确授权。
- `RALPH_TASK_GATE: PASS` 只有在验收证据、允许路径、当前 `HEAD`、Quality Gate 和
  Standards Review 全部有效时才能写入。

## Receipt Template

```text
# <TASK-ID> — <title>

- feature: <feature-id>
- base_revision: <sha>
- head_revision: <sha>
- changed_paths: <paths>
- commands: <commands and exit codes>
- quality_verdict: QUALITY_VERDICT: pass
- standards_verdict: STANDARDS_VERDICT: pass
- ralph_task_gate: RALPH_TASK_GATE: PASS
- residual_risks: <none or list>
- recorded_at: <YYYY-MM-DD>
```

## Evidence Template

`evidence.md` 使用 `harness/evidence` 的必填字段（`feature_id`、`phase_id`、
`base_revision`、`head_revision`、`working_directory`、`recorded_at`、`result`、
limitations），并链接实际 PR、CI 运行和 ADR。Completion 只描述当前 `HEAD` 能支持的结论；
PR 结果必须写入 `status` 字段，缺少或矛盾的结果不算收口。
