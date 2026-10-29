# Evidence — Delivery Bundle v0.1.3 upgrade

## Identity and scope

- **feature_id**: `delivery-v013-upgrade` (Lightweight run label; no Feature created)
- **phase_id**: `delivery-v013-upgrade`
- **base_revision**: `881dcfeb4885c044d39071660606775509d64165`
- **head_revision**: working-tree (base `881dcfeb4885c044d39071660606775509d64165`; no commit)
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-29
- **result**: pass for scoped installation consistency, docs and governance checks; Doctor blocked
- **superseded_by**: `harness/evidence/delivery-v014-upgrade.md`

Route: **Lightweight**. The maintainer requested the pinned release upgrade. This refreshes
existing third-party development resources, not Python behavior, APIs, dependencies or
architecture. No new Spec/Plan/Tasks, delivery Workflow run or Ralph queue is needed.
The starting worktree was clean on `main`; the index and HEAD remain unchanged.

## Changed paths and ownership

- Installer-owned `.opencode/commands/`: refresh affected prompts and add
  `speckit.delivery.explore.md` / `speckit.delivery.review-fix.md`.
- `.specify/{extension,workflow,bundle}-catalogs.yml`, `bundle-records.json`,
  `extensions/.registry`: pinned v0.1.3 sources, versions and ownership.
- `.specify/extensions/{decision,delivery,diagram,docs-sync,evidence,quality,ralph,review,simplify}/`:
  release manifests/resources, including exploration, continuation and Reviewer templates.
- `.specify/workflows/{feature-delivery,bugfix-delivery,lightweight-delivery}/workflow.yml`
  and `workflow-registry.json`: all three lanes refreshed together.
- `README.md`, `AGENTS.md`, `harness/README.md`,
  `docs/development/spec-kit-delivery.md`,
  `docs/decisions/engineering/0004-release-managed-delivery-installation.md`:
  current version, commands, compatibility notes and installation limitations.
- This evidence and `harness/build-log.md`: actual upgrade and verification record.

Project-owned extension configs, Constitution, core tasks skill/template and integration
selection are byte-preserved (14 protected files). No `packages/`, `scripts/`, CI, runtime
dependency, global configuration, historical Specs, remote metadata or user skill changes.
Vendor files are not hand-edited, formatted, or patched to hide a release defect.

## Source, permissions and reproducibility

Source: [v0.1.3 Release](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.1.3),
MIT-licensed tooling; Specify CLI remains 1.2.3 / Python 3.13.5. Bug remains the CLI-bundled
1.0.1. All nine Delivery extensions and three lane workflows are 0.1.3, with 13 Bundle
components in total. No new runtime dependency or global CLI installation.

Public GitHub Release/catalog/workflow downloads are read-only. Only the local project and
owned temporary directories are written; no private project content is uploaded. No
staging, commit, push, merge, publication, hooks or autonomous workflow execution.

Owned temporary root (assets, audit driver, backups, fixture, logs and hash records):
`C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-v013-47b5b4aaecb6467c90eee61196b827d4`.
`target-backup/` includes the pre-upgrade `.specify`, `.opencode` and project skills;
`fixture/` is a local clone of the clean base. Backups and local ignored artifacts are
retained for inspection, not committed or deleted.

The temporary audit driver is `upgrade.py`, executed with
`C:\Users\YanZh\AppData\Roaming\uv\tools\specify-cli\Scripts\python.exe`.
Its `audit`, `upgrade <project> <label>` and `check <project> <label>` actions record actual
commands/exits and verify protected SHA-256 values. It is not a new project quality tool.

Both fixture and target followed these exact commands, individually returning exit 0:

```powershell
$base = 'https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.1.3/catalogs'
specify extension catalog remove speckit-delivery
specify extension catalog add "$base/extensions.json" --name speckit-delivery --install-allowed
specify workflow catalog remove 0
specify workflow catalog add "$base/workflows.json" --name speckit-delivery
specify bundle catalog remove speckit-delivery
specify bundle catalog add "$base/bundles.json" --id speckit-delivery --policy install-allowed
specify bundle update speckit-delivery
```

Index `0` was confirmed by `specify workflow catalog list` before removal. No force
initialization, component deletion or manual Bundle record editing was used.

## Actual checks

Unless noted, commands run in the working directory above; fixture checks run under the
owned `fixture/`. Logs: `release-audit.log`, `fixture-upgrade.log`, `target-upgrade.log`,
`{fixture,target}-protected-before.json`, `{fixture,target}-verification.json`,
`native-commands.json` under the temporary root.

