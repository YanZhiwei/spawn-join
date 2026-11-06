# Harness Phase Context

[简体中文](README.md) | [English](README.en.md)

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

## Investigation continuity

- Keep investigation questions, relevant hypotheses, and evidence in the existing Explore packet
  or Bug assessment. Context holds only material summaries and exact references, not another
  investigation file, state machine, or queue.
- For a material hypothesis, identify its trigger, source version/snapshot, a test or observation
  distinguishing candidate explanations, support/rejection rationale, and remaining question/owner.
  Without discriminating verification it remains unresolved, not a confirmed root cause.
- Preserve rejected hypotheses and evidence; recheck version applicability on resume rather than
  rediscovering old proposals. Multiple summaries of one upstream origin are one evidence source;
  do not resolve conflicting evidence by vote.
- Stop research when evidence supports the current decision and material conflicts are resolved
  or explicitly blocking. Exhausting time/resources does not establish readiness. Return critical
  gaps to their owner; handle non-critical limitations through the existing gate, not a new approval.

## Phase handoff

Use the [role navigation](../../docs/architecture/repository-map.md#role-based-reading) to locate
sources. SD handoffs still use the installed
[Phase handoff](../../.specify/extensions/delivery/templates/exploration.md#phase-handoff) and the
receiving role's native packet, not a new receipt format. Lightweight work without an SD run needs
only proportionate scope, sources, and verification; do not create a run or Feature to fill fields.

A real handoff identifies the receiver/question, allowed operations/paths, exact approved sources
and actual approval state, required paths/sections/symbols with authority and relevance, conditional
reading triggers, existing input/requirements snapshot, expected evidence, and return conditions.
Separate user requirements, agent interpretation, hypotheses, and open questions; do not reinterpret
existing decisions by rewriting their summary.

The receiver verifies required sources and identity before judging, then connects sources to its
conclusion in its native output. Missing, stale, or conflicting critical inputs return an exact gap
and recovery path. Authorized read-only investigation may continue, but the gap is not a pass.
Routine dispatch references the approved snapshot; material changes follow the original owner's
freshness/approval process rather than relabeling old hashes to fit new content.

## Source-of-truth boundaries

- phase Build files own approved scope, non-goals, acceptance, and planned verification;
- Context files own material findings, decisions, constraints, and open questions;
- `harness/build-log.md` owns actual progress and observed verification evidence;
- Review files own detailed review findings and sign-off status;
- do not fully duplicate these files; use short summaries and links only when necessary.

See the repository [LICENSE](../../LICENSE).
