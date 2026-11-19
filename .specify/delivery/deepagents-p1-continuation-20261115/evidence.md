# Delivery evidence: deepagents-p1-continuation-20261115

- delivery_run: deepagents-p1-continuation-20261115
- lane: feature (continuation of the already-implemented PR #57 scope)
- base_revision: 1d52d48 (latest `main` merged into the continuation branch)
- verified_head: 035d618 (continuation fixes committed on top of merge `48dbbf9`)
- original_pr_head: 0bcc15e
- branch: `feat/013-deepagents-p1-cont` (published to `origin/feat/013-deepagents-p1`)
- working_directory: `C:/Users/YanZh/AppData/Local/Temp/opencode/sj-pr57`
- recorded_at: 2026-11-19
- result: pass
- status: verified; publication authorized, merge pending at record time

## Scope verified

One additive P1 surface in `spawn-join-agent-deepagents`, on top of the original PR #57 commit:

1. Rubric (beta): `RubricConfiguration` + `allow_experimental_rubric` gate, native
   `RubricMiddleware` support, `RubricReport`, beta warning and `experimental_features`.
2. Backend/permission reporting: `backend_kind()`, `PermissionReport` (allow/deny/
   interrupt/other), `ResourceReport.backend_kind` and `.permissions`.
3. HITL helpers: `PendingInterrupt`, `pending_interrupts()`, decision builders, and
   `resume_batched` / `resume_per_call` / `resume_with`.
4. Docs and example: Chinese/English package README, `examples/p1_capabilities.py`,
   ADR-0014 (Proposed).

Continuation work in this run: export `pending_interrupts` from the package root, add the
native-rubric beta gate and the "not both" exclusion, add the `other` permission counter,
and clear the type gate.

## Commands and results

All commands ran from the working directory above, on `035d618`.

| Command | Exit | Result |
|---|---|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents` | 0 | Black/isort clean (36 files unchanged), Ruff clean, Pyright strict 0 errors, 204 passed, docs 70 files / 351 local targets, wheel build + isolated install + `python -I` import pass |
| `uv lock --check --directory packages/infra/agent-deepagents` | 0 | lock consistent (82 packages) |
| `git diff --check` | 0 | no whitespace errors |

Merge context: `origin/main` (`1d52d48`) was merged into the continuation branch as
`48dbbf9`. Conflicts were limited to `__init__.py`, `errors.py` and
`tests/test_public_api.py`, and were resolved by keeping both surfaces (P1 rubric/HITL and
main's LLM error normalization) with `__all__` kept sorted.

## Type-gate repair in this run

Clearing 25 Pyright strict errors required three file-local changes with no behavior change
to assembled middleware, reports, or decision payloads:

- `interrupts.py`: replaced `hasattr`/`getattr` duck typing with a `runtime_checkable`
  `_InterruptLike` protocol plus `_interrupt_items()` / `_interrupt_parts()` narrowers.
- `rubric.py`: validation moved behind `object`-typed `_require_chat_model()` /
  `_require_positive_iterations()`; rejection of non-model graders and of
  boolean/float/string/non-positive `max_iterations` is unchanged and covered.
- `tests/test_rubric.py`: three untyped lambdas became `_discard_assembly`.

One deliberate narrowing: `pending_interrupts(state)` no longer returns `()` for a
non-`Mapping` `state`; the declared parameter type is `Mapping[str, Any]`. Malformed
`__interrupt__` payloads still yield an empty tuple.

## Limitations and residual risk

- No independent six-dimension review or Standards review was executed for this
  continuation. Verification here is the full package quality gate plus an operator diff
  review; that is weaker than an independent review and must not be reported as one.
- ADR-0014 remains `Proposed`. It records the P1 public boundary, including the intentional
  `PermissionReport`/`ResourceReport`/`AssemblyReport` field-order change and the advice to
  construct those reports with keyword arguments.
- Real rubric grader execution against a provider structured-output model, HITL approval
  persistence/checkpointer ownership, and remote async/profile behavior remain unverified.
- The `deepagents-p1-continuation-20261115` run has no runtime workspace (`runtime/`); it was
  driven inline, so there are no runtime receipts, reservations, or attempt counters.
