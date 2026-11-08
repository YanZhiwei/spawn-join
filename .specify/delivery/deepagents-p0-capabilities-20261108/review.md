# Independent Review: deepagents-p0-capabilities-20261108

- Scope: outgoing diff on `feat/012-deepagents-official-p0` vs `7dbc714`
- Reviewer: separate read-only agent session (same model family; independence is
  process/session-level, not a different vendor)
- Date: 2026-11-08

## Dimensions

| Dimension | Result | Notes |
| --- | --- | --- |
| Requirements | pass | All three P0 stories and acceptance scenarios are represented; spec error type corrected. |
| Code quality | pass | No dead abstractions; new modules are cohesive; strict typing passes. |
| Architecture | pass | Host-owned resources untouched; no MCP/DB/UI boundary violation; beta gates explicit. |
| Correctness | pass after repair | Review found 4 blocking issues; all fixed before final gates. |
| Security / compatibility | pass | Report excludes URL/headers/paths; 0.7.32 contract pinned; no new dependency. |
| Test effectiveness | pass | 146 tests; new negative and beta-gate coverage; registration ordering asserted. |

## Blocking findings and disposition

1. **False “replaced default” claim for package-managed memory**
   - Fixed: removed `MemoryMiddleware` from `replaced_defaults`; docs now say the package
     passes `memory=None` and adds its own middleware; fork-inheritance limitation documented.
2. **Profile could exclude package-managed `MemoryMiddleware`**
   - Fixed: `ProfilesConfiguration.apply(extra_reserved=...)` receives
     `MemoryMiddleware` when the package manages memory; new test covers it.
3. **Async fork bypassed the fork gate**
   - Fixed: async forms now pass through `validate_experimental_fork`; async gate is checked
     first; README/ADR state both gates are required.
4. **Spec/error-type mismatch for reserved profile exclusions**
   - Fixed: spec now requires `ProfileConfigurationError`, matching code and tests.

## Non-blocking findings and disposition

- Provider profiles do not reshape already-resolved `BaseChatModel` instances.
  Documented in README and ADR; kept because the public registration surface is still
  useful for upstream string-model paths and for host parity.
- `update_strategy` default aligned to upstream `"interrupt"`; test asserts the default.
- Async `general-purpose` name is rejected and `_has_general_purpose` ignores async forms.
- Profile registration remains process-wide and has no rollback; validation now runs
  before registration and the residual side effect is documented.
- Registration-before-create ordering is now asserted in tests.

## Residual risks

- No live remote Agent Protocol server was exercised; async behavior is verified through
  the native kwargs/report contract only.
- Profile effects on a real model harness were not exercised.
- `fork` + package-managed memory limitation is documented but not integration-tested.
