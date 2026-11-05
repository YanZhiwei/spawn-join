# Evidence — Delivery Bundle v0.4.1 upgrade

## Identity and scope

- **feature_id**: `delivery-v041-upgrade` (operational Lightweight run label; no Feature created)
- **phase_id**: `delivery-v041-upgrade`
- **route**: Lightweight（安装/升级交付工具，不创建 Feature 工件）
- **base_revision**: `8114053955d038679bc3041870719cb4325d6af0`
- **head_revision**: `working-tree`（本记录绑定本次安装后的 outgoing diff）
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: `2026-11-05`
- **result**: pass for the v0.4.1 Bundle/catalog upgrade and component registration; expected managed-file and historical freshness warnings remain
- **environment**: Windows, PowerShell 7, Specify CLI 1.2.3, Python 3.13.5

This is a release-managed tooling upgrade. It changes installer-managed commands,
manifests, catalogs, workflows, and project governance documentation; it does not
change Python package source, runtime dependencies, public APIs, or application data.
The pre-existing untracked `.specify/delivery/011-deepagents-product-capabilities/pull-request.md`
was retained and was not included in this installation scope.

## Source and release identity

- Release: [speckit-delivery v0.4.1](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.4.1)
- Annotated tag object: `4cedb363d9c03362e68a2d8f7796c84ff8a55534`
- Tag commit: `25a696361d3cbfff558fed61a0a43afd2780b7dd`
- Specify CLI: `1.2.3`
- Extension catalog URL: `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.1/catalogs/extensions.json`
  - GitHub contents SHA: `41ebe7c46d7b0a33abad7bb3c373e5d8091800b0`
- Workflow catalog URL: `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.1/catalogs/workflows.json`
  - GitHub contents SHA: `e7e1a0f56cd19291f5f33c49e8a5f5d372fe8ec1`
- Bundle catalog URL: `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.1/catalogs/bundles.json`
  - GitHub contents SHA: `dc80c3c5fab468480612d9ab417dd2a028559713`

The three published catalogs were read-only inspected before changing local catalog
sources. The catalog manifest declares 10 extensions, 3 workflows, and the v0.4.1
Bundle requires Specify CLI `>=1.2.3`.

## Changed paths and ownership

Installer-managed paths were refreshed by the catalog switch and
`specify bundle update speckit-delivery`, including:

- `.opencode/commands/speckit.*.md` and the manifest-provided `.opencode/commands/sd.md`
- `.specify/extensions/**` (v0.4.1 commands, runtime helper, templates, and manifests)
- `.specify/workflows/**`
- `.specify/extension-catalogs.yml`
- `.specify/workflow-catalogs.yml`
- `.specify/bundle-catalogs.yml`
- `.specify/bundle-records.json`
- `.specify/extensions/.registry`
- `.specify/workflows/workflow-registry.json`

Project-owned paths updated to keep the durable description accurate:

- `AGENTS.md`: current Bundle version and v0.4.1 capability summary
- `docs/development/spec-kit-delivery.md`: current release, alias behavior, upgrade path,
  verification and evidence link
- `docs/decisions/engineering/0004-release-managed-delivery-installation.md`: current
  release status and revision history
- `harness/build-log.md`: operational upgrade entry
- `harness/evidence/delivery-v041-upgrade.md`: this record

The following protected project files were compared byte-for-byte with the pre-upgrade
backup and remained unchanged:

- `.specify/extensions.yml`
- `.specify/extensions/delivery/delivery-config.yml`
- `.specify/extensions/quality/quality-config.yml`
- `.specify/extensions/docs-sync/docs-sync-config.yml`
- `.specify/templates/tasks-template.md`

The old thin `/sd` project wrapper was replaced by the v0.4.1 installer-managed alias,
which is the declared upstream ownership model. No `specify integration upgrade --force`
was used.

## Observed commands and results

