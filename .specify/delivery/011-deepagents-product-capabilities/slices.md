# Delivery slice plan: 011-deepagents-product-capabilities

## Identity and approval

- Delivery run / canonical path: shared-session Feature `011-deepagents-product-capabilities`; canonical packet `.specify/delivery/011-deepagents-product-capabilities/exploration.md`; this plan `.specify/delivery/011-deepagents-product-capabilities/slices.md`.
- Feature / spec / plan / tasks: `specs/011-deepagents-product-capabilities/spec.md`, `specs/011-deepagents-product-capabilities/plan.md`, `specs/011-deepagents-product-capabilities/tasks.md` (local-only Feature artifacts; not tracked).
- Baseline HEAD / relevant working-tree changes: `5e8eb7e4029d5a2ae4835e59ef3759c2abc26d82`; new Feature artifacts under `.specify/delivery/011-deepagents-product-capabilities/` and `specs/011-deepagents-product-capabilities/`; Proposed `docs/decisions/agent/0010-deepagents-product-boundary.md` and `docs/decisions/README.md`; pre-existing v0.3.2 installation changes remain in the working tree and are not part of this Feature's product diff.
- Design approval: user approved the Plan/public API contract/Proposed ADR-0010 baseline on 2026-11-04 ("批准进入 Tasks") against the unchanged Plan fingerprint `7f58094554c233cae2309d97ea984211ebabc8749a7d95218e604e33e1886f8e`.
- Analysis approval: user approved the Specification Analysis Report on 2026-11-04 ("批准进入 Slice gate"); 0 critical/high/medium, 6 intentional low notes.
- Slice plan revision: v2 on 2026-11-04 adds S0 (delivery/tooling baseline) after the user's explicit choice, because Ralph requires a clean worktree and the pending v0.3.2 upgrade must not be mixed into S1 product code. The previous 8-slice approval is superseded and must be re-approved.
- Artifact policy: ephemeral (`specs/` local-only; ADR and long-lived docs remain tracked).
- Planning timestamp: 2026-11-04.

## Merge decision

- PR slicing: `auto` (configured).
- Merge mode: `stacked`.
- Target branch: `main`.
- Integration branch: N/A.
- Stack provider: `manual`.
- Slice merge method: `squash`.
- Final merge method: `squash` (configured stacked final; not an integration rollup).
- Target sync method: `merge`.
- Merge queue: `no`.
- Delete branch after merge: `yes`.
- Freeze integration before final review: `yes`.
- Why this mode: every slice is classified `standalone`, so the configured `pr_slicing: auto` resolves to `stacked`; the repository uses a manual provider, linear history, and the configured squash/per-slice policy. No slice requires an integration branch or merge commit. S0 establishes the clean delivery/tooling baseline (v0.3.2 + Proposed ADR-0010 + 011 packet) before any product code; S8 is the release/documentation layer and is squashed last.

## Slice table

