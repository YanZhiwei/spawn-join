# Harness Code Review Records

[English](README.md) | [简体中文](README.zh-CN.md)

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

See the repository [LICENSE](../../LICENSE).
