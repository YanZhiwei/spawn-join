# Delivery Slice Plan — channels-closure-20261108

## Identity and approval

- Delivery run / canonical path: `channels-closure-20261108` /
  `.specify/delivery/channels-closure-20261108/`
- Feature / spec / plan / tasks:
  - `specs/015-llm-channel-closure/spec.md`
  - `specs/015-llm-channel-closure/plan.md`
  - `specs/015-llm-channel-closure/tasks.md`
- Baseline HEAD / relevant working-tree changes: `9f8cb1c78cc254450e2a7557eb88013bc7cdb302`;
  only this run’s local Delivery/spec artifacts are untracked. Product source is clean.
- Design approval: user selected “批准，但去掉 CLI” at the design gate. The plan,
  spec, and ADR-0012 were reduced to library-only closure and re-presented; CLI is
  out of scope. Accepted limitation: live Provider tests cannot run without
  credentials and remain opt-in.
- Artifact policy: ephemeral (`specs/` local-only; Delivery packet local-only).
- Planning timestamp: 2026-11-08

## Execution and publication decision

- `pr_slicing` request: `auto` → resolved to `single` because every slice is
  independently trunk-safe and no flag/integration topology is required.
- Internal review slicing: multiple (5 boundaries)
- Execution mode: single
- Merge mode (legacy alias for execution mode): single
- Publication mode: single
- Publication grouping: one PR for all slices
- Publication authorization: pending — slice approval does not authorize remote publication
- Target branch: `main`
- Integration branch: N/A
- Stack provider: manual (no stack required for `single`)
- Slice merge method: squash
- Final merge method: squash
- Target sync method: N/A
- Merge queue: no (not configured)
- Delete branch after merge: yes
- Freeze integration before final review: yes
- Why this execution/publication choice: all five slices are additive or
  new-package work with no runtime flag and no shared integration branch;
  `.specify/extensions/delivery/delivery-config.yml` requests `pr_slicing: auto`,
  and the project ruleset requires linear history with squash merges. A single
  ordinary feature branch and one eventual PR is the smallest compatible mode.

## Slice table

| ID | Goal | Kind | Depends on | Task IDs | Paths | Trunk-safe | Flag | Merge order | Publication group |
|---|---|---|---|---|---|---|---|---|---|
| S1 | Complete protocol channel contract | foundation | - | T001 | protocol `channels.py`, `errors.py`, `__init__.py`, tests | standalone | - | 1 | P1 |
| S2 | Create channel Distribution foundation | foundation | S1 | T002 | `packages/infra/llm-channel/` scaffold, credentials, error mapping, tests | standalone | - | 2 | P1 |
| S3 | Implement OpenAI/Anthropic transports and factory | behavior | S2 | T003, T004, T005 | channel `_openai.py`, `_anthropic.py`, `factory.py`, tests, README | standalone | - | 3 | P1 |
| S4 | Bridge channel/catalog into model factory | behavior | S1 | T006, T007, T008 | adapter `config.py`, `_catalog.py`, tests, README, quickstart | standalone | - | 4 | P1 |
| S5 | Integrate quality/CI/governance/docs | release | S3, S4 | T009, T010 | quality script, CI matrix, quality profile, AGENTS/README/architecture/ADR | standalone | - | 5 | P1 |

## Publication groups

| Group | Kind | Internal slices | Remote base/head shape | Publication artifact | Issue relation | Authorization |
|---|---|---|---|---|---|---|
| P1 | layer | S1, S2, S3, S4, S5 | ordinary feature branch → `main` | one PR | Closes (after separate publication authorization) | pending |

## Slice details

### S1 — Complete protocol channel contract

- Acceptance outcome: `ChannelStatus.UNSUPPORTED` and
  `ChannelAuthenticationError` exist, are exported, and are covered by the
  existing fake-channel/error/public-API tests; no SDK dependency is added.
- Task IDs: T001.
- Expected paths: modify `channels.py`, `errors.py`, `__init__.py`,
  `test_channels.py`, `test_errors.py`, `test_public_api.py`.