| ID | Goal | Kind | Depends on | Task IDs | Paths | Trunk-safe | Flag | Merge order |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S0 | Delivery/tooling baseline: Bundle v0.3.2, Proposed ADR-0010, and 011 Delivery packet | design | - | none (design/tooling baseline; no `tasks.md` task) | `.opencode/commands/`, `.specify/extensions/`, `.specify/workflows/`, `.specify/bundle-catalogs.yml`, `.specify/bundle-records.json`, `.specify/extension-catalogs.yml`, `.specify/extensions/.registry`, `AGENTS.md`, `docs/development/spec-kit-delivery.md`, `harness/build-log.md`, `harness/evidence/delivery-v032-upgrade.md`, `harness/evidence/delivery-sd-shortcut.md`, `docs/decisions/agent/0010-deepagents-product-boundary.md`, `docs/decisions/README.md`, `.specify/delivery/011-deepagents-product-capabilities/` | standalone | - | 1 |
| S1 | New Distribution skeleton, locked environment, quality/CI registration, and error taxonomy | foundation | S0 | T001–T007 | `packages/infra/agent-deepagents/`, `scripts/quality.ps1`, `scripts/test-quality.ps1`, `.specify/extensions/quality/quality-config.yml`, `.github/workflows/quality.yml` | standalone | - | 2 |
| S2 | Model-purpose, subagent, middleware-config, and report/event data contracts | foundation | S1 | T008–T011 | `src/spawn_join_agent_deepagents/{models,subagents,middleware,diagnostics}.py`, `tests/test_{models,subagents,middleware,diagnostics}.py` | standalone | - | 3 |
| S3 | Native supervisor assembly, public API, report, summarization replacement, offline declarative+compiled delegation | behavior | S2 | T012–T019 | `src/spawn_join_agent_deepagents/{supervisor,__init__}.py`, `tests/test_{supervisor,public_api,diagnostics,subagents}.py` | standalone | - | 4 |
| S4 | Effective supervisor/worker/override middleware scopes and summarization collision rules | behavior | S3 | T020–T024 | `src/spawn_join_agent_deepagents/{middleware,supervisor}.py`, `tests/test_{middleware,supervisor}.py` | standalone | - | 5 |
| S5 | Governed async delegation controller and policy middleware | behavior | S3 | T025–T030 | `src/spawn_join_agent_deepagents/{execution,supervisor}.py`, `tests/test_{execution,supervisor}.py` | standalone | - | 6 |
| S6 | Recovery context, checkpointer/interrupt validation, host-owned resource pass-through, native resume | behavior | S3 | T031–T035 | `src/spawn_join_agent_deepagents/{recovery,supervisor}.py`, `tests/test_{recovery,supervisor}.py` | standalone | - | 7 |
| S7 | Lifecycle diagnostics, correlation/redaction, sync/async callbacks, interruption | behavior | S3, S5 | T036–T040 | `src/spawn_join_agent_deepagents/{diagnostics,supervisor}.py`, `tests/test_diagnostics.py` | standalone | - | 8 |
| S8 | Upstream contracts, package README/examples, architecture/docs/quality integration, full validation | release | S1–S7 | T041–T053 | `tests/test_upstream_contract.py`, `README.md`, `examples/`, `docs/architecture/`, `AGENTS.md`, root `README.md`, `docs/development/quality-gates.md`, `tests/test_{public_api,package}.py` | standalone | - | 9 |

## Slice details

### S0 — Delivery/tooling baseline

