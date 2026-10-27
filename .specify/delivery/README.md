# Delivery Evidence and Ralph Receipts

本目录保存 Delivery 路线的durable 证据与 Ralph receipt；配置在
[`../extensions/delivery/delivery-config.yml`](../extensions/delivery/delivery-config.yml)。

## 边界

- Spec 工件按 ADR-0002 保持本地（`specs/` 忽略）；这里的证据必须自包含，不依赖
  本地 Spec 才能理解。
- 每个 Feature 使用 `.specify/delivery/<feature-id>/`。
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
limitations），并链接实际 PR、CI 运行和 ADR。Completion 只描述当前 `HEAD` 能支持的结论。
