# Evidence — Delivery Bundle v0.4.2 upgrade

## Identity and scope

- **feature_id**: `delivery-v042-upgrade` (operational Lightweight run label; no Feature created)
- **phase_id**: `delivery-v042-upgrade`
- **route**: Lightweight（安装/升级交付工具，不创建 Feature 工件）
- **base_revision**: `1ced9fe00ff9fb609642f54d989ede3876389a95`
- **head_revision**: `working-tree`（本记录绑定本次安装后的 outgoing diff）
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: `2026-11-05`
- **result**: pass for the v0.4.2 Bundle/catalog upgrade and component registration; expected managed-file and historical freshness warnings remain
- **environment**: Windows, PowerShell 7, Specify CLI 1.2.3, Python 3.13.5

This is a release-managed tooling upgrade. It changes installer-managed commands,
manifests, catalogs, workflows, runtime helpers, and project governance
documentation; it does not change Python package source, runtime dependencies,
public APIs, or application data. The pre-existing untracked
`.specify/delivery/011-deepagents-product-capabilities/pull-request.md` was retained
and was not included in this installation scope.

## Source and release identity

- Release: [speckit-delivery v0.4.2](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.4.2)
- Annotated tag object: `f1375b339a1ad5a3bab7b294e6a1cf355eecc83c`
- Tag commit: `0b468f45363d1eff57e7fd340d6c5dce13fade01`
- Specify CLI: `1.2.3`
- Extension catalog URL: `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.2/catalogs/extensions.json`
  - GitHub contents SHA: `bf029d1fa61b55dbf05e2ed3b44a5be39047817b`
- Workflow catalog URL: `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.2/catalogs/workflows.json`
  - GitHub contents SHA: `6293e01a6d84993b82f98a9539ac740f934a5a3a`
- Bundle catalog URL: `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.2/catalogs/bundles.json`
  - GitHub contents SHA: `1ece0235fba97ac2b8900e1b0fa43073a3f84e09`

The three published catalogs were read-only inspected before changing local catalog
sources. The v0.4.2 Bundle manifest declares 10 extensions, 3 workflows, and
requires Specify CLI `>=1.2.3`.

## Changed paths and ownership

Installer-managed paths were refreshed by the catalog switch and
`specify bundle update speckit-delivery`, including:

- `.opencode/commands/speckit.*.md` and the manifest-provided `.opencode/commands/sd.md`
- `.specify/extensions/**` (v0.4.2 commands, runtime/task/outcome helpers, templates, and manifests)
- `.specify/workflows/**`
- `.specify/extension-catalogs.yml`
- `.specify/workflow-catalogs.yml`
- `.specify/bundle-catalogs.yml`
- `.specify/bundle-records.json`
- `.specify/extensions/.registry`
- `.specify/workflows/workflow-registry.json`

Project-owned paths updated to keep the durable description accurate:

- `AGENTS.md`: current Bundle version and v0.4.2 capability summary
- `docs/development/spec-kit-delivery.md`: current release, task-close/outcome behavior,
  upgrade path, verification and evidence link
- `docs/decisions/engineering/0004-release-managed-delivery-installation.md`: current
  release status and revision history
- `harness/build-log.md`: operational upgrade entry
- `harness/evidence/delivery-v042-upgrade.md`: this record

The following protected project files were compared byte-for-byte with the pre-upgrade
backup and remained unchanged:

- `.specify/extensions.yml`
- `.specify/extensions/delivery/delivery-config.yml`
- `.specify/extensions/quality/quality-config.yml`
- `.specify/extensions/docs-sync/docs-sync-config.yml`
- `.specify/templates/tasks-template.md`

The v0.4.2 update keeps the Bundle-managed `/sd` alias and adds the task-close and
outcome helpers. No `specify integration upgrade --force` was used.

## Observed commands and results

