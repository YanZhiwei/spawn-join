# Evidence — Delivery Bundle v0.3.2 upgrade

## Identity and scope

- **feature_id**: `delivery-v032-upgrade` (operational Lightweight run label; no Feature created)
- **phase_id**: `delivery-v032-upgrade`
- **base_revision**: `5e8eb7e4029d5a2ae4835e59ef3759c2abc26d82`
- **head_revision**: `working-tree`
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: `2026-11-04`
- **result**: pass for the Bundle/catalog upgrade and component registration; docs quality remains blocked by a pre-existing historical Spec link

Route: **Lightweight**. This is an installation/upgrade of project delivery tooling. It changes
installer-managed commands, manifests, catalogs, and workflows, but does not add product behavior,
Python dependencies, public APIs, runtime data, or a Feature execution queue.

The upgrade was explicitly requested for release `v0.3.2` and used the existing Bundle update path.
It did not run a Delivery workflow, Ralph, review, publish, push, merge, or remote write.

## Source and release identity

- Release: [speckit-delivery v0.3.2](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.3.2)
- Release commit: `0a72947d983551d14ad011fec9a12ea66790ef15`
- Specify CLI: `1.2.3`
- Extension catalog URL: `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.3.2/catalogs/extensions.json`
  - GitHub contents SHA: `b2a6f255ec293df8fa0cc45e9a189b093cb5a044`
- Workflow catalog URL: `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.3.2/catalogs/workflows.json`
  - GitHub contents SHA: `68bb6cfe8890460729fca81b2362ce95d9809f6e`
- Bundle catalog URL: `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.3.2/catalogs/bundles.json`
  - GitHub contents SHA: `7cc6121aa99717f07e47f2fafe9c214d6f22b40a`

The three catalog objects were read-only verified through GitHub API before changing the local
catalog sources. The raw transport helper reported an unrelated transport error; the Specify
installer itself successfully fetched and installed the catalog contents.

## Changed paths and ownership

Installer-managed paths were refreshed by `specify bundle update speckit-delivery`, including:

- `.opencode/commands/speckit.*.md`
- `.specify/extensions/**`
- `.specify/workflows/**`
- `.specify/extension-catalogs.yml`
- `.specify/workflow-catalogs.yml`
- `.specify/bundle-catalogs.yml`
- `.specify/bundle-records.json`
- `.specify/extensions/.registry`
- `.specify/workflows/workflow-registry.json`

The v0.3.2 update added the `speckit.delivery.method` command and method-adapter templates,
and refreshed the three Delivery workflows.

Project-owned paths updated to keep the durable description accurate:

- `AGENTS.md`: current Bundle version and v0.3.2 capability summary.
- `docs/development/spec-kit-delivery.md`: current release, Catalog commands, command count,
  upgrade instructions, and evidence link.
- `harness/build-log.md`: operational upgrade entry.
- `harness/evidence/delivery-v032-upgrade.md`: this record.

Pre-existing user changes were retained, including the project `/sd` shortcut and its evidence.
No `packages/` or runtime source paths were changed.

## Verification

| # | Command | Exit | Result |
|---|---|---:|---|
| 1 | `specify version` | 0 | CLI 1.2.3 available |
| 2 | `specify integration status` before update | 0 | OpenCode default; existing managed-file customization warnings recorded |
| 3 | Three Catalog remove/add pairs for the v0.3.2 URLs | 0 | Extension, Workflow, and Bundle sources switched to v0.3.2 |
| 4 | `specify bundle update speckit-delivery` | 0 | Three Workflows reinstalled; Bundle updated to v0.3.2 |
| 5 | `specify bundle list --json` | 0 | 10 extensions and 3 Workflows at v0.3.2; Bug remains CLI-bundled 1.0.1 |
| 6 | `specify extension list` / `specify workflow list` | 0 | All installed components listed; `speckit.delivery.method` present |
| 7 | `specify integration status` after update | 0 | No missing or invalid managed paths; 18 modified managed files reported as warnings |
| 8 | `pwsh -NoProfile -File scripts/check-governance.ps1` | 0 | 0 errors; 1 pre-existing evidence freshness warning |
| 9 | `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors; same freshness warning |
| 10 | `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 1 | Pre-existing local `specs/007-llm-protocol-abstraction/plan.md` points to missing ADR-0005 |
| 11 | `git diff --check` | 0 | No whitespace errors; Git reported normal LF/CRLF working-copy warnings |

The installed command set contains 39 `speckit.*` commands: 29 extension commands and 10
core commands. The project-level `.opencode/commands/sd.md` remains separate and was not replaced
by the Bundle update.

## Known limitations and follow-up

- The generated v0.3.2 Doctor still references
  `.specify/extensions/delivery/templates/package-readme.md`; the actual package README template
  is owned by Docs Sync at `.specify/extensions/docs-sync/templates/package-readme.md`. This is
  recorded as an upstream/install-contract issue and was not fixed by hand in an installer-managed
  command.
- The historical local Spec link causing `quality.ps1 -Check docs` to fail was not changed in this
  installation upgrade.
- The earlier Delivery audit findings about stale historical run records and retired operational
  reports were not altered by this tooling installation.
- `specify integration status` still warns about project-customized managed files. No
  `specify integration upgrade --force` was run, so those customizations were not overwritten.
- `bundle-records.json` reports version `0.3.2`, but the installer preserves the original
  `installed_at` timestamp from the prior Bundle update; it was not manually rewritten.
- No Delivery workflow, Doctor agent run, Ralph task, independent Review, PR, push, merge, or
  publication was performed.

## Rollback

Restore the v0.3.1 Catalog URLs and run `specify bundle update speckit-delivery` through the
previous documented path. Do not manually edit generated commands or Bundle records to conceal
version drift; retain this evidence as the historical v0.3.2 installation record.
