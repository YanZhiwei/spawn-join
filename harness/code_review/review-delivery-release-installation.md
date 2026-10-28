# Standards Review — Release-managed Delivery installation

- Date: 2026-10-28
- Base/head: `fdd0c072186ef3cea7f4b3261acd1d82b358ef56` plus the uncommitted migration.
- Scope: Release component installation, native host rendering, project configs, copied-facade
  removal, two governance-check adaptations, and their docs/tests/evidence.
- Review type: session-local Standards Review, not an independent-agent or approved PR review.

## Findings

| ID | Classification | Evidence / disposition |
|---|---|---|
| RI-001 | Resolved in v0.1.1 | v0.1.0 Bundle catalog failed; v0.1.1 fixed the catalog contract, published verified assets, and is now installed as a 12-component Bundle. Do not fall back to v0.1.0. |
| RI-002 | Preserved customization | Codex tasks skill and shared tasks template match backup. Integration warnings also include the extended machine-local ignore policy; do not force overwrite them. |
| RI-003 | Environment blocker | Default local static checks lack PSScriptAnalyzer 1.25.0. All configured checks passed with an explicit temporary module path; default-environment Doctor readiness is not claimed. |
| RI-004 | Resolved | Valid quoted gate was rejected and unquoted invalid YAML accepted by the old pattern. Both quote styles now pass and the unquoted form fails; red/green fixtures recorded. |
| RI-005 | Resolved | Installer-owned README/prompt links retain upstream context. Exclude those vendor surfaces from project-link validation instead of modifying release bytes; fixture covers the boundary. |
| RI-006 | Deliberate boundary | User-level shared copies are untouched. The project uses dot-separated native commands, confirmed through live OpenCode API discovery, not old global wrappers. |
| RI-007 | Resolved | PR #8 merged as `2b8b70d`; main Quality 14/14 passed. ADR-0004 is Accepted and tasks are closed. No Ralph loop or task receipt is claimed. |

## Standards verdict

```text
STANDARDS_VERDICT: pass
HEAD: 2b8b70db080096a5d12ee399409e3cd4c40dfa2f (PR #8 merge commit)
SCOPE: release-installation-working-tree
PATHS: .opencode/commands/; .specify/ (including bundle-records and catalogs); removed project facades; scripts/check-governance.ps1; scripts/test-governance.ps1; project docs and Harness records
EXCLUDED_PATHS: vendor implementation/prompt semantics outside this migration; user-level shared files
POLICY_SOURCES: Constitution; AGENTS.md; package boundaries; quality-gates.md; ADR-0001/0002/0003; Proposed ADR-0004
FINDINGS:
- ownership: pass — installer owns components/rendering; project owns config; no second runtime framework
- dependency-direction: pass — packages, runtime dependencies and public APIs unchanged
- DRY: pass — copied lifecycle facades removed; native checks reused through six profiles
- permissions: pass — auto hooks off; no Ralph, target-repository staging/commit, remote writes or private service access
- tests: pass — scoped failures established before adaptations; the governance suite has since expanded to 20 scenarios (including Delivery evidence and truncated-revision rejection)
ADR_IMPACT: propose
BLOCKERS:
- none for the scoped installation implementation; default-environment readiness remains separately blocked
FOLLOW_UP:
- upstream Bundle compatibility; local static-tool availability; authorized reviewed-HEAD closure
```

Generic generated prompts do not override mandatory project behavior-test policy. Core task
customizations are deliberately retained. Review does not convert mechanical check results into
architecture approval or make temporary environment setup permanent.

## Re-review — 2026-10-28

The follow-up audit added Delivery evidence validation, truncated-revision rejection,
`artifact_policy`/ADR safety checks, automatic-hook rejection, and a shared-tool Quality
Profile. `scripts/test-governance.ps1` now passes 20 scenarios; the existing 16 were retained
and four rejection scenarios were added. The review scope and verdict boundaries are unchanged:
this remains a session-local Standards Review of an uncommitted working tree, not a Ralph or
independent PR approval. See [installation evidence](../evidence/delivery-release-installation.md)
for actual commands, source/hash checks, preservation checks, environments and failed attempts.

## v0.1.1 Bundle re-review — 2026-10-28

RI-001 is resolved by the published v0.1.1 Bundle. The target migration preserved six extension
configs, the core tasks skill, the shared tasks template and the auto-hook-off setting; Bundle
ownership covers 12 components. RI-003 (default PSScriptAnalyzer) remains an environment
limitation. This re-review does not convert Bundle installation into Ralph execution or an
independent PR approval.

## Closure — 2026-10-28

PR #8 was merged as `2b8b70db080096a5d12ee399409e3cd4c40dfa2f`. The main Quality run
[40699123377](https://github.com/YanZhiwei/spawn-join/actions/runs/40699123377) passed 14/14
jobs. ADR-0004 is Accepted, tasks T001–T009 are complete, and RI-007 is resolved. No real
Ralph loop was run.
