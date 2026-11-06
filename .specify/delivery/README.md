# Delivery Evidence and Run Workspace

[English](README.md) | [简体中文](README.zh-CN.md)

This directory stores durable Delivery run evidence and the run workspace retained according to
policy; configuration lives in
[`../extensions/delivery/delivery-config.yml`](../extensions/delivery/delivery-config.yml).

## Boundaries

- Spec artifacts stay local under ADR-0002 (`specs/` is ignored); evidence here must be self-contained and understandable without local Specs.
- Each run uses `.specify/delivery/<delivery_run>/`.
- `evidence.md` is always the durable record: `feature_id`, `phase_id`, `base_revision`, `head_revision`, `working_directory`, `recorded_at`, `result`, limitations, and after the PR outcome is known, `speckit.delivery.close` writes `status`, `pull_request`, `outcome_recorded_at`, and `merged_revision` (`delivered`), or `superseded_by` and `reason` (`superseded`).
- The run workspace (`exploration.md`, `decision-context.md`, `slices.md`, `task-verdicts.yml`, `receipts/`, `reviews/`, `pull-request*.md`) follows `artifact_policy`; this project uses `ephemeral`, so the workspace is not the long-term authority. `merged` runs do not delete delivered evidence; `abandoned` and `superseded` runs retain only `evidence.md` per the close contract.
- Installation, upgrade, bootstrap, or manual governance records are not delivery runs; the authoritative record belongs in [`harness/evidence/`](../../harness/evidence/), with no second copy here.
- Every gated task writes one receipt: `receipts/<task-id>.md`.
- Never automatically push, merge, publish, or change remote settings; those actions still require explicit user authorization.
- `RALPH_TASK_GATE: PASS` may be written only when acceptance evidence, allowed paths, current `HEAD`, Quality Gate, and Standards Review are all valid.

## Receipt template

```text
# <TASK-ID> — <title>

- feature: <feature-id>
- base_revision: <sha>
- head_revision: <sha>
- changed_paths: <paths>
- commands: <commands and exit codes>
- quality_verdict: QUALITY_VERDICT: pass
- standards_verdict: STANDARDS_VERDICT: pass
- independent_review_verdict: REVIEW_VERDICT: pass
- ralph_task_gate: RALPH_TASK_GATE: PASS
- residual_risks: <none or list>
- recorded_at: <YYYY-MM-DD>
```

Task closure requires current Quality, Standards, and independent six-dimensional Review evidence;
the Review receipt must bind the exact current Quality and Standards results. A stale or blocked
result cannot close a task.

## Evidence template

`evidence.md` uses the required `harness/evidence` fields (`feature_id`, `phase_id`, `base_revision`,
`head_revision`, `working_directory`, `recorded_at`, `result`, limitations) and links the actual PR,
CI runs, and ADRs. Completion describes only conclusions supported by the current `HEAD`; the PR
outcome must be written into `status`, and a missing or contradictory result does not count as closed.

See the repository [LICENSE](../../LICENSE).
