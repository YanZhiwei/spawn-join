# Evidence — Delivery Bundle v0.3.0 upgrade

## Identity and scope

- **feature_id**: `delivery-v030-upgrade` (Lightweight run label; no Feature created)
- **phase_id**: `delivery-v030-upgrade`
- **base_revision**: `8d804f64511491757418abcb33b9452b49f4f1fd`
- **head_revision**: `working-tree`
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-31
- **result**: pass for scoped bundle upgrade consistency, asset checksum verification and generated-command checks; Workflows and independent Doctor prompt not run

Route: **Lightweight**. v0.3.0 is an upstream minor release of development tooling. It adds
`speckit.delivery.close` and changes the evidence/workspace model, but does not change Python
behavior, package dependencies, public APIs, architecture or durable runtime data, so no
Spec/Plan/Tasks, delivery Workflow run or Ralph queue is required.

The project started from `main` at `8d804f6` with a clean worktree. The upgrade was exercised
first in an isolated file-level copy of the worktree (excluding `.git`, `.venv`, `.codegraph`
and caches), then applied to the target with the Bundle update path. The installer performed no
push, merge, publication, hook or autonomous workflow execution.

## Changed paths and ownership

- Installer-owned `.opencode/commands/speckit.delivery.*` and
  `.specify/extensions/**`: refreshed to `0.3.0`; new
  `speckit.delivery.close` command and Delivery close semantics.
- Installer-owned `.specify/workflows/**`,
  `.specify/{extension,workflow,bundle}-catalogs.yml`, `bundle-records.json` and
  `extensions/.registry`: pinned to v0.3.0 catalogs and versions.
- Project-owned `.specify/extensions/<ext>/*-config.yml`, `.specify/extensions.yml` and
  `.specify/templates/tasks-template.md`: byte-preserved (see verification table).
- Project-owned `docs/development/spec-kit-delivery.md`, `AGENTS.md`, `README.md` and
  `harness/README.md`: current version, `close` semantics and command count updated.
- `.specify/delivery/008-langchain-first-llm-runtime/evidence.md`: outcome fields added per the
  `speckit.delivery.close` contract (`status: delivered`, `pull_request: 18`,
  `outcome_recorded_at`, `merged_revision`); history sections unchanged.
- This evidence and `harness/build-log.md`: upgrade record.

`packages/`, `scripts/`, CI, runtime dependencies, Constitution, core Spec Kit skills/templates,
global configuration, historical Specs and remote metadata are unchanged.

## Source, permissions and reproducibility

Source: [v0.3.0 Release](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.3.0),
MIT-licensed tooling. All 10 release ZIP assets were downloaded and their SHA-256 digests
matched the release metadata (`10/10`). Catalogs were read from the pinned tag
`v0.3.0/catalogs/`. Specify CLI remains 1.2.3 / Python 3.13.5; Bug remains the CLI-bundled
1.0.1. Ten Delivery extensions and three Workflows are 0.3.0, for 13 Bundle components.

Public GitHub downloads are read-only. Only the local project, an isolated temporary fixture and
owned temporary directories were written; no private content was uploaded. The installer
performed no staging, commit, push, merge, publication, hooks or autonomous workflow execution;
the upgrade commit and its PR are separate authorized actions.

Owned temporary root for this run:
`C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-v030-fixture` (file-level pre-upgrade copy
used to exercise the Bundle update and diff the result). It is removed after verification and is
not a durable record.

## What changed in v0.3.0

- `speckit.delivery.close` records the actual PR outcome: `merged` → `delivered`,
  closed-unmerged → `abandoned`, replaced → `superseded`; it never pushes, creates or merges a
  PR.
- `evidence.md` is always the durable record and binds the reviewed head plus the PR reference;
  the run workspace (`exploration.md`, `slices.md`, receipts, verdicts, reviews, rendered PR
  body) is separate and governed by `artifact_policy`.
- `speckit.delivery.doctor` reports missing/contradictory outcomes, unresolved
  `superseded_by`, and installation/upgrade records kept under the delivery root.
- Route, Handoff and lane references treat close-out as part of completion.
- No new required project configuration fields; the Delivery config template only clarifies
  `artifact_policy` semantics.

