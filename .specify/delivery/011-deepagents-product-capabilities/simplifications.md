# Simplification scan: 011-deepagents-product-capabilities

- Scope: outgoing diff `main..HEAD` (base `5e8eb7e4029d5a2ae4835e59ef3759c2abc26d82`,
  reviewed content at the scan HEAD), with focus on
  `packages/infra/agent-deepagents/`.
- Method: public-surface and usage inspection, consumer search, test/example review,
  and comparison against the approved contract. No repository-wide audit was performed.
- Result: one local, behavior-preserving removal applied; no speculative abstraction or
  duplicate representation warranted a new task/ADR.

## Candidates and dispositions

| Candidate | Consumer evidence | Net effect | Disposition |
|---|---|---|---|
| `DelegationPolicyMiddleware.controller` property | No production, test, example, or documented consumer; the controller is already held by the middleware and exposed through `SupervisorAssembly`. | Removes 4 lines of unused accessor; behavior and public contract unchanged. | **Applied** as final diff cleanup under T053; package tests and gates re-run. |
| `DiagnosticEmitter.emit` (sync path) | Used by `DelegationDiagnosticsMiddleware.wrap_tool_call`; sync execution is a supported native path. | Not removable without breaking sync diagnostics. | Keep. |
| `DiagnosticEvent.detail` | Not populated by current emitters; part of the approved public event contract for bounded non-secret metadata. Tests cover immutability. | Removing would be a public-contract change for an intentional extension field. | Keep; documented as an optional field. |
| `SubagentReport.warnings` | Defaults to empty; part of the approved report contract and available for fork/compiled reporting. | Removing would change the public report shape; no behavioral defect. | Keep; empty tuple is valid. |
| `ModelCatalogLike` protocol | Accepts the concrete `ModelCatalog` plus structural test doubles without importing the adapter into the core binding logic. | Replacing it with a concrete type would increase coupling and test setup. | Keep; not speculative. |
| `DelegationPolicyMiddleware` and `DelegationDiagnosticsMiddleware` | Separate policy enforcement from event emission; both are composed in `build_supervisor` and have distinct failure/cleanup responsibilities. | Merging would couple diagnostics to policy and make optional diagnostics harder to reason about. | Keep; different owners. |
| `_empty_worker_overrides` and typed `default_factory` helpers | Required to keep Pyright strict happy with immutable dataclass defaults. | Removing reintroduces partially-unknown types or mutable defaults. | Keep. |
| `DelegationStats` from the data-model sketch | Never implemented or exported; the contract exposes counters directly on `DelegationController`. | No code to delete; adding it would be speculative. | Do not add. |

## Not simplified / rejected

- No duplicate model-file, credential, Provider SDK, retry, or tracing layer exists in the
  package; those behaviors remain with the model adapter or host as designed.
- No hand-rolled DeepAgents subagent registry or Middleware replacement logic exists; the
  package delegates name/ordering semantics to upstream.
- No redundant lifecycle state was found. The controller's active/waiting counters are the
  operational state, and the assembly report is an immutable snapshot.
- No test-only public behavior was found: examples and tests exercise the same public
  entry points used by hosts.

## Verification after the applied removal

- `uv run --locked --no-sync --directory packages/infra/agent-deepagents pytest ... tests -q`
- `uv run ... ruff check ... src tests`
- `uv run ... pyright ... src tests`
- `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents`
- `pwsh -NoProfile -File scripts/quality.ps1 -Check docs`
- `pwsh -NoProfile -File scripts/quality.ps1 -Check governance`
- `pwsh -NoProfile -File scripts/quality.ps1 -Check static`

Exact results are recorded in `evidence.md` and the final review report.
