# Evidence — Delivery Bundle v0.1.4 upgrade

## Identity and scope

- **feature_id**: `delivery-v014-upgrade` (Lightweight run label; no Feature created)
- **phase_id**: `delivery-v014-upgrade`
- **base_revision**: `881dcfeb4885c044d39071660606775509d64165`
- **head_revision**: `7bbd072aa60173c05384f55e10b4ee546474f523` (upgrade commit; this record is re-anchored one bookkeeping commit later)
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-29
- **result**: pass for scoped installation consistency and generated-command checks; Doctor blocked by environment

Route: **Lightweight**. This is an upstream patch-release upgrade of development tooling.
It does not change Python behavior, dependencies, public APIs, architecture or durable data,
so no Spec/Plan/Tasks, delivery Workflow run or Ralph queue is required.

The starting worktree already contained the uncommitted v0.1.3 upgrade from the same session
([record](delivery-v013-upgrade.md)); those changes were preserved and this upgrade applied
on top. The Git index and HEAD remain untouched.

## Changed paths and ownership

- Installer-owned `.opencode/commands/speckit.delivery.doctor.md`: corrected Reviewer
  template reference, plus version-stamped resource refreshes from the release.
- `.specify/{extension,workflow,bundle}-catalogs.yml`, `bundle-records.json`,
  `extensions/.registry`: pinned v0.1.4 catalogs and versions.
- `.specify/extensions/**`, `.specify/workflows/**`: release manifests, resources and all
  three lane workflows refreshed together; no project configuration rewritten.
- `README.md`, `AGENTS.md`, `harness/README.md`,
  `docs/development/spec-kit-delivery.md`,
  `docs/decisions/engineering/0004-release-managed-delivery-installation.md`: current
  version, corrected Doctor contract and upgrade guidance.
- This evidence, the v0.1.3 successor note and `harness/build-log.md`.

Project-owned extension configs, Constitution, core tasks skill/template and integration
selection are byte-preserved (14 protected files). No `packages/`, `scripts/`, CI, runtime
dependency, global configuration, historical Specs, remote metadata or user skill changes.
Vendor files are not hand-edited or patched to fake a passing state.

## Source, permissions and reproducibility

Source: [v0.1.4 Release](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.1.4),
MIT-licensed tooling. Specify CLI remains 1.2.3 / Python 3.13.5; Bug remains the CLI-bundled
1.0.1. Nine Delivery extensions and three workflows are 0.1.4, for 13 Bundle components.
No new runtime dependency, global CLI install or configuration format change.

Public GitHub downloads are read-only. Only the local project and owned temporary
directories are written; no private content is uploaded. No staging, commit, push, merge,
publication, hooks or autonomous workflow execution.

Owned temporary root (assets, driver, backups, fixture, logs and verification records):
`C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-v014-787d3eeb8f5e44b5b8ac59852ea32300`.
`fixture/` is a file-level copy of the current worktree (excluding `.git`, `.venv`,
`.codegraph` and caches) so the v0.1.3 uncommitted state could be exercised before the
target. `target-backup/` holds the pre-upgrade `.specify`, `.opencode` and project skills.
Backups are retained for inspection, not committed or deleted.

The temporary driver `upgrade.py` was executed with
`C:\Users\YanZh\AppData\Roaming\uv\tools\specify-cli\Scripts\python.exe` and records each
command and exit code. It is a run-scoped audit helper, not a new project quality tool.

Both fixture and target followed these exact commands, individually exiting 0:

```powershell
$base = 'https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.1.4/catalogs'
specify extension catalog remove speckit-delivery
specify extension catalog add "$base/extensions.json" --name speckit-delivery --install-allowed
specify workflow catalog remove 0
specify workflow catalog add "$base/workflows.json" --name speckit-delivery
specify bundle catalog remove speckit-delivery
specify bundle catalog add "$base/bundles.json" --id speckit-delivery --policy install-allowed
specify bundle update speckit-delivery
```

The workflow catalog index was resolved from `specify workflow catalog list` rather than
assumed. No force initialization, component deletion or Bundle record editing was used.

## Actual checks

Commands ran in the working directory above; fixture checks ran under the owned `fixture/`.
Records: `release-audit.log`, `fixture-upgrade.log`, `target-upgrade.log`,
`{fixture,target}-protected-before.json`, `{fixture,target}-verification.json`.

