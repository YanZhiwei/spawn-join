# Harness Phase Context

[English](README.md) | [简体中文](README.zh-CN.md)

`harness/context/` stores only material context with a real impact on future work. Maintain at most
one phase-context file per approved phase, preferably named:

```text
phase-<NN>-<phase-slug>-context.md
```

## Create and update timing

- create after the phase starts and required approvals are obtained;
- update when a finding affects scope, implementation approach, interfaces, dependencies, ownership, acceptance, verification, or risk;
- recheck before phase handoff;
- do not treat the context file as a chat log, progress log, or command-output dump.

## Materiality test

Record something only when omitting it could cause:

- a change to approved scope or implementation approach;
- future phases to rediscover or re-decide the same thing;
- impact on interfaces, dependencies, invariants, or module ownership;
- a change to acceptance criteria or required verification;
- impact on security, privacy, reliability, observability, rollback, or recovery;
- hidden blockers, open assumptions, accepted limitations, or follow-up actions.

## Required provenance

Each material record should link to its source where possible, such as a file, command, test result,
review finding, user decision, or Spec/Plan/Tasks path. Never write credentials, tokens, secrets, or
unnecessary personal information.

## Source-of-truth boundaries

- phase Build files own approved scope, non-goals, acceptance, and planned verification;
- Context files own material findings, decisions, constraints, and open questions;
- `harness/build-log.md` owns actual progress and observed verification evidence;
- Review files own detailed review findings and sign-off status;
- do not fully duplicate these files; use short summaries and links only when necessary.

See the repository [LICENSE](../../LICENSE).
