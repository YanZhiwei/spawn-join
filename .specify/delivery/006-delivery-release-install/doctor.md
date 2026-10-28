# Delivery Doctor — Release installation audit

This follows the installed `.opencode/commands/speckit.delivery.doctor.md` read-only contract.
Installation is coherent; the verdict below describes the **default local environment**, not
the separately verified environment with a temporary PSScriptAnalyzer path.

```text
SD_DOCTOR_VERDICT: blocked
INTEGRATION: opencode (Codex retained)
COMPONENTS:
- Bundle speckit-delivery 0.1.1: installed — 12 contributed components; record and catalogs verified
- delivery/decision/ralph/review/simplify/evidence/quality/docs-sync: installed — v0.1.1 published catalog; manifests/registry/native commands verified
- bug: installed — v1.0.1 bundled with Specify CLI 1.2.3
WORKFLOWS:
- feature-delivery: ready — v0.1.1 published catalog; 21 unique commands resolve
- bugfix-delivery: ready — v0.1.1 published catalog; 13 unique commands resolve
- lightweight-delivery: ready — v0.1.1 published catalog; 8 unique commands resolve
POLICY_COVERAGE:
- four Distribution profiles: covered — original locked quality commands, all executed successfully
- project automation: covered — static checks and 9/20/3 regression suites executed successfully
- governance/docs: covered — source/link/structure checks executed successfully
- DRY/ownership/public API/comments: covered — review owner and applicable policy sources
- simplification/architecture decisions: covered — Simplify and ADR owner/mechanism
BLOCKERS:
- local-static-tool: default PSModulePath lacks PSScriptAnalyzer 1.25.0; provide the documented module before default-environment autonomous execution
```

All configured Profile commands passed when the fixed module was supplied through an explicit
process-local `PSModulePath`; no global module installation was performed. The live OpenCode
service lists all 31 project-native commands. Bundle v0.1.1 installation is verified; this audit
does not run a Workflow or Ralph. A global environment change needs separate scope.