| Command/check | Exit | Observed result |
|---|---:|---|
| `git status --short --branch`; `git rev-parse HEAD` | 0 each | base `881dcfe`, `main`; prior v0.1.3 work preserved |
| `gh release view v0.1.4 --repo YanZhiwei/speckit-delivery --json tagName,name,body,assets,targetCommitish,url,isDraft,isPrerelease` | 0 | published, not draft/prerelease; 10 ZIP assets |
| `gh release download v0.1.4 --repo YanZhiwei/speckit-delivery --pattern '*-0.1.4.zip' --dir <owned-temp>/assets` | 0 | all 10 assets downloaded |
| Temporary driver `audit` | 0 | all 10 SHA-256 digests match Release API; catalogs pinned to v0.1.4 and parse; Bundle declares 10 extensions + 3 workflows |
| `specify workflow catalog list` before removal | 0 | one Delivery catalog at index 0, confirmed rather than assumed |
| Temporary driver `upgrade <fixture> fixture` | 0 | 0.1.3 → 0.1.4 on a copy of the live worktree; protected files unchanged |
| Temporary driver `upgrade D:\Repos\Github\spawn-join target` | 0 | target at 0.1.4; 13 components; 14 protected files unchanged |
| Release-content comparison | 0 | 53 non-config extension files byte-identical to verified ZIPs |
| Workflow comparison and command closure | 0 | three workflows byte-identical to Tag; Feature 24, Bugfix 16, Lightweight 9 unique commands resolve |
| Doctor reference assertion | 0 | generated command names `.specify/extensions/review/templates/reviewer.md`; stale Delivery path absent |
| `pwsh -NoProfile -File <owned-temp>/check-native.ps1` | 0 | live `opencode api get /api/command` at the explicit project location; 35 native commands |
| `specify bundle list --json`; `specify integration status` | 0 each | Bundle 0.1.4 / Bug 1.0.1; OpenCode default, Codex retained; 0 missing managed files, 0 invalid manifest paths |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 66 files / 179 local targets, including this untracked evidence |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors / 0 warnings |
| `git diff --check` (also invoked by the docs gate) | 0 | no whitespace errors; LF/CRLF notices only |
| `git diff --name-only -- packages scripts .github pyproject.toml` | 0 | empty; no runtime, automation or shared-tool changes |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | 1 | PSScriptAnalyzer 1.25.0 unavailable in default environment |

## Doctor and standards assessment

```text
SD_DOCTOR_VERDICT: blocked
INTEGRATION: opencode (Codex retained)
COMPONENTS: all 13 Bundle components installed at their expected versions
WORKFLOWS: all three at 0.1.4; installed command closure passed
POLICY_COVERAGE: seven existing profiles unchanged; Quality owns mechanical checks;
  Review/Simplify/ADR own semantic standards; repair budget remains 2
BLOCKERS:
- V014-ENV: PSScriptAnalyzer 1.25.0 is absent; the static command actually fails.
```

The v0.1.3 `V013-PATH` blocker (Doctor pointing at a nonexistent Delivery Reviewer
template) is resolved in this release and re-verified above. The remaining blocker is
environmental: install the documented module with maintainer authorization or provide an
explicit verified process-local module path, then rerun the actual checks. Earlier
temporary-path success is not reused as evidence for the current environment.

Session-local standards assessment: installer owns resources and commands, project owns
configs; no duplicate template was created; dependency direction and Python public APIs are
unchanged; existing gates are reused; automatic hooks and remote writes stay disabled. This
is not an independent Review, a Ralph receipt, or an end-to-end semantic workflow pass.

## Compatibility and limitations

- v0.1.4 changes no command surface, configuration format, Review dimension, snapshot
  contract, repair budget or runtime dependency. Direct Workflow inputs remain
  `delivery_run` (and `bug_slug` for Bugfix).
- Task closure still requires current content/requirements-bound Quality, Standards and
  independent Review; no earlier receipt is promoted to the new contract.
- Scoped installation checks are not full Quality readiness. Four-package tests, builds and
  types, full quality, quality/static regression suites, direct Workflow execution,
  independent Review, real Feature/Bugfix/Ralph delivery and remote CI were not run for this
  tooling-only patch. No full-suite pass is claimed.
- LF/CRLF warnings are existing platform behavior; no global Git setting is changed.
- Evidence covers this uncommitted working tree, not a future commit/merge or another host.
  Reconfirm source identities, scope and readiness if HEAD or relevant contents change.
