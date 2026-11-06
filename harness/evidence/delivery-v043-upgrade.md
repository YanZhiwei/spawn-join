# Evidence — Delivery Bundle v0.4.3 upgrade

## Current operational outcome — 2026-11-06

- **status**: delivered (operational upgrade; not a native Delivery run)
- **pull_request**: https://github.com/YanZhiwei/spawn-join/pull/39
- **outcome**: merged
- **reviewed_head**: `e2ba0537c4dfaf1f8baeaaa7c56cfed90c2c087f` (author self-review, not an independent native receipt)
- **original_pr_head**: `e2ba0537c4dfaf1f8baeaaa7c56cfed90c2c087f`
- **merge_base_revision**: `02c14ccc1b35bdb9d92d4ad6890ebdf325170e0a`
- **merged_revision**: `a38f9a795e1bf16e8c463c1c3bfcbea54b31b4b9`
- **merged_at**: `2026-11-06T03:35:01Z`
- **observed_at**: `2026-11-06T03:35:24.2048484Z`
- **merge_proof**: full PR-head and squash-merge trees both equal `db08ed446e07f2a2345a76a799832012dde78ae6`; merged commit reachable from `origin/main`
- **remote_ci**: [Quality run 42156804491](https://github.com/YanZhiwei/spawn-join/actions/runs/42156804491), all 17 jobs successful for the PR, including required `Quality Gate`

The user explicitly authorized merge and wrap-up after the draft PR was published. GitHub reported
no submitted reviews; the already-disclosed author self-review limitation is retained, not replaced
with an invented independent pass. Repository Ruleset requires PR, linear history, and `Quality Gate`,
with zero required approving reviews. The merge used ordinary `gh pr merge --squash
--match-head-commit e2ba0537c4dfaf1f8baeaaa7c56cfed90c2c087f`; no admin bypass or policy change.

Commands from `D:\Repos\Github\spawn-join`, all exit 0: `gh pr checks 39`, Ruleset inspection,
`gh pr ready 39`, guarded squash merge, tracker re-observation, `git fetch origin main`, merge
reachability and complete tree equality checks, then `git switch main` and `git merge --ff-only
origin/main`. A separate classic branch-protection API probe returned 404; the effective Ruleset was
then verified via `repos/YanZhiwei/spawn-join/rules/branches/main`, not assumed absent.

This outcome is kept in Harness, the authoritative home for one-off installation records. No
`.specify/delivery/` run or native Close state was created, and no Ralph execution is claimed.
The unrelated pre-existing untracked Delivery record remains untouched. The sections below are
historical snapshots: their draft/pending/no-merge statements describe those earlier observations,
not the current outcome. This docs-only closure does not relabel the historical PR head as the
effective merge revision or change any installed component.

Closure-document verification at base `a38f9a795e1bf16e8c463c1c3bfcbea54b31b4b9` ran in the
isolated verification worktree named below: `quality.ps1 -Check docs` (exit 0, 53 files/268 local
targets), `quality.ps1 -Check governance` (exit 0, 0 errors/1 historical warning), and
`git diff --check` (exit 0). The outgoing closure scope is exactly this evidence and
`harness/build-log.md`; no package or installer file changed. Future docs-closure CI is separate
from the already verified upgrade PR CI above.

## Identity and scope

- **feature_id**: `delivery-v043-upgrade` (operational Lightweight run label; no Feature created)
- **phase_id**: `delivery-v043-upgrade`
- **route**: Lightweight（安装/升级交付工具，不创建 Feature 工件）
- **base_revision**: `02c14ccc1b35bdb9d92d4ad6890ebdf325170e0a`
- **head_revision**: `working-tree`（本次安装后的 outgoing diff）
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: `2026-11-06`
- **result**: pass for the v0.4.3 Bundle/catalog upgrade and component registration; expected managed-file customization warnings remain
- **environment**: Windows, PowerShell 7.6.9, Specify CLI 1.2.3, Python 3.13.5

This is a release-managed tooling upgrade. It changes installer-managed commands,
manifests, catalogs, workflows, runtime helpers, and project governance
documentation; it does not change Python package source, runtime dependencies, public APIs,
or application data. The pre-existing untracked
`.specify/delivery/readme-governance-package-retirement-20261105/` was retained and was not
included in this installation scope.

## Source and release identity

- Release: [speckit-delivery v0.4.3](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.4.3)
- Annotated tag object: `1b3d436dc8eb884206c3824e0ea8bab665cd03e3`
- Tag commit: `3db3bb7019d19110360f8ddceda0737bb1803be9`
- Specify CLI: `1.2.3`
- Extension catalog URL: `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.3/catalogs/extensions.json`
- Workflow catalog URL: `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.3/catalogs/workflows.json`
- Bundle catalog URL: `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.3/catalogs/bundles.json`
- GitHub Release API reports 10 uploaded assets (nine Delivery extension ZIPs and the Bundle), including the v0.4.3 Bundle asset with digest
  `sha256:1a468a93ef182c21d270c2b1d4c6f4952f7d998091fb8d9490bd2dfd28f76422`.

The three published catalogs and the Release page/API were read-only inspected before changing
local catalog sources. The v0.4.3 Bundle declares 10 extensions, 3 workflows, and requires
Specify CLI `>=1.2.3`.

## Changed paths and ownership

Installer-managed paths were refreshed by the catalog switch and
`specify bundle update speckit-delivery`, including:

- `.opencode/commands/` generated Delivery commands and the manifest-provided `sd.md` alias;
- `.specify/extensions/**` v0.4.3 extension manifests, commands, runtime helpers, README/templates;
- `.specify/workflows/**` v0.4.3 Feature, Bugfix, and Lightweight workflows;
- `.specify/extension-catalogs.yml`, `.specify/workflow-catalogs.yml`, and
  `.specify/bundle-catalogs.yml`;
- `.specify/bundle-records.json`, `.specify/extensions/.registry`, and
  `.specify/workflows/workflow-registry.json`.

Project-owned paths updated to keep the durable description accurate:

- `AGENTS.md` current Bundle version and v0.4.3 capability summary;
- `docs/development/spec-kit-delivery.md` current release, upgrade path, verification, and evidence link;
- `docs/decisions/engineering/0004-release-managed-delivery-installation.md` current release status and revision history;
- `harness/build-log.md` operational upgrade entry;
- this evidence record.

The following protected project files were compared byte-for-byte with the pre-upgrade backup and
remained unchanged:

- `.specify/extensions.yml`
- `.specify/extensions/delivery/delivery-config.yml`
- `.specify/extensions/quality/quality-config.yml`
- `.specify/extensions/docs-sync/docs-sync-config.yml`
- `.specify/templates/tasks-template.md`

The v0.4.3 update keeps the Bundle-managed `/sd` alias, adds the `owner-result` runtime entry,
and removes the duplicate whole-run Feature Quality Brief before Ralph. No
`specify integration upgrade --force` was used.

## Observed commands and results

| # | Command/check | Exit | Result |
|---|---|---:|---|
| 1 | `git status --short --branch; git rev-parse HEAD` | 0 | Started on `main` at `02c14ccc`; pre-existing untracked Delivery record retained |
| 2 | `specify version` | 0 | Specify CLI 1.2.3; Python 3.13.5 |
| 3 | Release page/API, tag, and three v0.4.3 catalogs read-only audit | 0 | Release, tag, assets, and pinned catalog identities recorded above |
| 4 | Installer-managed `.specify`/`.opencode` backup | 0 | Backup at `C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-delivery-v043-20261106-093708` |
| 5 | Three Catalog remove/add pairs for the v0.4.3 URLs | 0 | Extension, Workflow, and Bundle sources switched to v0.4.3 |
| 6 | `specify bundle update speckit-delivery` | 0 | Bundle updated; all three Delivery workflows reinstalled |
| 7 | `specify bundle list --json` | 0 | Bundle 0.4.3; nine Delivery extensions and three workflows at 0.4.3, plus Bug 1.0.1 (13 components) |
| 8 | `specify extension list` / `specify workflow list` | 0 | All expected components enabled at v0.4.3 |
| 9 | `specify integration status` | 0 | No missing/invalid paths; 18 expected managed-file customization warnings |
| 10 | Protected-file SHA-256 comparison | 0 | All five protected files unchanged |
| 11 | `py -3 -m py_compile ...` and `py -3 delivery_runtime.py --help` | 0 | Runtime helpers parse; `owner-result` and its evidence/record options are present |
| 12 | `codegraph sync` | 0 | CodeGraph index already up to date after the installer refresh |
| 13 | OpenCode command count and Feature Workflow inspection | 0 | 39 `speckit.*` commands, `sd.md`, no duplicate global Brief before Ralph, task-scoped Ralph Brief retained |
| 14 | `git diff --check` | 0 | No whitespace errors; Git emitted normal LF/CRLF working-copy warnings |
| 15 | `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 110 files / 321 local targets checked; documentation checks passed |
| 16 | `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 1 | Blocked by pre-existing untracked evidence missing `head_revision`; one historical freshness warning also remains |
| 17 | `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | 0 | Static analysis reported 0 failing checks |
| 18 | `pwsh -NoProfile -File scripts/test-governance.ps1` | 0 | 23 governance regression scenarios passed |
| 19 | `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | 11 quality-gate regression scenarios passed |
| 20 | `pwsh -NoProfile -File scripts/test-static.ps1` | 0 | 3 static-analysis regression scenarios passed |

## v0.4.3 behavior observed

- `delivery_runtime.py owner-result` derives the stage identity from the exact pending ticket,
  hashes the native report and run-local evidence references, writes a native receipt and
  normalized result, and can delegate to the existing `record` validation in one call.
- Feature Delivery no longer dispatches a separate whole-run Quality Brief immediately before
  Ralph; Ralph still receives its task-scoped Brief and declared verification instructions.
- Existing task-close, Close outcome, publication-group, Slice, `/sd`, resume/checkpoint, and
  conditional owner behavior remain installed through the Bundle update path.

## Verification state

- **Installation/catalog consistency**: pass.
- **Configuration/customization preservation**: pass for the protected files listed above.
- **Managed integration status**: pass with warnings; the installer reports the existing modified
  Codex, OpenCode, and shared Spec Kit managed files. These existing customizations were not force-upgraded.
- **Runtime smoke checks**: pass for Python parsing and `delivery_runtime.py --help`.
- **Documentation check**: pass (`quality.ps1 -Check docs`).
- **Static check and regression suites**: pass (`quality.ps1 -Check static`, governance/quality/static regression scripts).
- **Actual governance check**: blocked by the pre-existing untracked evidence record described below;
  this installation did not alter that user-owned file.
- **Project package quality gates**: not applicable to the installer-only diff; no Python package
  source, package metadata, or runtime dependency changed.
- **Delivery workflow/Doctor/Ralph**: not run. Installation does not claim a completed Feature,
  Bugfix, Ralph loop, or full Delivery cycle.

## Failed attempts and corrections

- The first local `python -m py_compile`/runtime smoke command failed because `python.exe` is not
  available as a PATH alias in this environment. The project-supported `py -3` invocation was
  rerun successfully.
- The first backup comparison probe used an incorrect relative-path slice and reported lookup
  errors; the comparison was corrected and all five protected-file hashes then matched.

## Known limitations and follow-up

- `specify integration status` continues to report the existing managed-file customization
  warnings. No `--force` overwrite was authorized or performed.
- The actual governance check also reports the pre-existing untracked
  `.specify/delivery/readme-governance-package-retirement-20261105/evidence.md` is missing
  `head_revision`, plus one historical freshness warning in `harness/evidence/delivery-v022-upgrade.md`.
  The untracked record was present before this upgrade and was deliberately not modified.
- This evidence is scoped to the local working tree before any future commit or PR; remote CI,
  commit, merge, and publication evidence must be recorded separately.
- No remote write, push, PR, merge, publication, or Delivery workflow execution was performed as
  part of the installation commands recorded above.

## Rollback

Restore the backed-up installer-managed paths from the backup directory above, restore the v0.4.2
catalog URLs, and run the documented v0.4.2 `specify bundle update speckit-delivery` path. Do not
manually edit generated commands or Bundle records to conceal version drift; retain this evidence
as the historical v0.4.3 installation record.

## PR preparation — 2026-11-06

The user separately authorized creating a PR after installation. This remains an operational
Lightweight tooling update, not a newly initialized Delivery run. No Spec/Plan/Tasks or synthetic
Ralph/runtime pass was created. The target is `main`, with base
`02c14ccc1b35bdb9d92d4ad6890ebdf325170e0a`; `git fetch origin main` confirmed no base drift.
Publication will use only the upgrade paths listed above and this evidence, not the pre-existing
untracked Delivery record. The original installation checks and limitations above remain historical.

### Isolated outgoing-content validation

Verification worktree:
`C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-v043-pr-20261106`.
It was created at the base and populated with only the candidate PR changes. No file was removed
or hidden from the original worktree. The unrelated local evidence missing `head_revision` is not
part of this PR; the original worktree's governance failure remains real and unchanged.

| Command/check | Working directory | Exit | Result |
|---|---|---:|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | verification worktree | 0 | Documentation and local targets pass |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | verification worktree | 0 | 0 errors; one historical v0.2.2 evidence freshness warning |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | verification worktree | 0 | 0 failing checks |
| Three installed helper and three Workflow comparisons | original worktree against v0.4.3 tag checkout | 0 | Exact text equality after CRLF-to-LF normalization |
| `py -3 scripts/test_delivery_runtime.py` | upstream v0.4.3 checkout | 0 | 37 runtime regression tests pass, including owner-result |
| Specify tool Python: `scripts/validate_distribution.py` | upstream v0.4.3 checkout | 0 | Catalogs, manifests, workflows, Bundle coherent |
| Specify tool Python: `scripts/test_validate_distribution.py` | upstream v0.4.3 checkout | 0 | 62 distribution regression tests pass |

The upstream checkout is
`C:\Users\YanZh\AppData\Local\Temp\opencode\speckit-delivery-v043-pr-source`, pinned to
`3db3bb7019d19110360f8ddceda0737bb1803be9`. The Specify tool interpreter used was
`C:\Users\YanZh\AppData\Roaming\uv\tools\specify-cli\Scripts\python.exe`.
The runtime tests ran with `TEMP`/`TMP` set to the approved OpenCode temporary directory.
These tests use fixtures, not real model calls or an actual project Ralph execution.

### Scope and standards review

| Dimension | Observed result |
|---|---|
| Requirements | Fixed v0.4.3 Release installed; no new product behavior requested or implemented |
| Code quality / ownership | Runtime behavior remains upstream-owned; generated commands and registries are installer-managed |
| Architecture | No Distribution, package dependency, public export, or ADR installation-policy change |
| Correctness | Helper/Workflow source identity and upstream regression results checked; generated alias retained |
| Security / compatibility | No credentials, hooks, project permission change, or automatic publish/merge introduced; CLI 1.2.3 retained |
| Test effectiveness | Real runtime/distribution regressions supplement project checks; package builds/tests not rerun because packages are untouched |

Simplification scan: no project-owned runtime abstraction added and no justified deletion candidate;
do not hand-edit vendor files to simplify them. Package README applicability: none, because no
package manifest, source, public API, or README-affecting surface is changed.

This is an author self-review, not an independent native Review receipt. The PR is prepared as a
**draft** for independent human review and remote CI. No `HANDOFF_READY` or full Delivery completion
is claimed, and no merge is authorized. The published Git commit and its exact changed-path/content
identity will be verified separately at PR creation; no future merge revision is inferred here.
