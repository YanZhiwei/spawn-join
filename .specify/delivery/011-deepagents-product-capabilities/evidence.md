# Delivery evidence: 011-deepagents-product-capabilities

- **delivery_run**: `011-deepagents-product-capabilities`
- **lane**: `feature`
- **evidence_path**: `.specify/delivery/011-deepagents-product-capabilities/evidence.md`
- **exploration_path**: `.specify/delivery/011-deepagents-product-capabilities/exploration.md`
- **feature_id**: `011-deepagents-product-capabilities`
- **phase_id**: `s8-final-validation`
- **base_revision**: `5e8eb7e4029d5a2ae4835e59ef3759c2abc26d82`
- **head_revision**: `d5afbd5ea1c019ff70a5deb96188590cbab67ce8`
- **merge_base**: `5e8eb7e4029d5a2ae4835e59ef3759c2abc26d82`
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-11-04
- **status**: active
- **result**: pass for local implementation, package/full quality gates, independent six-dimension review, ADR finalization, and single-PR handoff; PR #32 created. CI run 41860603215 passed on `3196ab8`; a Python 3.11 deadline fix landed in `d5afbd5` and requires a fresh CI run.
- **pull_request**: 32 (https://github.com/YanZhiwei/spawn-join/pull/32)
- **content_fingerprint**: `1a1f2fe9220240914d2e323302e89e99ed183507c3f84398f0fb08d0db06b71b`
  Method: for each changed tracked regular file, current worktree bytes normalized CRLF->LF, SHA-256 per file; manifest `<git-mode>\t<normalized-sha256>\t<repo-relative-path>` with ordinal path sort; SHA-256 over the UTF-8 manifest with a final newline. Excludes `.specify/delivery/011-deepagents-product-capabilities/reviews/**`, `.specify/delivery/011-deepagents-product-capabilities/evidence.md`, the historical `.specify/delivery/010-model-metadata-sync/evidence.md`, and `harness/build-log.md` as declared review/receipt bookkeeping. 113 reviewed paths. The reviewed content includes the F-07 deadline fix at `d5afbd5`; later commits add only bookkeeping.
- **requirements_fingerprint**: `1cae8bd8a6c398adaa253edcf28d3ab25031ab3aba9554484cdd4a7e21f438bd`
  Method: same normalized per-file SHA-256; manifest `<normalized-sha256>\t<path>` with ordinal path sort; SHA-256 over the UTF-8 manifest with a final newline. Inputs: spec.md, plan.md, research.md, data-model.md, contracts/public-api.md, tasks.md, quickstart.md, exploration.md, decision-context.md, slices.md, constitution.md, AGENTS.md, package-boundaries.md, quality-gates.md, ADR-0010, delivery-config.yml, reviewer.md.
- **method_identity**: `builtin` reviewer contract; no external method/config/resource selected
- **bug_slug**: not-applicable
- **assessment_path**: not-applicable

## Scope implemented

- New Distribution `spawn-join-agent-deepagents` under `packages/infra/agent-deepagents/`
  with its own `pyproject.toml`, `uv.lock`, `.venv`, `src/` layout, tests, README, LICENSE,
  `py.typed`, and offline examples.
- Explicit model-purpose bindings (`SUPERVISOR`, `WORKER`, `SUMMARIZATION`) with direct,
  catalog, or explicitly declared inheritance; no implicit fallback.
- Declarative and compiled subagents, duplicate/blank/fork validation, generated
  summarization replacement, and a package-controlled default `general-purpose` using the
  resolved `WORKER` model and `workers` middleware. `control_default_subagent=False` preserves
  and reports the upstream supervisor-owned default.
- Supervisor/worker/per-subagent middleware scopes with reserved-name, duplicate, and
  compiled-override validation. Reports record requested order and replaced defaults; the
  final upstream base-stack position is upstream-owned.
- Async-first governed delegation: bounded FIFO, concurrency ceiling, deadline, parent
  cancellation, queue rejection, worker failure, cleanup, and explicit sync rejection.
- Immutable assembly report and redacted lifecycle diagnostics with sync/async callbacks,
  runtime correlation, interruption handling, and callback-exception propagation.
- `RecoveryContext`, explicit and permission-driven interrupt/checkpointer validation,
  host-owned Store/Checkpointer/MCP/sandbox/provided Backend pass-through, native
  `Command(resume=...)` behavior, and an ephemeral in-memory `StateBackend` fallback when the
  host omits a backend.
- Quality profile, `scripts/quality.ps1` registration, `scripts/test-quality.ps1` assertion,
  CI matrix entry, package-boundary/repository-map/AGENTS/README updates.
- ADR-0010 finalized as **Accepted** by the repository maintainer on 2026-11-04.
- Publication amendment: the user explicitly chose one combined PR (`S8 → main`, squash)
  instead of the original per-slice PR plan; S0–S8 remain review/commit boundaries.

## Commands and results

All commands were executed from the repository root unless noted.

| Command | Working directory | Exit code | Result |
|---|---|---|---|
| `uv run --python 3.11 --directory packages/infra/agent-deepagents pytest -c <root>/pyproject.toml tests -q` | repo root | 0 | 115 tests passed on Python 3.11.13 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents` | repo root | 0 | format/lint/strict type/test/build, four local wheels, isolated install, `pip check`, isolated import |
| `pwsh -NoProfile -File scripts/quality.ps1` | repo root | 0 | all six Distributions, docs, governance, and static checks passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | repo root | 0 | 101 files, 257 local targets |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | repo root | 0 | 0 errors; one pre-existing v0.2.2 freshness warning |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | repo root | 0 | 0 failing checks |
| `pwsh -NoProfile -File scripts/test-quality.ps1` | repo root | 0 | 11 gate-regression scenarios |
| `pwsh -NoProfile -File scripts/test-governance.ps1` | repo root | 0 | 23 governance scenarios |
| `pwsh -NoProfile -File scripts/test-static.ps1` | repo root | 0 | 3 static-analysis scenarios |
| `uv run --locked --no-sync --directory packages/infra/agent-deepagents python examples/basic_supervisor.py` | repo root | 0 | Offline declarative delegation and final native response |
| `uv run --locked --no-sync --directory packages/infra/agent-deepagents python examples/governed_delegation.py` | repo root | 0 | Selected/started/completed diagnostics with governed delegation |
| Wheel build + `zipfile` inspection | temp directory | 0 | one wheel and sdist; all modules, `py.typed`, LICENSE, METADATA present |
| `git diff --check main..HEAD` | repo root | 0 | no whitespace errors |
| `git status --short --untracked-files=all` | repo root | 0 | clean before evidence/review bookkeeping edits |

## Independent review

- A read-only independent Standards Review was performed on the outgoing diff.
- Initial verdict: **blocked**, with one blocker (slow `on_queued` queue cleanup), two high
  findings (public callback exports; subagent/boolean checkpointer validation), and several
  medium/low findings.
- The blocker and high findings were fixed; follow-up Standards Review returned
  **pass-with-notes**.
- The final six-dimension outgoing-diff Review at `13692d7e` returned **pass** after the
  permission-interrupt, default `general-purpose`, middleware-order, test-coverage, and
  backend-ownership fixes. The review was refreshed after ADR finalization and the single-PR
  amendment at `ff91d98` and returned **pass** with updated fingerprints.
- Open minor findings: F-04 (graph-level queue/deadline/cancel/worker-failure and fork
  execution coverage) and F-06 (explicit `require_worker=False` conflicts with the controlled
  default `general-purpose` and fails at model resolution rather than a dedicated validation
  error). Both fail safely before graph execution and do not block this delivery.
- Review report: `.specify/delivery/011-deepagents-product-capabilities/reviews/outgoing-diff/review.yml`.
- F-07: a Python 3.11 Windows CI run exposed a native `TimeoutError` leak when the controller deadline expired at the clock boundary. `execution.py` now uses `asyncio.Timeout.expired()` to distinguish controller expiry from a worker-owned `TimeoutError`; the new regression test and all 115 package tests pass on Python 3.11.13.

## Limitations and residual risk

- Local validation includes Windows/Python 3.13 and a targeted/full package run on Python 3.11.13.
  Remote CI run 41860603215 passed the configured Linux 3.11/3.14 and Windows 3.11 matrix on
  `3196ab8`; the F-07 fix in `d5afbd5` requires a fresh remote run before merge.
- Tests use deterministic fake models, structural fake catalogs, and in-memory checkpointing.
  No real Provider, network, MCP server, sandbox, or durable Store was exercised.
- F-04 and F-06 are open non-blocking minors as described above.
- `checkpointer` accepts arbitrary non-checkpointer objects at the package boundary; invalid
  types may fail later in upstream LangGraph rather than during assembly.
- The public API test set is hand-maintained and mirrors the documented contract; it does not
  automatically derive future names from the contract.
- Resource-identity tests verify model/checkpointer/store/backend identity but not the
  summarization backend identity.
- The slow-queue cleanup regression test is timing-based and could be sensitive on heavily
  loaded CI.
- The historical `harness/evidence/delivery-v022-upgrade.md` freshness warning remains
  pre-existing and unmodified.
- `.specify/delivery/010-model-metadata-sync/evidence.md` was closed as `delivered` on
  2026-11-04 against PR #31 (squash merge commit `5e8eb7e`) to resolve the pre-existing
  governance blocker. The historical record is retained; the close corrects only its Delivery
  status/metadata and is excluded from this Feature's content fingerprint as receipt bookkeeping.
- The local-only `specs/007-llm-protocol-abstraction/plan.md` link was repaired locally to let
  the docs gate run; no tracked historical Spec was modified.
- The single combined PR is an explicit user-authorized deviation from the original per-slice
  PR plan; S0–S8 review/commit boundaries and receipts remain intact.
- PR #32 was created; remote CI run 41860603215 passed all package matrix jobs and the required
  `Quality Gate` on `3196ab8`. The F-07 deadline fix is in `d5afbd5`; its fresh `Quality Gate`
  is required before the authorized squash merge. Merge and release were not performed when
  this record was refreshed.

## Changed paths (main..HEAD, excluding review bookkeeping in the content fingerprint)

- `packages/infra/agent-deepagents/` (new Distribution, tests, examples)
- `scripts/quality.ps1`, `scripts/test-quality.ps1`
- `.specify/extensions/quality/quality-config.yml`
- `.github/workflows/quality.yml`
- `docs/architecture/package-boundaries.md`, `docs/architecture/repository-map.md`
- `docs/development/quality-gates.md`, `docs/development/spec-kit-delivery.md`,
  `docs/development/technical-diagrams.md`
- `AGENTS.md`, `README.md`
- `docs/decisions/agent/0010-deepagents-product-boundary.md`, `docs/decisions/README.md`
- `.specify/delivery/011-deepagents-product-capabilities/` (exploration, decision context,
  slices, task/slice verdicts, simplifications, review report, this evidence)
- v0.3.2 installer/tooling baseline commit `80721216d7051345f6fc50bc22edc0a9dc46af56`
  (separate S0 baseline; not product code)

## Next required gates

1. The final bookkeeping push must pass a fresh required `Quality Gate` on the resulting head.
2. Squash-merge PR #32 under the user's explicit authorization; do not use a merge commit.
3. After the PR is merged, run `speckit.delivery.close` with `outcome=merged` and the observed
   merge revision, then update this record's final status/outcome.