| # | Command/check | Exit | Result |
|---|---|---:|---|
| 1 | `git status --short --branch; git rev-parse HEAD` | 0 | Baseline `main`, `HEAD 8114053`; one pre-existing untracked PR body |
| 2 | `specify version` | 0 | Specify CLI 1.2.3 available |
| 3 | Release page, tag, and three v0.4.1 catalogs read-only audit | 0 | Release and pinned catalog identities recorded above |
| 4 | Installer-managed `.specify`/`.opencode/commands` backup | 0 | Backup at `C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-delivery-v041-6fa781357d0b4a13aa4724a63961c371` |
| 5 | Three Catalog remove/add pairs for the v0.4.1 URLs | 0 | Extension, Workflow, and Bundle sources switched to v0.4.1 |
| 6 | `specify bundle update speckit-delivery` | 0 | Bundle updated; all three Delivery workflows reinstalled |
| 7 | `specify bundle list --json` | 0 | Bundle 0.4.1; 10 extensions and 3 workflows at 0.4.1; Bug remains 1.0.1 |
| 8 | `specify extension list` / `specify workflow list` | 0 | All expected components enabled; v0.4.1 `sd` alias/runtime capability present |
| 9 | `specify integration status` | 0 | No missing/invalid paths; 18 expected managed-file customization warnings |
| 10 | Protected-file SHA-256 comparison | 0 | Configurations and Tasks template unchanged |
| 11 | OpenCode command and new-file inspection | 0 | 39 `speckit.*` commands, `sd.md`, runtime helper, Core/Ralph templates present |
| 12 | `py -3` AST parse and runtime `--help` smoke check | 0 | New runtime helper parses and exposes the expected CLI |
| 13 | `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 102 files / 258 local targets; documentation checks passed |
| 14 | `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors / 1 historical freshness warning |
| 15 | `pwsh -NoProfile -File scripts/test-governance.ps1` | 0 | 23 governance regression scenarios passed |
| 16 | `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | 11 quality-gate regression scenarios passed |
| 17 | `pwsh -NoProfile -File scripts/test-static.ps1` | 0 | 3 static-analysis regression scenarios passed |
| 18 | `git diff --check` | 0 | No whitespace errors; Git emitted normal LF/CRLF working-copy warnings |

## Verification state

- **Installation/catalog consistency**: pass.
- **Configuration/customization preservation**: pass for the protected files listed above.
- **Managed integration status**: pass with warnings; the installer reports 1 modified Codex,
  10 modified OpenCode, and 7 modified shared Spec Kit managed files. These pre-existing
  customizations were not force-upgraded.
- **Product/package quality gates**: not applicable to the installer-only diff; no Python source,
  package metadata, or runtime dependency changed.
- **Delivery workflow/Doctor/Ralph**: not run. Installation does not claim a completed Feature,
  Bugfix, Ralph loop, or full Delivery cycle.

## v0.4.1 behavior observed

- Delivery manifest declares `aliases: [sd]`; the installer now owns `/sd` alongside the route.
- Delivery includes the standard-library `delivery_runtime.py` helper and runtime/Core adapter
  templates for explicit `delivery_run`, resume, checkpoint, and conditional owner dispatch.
- Review-before-Quality/Standards refreshes use runtime `needs` checks so current passing receipts
  can be reused.
- A no-candidate Simplify scan is excluded from the canonical snapshot and does not invalidate
  current Quality/Standards receipts.

## Known limitations and follow-up

- `specify integration status` continues to report the existing managed-file customization
  warnings. No `--force` overwrite was authorized or performed.
- The installation evidence is scoped to the local working tree before the PR commit; after the
  PR branch is created, commit/remote CI evidence must be recorded separately.
- No remote write, push, PR, merge, or publication was performed as part of the installation
  commands recorded above.

## Rollback

Restore the backed-up installer-managed paths if necessary, restore the v0.3.2 catalog URLs,
and run the documented v0.3.2 `specify bundle update speckit-delivery` path. Do not manually
edit generated commands or Bundle records to conceal version drift; retain this evidence as the
historical v0.4.1 installation record.