- Acceptance outcome: Bundle v0.3.2 installation records, Proposed ADR-0010 in the ADR index, and the canonical 011 Delivery packet are committed on a clean S0 branch; no product package or runtime code exists yet.
- Task IDs: none (design/tooling baseline; no `tasks.md` task).
- Expected paths: `.opencode/commands/` (including `sd.md` and `speckit.delivery.method.md`), `.specify/extensions/` (including the Ralph slice template and Delivery method templates), `.specify/workflows/`, `.specify/bundle-catalogs.yml`, `.specify/bundle-records.json`, `.specify/extension-catalogs.yml`, `.specify/extensions/.registry`, `AGENTS.md`, `docs/development/spec-kit-delivery.md`, `harness/build-log.md`, `harness/evidence/delivery-v032-upgrade.md`, `harness/evidence/delivery-sd-shortcut.md`, `docs/decisions/agent/0010-deepagents-product-boundary.md`, `docs/decisions/README.md`, `.specify/delivery/011-deepagents-product-capabilities/{exploration.md,decision-context.md,slices.md}`.
- Trunk-safe: `standalone`.
- Evidence: the v0.3.2 upgrade has its own durable evidence; ADR-0010 is Proposed and indexed; the Delivery packet is present; no existing package/runtime behavior changes and no product code is included. `specs/011...` remains local-only and is not committed.
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` (expect 0 errors; the known pre-existing v0.2.2 freshness warning may remain); `pwsh -NoProfile -File scripts/quality.ps1 -Check static` (or `blocked` if actionlint/PSScriptAnalyzer is unavailable); targeted docs link/whitespace check over the changed docs; `git diff --check`. Full `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` remains blocked by the historical `specs/007` link and is **not** an S0 pass criterion; it must be resolved or explicitly carried before final delivery.
- Flag: N/A.
- Integration checkpoints: N/A.
- Review focus: v0.3.2 installation/record integrity; ADR status remains Proposed and indexed; no product code, generated package artifacts, or `specs/` content committed; no secrets in evidence/docs; the Delivery packet matches the approved Feature identity.
- Not in this slice: T001–T053 and all product code/documentation (S1–S8).
- Rollback: revert the S0 commit; no runtime or migration impact. The previous install state can be restored from the recorded v0.3.2 evidence.
- Diff budget: governance/tooling baseline; installer-managed command/template/workflow files and generated/vendor files are excluded from the product line heuristic, but the commit is still reviewed for installation integrity. Explicit budget exception requested.

### S1 — New Distribution foundation and registration

- Acceptance outcome: `spawn-join-agent-deepagents` is a lockable, buildable, testable Distribution with the shared error taxonomy, quality profile, CI matrix entry, and package smoke tests; no supervisor behavior is claimed yet.
- Task IDs: T001, T002, T003, T004, T005, T006, T007.
- Expected paths: new `packages/infra/agent-deepagents/` (`pyproject.toml`, `LICENSE`, `README.md`, `uv.lock`, `src/spawn_join_agent_deepagents/{__init__.py,py.typed,errors.py}`, `tests/{conftest.py,test_package.py,test_public_api.py}`); modified `scripts/quality.ps1`, `scripts/test-quality.ps1`, `.specify/extensions/quality/quality-config.yml`, `.github/workflows/quality.yml`.
- Trunk-safe: `standalone`.
- Evidence: the package has no consumers; its tests and build run independently. Existing Distributions and runtime behavior are unchanged. The quality script map includes local build dependencies; the CI matrix runs the same package command.
- Target verification: `uv lock --check --directory packages/infra/agent-deepagents`; `uv sync --locked --directory packages/infra/agent-deepagents`; `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents`; `pwsh -NoProfile -File scripts/test-quality.ps1`; `pwsh -NoProfile -File scripts/quality.ps1 -Check governance`; `git diff --check`.
- Flag: N/A (new package, no existing behavior).
- Integration checkpoints: N/A.
- Review focus: dependency versions and direction; `src/`/setuptools/lock layout; error messages do not include secrets; quality/CI registration is real.
- Not in this slice: ADR/Delivery baseline (S0); supervisor/model/middleware/delegation behavior (S2–S7); package README final content/examples (S8).
- Rollback: revert the new package directory and the script/profile/CI edits; no migrations or data.
- Diff budget: new package skeleton and tests plus a generated `uv.lock`; generated lock file is excluded from the line heuristic. The requested budget exception is the new-Distribution bootstrap; it is accepted only if the slice gate approves this plan.

### S2 — Shared contracts

- Acceptance outcome: model-purpose, subagent, middleware-scope, and report/event data contracts exist with unit tests; no public `build_supervisor` is claimed.
- Task IDs: T008, T009, T010, T011.
- Expected paths: new `src/spawn_join_agent_deepagents/{models,subagents,middleware,diagnostics}.py`; new `tests/test_{models,subagents,middleware,diagnostics}.py`.
- Trunk-safe: `standalone`.
- Evidence: modules are additive; no existing package imports them; package build/tests remain green. The public surface is not exported yet.
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents`; `pytest tests/test_models.py tests/test_subagents.py tests/test_middleware.py tests/test_diagnostics.py -q`.
- Flag: N/A.
- Integration checkpoints: N/A.
- Review focus: explicit inheritance/no fallback; `tools=None` vs `tools=()`; unique names; reserved summarization name; immutable/safe report/event records.
- Not in this slice: supervisor assembly (S3), user middleware behavior (S4), delegation controller (S5), lifecycle events (S7).
- Rollback: revert the additive modules/tests.
- Diff budget: may exceed 400 changed lines because four contract families and their tests are introduced. Requested exception: contract/test density; accepted only with the slice gate.

### S3 — Supervisor assembly MVP