- Trunk-safe: standalone (additive enum member and error subclass).
- Publication group: P1.
- Evidence: existing contract tests enumerate `ChannelStatus`; adding a member
  is additive; no consumer uses exhaustive matching in this repository.
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider`.
- Flag: N/A.
- Integration checkpoints: N/A.
- Risk probes: N/A; pure type/contract change.
- Review focus: public API exactness, backward compatibility, no SDK import.
- Not in this slice: transport implementation (S2/S3), adapter bridge (S4).
- Rollback: revert the additive commit; no data migration.
- Diff budget: 6 files, < 60 changed lines.

### S2 — Create channel Distribution foundation

- Acceptance outcome: `spawn-join-llm-channel` is an independent uv project with
  credentials and SDK error mapping; package imports without LangChain; quality
  gate runs for the new Distribution.
- Task IDs: T002.
- Expected paths: new `packages/infra/llm-channel/{pyproject.toml,uv.lock,LICENSE}`,
  `src/spawn_join_llm_channel/{__init__.py,_credentials.py,_errors.py,py.typed}`,
  `tests/{test_credentials.py,test_errors.py,test_public_api.py,test_package.py}`.
- Trunk-safe: standalone (new Distribution; no existing consumer).
- Publication group: P1.
- Evidence: new package has no import path in existing packages; manifest
  dependency direction is protocol + SDKs only.
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-channel`.
- Flag: N/A.
- Integration checkpoints: N/A.
- Risk probes: `uv lock --check` and import test proving `langchain` is absent.
- Review focus: dependency direction, credential safety, error mapping table,
  package metadata/README placeholders.
- Not in this slice: concrete OpenAI/Anthropic transports (S3).
- Rollback: delete the new package directory and quality/CI entries; no data.
- Diff budget: ~12 files, < 500 changed lines (new package foundation).

### S3 — Implement OpenAI/Anthropic transports and factory

- Acceptance outcome: both concrete channels implement `ping`/`list_models`/
  `aclose`; `create_channel` dispatches by protocol; fake-client tests cover
  success and all error paths; live tests skip without env credentials.
- Task IDs: T003, T004, T005.
- Expected paths: new `_openai.py`, `_anthropic.py`, `factory.py`,
  `test_openai_channel.py`, `test_anthropic_channel.py`, `test_factory.py`,
  `test_live.py`, package READMEs.
- Trunk-safe: standalone (new package code; no existing consumer).
- Publication group: P1.
- Evidence: no existing caller; behavior is exercised only by new tests.
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-channel`.
- Flag: N/A.
- Integration checkpoints: N/A.
- Risk probes: fake 401/403, timeout, connection, 429, 5xx, 404/405, empty page,
  limit/cursor; sentinel-key leakage; client close.
- Review focus: SDK API use, cursor/limit semantics, error mapping, credential
  priority, lifecycle, public API, README accuracy.
- Not in this slice: adapter bridge/catalog (S4), governance updates (S5).
- Rollback: revert new transport files; package foundation remains usable only
  for credential/error mapping.
- Diff budget: ~10 files, ~600 changed lines (new transport + tests + docs).
  Budget exception: new Distribution transport and its regression suite cannot
  be represented as a smaller independently useful slice.

### S4 — Bridge channel/catalog into model factory

- Acceptance outcome: `ChatModelConfig.from_channel`, `ModelSummary.from_model_info`,
  `ModelSummary` inspection fields, and `ModelCatalog.get/names/__len__/__contains__`
  work without network; existing `create_chat_model` and 301 adapter tests remain
  green; offline loop test passes.
- Task IDs: T006, T007, T008.
- Expected paths: modify adapter `config.py`, `_catalog.py`; add
  `test_channel_bridge.py`, `test_catalog_inspection.py`, `test_channel_loop.py`;
  update adapter READMEs and feature `quickstart.md`.
- Trunk-safe: standalone (additive public API and classmethods).
- Publication group: P1.
- Evidence: classmethods reuse existing validators; existing constructor and
  factory signatures unchanged.
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain`.
- Flag: N/A.
- Integration checkpoints: N/A.
- Risk probes: offline loop from fake channel to native model; unknown catalog
  name error; positional/keyword compatibility of `ModelSummary`.
- Review focus: no wrapper, no network, no YAML schema change, public export
  remains exactly five names, optional fields are backward compatible.
- Not in this slice: governance/CI docs (S5).
- Rollback: revert additive classmethods/fields; existing model factory is
  unaffected.
- Diff budget: ~8 files, < 400 changed lines.

### S5 — Integrate quality/CI/governance/docs

- Acceptance outcome: new Distribution is in quality ValidateSet/map, CI matrix,
  and quality profile; AGENTS/README/architecture maps describe seven packages;
  ADR-0012 is indexed as Proposed; docs/governance checks pass; final evidence
  records actual commands and the live-test limitation.
- Task IDs: T009, T010.
- Expected paths: modify `scripts/quality.ps1`, `.github/workflows/quality.yml`,
  `.specify/extensions/quality/quality-config.yml`, `AGENTS.md`, `README.md`,
  `README.en.md`, `docs/architecture/package-boundaries.md`,
  `docs/architecture/repository-map.md`, `docs/decisions/README.md`,
  `docs/decisions/README.en.md`, `docs/decisions/llm-provider/0012-...`;
  write `.specify/delivery/channels-closure-20261108/evidence.md`.
