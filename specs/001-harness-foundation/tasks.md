---

description: "Task list for the Harness foundation feature"

---

# Tasks: Harness Foundation

**Input**: Design documents from `/specs/001-harness-foundation/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `quickstart.md`

**Tests**: Documentation validation is required; no Python tests are requested for this documentation-only Feature.

**Organization**: Tasks are grouped by user story and keep each artifact's ownership explicit.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the Harness directory skeleton without adding runtime behavior.

- [x] T001 [P] Create the Harness ownership entry point in `harness/README.md`.
- [x] T002 [P] Create phase-plan guidance in `harness/build/README.md`.
- [x] T003 [P] Create material-context guidance in `harness/context/README.md`.
- [x] T004 [P] Create review-record guidance in `harness/code_review/README.md`.
- [x] T005 [P] Create verification-evidence guidance in `harness/evidence/README.md`.
- [x] T006 Create the append-oriented observed progress log in `harness/build-log.md`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish source-of-truth boundaries before phase records are used.

**Checkpoint**: Harness artifact ownership is documented and does not replace Constitution,
AGENTS, Spec, Plan, or Tasks.

- [x] T007 Update `docs/architecture/repository-map.md` to record the actual `harness/` directory.
- [x] T008 Update `AGENTS.md` with the stable Harness boundary and current Feature baseline.
- [x] T009 Update `README.md` with the simplified Harness navigation entry.

---

## Phase 3: User Story 1 - Locate the authoritative project context (Priority: P1) 🎯 MVP

**Goal**: A maintainer can reach every governance and Harness owner from the repository root.

**Independent Test**: Follow the links from `AGENTS.md`, `README.md`, and `harness/README.md`; all
local targets resolve and no full directory tree or package table is duplicated in the entry files.

### Implementation for User Story 1

- [x] T010 [US1] Add the source-of-truth ownership table and lifecycle links in `harness/README.md`.
- [x] T011 [US1] Add cross-links from `harness/README.md` to `AGENTS.md`, Constitution,
  architecture docs, and the active Feature artifacts.

**Checkpoint**: The Harness navigation is independently usable from the repository root.

---

## Phase 4: User Story 2 - Plan and gate one implementation phase (Priority: P1)

**Goal**: A future phase has a bounded plan, approval gate, acceptance criteria, verification plan,
and stop condition.

**Independent Test**: Read `harness/build/README.md` and confirm it defines the required fields and
prevents implementation from starting before approval.

### Implementation for User Story 2

- [x] T012 [US2] Define phase-plan ownership, required sections, approval gates, and stop conditions in `harness/build/README.md`.
- [x] T013 [US2] Define phase context creation timing and materiality rules in `harness/context/README.md`.

**Checkpoint**: A future phase can be created without duplicating the Feature Plan or Tasks.

---

## Phase 5: User Story 3 - Preserve material context and observed evidence (Priority: P2)

**Goal**: Reviewers can distinguish planned work, material context, review findings, and actual
verification results.

**Independent Test**: Read the log, review, and evidence guidance and confirm each record requires
real provenance, limitations, and blocker states where applicable.

### Implementation for User Story 3

- [x] T014 [US3] Define append-oriented observed progress and evidence fields in `harness/build-log.md`.
- [x] T015 [US3] Define review finding severity, remediation, status, and provenance in `harness/code_review/README.md`.
- [x] T016 [US3] Define base/head, changed paths, command, exit code, result, and limitation fields in `harness/evidence/README.md`.

**Checkpoint**: The Harness cannot present planned or unavailable checks as passing evidence.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Validate documentation integrity and record the actual outcome.

- [x] T017 [P] Run the local Markdown link check from `specs/001-harness-foundation/quickstart.md`.
- [x] T018 [P] Run `git diff --check` and confirm no trailing whitespace in the changed documents.
- [x] T019 Confirm that only documentation, Harness, and Feature artifacts changed; record the verification result in `harness/build-log.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; creates the Harness documentation skeleton.
- **Foundational (Phase 2)**: Depends on Setup; updates repository navigation and boundaries.
- **User Story 1 (Phase 3)**: Depends on Foundational; is the MVP navigation slice.
- **User Story 2 (Phase 4)**: Depends on the Harness entry point from User Story 1.
- **User Story 3 (Phase 5)**: Depends on the ownership rules from User Stories 1 and 2.
- **Polish (Phase 6)**: Depends on all desired Harness records being present.

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on another user story after Phase 2.
- **User Story 2 (P1)**: Depends on the navigation and ownership contract from User Story 1.
- **User Story 3 (P2)**: Depends on the ownership and phase-gating contract from User Stories 1 and 2.

### Parallel Opportunities

- T001-T005 can run in parallel because they create separate Harness files.
- T017 and T018 can run in parallel after all documentation files exist.
- User Story 2 and User Story 3 must not be treated as independent until User Story 1's ownership
  links are complete.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Setup and Foundational phases.
2. Complete User Story 1 navigation and ownership links.
3. Run the link and diff checks.
4. Stop and review before adding executable hooks or quality gates.

### Incremental Delivery

1. Add Harness documentation and ownership boundaries.
2. Add phase-plan and context guidance.
3. Add evidence and review guidance.
4. Introduce executable validators only in a later Feature after stable quality commands exist.

## Notes

- `[P]` tasks touch different files and have no dependency on incomplete work.
- `tasks.md` remains the only execution queue for this Feature.
- No task authorizes source-code changes, dependencies, branch operations, commits, pushes,
  deployments, credentials, or external-system writes.