- Acceptance outcome: `build_supervisor` returns a native graph and immutable report; offline declarative and compiled subagents delegate; explicit model purposes and summarization replacement work; public exports match the contract.
- Task IDs: T012, T013, T014, T015, T016, T017, T018, T019.
- Expected paths: new `src/spawn_join_agent_deepagents/supervisor.py`; modified `__init__.py`; new/updated `tests/test_{supervisor,public_api,diagnostics,subagents}.py`.
- Trunk-safe: `standalone`.
- Evidence: the package is new; no existing consumer changes. Without delegation policy, the native DeepAgents behavior is used.
- Target verification: `pytest tests/test_supervisor.py tests/test_public_api.py tests/test_subagents.py tests/test_diagnostics.py -q`; package quality gate; offline `ainvoke` delegation test.
- Flag: N/A.
- Integration checkpoints: N/A.
- Review focus: native graph returned; `create_deep_agent` called once; model resolution and explicit inheritance; summarization replacement by name; compiled ownership; safe report/public API.
- Not in this slice: user middleware scopes (S4), governed delegation (S5), recovery validation (S6), lifecycle events (S7).
- Rollback: revert supervisor/public export changes; the package returns to contracts-only.
- Diff budget: may exceed 400 lines because the first usable assembly and its offline integration tests are introduced. Requested exception: MVP assembly/test density; accepted only with the slice gate.

### S4 — Middleware scopes

- Acceptance outcome: supervisor/worker/per-subagent middleware markers execute in their declared scopes; compiled subagents remain untouched; reserved/duplicate/unknown rules are enforced; summarization is replaced, not duplicated.
- Task IDs: T020, T021, T022, T023, T024.
- Expected paths: `src/spawn_join_agent_deepagents/{middleware,supervisor}.py`; `tests/test_{middleware,supervisor}.py`.
- Trunk-safe: `standalone`.
- Evidence: additive behavior behind explicit configuration; the default empty configuration keeps S3 behavior. No existing consumer changes.
- Target verification: `pytest tests/test_middleware.py tests/test_supervisor.py -q`; package quality gate; behavior test with marker middleware.
- Flag: N/A.
- Integration checkpoints: N/A.
- Review focus: behavior, not list order; compiled untouched; reserved-name rejection; no duplicate summarization.
- Not in this slice: governed delegation (S5), diagnostics (S7).
- Rollback: remove the scope merging/validation and the behavior tests.
- Diff budget: expected under 400 lines; if test coverage pushes it over, record the actual count and review focus.

### S5 — Governed delegation

- Acceptance outcome: an explicit async controller enforces concurrency ceiling, bounded FIFO, deadline covering queue+execution, parent cancellation, worker failure, and cleanup; sync policy use fails explicitly.
- Task IDs: T025, T026, T027, T028, T029, T030.
- Expected paths: `src/spawn_join_agent_deepagents/{execution,supervisor}.py`; `tests/test_{execution,supervisor}.py`.
- Trunk-safe: `standalone`.
- Evidence: policy is optional; when omitted, native `task` behavior remains. The controller has no process-global state.
- Target verification: `pytest tests/test_execution.py tests/test_supervisor.py -q`; package quality gate; deterministic concurrency/deadline/cancel tests.
- Flag: N/A.
- Integration checkpoints: N/A.
- Review focus: active/waiting counters; exactly-once slot release; no sync thread abandonment; controller loop binding; no global state.
- Not in this slice: lifecycle diagnostics (S7); recovery (S6).
- Rollback: omit `DelegationConfiguration`; revert execution module and wiring.
- Diff budget: may exceed 400 lines due to controller state machine and concurrency tests. Requested exception: concurrency correctness evidence; accepted only with the slice gate.

### S6 — Recovery and resources

- Acceptance outcome: host-owned resources pass through by identity; missing checkpointer/thread id fails safely; native interrupt/resume works with the same `thread_id`; the package never closes resources.
- Task IDs: T031, T032, T033, T034, T035.
- Expected paths: `src/spawn_join_agent_deepagents/{recovery,supervisor}.py`; `tests/test_{recovery,supervisor}.py`.
- Trunk-safe: `standalone`.
- Evidence: additive validation/pass-through; resource ownership remains host-owned. The native graph still uses the same LangGraph APIs.
- Target verification: `pytest tests/test_recovery.py tests/test_supervisor.py -q`; package quality gate; `InMemorySaver` interrupt/resume integration.
- Flag: N/A.
- Integration checkpoints: N/A.
- Review focus: no create/close/health lifecycle; checkpointer identity; native `Command(resume=...)`; no exactly-once claim.
- Not in this slice: diagnostics interruption event (S7); no durable database/store implementation.
- Rollback: remove recovery validation/module; native graph still works with host-provided resources.
- Diff budget: expected under 400 lines; if the interrupt test fixture pushes it over, record the actual count.

