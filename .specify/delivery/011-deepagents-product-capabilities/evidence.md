# Delivery evidence: 011-deepagents-product-capabilities

- **feature_id**: `011-deepagents-product-capabilities`
- **phase_id**: `s8-final-validation`
- **base_revision**: `5e8eb7e4029d5a2ae4835e59ef3759c2abc26d82`
- **head_revision**: `3280fdf4db7706b37360826d963eb0f2b4d7c200`
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-11-04
- **status**: active
- **result**: pass for local implementation, package/full quality gates, and independent standards review (pass-with-notes); no push, PR, or merge has been performed
- **pull_request**: none

## Scope implemented

- New Distribution `spawn-join-agent-deepagents` under `packages/infra/agent-deepagents/`
  with its own `pyproject.toml`, `uv.lock`, `.venv`, `src/` layout, tests, README, LICENSE,
  `py.typed`, and offline examples.
- Explicit model-purpose bindings (`SUPERVISOR`, `WORKER`, `SUMMARIZATION`) with direct,
  catalog, or explicitly declared inheritance; no implicit fallback.
- Declarative and compiled subagents, duplicate/blank/fork validation, and generated
  summarization replacement.
- Supervisor/worker/per-subagent middleware scopes with reserved-name, duplicate, and
  compiled-override validation.
- Async-first governed delegation: bounded FIFO, concurrency ceiling, deadline, parent
  cancellation, queue rejection, worker failure, cleanup, and explicit sync rejection.
- Immutable assembly report and redacted lifecycle diagnostics with sync/async callbacks,
  runtime correlation, interruption handling, and callback-exception propagation.
- `RecoveryContext`, interrupt/checkpointer validation, host-owned Store/Backend/Checkpointer
  pass-through, native `Command(resume=...)` behavior, and boolean checkpointer rejection.
- Quality profile, `scripts/quality.ps1` registration, `scripts/test-quality.ps1` assertion,
  CI matrix entry, package-boundary/repository-map/AGENTS/README updates.
- Proposed ADR-0010 remains Proposed; it was not accepted by this run.

## Commands and results

All commands were executed from the repository root unless noted.

| Command | Working directory | Exit code | Result |
|---|---|---|---|
| `uv run --locked --no-sync --directory packages/infra/agent-deepagents pytest -c <root>/pyproject.toml tests -q` | repo root | 0 | 108 tests passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents` | repo root | 0 | format/lint/strict type/test/build, four local wheels, isolated install, `pip check`, isolated import |
| `pwsh -NoProfile -File scripts/quality.ps1` | repo root | 0 | all six Distributions, docs, governance, and static checks passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | repo root | 0 | 101 files, 251 local targets |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | repo root | 0 | 0 errors; one pre-existing v0.2.2 freshness warning |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | repo root | 0 | 0 failing checks |
| `pwsh -NoProfile -File scripts/test-quality.ps1` | repo root | 0 | 11 gate-regression scenarios |
| `pwsh -NoProfile -File scripts/test-governance.ps1` | repo root | 0 | 23 governance scenarios |
| `pwsh -NoProfile -File scripts/test-static.ps1` | repo root | 0 | 3 static-analysis scenarios |
| `uv run --locked --no-sync --directory packages/infra/agent-deepagents python examples/basic_supervisor.py` | repo root | 0 | Offline declarative delegation and final native response |
| `uv run --locked --no-sync --directory packages/infra/agent-deepagents python examples/governed_delegation.py` | repo root | 0 | Selected/started/completed diagnostics with governed delegation |
| Wheel build + `zipfile` inspection | temp directory | 0 | one wheel and sdist; all modules, `py.typed`, LICENSE, METADATA present |
| `git diff --check main..HEAD` | repo root | 0 | no whitespace errors |
| `git status --short --untracked-files=all` | repo root | 0 | clean tracked worktree |

## Independent review

- A read-only independent Standards Review was performed on the outgoing diff.
- Initial verdict: **blocked**, with one blocker (slow `on_queued` queue cleanup), two high
  findings (public callback exports; subagent/boolean checkpointer validation), and several
  medium/low findings.
- The blocker and high findings were fixed; the follow-up review returned
  **pass-with-notes**, with no blocker or high finding.
- The last review identified `checkpointer=True` as an invalid root-graph checkpointer; it was
  fixed with `validate_checkpointer_value()` and regression tests, then re-verified as closed.
- The reviewer did not re-run the mechanical quality gates; the commands above are the actual
  local gate evidence.

## Limitations and residual risk

- Local validation was Windows/Python 3.13 only. The configured CI matrix (Linux 3.11/3.14,
  Windows 3.11) was not executed remotely; do not claim remote CI success.
- Tests use deterministic fake models, a structural fake catalog, and in-memory checkpointing.
  No real Provider, network, MCP server, sandbox, or durable Store was exercised.
- `checkpointer` accepts arbitrary non-checkpointer objects at the package boundary; invalid
  types may fail later in upstream LangGraph rather than during assembly.
- The public API test set is hand-maintained and mirrors the documented contract; it does not
  automatically derive future names from the contract.
- The resource-identity test verifies model/checkpointer/store/backend identity but not the
  summarization backend identity.
- The slow-queue cleanup regression test is timing-based and could be sensitive on heavily
  loaded CI.
- ADR-0010 remains Proposed. Finalization requires reviewed implementation and a matching HEAD.
- The historical `harness/evidence/delivery-v022-upgrade.md` freshness warning remains
  pre-existing and unmodified.
- The local-only `specs/007-llm-protocol-abstraction/plan.md` link was repaired locally to let
  the docs gate run; no tracked historical Spec was modified.
- No push, PR creation, merge, release, or remote CI run was authorized or performed.

## Changed paths (main..HEAD)

- `packages/infra/agent-deepagents/` (new Distribution and tests/examples)
- `scripts/quality.ps1`, `scripts/test-quality.ps1`
- `.specify/extensions/quality/quality-config.yml`
- `.github/workflows/quality.yml`
- `docs/architecture/package-boundaries.md`, `docs/architecture/repository-map.md`
- `docs/development/quality-gates.md`, `docs/development/spec-kit-delivery.md`,
  `docs/development/technical-diagrams.md`
- `AGENTS.md`, `README.md`
- `docs/decisions/agent/0010-deepagents-product-boundary.md`,
  `docs/decisions/README.md`
- `.specify/delivery/011-deepagents-product-capabilities/` (exploration, decision context,
  slices, task/slice verdicts, this evidence)
- v0.3.2 installer/tooling baseline commit `80721216d7051345f6fc50bc22edc0a9dc46af56`
  (separate S0 baseline; not product code)

## Next required gates

1. User review of the final outgoing diff and local evidence.
2. A fresh independent review if the reviewed HEAD changes materially.
3. `speckit.decision.finalize` / `speckit.decision.check` for ADR-0010 after reviewed HEAD.
4. Remote CI on the configured matrix (not yet run).
5. Explicit authorization before push, PR creation, or merge; Delivery handoff must write a
   real `PR_BODY_PATH` with `gh pr create --body-file`.
