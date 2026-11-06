# SpawnJoin Harness

[English](README.md) | [简体中文](README.zh-CN.md)

Harness is SpawnJoin's phase execution and evidence-record layer. It keeps "approved phase plans",
"material context", "review findings", and "actual verification results" separate so maintainers can
distinguish plans, observations, and conclusions.

**Contents**

- [Scope](#scope)
- [Source-of-truth boundaries](#source-of-truth-boundaries)
- [Lifecycle](#lifecycle)
- [Directory guide](#directory-guide)
- [Related project documents](#related-project-documents)
- [Current limitations](#current-limitations)

## Scope

Harness is a documentation convention and traceable record layer; it does not automatically create
branches, commits, pushes, deployments, or external writes. Python Quality Gates add independent
verification scripts and CI configuration; they explicitly run mechanical checks and are not
automatic Harness or Spec Kit hooks. Only checks that actually ran can provide passing evidence.

## Source-of-truth boundaries

| Artifact | Owns | Must not replace |
|---|---|---|
| `.specify/memory/constitution.md` | non-negotiable project principles | Harness phase state and command results |
| `AGENTS.md` | Agent working conventions, stable boundaries, and navigation | Feature plans and actual evidence |
| `specs/<feature-id>/spec.md` | user scenarios, requirements, scope, and success criteria | actual implementation results |
| `specs/<feature-id>/plan.md` | Feature technical layout, design decisions, and verification approach | phase execution logs |
| `specs/<feature-id>/tasks.md` | the Feature's sole execution queue | Harness evidence or review sign-off |
| `docs/decisions/` | domain-classified long-term decision rationale, key design, and necessary diagrams | Spec/Plan/Tasks, formal contracts, or actual verification evidence |
| `harness/build/` | approved scope and implementation plan for one phase | the Feature's overall Plan/Tasks |
| `harness/context/` | material findings, decisions, and open items within a phase | step-by-step progress logs or full command output |
| `harness/code_review/` | detailed review findings, fix status, and re-review results | automated test results themselves |
| `harness/evidence/` | verification records bound to real revision and changed paths | pre-planned commands |
| `harness/build-log.md` | progress that actually occurred and observed results | pass conclusions for checks not executed |

## Lifecycle

```text
Spec / Plan / Tasks
        │
        ▼
approved phase plan
        │
        ├── phase context
        ├── implementation
        ├── review findings
        └── observed evidence
                │
                ▼
          build log / handoff
```

`tasks.md` remains the sole execution queue. Harness files must not create a second task system by
copying a task list.

## Directory guide

- [`build/`](build/README.md): phase plans and human approval boundaries; one record per phase.
- [`context/`](context/README.md): only material context affecting future decisions, scope, interfaces, verification, or risk.
- [`code_review/`](code_review/README.md): detailed review findings, severity, fixes, and re-review status.
- [`evidence/`](evidence/README.md): actual commands, working directory, exit codes, results, revision, and limitations.
- [`build-log.md`](build-log.md): append-only actual progress; never disguise plans as facts that already happened.

## Related project documents

- [Constitution](../.specify/memory/constitution.md)
- [Agent rules](../AGENTS.md)
- [Repository map](../docs/architecture/repository-map.md)
- [Package boundaries](../docs/architecture/package-boundaries.md)
- [Architecture decisions](../docs/decisions/README.md)
- [Project technical diagrams](../docs/development/technical-diagrams.md)
- [Python quality gates](../docs/development/quality-gates.md)
- Local historical Feature: `specs/001-harness-foundation/` (untracked by ADR-0002, local only; a clean checkout is not guaranteed to contain it)
- Local quality-gate tasks: `specs/002-python-quality-gates/tasks.md` (Git-ignored; a clean checkout is not guaranteed to contain it)

## Current limitations

- Black/isort/Ruff/Pyright/pytest and CI configuration exist; remote CI has run, the Ruleset
  configures a required `Quality Gate`, and a temporary failing PR was verified as `BLOCKED`.
- `.specify/extensions.yml` registers Bundle v0.4.3 components, but automatic hooks are disabled and
  no hook is registered; [Delivery installation](../docs/development/spec-kit-delivery.md) does not
  mean Ralph or the full delivery loop has executed.
- `scripts/check-governance.ps1` validates Harness/Delivery evidence metadata, truncated revisions,
  build-log references, the ADR index, Spec/Tasks consistency, Delivery safety settings, and the
  automatic-hook switch; freshness warns when non-documentation paths change, and semantic judgment
  still requires human review.
- If `HEAD` or outgoing paths change, old evidence must be reconfirmed and must not be reused directly.

See the repository [LICENSE](../LICENSE).