| # | Command/check | Exit | Result |
|---|---|---:|---|
| 1 | `git switch main; git pull --ff-only origin main` | 0 | Started from current `main`; local and remote base `1ced9fe` |
| 2 | `specify version` | 0 | Specify CLI 1.2.3 available |
| 3 | Release page, tag, and three v0.4.2 catalogs read-only audit | 0 | Release and pinned catalog identities recorded above |
| 4 | Installer-managed `.specify`/`.opencode/commands` backup | 0 | Backup at `C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-delivery-v042-206427601fde440a8ca240e97430fee6` |
| 5 | Three Catalog remove/add pairs for the v0.4.2 URLs | 0 | Extension, Workflow, and Bundle sources switched to v0.4.2 |
| 6 | `specify bundle update speckit-delivery` | 0 | Bundle updated; all three Delivery workflows reinstalled |
| 7 | `specify bundle list --json` | 0 | Bundle 0.4.2; 10 extensions and 3 workflows at 0.4.2; Bug remains 1.0.1 |
| 8 | `specify extension list` / `specify workflow list` | 0 | All expected components enabled at v0.4.2 |
| 9 | `specify integration status` | 0 | No missing/invalid paths; 18 expected managed-file customization warnings |
| 10 | Protected-file SHA-256 comparison | 0 | Configurations and Tasks template unchanged |
| 11 | OpenCode command and new-file inspection | 0 | 39 `speckit.*` commands, `sd.md`, task/outcome/runtime helpers, and updated templates present |
| 12 | `py -3` AST parse and runtime `--help` smoke check | 0 | v0.4.2 runtime, task, and outcome helpers parse and expose task-close/Close operations |
| 13 | `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 103 files / 260 local targets; documentation checks passed |
| 14 | `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors / 1 historical freshness warning |
| 15 | `pwsh -NoProfile -File scripts/test-governance.ps1` | 0 | 23 governance regression scenarios passed |
| 16 | `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | 11 quality-gate regression scenarios passed |
| 17 | `pwsh -NoProfile -File scripts/test-static.ps1` | 0 | 3 static-analysis regression scenarios passed |
| 18 | `git diff --check` | 0 | No whitespace errors; Git emitted normal LF/CRLF working-copy warnings |

## v0.4.2 behavior observed

- Ralph receives executable task-close transport through `delivery_tasks.py` and the
  central runtime: task start, task gate, task commit association, and task-closure audit.
- Task closure validates the original branch/HEAD, allowed paths, native task-scoped
  Quality/Standards/Review evidence, committed Git blobs/modes, parent, and checkbox transition.
- Close outcome handling is separated into `delivery_outcome.py`; it keeps reviewed head,
  original PR head, base, and merged revision distinct and writes the current outcome atomically.
- Slice planning now distinguishes internal review/execution slices from later publication
  groups, so one PR can represent multiple internal slices without changing the execution queue.
- The installed `/sd` path and legacy forwarding behavior are covered by the v0.4.2 release's
  runtime behavior probes; this installation did not run a Delivery workflow.

## Verification state

- **Installation/catalog consistency**: pass.
- **Configuration/customization preservation**: pass for the protected files listed above.
- **Managed integration status**: pass with warnings; the installer reports 1 modified Codex,
  10 modified OpenCode, and 7 modified shared Spec Kit managed files. These existing
  customizations were not force-upgraded.
- **Product/package quality gates**: not applicable to the installer-only diff; no Python source,
  package metadata, or runtime dependency changed.
- **Delivery workflow/Doctor/Ralph**: not run. Installation does not claim a completed Feature,
  Bugfix, Ralph loop, or full Delivery cycle.

## Known limitations and follow-up

- `specify integration status` continues to report the existing managed-file customization
  warnings. No `--force` overwrite was authorized or performed.
- The installation evidence is scoped to the local working tree before the PR commit; after the
  PR branch is created, commit/remote CI evidence must be recorded separately.
- No remote write, push, PR, merge, or publication was performed as part of the installation
  commands recorded above.

## Rollback

Restore the backed-up installer-managed paths if necessary, restore the v0.4.1 catalog URLs,
and run the documented v0.4.1 `specify bundle update speckit-delivery` path. Do not manually
edit generated commands or Bundle records to conceal version drift; retain this evidence as the
historical v0.4.2 installation record.
