# Exploration Packet — DeepAgents P1 continuation

- Delivery run: `deepagents-p1-continuation-20261115`
- Lane: Feature continuation (existing PR #57)
- Branch: `feat/013-deepagents-p1-cont`
- Base: `15f5c03` at continuation start; re-anchored to `1d52d48` after merging latest
  `main` on 2026-11-19
- Original branch head: `0bcc15e` (single feature commit, 2026-11-08)
- Working directory: `C:\Users\YanZh\AppData\Local\Temp\opencode\sj-pr57`
- Artifact policy: ephemeral (`specs/` ignored; this packet is the durable record)

## Why this run exists

PR #57 implemented DeepAgents official P1 capabilities but was never attached to a Delivery
run, and its branch is behind `main`. The user asked to continue the open P1 work before
the conflicting error-normalization PR (#59). This run verifies, repairs, reviews, and
closes that already-implemented scope; it does not add a new product direction.

The original local Spec/Plan/Tasks were ephemeral and are no longer present. This packet
reconstructs the approved scope from the existing PR description, the committed source,
tests, README, and the governing ADRs. It does not claim the missing artifacts were
reviewed earlier.

## Implemented scope under verification

The branch adds one additive P1 surface to `spawn-join-agent-deepagents`:

1. **Rubric grading (beta)**
   - `RubricConfiguration` (grader model, optional prompt/tools, `max_iterations`,
     `on_evaluation`) with `RubricConfigurationError`.
   - `SupervisorSpec.allow_experimental_rubric` + `rubric`; native `RubricMiddleware`
     is appended to the supervisor stack only when configured and explicitly allowed.
   - `RubricReport` in `AssemblyReport`, plus a management warning and
     `experimental_features=("rubric",)`.
2. **Backend and permission visibility**
   - `backend_kind()` classifies host backends (`local_shell`, `sandbox`, `state`, `store`,
     `composite`, `filesystem`, `context_hub`, `custom`, `default_state`).
   - `PermissionReport` counts allow/deny/interrupt rules without exposing paths or rules;
     `ResourceReport` adds `backend_kind` and `permissions`.
3. **HITL helpers**
   - `PendingInterrupt`, `pending_interrupts()`, `approve_decision`, `edit_decision`,
     `reject_decision`, `respond_decision`, `resume_batched`, `resume_per_call`,
     `resume_with`.
   - Helpers only shape native LangGraph `Command`/HITL payloads; they do not approve,
     persist, or promise exactly-once behavior.
4. **Docs and example**
   - Chinese/English package README sections and offline `examples/p1_capabilities.py`.
   - Public `__all__` exports, including the continuation fix for `pending_interrupts`,
     which the README example already imported from the package root.

## Current evidence

| Check | Result |
|---|---|
| `origin/main...HEAD` diff before continuation fixes | 14 files, 720 insertions, 1 deletion |
| Merge of latest `main` (`1d52d48`) into the continuation branch | merge commit `48dbbf9`; conflicts in `__init__.py`, `errors.py`, `tests/test_public_api.py` resolved by keeping both the P1 rubric/HITL surface and main's LLM error normalization |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents` (committed merge head `48dbbf9`, WIP stashed) | exit 0; pyright 0 errors; 187 passed |
| Same full gate with the continuation fixes applied (2026-11-19) | exit 0; Black/isort/Ruff clean, pyright 0 errors, **204 passed**, build and isolated install pass |
| Type-gate repair required by this run | 25 pyright strict errors cleared in `interrupts.py`, `rubric.py`, `tests/test_rubric.py`; no behavior change to assembled middleware, reports, or decision payloads |
| Public API gap found before review | README imports `pending_interrupts` from the package root, but `__init__.py` did not export it; fixed in this run |
| Delivery record | Previously absent; this packet and the evidence record are new |

## Continuation on 2026-11-19

- Latest `main` (`1d52d48`, containing the v0.4.7 bundle upgrade and the agent middleware
  package) was merged into the continuation branch; the PR was conflict-free afterwards.
- The uncommitted continuation fixes were then brought under the full package gate, which
  required clearing 25 pyright strict errors. The repairs kept the observable contract:
  `pending_interrupts` still returns an empty tuple for malformed `__interrupt__` payloads
  and still reads mapping- and object-shaped interrupts; rubric validation still rejects
  non-model graders and non-positive/boolean/non-integer `max_iterations`.
- One deliberate narrowing: `pending_interrupts(state)` no longer tolerates a non-`Mapping`
  `state` value (the parameter is declared `Mapping[str, Any]`); it raises instead of
  returning `()`. Malformed payload handling is unchanged.

## Alternatives considered

1. **Reopen the P1 design as a new Feature and regenerate Spec/Plan/Tasks** — rejected for
   this continuation because the implementation already exists, the original artifacts are
   unavailable, and regenerating them now would fabricate prior approvals rather than
   verify the real diff.
2. **Treat the work as Lightweight** — rejected: it adds public API and a beta middleware
   seam; behavior and contract review are required.
3. **Fold P1 into the error-normalization PR #59** — rejected: independent scope, and
   combining would make review/rollback harder.
4. **Add a new ADR before verification** — deferred: first verify the implemented boundary
   and let review decide whether ADR-0010/0012 coverage is sufficient or a new ADR is
   required.

## Excluded scope

- Real rubric grader execution against a live/provider structured-output model; tests
  cover assembly and report behavior only.
- HITL approval persistence, checkpointer ownership, queueing, exactly-once semantics, or
  retry policy.
- New backend implementations, permission engines, sandbox/context-hub lifecycle changes.
- Error normalization (#59), channel transport (#58, already merged), CLI, or Agent
  assembly changes outside the P1 surface above.
- Reopening P0 behavior or changing existing public signatures; all additions are optional
  fields, new types, or new functions.

## Risks and open questions

- The P1 public surface is additive but includes a beta seam; review must confirm the beta
  gate cannot be bypassed and reports do not leak paths/permissions.
- `pending_interrupts()` normalizes loosely typed native payloads; malformed shapes should
  not crash or fabricate approvals.
- ADR coverage is unproven: ADR-0012 remains `Proposed`, and no P1-specific decision exists.
  Review should state whether a revision note or a new ADR is required before merge.
- The branch predates the current `main`; merge and full-gate evidence must be refreshed at
  the final head.
- Live provider behavior and real HITL execution remain unverified in this environment.

## User scope decision

The user asked to continue the existing open P1 PR after #58, following the recommendation
to take #57 first and rebase #59 afterwards. No scope expansion beyond the already
implemented P1 surface was requested.