- Trunk-safe: standalone (policy/docs/CI only; no runtime behavior).
- Publication group: P1.
- Evidence: all paths are policy/documentation; quality script/matrix mirror
  existing package entries.
- Target verification: `scripts/quality.ps1 -Check docs`, `-Check governance`,
  full `scripts/quality.ps1`, `git diff --check`.
- Flag: N/A.
- Integration checkpoints: N/A.
- Risk probes: quality script profile coverage (`unprofiled_changed_paths: block`),
  CI matrix package name, docs links, ADR index.
- Review focus: no unprofiled paths, no stale six-package statements, ADR remains
  Proposed until reviewed HEAD, evidence does not claim live tests passed.
- Not in this slice: any new runtime behavior.
- Rollback: revert policy/docs/CI entries; no runtime data.
- Diff budget: ~12 files, < 200 changed lines.

## Coverage and validation

- Task coverage: T001→S1; T002→S2; T003/T004/T005→S3; T006/T007/T008→S4;
  T009/T010→S5. No task is unmapped or spans multiple slices.
- Requirement coverage:
  - FR-001/002/003/004/005/006/007/008 → S1/S2/S3.
  - FR-009/010 → S4.
  - FR-011 (CLI out of scope) → S1–S5 negative coverage.
  - FR-012/013/014 → S2/S3.
  - FR-015 → S5.
  - SC-001–SC-006 → S1–S5 verification.
- Classification coverage: all slices are standalone; no flag or integration
  branch is required. Evidence is the new-package/additive-API nature of each
  slice and absence of existing consumers.
- Behavioral probe coverage: offline fake-client loop → S3/S4; no concurrency or
  recovery probe applies because there is no shared state or background worker.
- Dependency order: S1 → S2 → S3 → S4 → S5; S4 depends only on S1 but follows
  S3 in the linear execution order. Acyclic.
- Publication coverage: every slice maps to P1; no rollup group; P1 has ordinary
  branch → `main`, one PR, publication authorization pending.
- Budget exceptions: S3 exceeds the 400-line warning because it is a new
  Distribution transport plus its full regression suite; accepted for this
  new-package slice. All other slices are within budget.
- Policy compatibility: squash slice/final merges, no merge queue, delete branch,
  linear history; matches repository ruleset and delivery config
  (`pr_slicing: auto`, `merge_policy.final: squash`).
- User authorization boundary: design approval is recorded; slice approval is
  this gate’s separate decision; remote publication/PR remains separately
  unauthorized.
- Open decisions: none. CLI is explicitly out of scope by user design decision.

## Merge and publication plan

- Execution order: S1, S2, S3, S4, S5.
- Ralph branch/topology: ordinary feature branch
  `ralph/015-llm-channel-closure` from `main`/approved baseline; one branch for
  all slices.
- Per-slice merge: N/A for remote publication; internal slice receipts are
  review boundaries on the same branch.
- Publication groups: P1 contains all slices; intended remote target `main`.
- Final rollup: N/A (single publication group).
- Target sync: N/A (no integration branch).
- Queue/freeze: no merge queue; freeze before final review yes; delete branch
  after merge yes.
- Issue closure: no issue is bound; use `Part of`/`Closes` only after separate
  publication authorization.
- Rollback per slice/group: S1 additive revert; S2 new package delete; S3
  transport revert; S4 additive API revert; S5 policy/docs revert. No data
  migration.

## Approval record

- SLICE_PLAN_VERDICT: ready
- SLICE_PLAN_FINGERPRINT: sha256:91077d5be4a5627e97a381e0337a2418e931a9421d36b9800966721189d8d165 (presented slices.md)
- SLICE_APPROVAL: approved
- Approved by: user (conversation, 2026-11-08)
- Choice / accepted risks: “批准执行 (Recommended)”; S3 diff-budget exception accepted;
  live Provider tests remain opt-in/unexecuted without credentials.
- Approved execution mode: single
- Approved publication mode: single
- Approved publication groups: P1 (S1–S5, one ordinary feature branch → `main`)
- Publication authorization: pending — separate remote publication/PR authorization
  is still required
- Approved mode / snapshot: execution=single; publication=single; group=P1;
  spec/plan/tasks/slices fingerprints as presented by the runtime
- Approved at: 2026-11-08

The gate displays this exact plan. After the gate, Delivery’s
`action=record-approval` writer records the actual choice and current snapshot
here; the gate itself does not edit this file. A ready plan, a successful
command, or an agent recommendation is not approval, and context-only approval
cannot authorize Ralph or remote publication.
