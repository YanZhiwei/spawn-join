# Harness Code Review Records

[简体中文](README.md) | [English](README.en.md)

`harness/code_review/` stores detailed review findings that must survive across phases. Ordinary chat
comments cannot replace blockers, fix status, and re-review results recorded here.

Recommended filenames:

```text
review-<phase-id>-<short-slug>.md
```

## Required finding fields

Each review finding contains at least:

- a unique Finding ID;
- severity: Blocker, Major, Minor, or Note;
- associated Spec, Plan, Task, phase, and changed paths;
- observed problem and reproducible evidence;
- impact: correctness, standards, architecture, security, reliability, or evidence completeness;
- proposed fix and explicit non-goals;
- status: Open, In Progress, Resolved, Accepted Risk, or Rejected;
- post-fix re-review command, revision, and result;
- residual risk and next step.

## Review rules

- review must target real base/head and the outgoing diff;
- passing tests cannot replace review of DRY, module ownership, directory ownership, public API, and dependency direction;
- a phase cannot be declared complete while a Blocker remains open;
- findings requiring code or configuration fixes must be written back to `tasks.md` or reopen an existing task;
- after a new commit or changed scope, old reviews must be reconfirmed rather than reused directly.

Review records own "findings and sign-off status"; they do not own test results, full command logs,
or the Feature execution queue.

## Consumer verification

Select real-consumer checks for the actual change, not a new universal gate or unrelated matrix:

| Changed surface | Actual boundary to verify | What this cannot establish |
|---|---|---|
| Package/build/public exports | Reuse the [quality entry point](../../docs/development/quality-gates.md#artifact-isolation) for isolated wheel installation/import; verify affected callers when contracts change | Passing source-environment tests do not prove the distribution works |
| CLI, configuration, SDK/adapter boundary | Exercise the affected real entry with focused cases; keep unit tests offline and separately record permissions/environment/results for real external services | Passing mocks/helpers do not establish protocol or resource-lifecycle correctness |
| Generated commands, Workflow, role handoffs | Separate installation identity, fixture/structural checks, and real host handoffs; explicitly record unexecuted handoffs as gaps | Installation or fixtures do not establish model behavior evals or a full SD/Ralph run |

Reuse current valid evidence; add focused verification only for a named risk/gap. Unavailable
environments are not-run or blocked, not invented success. Pre-implementation requirements/design
review still uses existing Clarify/Analyze/gates. Agent interpretation is not user approval, and
pre-implementation review does not replace independent code Review.

## Closure and reusable learning

During existing Docs Sync/closure, select reusable lessons from current re-reviewed findings and
material context. Usually 0–3 are enough; explicitly note none apply when appropriate rather than
creating rules or documents to meet a quota.

- Each lesson identifies its trigger, verified conclusion, applicable package/version, evidence
  or Finding ID, limitations, and recheck conditions. Unproven hypotheses stay with the investigation
  owner; a one-off environmental correlation does not become a global constraint.
- API usage belongs in the owning package documentation; composition belongs in existing
  architecture/development docs. Only stable long-term cross-implementation decisions enter ADRs.
  Merge with existing knowledge, not a new Learning/KnowledgeBase database or copied logs.
- Update documentation within the approved scope alongside the change. Scope/design expansion
  returns to its owner and existing queue/approval process; lesson extraction does not authorize
  incidental code changes, deletion of safeguards, or new enforcement mechanisms.
- Recheck lessons when interfaces, dependencies, platforms, or source implementations change.
  Correct/mark stale guidance without rewriting historical evidence. Reference updated paths and
  reasons in the existing closure record; lessons do not own task closure or review exemptions.

See the repository [LICENSE](../../LICENSE).
