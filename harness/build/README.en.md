# Harness Build Phase Records

[简体中文](README.md) | [English](README.en.md)

`harness/build/` records one approved, clearly bounded implementation phase. Filenames use:

```text
phase-<NN>-<phase-slug>.md
```

## Required sections

Each phase plan contains at least:

- phase number, title, and status;
- source documents and current Feature;
- goal;
- in-scope work;
- explicit non-goals;
- dependencies and prerequisites;
- expected affected paths or components;
- decisions requiring user confirmation;
- approval gate;
- Red, Green, Refactor, and Verification plans when applicable;
- exact verification commands;
- safety, privacy, reliability, rollback, and recovery considerations when applicable;
- observable acceptance criteria;
- Evidence that must be recorded before completion;
- Handoff or Stop conditions.

## Ownership rules

- `specs/<feature-id>/plan.md` owns the whole Feature's technical solution;
- `specs/<feature-id>/tasks.md` owns the sole execution queue;
- files here own only one phase's approved scope and execution plan;
- a phase plan is not proof of implementation completion and must not turn expected commands into passing results;
- before explicit phase approval, an Agent must stop at planning and review.

If phase scope changes, first update Spec/Plan/Tasks or reopen tasks, then update the phase file; do
not silently expand scope inside a phase file.

See the repository [LICENSE](../../LICENSE).