| Command/check | Exit | Observed result |
|---|---:|---|
| `git status --short --branch`; `git rev-parse HEAD` | 0 each | clean base `881dcfe`, `main` |
| `specify version` | 0 | 1.2.3; no CLI upgrade needed |
| Baseline `quality.ps1 -Check docs` / `-Check governance` | 0 each | 64 files / 169 targets; governance 0 errors / 0 warnings |
| `gh release view v0.1.3 --repo YanZhiwei/speckit-delivery --json tagName,name,body,assets,targetCommitish,url` | 0 | published Release, 10 ZIPs |
| `gh release download v0.1.3 --repo YanZhiwei/speckit-delivery --pattern '*-0.1.3.zip' --dir <owned-temp>/assets` | 0 | all 10 assets downloaded |
| Temporary driver `audit` | 0 | all 10 SHA-256 digests match Release API; catalog JSON parses |
| `git clone --local --no-hardlinks D:\Repos\Github\spawn-join <owned-temp>/fixture` | 0 | clean isolated baseline; no remote write |
| Temporary driver `upgrade <fixture> fixture` | 0 | Bundle 0.1.2 → 0.1.3; protected files unchanged |
| Temporary driver `upgrade D:\Repos\Github\spawn-join target` | 0 | target upgraded; 13 components; all 14 protected files unchanged |
| Release-content comparison | 0 | 53 non-config extension files byte-identical to verified ZIPs |
| Workflow command closure | 0 | Feature 24, Bugfix 16, Lightweight 9 unique commands all resolve |
| Temporary driver `check D:\Repos\Github\spawn-join target` | 0 | all three workflows byte-identical to v0.1.3 Tag; eight configs parse; 14 protected files unchanged; repair budget 2 |
| `specify bundle list --json`; `specify extension list`; `specify workflow list` | 0 each | consistent Bundle/components; Delivery has eight commands |
| `specify integration status` | 0 | OpenCode default, Codex retained; same 18 pre-existing managed-file warnings, zero missing paths |
| `pwsh -NoProfile -File <owned-temp>/check-native.ps1` | 0 | live `opencode api get /api/command` at explicit project location; 35 native commands, including both additions |
| `pwsh -NoProfile -File scripts/test-governance.ps1` | 0 | all 23 scenarios passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 65 files / 175 local targets; includes this untracked evidence |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors / 0 warnings |
| `git diff --check` (also invoked by docs gate) | 0 | no whitespace errors; LF/CRLF notices only |
| `git diff --name-only -- packages scripts .github pyproject.toml` | 0 | empty; no runtime, automation or shared-tool changes |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | 1 | PSScriptAnalyzer 1.25.0 unavailable in default environment |

The first live-API parse used Windows PowerShell's default external-output decoding and
failed on CJK metadata (`ConvertFrom-Json`); its printed zero count was invalid, not an
installation result. Repeating through PowerShell 7 with explicit UTF-8 succeeded and
asserted the project location and all 35 commands.

## Doctor and standards assessment

This session read and applied the newly installed `speckit.delivery.doctor` read-only
checklist. It is an Agent Prompt, not an executable found on PATH.

```text
SD_DOCTOR_VERDICT: blocked
INTEGRATION: opencode (Codex retained)
COMPONENTS: all 13 Bundle components installed at their expected versions
WORKFLOWS: all three at 0.1.3; installed command closure passed
POLICY_COVERAGE: seven existing profiles; Quality owns mechanical checks;
  Review/Simplify/ADR own semantic standards; repair budget remains 2
BLOCKERS:
- V013-ENV: PSScriptAnalyzer 1.25.0 is absent; static command actually fails.
- V013-PATH: generated Doctor references delivery/templates/reviewer.md,
  but the Release ships review/templates/reviewer.md and Review Run uses that path.
```

V013-ENV remediation: install the documented module with maintainer authorization or
provide an explicit verified process-local module path, then rerun the actual checks.
Do not reuse earlier temporary-path success as evidence for the current environment.

V013-PATH location: `.opencode/commands/speckit.delivery.doctor.md:39` (also in its
installer-owned source). The actual template is
[Reviewer](../../.specify/extensions/review/templates/reviewer.md). The installed ZIP files
match upstream, so this is a published Prompt path defect, not a missing installation.
Remediation: an upstream fixed Release; no fake duplicate or local vendor patch. No
GitHub Issue is opened without separate authorization.

Session-local standards assessment: installer owns resources/commands, project owns
configs; dependency direction and Python public APIs unchanged; existing gates reused;
automatic hooks and remote writes remain disabled. This is not an independent Review,
Ralph receipt, or a claim that the new semantic workflow passed end-to-end.

## Compatibility and limitations

> Successor: the published v0.1.4 patch corrects the V013-PATH defect. This record stays
> as the v0.1.3 history; the current installed state is documented in
> [v0.1.4 evidence](delivery-v014-upgrade.md).

- Direct Workflow invocations now need `delivery_run`; Bugfix also needs `bug_slug`.
  Stable run identity/ignored packets must be retained on resume. Examples are in the
  [installation guide](../../docs/development/spec-kit-delivery.md).
- Task closure now needs Quality, Standards and independent Review tied to actual content
  and requirements. Existing HEAD/path-only receipts are not enough; no old receipt is
  promoted to the new contract by this installation.
- Scoped installation checks are distinct from full Quality/Doctor readiness. Four-package
  tests/builds/types and full quality, quality/static regression suites, direct Workflow
  execution, independent Review, real Bugfix/Feature/Ralph delivery and remote CI are not
  run for this tooling-only refresh. No full-suite pass is claimed.
- LF/CRLF warnings are existing platform behavior; no global Git setting is changed.
- Evidence covers this uncommitted working tree, not a future commit/merge or fresh host.
  Reconfirm source identities, scope and readiness if HEAD or relevant contents change.
