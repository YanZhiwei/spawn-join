# Feature Specification: Harness Foundation

**Feature Branch**: `main` (feature directory: `001-harness-foundation`; no branch was created)

**Created**: 2026-10-26

**Status**: Draft

**Input**: User description: "开始增加 Harness"

## User Scenarios & Testing

### User Story 1 - Locate the authoritative project context (Priority: P1)

As a maintainer or coding agent, I want to know where project rules, package boundaries,
feature plans, phase plans, and verification evidence belong, so that I can use the current
repository state without guessing or maintaining duplicate sources of truth.

**Why this priority**: Without clear ownership, later phases can record the same decision in
multiple files and allow the directory map, plan, and evidence to drift apart.

**Independent Test**: Start from the repository root and follow the links in `AGENTS.md` and
`harness/README.md`; every governance artifact has one stated owner and every referenced path
is either present or explicitly marked as created by a later Feature.

**Acceptance Scenarios**:

1. **Given** a maintainer starts at the repository root, **when** they open `AGENTS.md`,
   **then** they can reach the repository map, package boundaries, Constitution, and Harness
   ownership documents without searching the source tree.
2. **Given** two documents describe the same concern, **when** the ownership table is checked,
   **then** exactly one document is identified as authoritative and the other contains only a
   reference or stable summary.

---

### User Story 2 - Plan and gate one implementation phase (Priority: P1)

As a maintainer, I want one bounded phase to have an explicit scope, non-goals, approval gate,
acceptance criteria, and verification plan, so that an agent cannot silently start unrelated
work or move to the next phase without evidence.

**Why this priority**: Small, human-gated phases are the minimum useful Harness behavior and
directly support the project's incremental-delivery principles.

**Independent Test**: Inspect a phase file under `harness/build/` and confirm it identifies its
source inputs, scope, non-goals, dependencies, approval gate, acceptance criteria, verification
commands, and stop condition.

**Acceptance Scenarios**:

1. **Given** a phase has not been approved, **when** an agent reads its phase file, **then** the
   file directs the agent to stop before implementation.
2. **Given** a phase is approved, **when** implementation begins, **then** its context and
   evidence records use the phase identifier and do not replace the Feature's Spec, Plan, or
   Tasks as the source of intent.

---

### User Story 3 - Preserve material context and observed evidence (Priority: P2)

As a reviewer or future maintainer, I want material decisions, review findings, and actual
verification results to be recorded separately from plans, so that I can distinguish what was
intended from what really happened and reproduce the result after the repository evolves.

**Why this priority**: Reliable handoff and review require evidence tied to the real diff,
without turning context files into transcripts or rewriting failed attempts.

**Independent Test**: Read the Harness ownership documents and an initial build log entry; the
record format distinguishes planned work, material context, review findings, and observed
commands/results, including limitations and blockers.

**Acceptance Scenarios**:

1. **Given** a verification command is unavailable or fails, **when** the result is recorded,
   **then** it is marked as blocked or failed with the reason rather than reported as passed.
2. **Given** the repository `HEAD` or outgoing paths change after evidence is recorded, **when**
   the evidence is reused, **then** it is marked stale and must be re-confirmed.

## Edge Cases

- The `specs/` directory may not exist before the first Feature; the Harness must not treat a
  planned Feature path as current repository evidence.
- A phase may stop before implementation because of an unresolved decision, missing permission,
  unavailable dependency, or failed verification; the build log must preserve that blocker.
- A phase can produce no code changes and still require context or review evidence when it changes
  governance or repository configuration.
- A directory or package may move while a phase is in progress; evidence must record the actual
  changed paths and the repository map must be updated only after the move is approved.
- A user may request only a planning or documentation artifact; that request must not authorize
  application code, dependency, branch, commit, push, deployment, or external-system changes.

## Requirements

### Functional Requirements

- **FR-001**: The repository MUST provide a `harness/README.md` that defines Harness scope,
  lifecycle, artifact ownership, and explicit non-goals.
- **FR-002**: The repository MUST provide separate locations for phase plans, phase context,
  code-review records, verification evidence, and observed build progress.
- **FR-003**: Each Harness artifact type MUST state what it owns and what it must not duplicate
  from Constitution, AGENTS, Spec, Plan, Tasks, or other evidence.
- **FR-004**: Phase-plan guidance MUST require scope, non-goals, dependencies, approval gate,
  acceptance criteria, verification commands, and a stop/handoff condition.
- **FR-005**: Context guidance MUST restrict records to material decisions, discoveries,
  constraints, unresolved questions, accepted limitations, and future-useful provenance.
- **FR-006**: Evidence guidance MUST require the actual commands, working directory, exit codes,
  results, base/head revisions, changed paths, limitations, and blockers.
- **FR-007**: The Harness MUST distinguish planned, observed, failed, skipped, and blocked states;
  it MUST NOT convert an intended command into passing evidence.
- **FR-008**: `AGENTS.md`, `README.md`, and the architecture documents MUST link to the Harness
  ownership entry point without maintaining a second full Harness structure.
- **FR-009**: This Feature MUST NOT add runtime code, Python dependencies, CI workflows, hook
  executors, automatic commits, branch changes, pushes, deployments, or external-system writes.

### Key Entities

- **Phase Plan**: The approved scope and verification plan for one bounded implementation phase.
- **Phase Context**: Material discoveries, decisions, constraints, and unresolved questions that
  future work needs to understand.
- **Build Log Entry**: An append-oriented record of observed implementation progress and results.
- **Review Finding**: A correctness, standards, architecture, or evidence issue with severity,
  status, remediation, and provenance.
- **Evidence Record**: Verification bound to a real repository revision, changed paths, command,
  environment, exit code, result, and limitations.

## Success Criteria

### Measurable Outcomes

- **SC-001**: A maintainer can locate the owner of each Harness artifact from the repository root
  by following at most two Markdown links.
- **SC-002**: The Harness contains no duplicate full directory tree or duplicate package-boundary
  table outside the designated architecture documents.
- **SC-003**: Every phase-plan example and guidance section names an approval gate, acceptance
  criteria, verification plan, and stop condition.
- **SC-004**: Every evidence example names base/head, changed paths, commands, working directory,
  exit code, result, and limitations.
- **SC-005**: A documentation-only validation run completes without modifying Python source,
  package manifests, dependencies, branches, commits, or external systems.

## Assumptions

- The current repository uses Markdown files and Git as its first Harness persistence layer.
- Spec Kit remains the source of truth for Feature Spec, Plan, and Tasks artifacts.
- `tasks.md` remains the only execution queue for a Feature; Harness files provide phase context
  and evidence but do not replace task completion state.
- Automated quality tools and Spec Kit extension hooks will be introduced by later Features after
  the repository has stable commands to execute.
- The initial Harness is intentionally documentation-first and does not claim to enforce rules
  until executable validators exist.
