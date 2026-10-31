# Delivery slice plan

## Identity and approval

- Delivery run / canonical path: `008-langchain-first-llm-runtime` / `.specify/delivery/008-langchain-first-llm-runtime/`
- Feature / spec / plan / tasks: `specs/008-langchain-first-llm-runtime/spec.md`, `plan.md`, `tasks.md`
- Baseline HEAD / relevant working-tree changes: `353af49cf9db6014b7af0437a3f9dc0dd651437c`
  (`origin/main`); new ADR-0006/ADR-0007, ADR index rows, Delivery policy/config updates,
  exploration/decision-context, local ignored `specs/008-*`
- Design approval: user approved the plan on 2026-10-31 after the `ChannelConfig.name` correction
  ("开始"); user then required default Slice delivery ("默认开启"), which reopens the delivery
  boundary and adds S0
- Artifact policy: tracked Delivery records; `specs/` is local and Git-ignored
- Planning timestamp: 2026-10-31

## Merge decision

- PR slicing: auto
- Merge mode: stacked
- Target branch: `main`
- Integration branch: N/A
- Stack provider: manual
- Slice merge method: squash
- Final merge method: N/A (stacked; each slice is squash-merged)
- Target sync method: merge
- Merge queue: no
- Delete branch after merge: yes
- Freeze integration before final review: yes
- Why this mode: `delivery-config.yml` now sets `pr_slicing: "auto"` and every slice is classified
  `standalone` (S1–S3 are provisional until their boundary checks); the slice command therefore
  selects stacked. `stack_provider: manual` and `use_queue: false` mean no native stack or merge
  queue is claimed. `merge_policy.final: squash` is reserved for an integration rollup and is
  unused in stacked mode. S0 is a bootstrap policy PR because `main` still has `pr_slicing: "off"`
  until S0 lands.

## Slice table

| ID | Goal | Kind | Depends on | Task IDs | Paths | Trunk-safe | Flag | Merge order |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | Enable default Slice delivery and record the policy | governance | - | T001–T002 | `.specify/extensions/delivery/delivery-config.yml`, `docs/decisions/engineering/0007-default-slice-delivery.md`, `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md`, `.specify/delivery/008-langchain-first-llm-runtime/{exploration,decision-context,slices,evidence}.md`, `task-verdicts.yml`, `receipts/{T001,T002}.md`, `docs/decisions/README.md`, `AGENTS.md`, `docs/development/spec-kit-delivery.md`, `docs/decisions/engineering/0004-release-managed-delivery-installation.md` | standalone (verified at gate) | - | 1 |
| S1 | Core options/channel/errors contract, tests and README | foundation + behavior | S0 | T003–T010 | `packages/core/llm-provider/`, `.specify/delivery/008-langchain-first-llm-runtime/evidence.md` | standalone (provisional) | - | 2 |
| S2 | LangChain model factory, tests, adapter README and architecture docs | behavior + documentation | S1 | T011–T017 | `packages/infra/llm-provider-langchain/`, `docs/architecture/package-boundaries.md`, `AGENTS.md`, `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` | standalone (provisional) | - | 3 |
| S3 | Full gates, quickstart validation, evidence and hygiene | verification | S2 | T018–T020 | `.specify/delivery/008-langchain-first-llm-runtime/evidence.md`, `specs/008-langchain-first-llm-runtime/quickstart.md` | standalone (provisional) | - | 4 |

The base classification is `standalone`; S1–S3 remain hypotheses until the declared boundary checks
run. S0 is verified by the current gate's docs/governance/YAML receipts.

## Slice details

### S0 — Default Slice delivery policy

- Acceptance outcome: `pr_slicing` is `auto`; ADR-0007 is Accepted and indexed; AGENTS and
  Delivery docs match; ADR-0004 keeps its historical single-PR note and links ADR-0007.
