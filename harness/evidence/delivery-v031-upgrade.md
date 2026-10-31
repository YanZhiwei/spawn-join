# Evidence — Delivery Bundle v0.3.1 upgrade

## Identity and scope

- **feature_id**: `delivery-v031-upgrade` (Lightweight run label; no Feature created)
- **phase_id**: `delivery-v031-upgrade`
- **base_revision**: `8f445086599152b00d2e01fd36c134d97ad6942c`
- **head_revision**: `working-tree`
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-11-01
- **result**: pass for scoped bundle upgrade consistency, asset checksum verification and generated-command checks; Workflows and independent Doctor prompt not run

Route: **Lightweight**. v0.3.1 adds the Docs Sync package-README node and configuration. It
does not change Python behavior, package dependencies, public APIs, architecture or durable
runtime data, so no Spec/Plan/Tasks, delivery Workflow run or Ralph queue is required.

The project started from `main` at `8f44508` with a clean worktree. The upgrade was exercised
first in an isolated file-level copy of the worktree (excluding `.git`, `.venv`, `.codegraph`
and caches), then applied to the target with the Bundle update path. The installer performed no
push, merge, publication, hook or autonomous workflow execution.

## Changed paths and ownership

- Installer-owned `.opencode/commands/speckit.*` and `.specify/extensions/**`: refreshed to
  `0.3.1`; new `speckit.docs-sync.package-readme` command and
  `extensions/docs-sync/templates/package-readme.md`.
- Installer-owned `.specify/workflows/**`, `.specify/{extension,workflow,bundle}-catalogs.yml`,
  `bundle-records.json` and `extensions/.registry`: pinned to v0.3.1 catalogs and versions.
- Project-owned `.specify/extensions/docs-sync/docs-sync-config.yml`: adds explicit
  `package_readme: auto` and `package_roots: []`; other `*-config.yml`, `extensions.yml` and
  `tasks-template.md` are byte-preserved.
- Project-owned `docs/development/spec-kit-delivery.md`, `AGENTS.md`, `README.md` and
  `harness/README.md`: current version, command count and package-README policy updated.
- This evidence and `harness/build-log.md`: upgrade record.

`packages/`, `scripts/`, CI, runtime dependencies, Constitution, core Spec Kit skills/templates,
global configuration, historical Specs and remote metadata are unchanged.

## Source, permissions and reproducibility

Source: [v0.3.1 Release](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.3.1),
MIT-licensed tooling. All 10 release ZIP assets were downloaded and their SHA-256 digests
matched the release metadata (`10/10`). Catalogs were read from the pinned tag
`v0.3.1/catalogs/`. Specify CLI remains 1.2.3 / Python 3.13.5; Bug remains the CLI-bundled
1.0.1. Ten Delivery extensions and three Workflows are 0.3.1, for 13 Bundle components.

Public GitHub downloads are read-only. Only the local project, an isolated temporary fixture and
owned temporary directories were written; no private content was uploaded. The installer
performed no staging, commit, push, merge, publication, hooks or autonomous workflow execution;
the upgrade commit and its PR are separate authorized actions.

Owned temporary root for this run:
`C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-v031-fixture` (file-level pre-upgrade copy
used to exercise the Bundle update and diff the result). It is removed after verification and is
not a durable record.

## What changed in v0.3.1

- `speckit.docs-sync.package-readme` creates or refreshes a package README from the package's
  real manifest, public exports, CLI, configuration, dependencies and test commands.
- `extensions/docs-sync/templates/package-readme.md` is the packaged structure for that contract.
- All three lane workflows run the node after the final code-affecting step and before review.
- Docs Sync configuration adds `package_readme: auto | required | off` and `package_roots`.
- Doctor requires Docs Sync for every lane and verifies the command, template and placement.

## Verification

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | Isolated fixture `specify bundle update speckit-delivery` | 0 | Three Workflows reinstalled; Bundle updated to v0.3.1 |
| 2 | Target catalog update + `specify bundle update speckit-delivery` | 0 | Same three Workflows; target updated to v0.3.1 |
| 3 | `specify bundle list --json` | 0 | Bundle `0.3.1`; 10 extensions at `0.3.1` plus Bug `1.0.1`; 3 Workflows at `0.3.1` |
| 4 | Config/template hash comparison | 0 | Seven untouched `*-config.yml`, `extensions.yml` and `tasks-template.md` unchanged; only Docs Sync changed intentionally |
| 5 | `Get-ChildItem .opencode/commands -Filter 'speckit.*.md'` | 0 | 38 commands; `speckit.docs-sync.package-readme.md` present |
| 6 | Package README presence | 0 | All four Distribution READMEs exist |
| 7 | Release asset SHA-256 check | 0 | 10 assets, `10/10` match release digests |
| 8 | `quality.ps1 -Check governance` | 0 | 0 error; 1 pre-existing freshness warning |
| 9 | `quality.ps1 -Check docs` | 0 | 80 files / 207 local targets |
| 10 | `git diff --check` | 0 | No whitespace errors |

## Doctor and standards assessment

```text
SD_DOCTOR_VERDICT: not-run
INTEGRATION: opencode (Codex retained)
COMPONENTS: 13 Bundle components installed at their expected versions
WORKFLOWS: all three at 0.3.1; package-README node present
POLICY_COVERAGE: seven existing profiles unchanged; Quality owns mechanical checks;
  Review/Simplify/ADR own semantic standards; repair budget remains 2
MANUAL CONTRACT CHECKS: package-README command/template/pre-review placement,
  Docs Sync config, close fields, merge policy, PR template, Handoff path, hooks
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

- v0.3.1 does not rewrite existing package READMEs. The package-README node runs on the next
  package change; the project chose `package_readme: auto`, so gaps are reported rather than
  blocking. All four packages currently have READMEs.
- The node was not executed in this install; no package README was regenerated or reviewed.
- Direct Workflow execution, independent Review, Doctor agent run and a real Feature/Bugfix/
  Ralph delivery were not run for this patch release.
- Command count is 38 (28 extension commands + 10 core); the previous baseline was 37.
- LF/CRLF warnings are existing platform behavior; installer-refreshed files may appear in
  `git status` as line-ending-only entries even when their content hash matches the index.
  `git diff --name-only` remains the content diff.
- Later material changes require renewed confirmation rather than reuse of this record.

## Rollback

Revert the upgrade commit and run the v0.3.0 Bundle catalog update/`bundle update` path to
restore the previous generated commands and Workflows; remove the two `package_readme` keys from
Docs Sync. Project configs, core templates, Python code and runtime data are otherwise
unaffected.