### S7 — Lifecycle diagnostics

- Acceptance outcome: optional sync/async callbacks receive redacted, correlated events for selected/queued/started/completed/failed/timed-out/cancelled/rejected/interrupted; callback errors propagate; no queue/backpressure backend is added.
- Task IDs: T036, T037, T038, T039, T040.
- Expected paths: `src/spawn_join_agent_deepagents/{diagnostics,supervisor}.py`; `tests/test_diagnostics.py`.
- Trunk-safe: `standalone`.
- Evidence: diagnostics are optional; the graph works without callbacks. Events use native runtime execution info and tool call id.
- Target verification: `pytest tests/test_diagnostics.py -q`; package quality gate; success/failure/timeout/cancel/interrupt/reject scenarios.
- Flag: N/A.
- Integration checkpoints: N/A.
- Review focus: event sequence; redaction; callback exception behavior; async callback in sync mode; `GraphInterrupt` re-raised; no hidden persistence/queue.
- Not in this slice: web/SSE/timeline adapters; production observability backend; tenant/billing/UI.
- Rollback: omit `DiagnosticsConfig`; revert event emission additions.
- Diff budget: may exceed 400 lines due to event/callback matrix. Requested exception: redaction and lifecycle coverage; accepted only with the slice gate.

### S8 — Distribution, documentation, and final validation

- Acceptance outcome: the package is independently installable with README/examples; architecture/AGENTS/quality docs are current; upstream contract tests pass; full package/repository gates and quickstart are recorded; wheel contents are correct.
- Task IDs: T041, T042, T043, T044, T045, T046, T047, T048, T049, T050, T051, T052, T053.
- Expected paths: `tests/test_upstream_contract.py`; `packages/infra/agent-deepagents/README.md`; `examples/{basic_supervisor,governed_delegation}.py`; `docs/architecture/{package-boundaries,repository-map}.md`; `AGENTS.md`; root `README.md`; `docs/development/quality-gates.md`; `tests/test_{public_api,package}.py`.
- Trunk-safe: `standalone`.
- Evidence: documentation/examples/tests only for an already functional package; no existing runtime behavior changes. The full gate can be run on the target branch.
- Target verification: `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents`; `pwsh -NoProfile -File scripts/quality.ps1`; `-Check docs/governance/static`; `pwsh -NoProfile -File scripts/test-quality.ps1`; quickstart scenarios; `git diff --check`.
- Flag: N/A.
- Integration checkpoints: N/A.
- Review focus: README facts vs pyproject/contracts; examples offline/no secrets; version/dependency compatibility; CI/profile; wheel `py.typed`/LICENSE/README; known historical blockers separated.
- Not in this slice: new runtime capabilities, provider SDKs, MCP/database/sandbox/observability backend, web/SSE, tenant/billing/UI.
- Rollback: revert docs/examples/contract tests; the functional package remains.
- Diff budget: may exceed 400 lines due to documentation/examples and final contract checks. Requested exception: release/documentation slice; generated lock excluded; accepted only with the slice gate.

## Coverage and validation

- Task coverage: S0 has no `tasks.md` task IDs (design/tooling baseline); T001–T007 → S1; T008–T011 → S2; T012–T019 → S3; T020–T024 → S4; T025–T030 → S5; T031–T035 → S6; T036–T040 → S7; T041–T053 → S8. Every task maps exactly once; no task spans slices.
- Requirement coverage:
  - FR-001 (Distribution) → S1, S8.
  - FR-002 (assembly/native graph/report) → S3.
  - FR-003 (declarative/compiled subagents) → S2, S3.
  - FR-004 (model adapter/direct BaseChatModel) → S2, S3.
  - FR-005 (purpose binding/explicit inheritance) → S2, S3.
  - FR-006 (middleware/scopes/no duplicate upstream rules) → S2, S4.
  - FR-007 (governed delegation) → S5.
  - FR-008 (native resources/recovery) → S6.
  - FR-009 (diagnostics/redaction) → S2, S7.
  - FR-010 (docs/compatibility) → S8.
  - FR-011 (offline tests) → S1–S8.
  - FR-012 (quality/CI/profile) → S1, S8.
  - SC-001 (clean wheel install) → S8.
  - SC-002 (offline declarative+compiled delegation) → S3.
  - SC-003 (invalid assembly/no secret) → S3, S4.
  - SC-004 (concurrency/deadline/cancel) → S5.
  - SC-005 (checkpoint/interrupt/resume) → S6.
  - SC-006 (diagnostics) → S7.
  - SC-007 (quality/CI) → S1, S8.