## Verification

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `specify version` | 0 | Specify CLI 1.2.3, Python 3.13.5, Windows AMD64 |
| 2 | Isolated fixture `specify bundle update speckit-delivery` | 0 | Three Workflows reinstalled; Bundle updated to v0.3.0 |
| 3 | Target catalog update + `specify bundle update speckit-delivery` | 0 | Same three Workflows; target updated to v0.3.0 |
| 4 | `specify bundle list --json` | 0 | Bundle `0.3.0`; 10 extensions at `0.3.0` plus Bug `1.0.1`; 3 Workflows at `0.3.0` |
| 5 | Config/template hash comparison | 0 | All eight `*-config.yml`, `extensions.yml` and `tasks-template.md` SHA-256 values unchanged |
| 6 | Target vs fixture `.specify`/`.opencode` diff | 0 | Identical except install registries (`bundle-records.json`, `extensions/.registry`, `workflow-registry.json`) that record install time/path |
| 7 | `Get-ChildItem .opencode/commands -Filter 'speckit.*.md'` | 0 | 37 commands; `speckit.delivery.close.md` present |
| 8 | Release asset SHA-256 check | 0 | 10 assets, `10/10` match release digests |
| 9 | `specify integration status` (fixture) | 0 | WARNING only for 18 pre-existing managed-file customizations; 0 missing/invalid/unchecked manifests |
| 10 | `git diff --check` | 0 | No whitespace errors |

## Doctor and standards assessment

```text
SD_DOCTOR_VERDICT: not-run
INTEGRATION: opencode (Codex retained)
COMPONENTS: 13 Bundle components installed at their expected versions
WORKFLOWS: all three at 0.3.0; installed command closure checked
POLICY_COVERAGE: seven existing profiles unchanged; Quality owns mechanical checks;
  Review/Simplify/ADR own semantic standards; repair budget remains 2
MANUAL CONTRACT CHECKS: close command and outcome fields, evidence/workspace split,
  merge policy, PR template, Handoff body path, reviewer template and hook settings
```

The Doctor is an Agent Prompt, not a PATH executable. The read-only contract checks above were
performed directly, but no independent Doctor agent run is claimed. The `integration status`
warnings are project-owned customizations, not missing installation files; `specify integration
upgrade --force` was deliberately not used.

Session-local standards assessment: installer owns commands/resources, project owns configs and
core task customizations; no duplicate template was created; dependency direction and Python
public APIs are unchanged; existing gates are reused; automatic hooks and remote writes stay
disabled. This is not an independent Review, a Ralph receipt, or an end-to-end semantic workflow
pass.

## Compatibility and limitations

- v0.3.0 changes the delivery evidence lifecycle: `evidence.md` now binds the reviewed head and
  PR reference, and the outcome is recorded afterwards through `speckit.delivery.close`. The
  previously merged 008 run was updated with `status: delivered`, `pull_request: 18`,
  `outcome_recorded_at: 2026-10-31` and `merged_revision: 468ee7f`; its history and workspace were
  retained because `merged` runs keep their artifacts.
- The close update was applied by following the installed command contract, not by running the
  Agent Prompt end-to-end; no independent review of that record is claimed.
- Installer/upgrade records already live under `harness/evidence/`, the project's durable
  evidence root, so no migration from `.specify/delivery/<id>/` was required.
- Direct Workflow execution, independent Review, Doctor agent run and a real Feature/Bugfix/
  Ralph delivery were not run for this tooling-only release.
- Command count is 37 (27 extension commands + 10 core); the previous baseline was 36.
- LF/CRLF warnings are existing platform behavior; installer-refreshed files may appear in
  `git status` as line-ending-only entries even when their content hash matches the index.
  `git diff --name-only` remains the content diff.
- Later material changes require renewed confirmation rather than reuse of this record.

## Rollback

Revert the upgrade commit and run the v0.2.2 Bundle catalog update/`bundle update` path to
restore the previous generated commands and Workflows. Project configs, core templates, Python
code and runtime data are unaffected, so no migration or cleanup is required.