- Task IDs: T001, T002
- Expected paths: `.specify/extensions/delivery/delivery-config.yml` (modify);
  `docs/decisions/engineering/0007-default-slice-delivery.md` (new);
  `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` (new, planning artifact);
  `.specify/delivery/008-langchain-first-llm-runtime/{exploration,decision-context,slices,evidence}.md`,
  `task-verdicts.yml`, and `receipts/{T001,T002}.md` (new, planning/task-state artifacts);
  `docs/decisions/README.md` (modify);
  `AGENTS.md` (modify); `docs/development/spec-kit-delivery.md` (modify);
  `docs/decisions/engineering/0004-release-managed-delivery-installation.md` (modify)
- Trunk-safe: standalone
- Evidence: policy/docs only; no runtime source or dependency change. Target verification is
  `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` and `-Check governance`.
- Target verification: the two commands above; also parse
  `.specify/extensions/delivery/delivery-config.yml` with PyYAML and assert
  `pr_slicing == "auto"`, `stack_provider == "manual"`, and `use_queue is False`.
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: policy text, ADR lifecycle, no claim that stacked PRs or merge queue are native.
- Not in this slice: runtime code, adapter dependencies, package READMEs.
- Rollback: revert the S0 commit; restore `pr_slicing: "off"` and remove ADR-0007, ADR-0006 and the
  S0 Delivery planning/task-state records.
- Diff budget: 14 files, approximately 900 changed lines including `evidence.md`, `task-verdicts.yml`
  and task receipts (5 modified + 9 new). This exceeds `slice_warn_lines: 400`; the accepted reason
  is that the planning/ADR/evidence records are required by S1–S3 and the policy cannot be reviewed
  without its ADR. S0 is a bootstrap single PR because the policy is not active on `main` until it
  lands.

### S1 — Core contract

- Acceptance outcome: `spawn-join-llm-provider` exposes only options/channel/errors; channel config
  includes `name`; fake channel distinguishes all outcomes; core quality gate passes.
- Task IDs: T003, T004, T005, T006, T007, T008, T009, T010
- Expected paths: `packages/core/llm-provider/src/spawn_join_llm_provider/{errors,options,channels,__init__}.py`
  (new/modify); remove `abstractions/__init__.py`;
  `packages/core/llm-provider/tests/{test_errors,test_options,test_channels,test_public_api}.py`
  (new) and `test_package.py` (modify); `packages/core/llm-provider/{pyproject.toml,README.md}`
  (modify); `.specify/delivery/008-langchain-first-llm-runtime/evidence.md` (new baseline)
- Trunk-safe: standalone (provisional)
- Evidence: the adapter remains a skeleton and does not import the new core symbols; both package
  quality gates can pass on this prefix. The declared verification must run before claiming
  standalone.
- Target verification:
  - `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider`
  - `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain`
  - `pwsh -NoProfile -File scripts/quality.ps1 -Check docs`
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: exact 20 exports, no message/Provider types, channel `name` validation, fake
  channel outcome matrix, no LangChain dependency.
- Not in this slice: adapter factory, adapter README, architecture package-boundary updates.
- Rollback: revert the S1 commit; the adapter skeleton remains valid.
- Diff budget: approximately 13 files; likely more than 400 changed lines because contract tests
  are included. Exception reason: the core contract and its tests are the smallest independently
  testable prefix; splitting source and tests would violate the same-task test rule.

### S2 — LangChain model factory

- Acceptance outcome: three explicit protocol configs construct `BaseChatModel` instances offline;
  options map correctly; API key is masked; adapter quality gate passes; docs match.
- Task IDs: T011, T012, T013, T014, T015, T016, T017
- Expected paths:
  `packages/infra/llm-provider-langchain/src/spawn_join_llm_provider_langchain/{config,factory,__init__}.py`
  (new/modify); remove `providers/` namespace;
  `packages/infra/llm-provider-langchain/tests/{test_validation,test_factory,test_public_api}.py`
  (new) and `test_package.py` (modify);
  `packages/infra/llm-provider-langchain/{pyproject.toml,README.md,uv.lock}` (modify);
  `docs/architecture/package-boundaries.md` and `AGENTS.md` (modify);
  `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` (modify verification status)
- Trunk-safe: standalone (provisional)
- Evidence: S1 provides the core contract; S2 only adds the adapter consumer. The adapter and core
  quality gates are expected to pass on this prefix; verify at the S2 boundary before claiming
  standalone.