- Dependency order: S0 → S1 → S2 → S3 → S4 → S5 → S6 → S7 → S8. Acyclic and linear. S1 depends on S0; S7 depends on S5; S4/S5/S6 all depend on S3 but are ordered for a single stack.
- Budget exceptions: S0, S1, S2, S3, S5, S7, S8 are expected to exceed the 400-line heuristic because they introduce the delivery/tooling baseline, a new Distribution, contract families, the MVP assembly, concurrency correctness evidence, and release/docs. Generated `uv.lock` and installer-managed command/template/workflow files are excluded from the product line heuristic. These exceptions are presented for the slice gate; they are not silently accepted.
- Policy compatibility: `main` requires PR, linear history, and the `Quality Gate` required check with strict sync; no merge queue; manual stacked squash preserves linear history. `merge_policy.final: squash` is valid for stacked mode; no integration rollup is used. Branch deletion is enabled after merge.
- Open decisions: none. The only choices are the stacked linear order (S0→S8) and the explicit budget exceptions; both are presented for approval, not inferred.

## Merge plan

- Order: S0, S1, S2, S3, S4, S5, S6, S7, S8.
- Per-slice merge: each slice is a separate PR against `main`, squash-merged after its predecessor; no PR is created or merged without separate user authorization.
- Final rollup: S8 squash to `main` (configured stacked final); no merge commit.
- Target sync: merge `main` into the next stacked branch as needed; strict required checks must be satisfied.
- Queue/freeze: no merge queue; freeze before final review; delete branches after merge.
- Issue closure: use `Part of #<issue>` on S0–S7 and `Closes #<issue>` on S8 only if a real GitHub issue exists and the user authorizes tracker writes. No issue is created by this plan.
- Rollback per slice: revert that slice's governance/tooling/package/docs changes; no data migration. S0 rollback restores the pre-v0.3.2 install/tooling state; S1 rollback removes the package; S2–S7 rollback removes additive modules/wiring; S8 rollback removes docs/examples/contract tests.

## Approval record

- SLICE_PLAN_VERDICT: ready
- SLICE_PLAN_FINGERPRINT: `e024df3836ca6cb00a56ee797d4373c4aeec99d265aee81a8e49c6bdb4387fba`.
- Fingerprint method: SHA-256 over the UTF-8 canonical manifest below (paths relative to the repository root, forward slashes, tab-separated fields, final newline included); each file hash is SHA-256 of the raw file bytes.
- Fingerprint manifest:

```text
plan.md	e771d6c1f2176dd3311119cb8039e83b130a570a39532f38a93b9777dd716789
spec.md	639480e8b6e70b002ffeb9d68dbebca106001624aa20bbb298b9355866293056
tasks.md	016aa0696d6a410c265226b5387432f5f756f1484aa8b9450d8d4186cbf95b59
merge_mode	stacked
target	main
provider	manual
slice_method	squash
final_method	squash
S0	none	standalone
S1	T001-T007	standalone
S2	T008-T011	standalone
S3	T012-T019	standalone
S4	T020-T024	standalone
S5	T025-T030	standalone
S6	T031-T035	standalone
S7	T036-T040	standalone
S8	T041-T053	standalone
```

- SLICE_APPROVAL: approved
- Approved by: 用户 (human, 2026-11-04)
- Choice / accepted risks: 批准修订后的 S0–S8；授权创建 `ralph/011-deepagents-product-capabilities/S0` baseline 提交与分支；接受 S0/S1/S2/S3/S5/S7/S8 的预算例外（生成 `uv.lock`、installer-managed 命令/模板/workflow 不计入产品行数启发式）。
- Approved mode / snapshot: `stacked`; target `main`; provider `manual`; slice/final `squash`; S0–S8 mapping; fingerprint `e024df3836ca6cb00a56ee797d4373c4aeec99d265aee81a8e49c6bdb4387fba`.
- Approved at: 2026-11-04T19:09:36.0740750+08:00
