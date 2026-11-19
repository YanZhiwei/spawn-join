<!-- DELIVERY_CURRENT_OUTCOME_BEGIN -->
## Current delivery outcome

- **delivery_run**: deepagents-p1-continuation-20261115
- **lane**: feature
- **status**: delivered
- **outcome**: merged
- **provider**: github
- **repository**: yanzhiwei/spawn-join
- **number**: 57
- **pull_request**: https://github.com/yanzhiwei/spawn-join/pull/57
- **original_pr_head**: 0bcc15e99a6d8a38307da6858e4e8eb95f69c3b7
- **base_revision**: 1d52d48cfb9e824af470d5eaf481a88fe371228e
- **merged_revision**: a06eb2e3e6b4c4ad9ace1bdee040a15a81139797
- **effective_head**: a06eb2e3e6b4c4ad9ace1bdee040a15a81139797
- **merged_at**: 2026-11-19T15:09:06Z
- **observed_at**: 2026-11-19T15:10:00Z
- **outcome_recorded_at**: 2026-11-19T15:10:00Z
<!-- DELIVERY_CURRENT_OUTCOME_END -->

# Delivery evidence: deepagents-p1-continuation-20261115

- feature_id: deepagents-p1-continuation-20261115
- phase_id: close
- base_revision: 1d52d48cfb9e824af470d5eaf481a88fe371228e
- head_revision: a06eb2e3e6b4c4ad9ace1bdee040a15a81139797
- working_directory: C:/Users/YanZh/AppData/Local/Temp/opencode/sj-pr57
- recorded_at: 2026-11-19
- result: pass

## Scope delivered

Continuation of the already-implemented DeepAgents official P1 surface in
`spawn-join-agent-deepagents`, published as PR #57 and squash-merged to `main` as
`a06eb2e3`. The delivery contains:

1. Rubric (beta): `RubricConfiguration`, the `allow_experimental_rubric` gate, native
   `RubricMiddleware` support with the exclusive-with-`rubric=` rule, `RubricReport`, the
   beta warning and the `rubric` experimental feature.
2. Backend/permission reporting: `backend_kind()`, `PermissionReport`
   (allow/deny/interrupt/other), `ResourceReport.backend_kind` and `.permissions`.
3. HITL helpers: `PendingInterrupt`, `pending_interrupts()` (exported from the package
   root), decision builders, and `resume_batched` / `resume_per_call` / `resume_with`.
4. Docs and decisions: Chinese/English package README, `examples/p1_capabilities.py`,
   ADR-0014 (`Proposed`), and this run packet.

## Branch history

| Commit | Purpose |
|---|---|
| `0bcc15e` | original PR #57 feature commit (2026-11-08) |
| `48dbbf9` | merge of `origin/main` (`1d52d48`) into the continuation branch |
| `035d618` | continuation fixes: `pending_interrupts` export, native rubric gate, `other` counter, docs/ADR |
| `3636d33` | first evidence attempt, withdrawn before merge (see Limitations) |
| `3ef80cd` | removes that evidence file and repoints ADR-0014 at the run packet directory |
| `a06eb2e3` | squash merge of PR #57 into `main` |

## Commands and results

Executed from the working directory above unless noted.

| Command | Exit | Result |
|---|---|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents` on `035d618` | 0 | Black/isort clean (36 files), Ruff clean, Pyright strict 0 errors, 204 passed, docs 70 files / 351 local targets, wheel build + isolated install + `python -I` import pass |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents -Check test` on `48dbbf9` (merge only, WIP stashed) | 0 | 187 passed; confirms the merge itself did not regress behavior |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents -Check type` on `48dbbf9` | 0 | Pyright strict 0 errors |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` on `3ef80cd` | 0 | 0 errors, 1 pre-existing warning (`harness/evidence/delivery-v022-upgrade.md` head_revision behind HEAD) |
| `git diff --check` | 0 | no whitespace errors |
| GitHub Actions run 44550428387 (head `3636d33`) | fail | `Governance and gate regression` rejected the withdrawn evidence file; all 21 package jobs passed |
| GitHub Actions run on head `3ef80cd` | pass | every package job plus `Governance and gate regression` and `Quality Gate` passed |
| `gh pr merge 57 --squash --delete-branch` | 0 | merged as `a06eb2e3`; branch deleted |

Conflict resolution when merging `1d52d48` was limited to `__init__.py`, `errors.py` and
`tests/test_public_api.py`, and kept both surfaces (P1 rubric/HITL and main's LLM error
normalization) with `__all__` kept sorted.

## Type-gate repair in this run

Clearing 25 Pyright strict errors required three file-local changes that preserved behavior:

- `interrupts.py`: `hasattr`/`getattr` duck typing replaced by a `runtime_checkable`
  `_InterruptLike` protocol plus `_interrupt_items()` / `_interrupt_parts()` narrowers.
- `rubric.py`: validation moved behind `object`-typed `_require_chat_model()` /
  `_require_positive_iterations()`; rejection of non-model graders and of
  boolean/float/string/non-positive `max_iterations` is unchanged and tested.
- `tests/test_rubric.py`: three untyped lambdas became `_discard_assembly`.

## Limitations

- **No independent review.** No six-dimension Review or Standards review was executed for
  this continuation, and the run has no runtime workspace (`runtime/`), so there are no
  review receipts, reservations, or attempt counters. Verification is the full package
  quality gate, the repository governance check, passing CI, and an operator diff review.
  This must not be reported as an independent review.
- **Withdrawn evidence attempt.** Commit `3636d33` added an `evidence.md` that used short
  SHAs and non-schema field names, which failed `check-governance.ps1` in CI. It was
  removed in `3ef80cd` because a pre-merge `head_revision` would become unreachable after
  the branch deletion; this file is the replacement, bound to the merged revision.
- **ADR-0014 remains `Proposed`.** It records the P1 public boundary (including the
  intentional `PermissionReport`/`ResourceReport`/`AssemblyReport` field-order change and
  the advice to construct those reports with keyword arguments). Accepting it requires a
  reviewed HEAD that matches the implementation.
- **Deliberate narrowing.** `pending_interrupts(state)` no longer returns `()` for a
  non-`Mapping` `state` (declared `Mapping[str, Any]`); malformed `__interrupt__` payloads
  still yield an empty tuple.
- **Unverified behavior.** Real rubric grader execution against a provider structured-output
  model, HITL approval persistence/checkpointer ownership, and remote async/profile
  behavior were not executed in this environment.
- **Freshness.** The pre-existing warning about `harness/evidence/delivery-v022-upgrade.md`
  being behind HEAD is unrelated to this run and was not changed here.