- Target verification:
  - `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain`
  - `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider`
  - `pwsh -NoProfile -File scripts/quality.ps1 -Check docs`
  - `pwsh -NoProfile -File scripts/quality.ps1 -Check governance`
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: explicit protocol selection, `use_responses_api` and `max_retries`, option mapping,
  `SecretStr`, no Provider wrapper, no real HTTP, dependency direction.
- Not in this slice: full repository static check, quickstart final validation, final evidence.
- Rollback: revert the S2 commit; the core package remains usable without the adapter.
- Diff budget: approximately 14 files including `uv.lock`; likely more than 400 changed lines.
  Exception reason: the adapter factory and its tests are one behavior boundary; generated lockfile
  content is not a review target but remains in the diff.

### S3 — Verification and evidence

- Acceptance outcome: both package gates and repository docs/governance/static checks pass; quickstart
  scenarios are accurate; worktree has no build artifacts; evidence records exact commands.
- Task IDs: T018, T019, T020
- Expected paths: `.specify/delivery/008-langchain-first-llm-runtime/evidence.md` (modify);
  `specs/008-langchain-first-llm-runtime/quickstart.md` (modify only if stale)
- Trunk-safe: standalone (provisional)
- Evidence: no source changes; only verification and evidence. The declared commands must run at
  the current HEAD.
- Target verification: all T018 commands plus `git diff --check` and
  `git status --short --branch`.
- Flag: N/A
- Integration checkpoints: N/A
- Review focus: commands, exit codes, base/head, unexecuted or blocked checks, no false pass claims.
- Not in this slice: implementation changes; if a check fails, return to the owning slice.
- Rollback: revert the S3 commit; source behavior is unchanged.
- Diff budget: 2–3 files, under 20 files and 400 lines.

## Coverage and validation

- Task coverage: T001–T020 each mapped exactly once; no task spans slices.
  - S0: T001–T002
  - S1: T003–T010
  - S2: T011–T017
  - S3: T018–T020
- Requirement coverage: FR-001–FR-019 and SC-001–SC-008 are mapped in `tasks.md`; the runtime
  requirements are covered by S1 + S2, with S3 providing verification evidence. S0 is a governance
  prerequisite, not a runtime requirement.
- Dependency order: S0 → S1 → S2 → S3; within S1 and S2 the task dependency chain is acyclic and
  documented in `tasks.md`.
- Budget exceptions: S0, S1 and S2 exceed `slice_warn_lines: 400`; the reasons are the required
  planning/ADR records in S0, the same-task test rule in S1, and the complete adapter replacement
  in S2. The user accepted these exceptions at the slice gate on 2026-10-31. S3 is within budget.
- Policy compatibility: `pr_slicing: auto`, stacked, manual provider, squash per slice, linear
  history, no merge queue. S0 is a bootstrap single PR before stacked delivery is active.
- Open decisions: none. S0/S1/S2 line-budget exceptions and the S0 bootstrap PR were accepted by
  the user on 2026-10-31.

## Merge plan

- Order: S0, S1, S2, S3.
- Per-slice merge: squash into `main`, in order, after the slice's declared checks pass.
- Final rollup: N/A; the last slice is S3.
- Target sync: merge `main` into the current slice branch before review if the target advances.
- Queue/freeze: no queue; freeze before final review per config.
- Issue closure: no Issue is created by this plan; PR bodies use the v0.2.2 Chinese template.
  Do not claim closure of PR #16.
- Rollback per slice: revert the slice's squash commit; later slices must be replayed or abandoned
  if an earlier prefix is reverted.

## Approval record

- SLICE_PLAN_VERDICT: ready
- SLICE_APPROVAL: approved
- Approved by: 用户 2026-10-31（对 S0–S3 与行数例外回复“好”）
- Choice / accepted risks: S0–S3 stacked；接受 S0/S1/S2 line-budget 例外；S0 为 bootstrap 单 PR
- Approved mode / snapshot: stacked; S0–S3; content fingerprint recorded in `evidence.md`
