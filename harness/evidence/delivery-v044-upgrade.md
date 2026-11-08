# Evidence — Delivery Bundle v0.4.4 upgrade

## Identity and scope

- **feature_id**: `delivery-v044-upgrade` (operational Lightweight label; no Feature created)
- **phase_id**: `delivery-v044-upgrade`
- **route**: Lightweight; fixed Release tooling update and reference analysis, no product behavior change
- **base_revision**: `e292f0e3b746fec266e71dca142fc20356841978`
- **head_revision**: `working-tree`
- **working_directory**: `C:\Users\YanZh\.local\share\opencode\worktree\86e56b\mighty-harbor`
- **recorded_at**: `2026-11-07`
- **result**: pass for installation, protected-file preservation, upstream runtime/distribution and targeted project checks; warnings and unexecuted work recorded below
- **environment**: Windows; Specify CLI 1.2.3 / its Python 3.13.5; PowerShell 7 for helper scripts

Started on a clean detached HEAD. The user authorized installing v0.4.4 and studying external
governance for possible improvements. No Feature Spec/Plan/Tasks was created: the change is a
release-managed tooling refresh, documentation synchronization and analysis, not implementation
of a new product or governance automation system.

## Source, backup and protected scope

- Release: [v0.4.4](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.4.4).
- Annotated tag object: `16e2b486f7be6dc90895d3aab2f68e5eeb1d7b7a`.
- Peeled checkout commit: `5f7e3788c25e8fab69e404edb8816f9e0eeffe05`.
- Bundle asset digest reported by the GitHub Release API:
  `sha256:6f1b79d8fa94566742321176e29180296d15a6c146a608b5603c06a04a11335e`.
- Pinned catalogs: `https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.4.4/catalogs/`
  with `extensions.json`, `workflows.json`, and `bundles.json`.
- Temporary root: `C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-delivery-v044-20261107`.
  `backup/` holds pre-upgrade `.specify`, `.opencode`, and `.agents`; `rehearsal/` is the isolated
  upgrade copy; `upstream/` is the pinned upstream clone. Helper scripts and SHA-256 manifest
  remain outside this repository.

Compared 164 protected files byte-for-byte using SHA-256 before/after both upgrades:
`.specify/extensions.yml`, all project `*-config.yml`, tracked `.specify/templates/**`, and
tracked `.agents/skills/**`. All remained unchanged. This includes core task customizations
and the pinned third-party skill; no forced integration upgrade was used.

## Changed paths and ownership

- Installer-managed: three catalog files, Bundle/extension/workflow registries, nine Delivery
  extension manifests, changed Explore/Route/Ralph/Review prompts and templates, generated OpenCode
  commands including `/sd`, and three Delivery workflows.
- Project-owned: `AGENTS.md`, `docs/development/spec-kit-delivery.md`, the current-version/history
  sections of ADR-0004, both `harness/README` language files, this evidence and `harness/build-log.md`.
- Analysis only: [Delivery/Harness reference review](../../docs/development/delivery-harness-reference-review.md).
  Proposed improvements are not adopted rules or completed tasks.
- No Distribution source, package manifest/lock, public API, runtime dependency, credential,
  permission, hook policy, task queue or remote resource was changed.

## Observed commands and results

Unless noted, commands ran at the project root above. Exit codes are actual process results.
The temporary `upgrade.ps1` runs the three catalog remove/add pairs shown in the
[installation guide](../../docs/development/spec-kit-delivery.md), then
`specify bundle update speckit-delivery` and `specify bundle list --json`, checking every exit code.

| Command/check | Working directory | Exit | Observed result |
|---|---|---:|---|
| `git status --short --branch`; `git rev-parse HEAD` | project | 0 | Clean detached HEAD at the base above |
| `specify version`; three catalog lists; `specify bundle list --json` | project, before upgrade | 0 | CLI 1.2.3; Bundle/catalogs at 0.4.3 |
| `codegraph status` | project | 0 | Reports Not initialized despite the `.codegraph/` placeholder; no index was created |
| `git ls-remote ... refs/tags/v0.4.4`; pinned `git clone --depth 1 --branch v0.4.4 ...` | project | 0 | Tag/commit identity recorded above |
| `snapshot.ps1 -Project <project>` | project, using `pwsh -NoProfile -File` | 0 | 164 protected hashes saved |
| `upgrade.ps1` | rehearsal | 0 | All catalogs updated and Bundle 0.4.4 registered |
| `snapshot.ps1 -Project <rehearsal> -Verify`; `specify integration status` | rehearsal | 0 | All protected files unchanged; no missing/invalid managed paths; customization warnings |
| `upgrade.ps1` | project | 0 | Bundle 0.4.4, 13 components: nine Delivery extensions and three workflows at 0.4.4, Bug at 1.0.1 |
| `snapshot.ps1 -Project <project> -Verify`; `specify integration status` | project | 0 | All protected files unchanged; 32 modified managed files reported, 0 missing/invalid paths |
| `py -3 scripts/test_delivery_runtime.py` | upstream | 0 | 37 tests passed |
| Specify tool Python: `scripts/validate_distribution.py` | upstream | 0 | Catalogs, manifests, workflows and Bundle coherent |
| Specify tool Python: `scripts/test_validate_distribution.py` | upstream | 0 | 65 tests passed |
| `specify integration status` | pre-upgrade backup | 0 | Same 32 modified managed files and same three customization findings; no missing/invalid paths |
| `verify-install.ps1 -Project <project>` | project, using `pwsh -NoProfile -File` | 0 | 73 tracked upstream extension/Workflow sources match after LF/CRLF normalization; 13 versions coherent; 39 native commands; `/sd` equals Route; static PR template text matches |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | project | 0 | 61 Markdown files / 288 local targets checked before final evidence updates; final rerun recorded below |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | project | 0 | 0 errors; one historical v0.2.2 evidence freshness warning |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | project | 0 | 0 failing checks |
| `pwsh -NoProfile -File scripts/test-governance.ps1` | project | 0 | 26 regression scenarios passed |
| `pwsh -NoProfile -File scripts/test-static.ps1` | project | 0 | 3 regression scenarios passed |
| `pwsh -NoProfile -File scripts/test-quality.ps1` | project | 0 | 11 regression scenarios passed; no root project artifacts |
| Final `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | project | 0 | 61 files / 290 local targets checked; project documentation passes |
| Final `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | project | 0 | 0 errors / 1 historical warning |
| `git -c core.safecrlf=false diff --check`; `git status --short --branch`; `git rev-parse HEAD` | project | 0 | No whitespace error; still detached at base with expected uncommitted installation/documentation changes |

The content diff contains 36 modified tracked files plus the two new analysis/evidence documents.
Raw status also lists installer-rewritten vendor files with LF/CRLF-only changes; these were not
reverted, hand-edited, or mistaken for new runtime behavior. The source-identity comparison above
normalizes only line endings, not substantive content. Git's working-copy conversion warnings
do not indicate whitespace-check failure. Final documentation result bookkeeping and the short
API/design-navigation explanation do not change the verified installer/configuration scope.

Upstream distribution tests used
`C:\Users\YanZh\AppData\Roaming\uv\tools\specify-cli\Scripts\python.exe`;
`TEMP`/`TMP` were set to the approved OpenCode temporary parent. These are fixture/structural
tests, not real model behavior evaluations or a project Ralph run.

## Failed attempts and corrections

- Initial backup setup copied the three directories successfully, then Windows PowerShell 5.1
  failed on `[IO.Path]::GetRelativePath` (exit 1). No catalog or installed component had changed.
  The hashing/upgrade helpers were run with PowerShell 7 instead and succeeded.
- Two documentation patches failed context verification and applied no changes; corrected,
  smaller patches were used. An upstream prompt read used an incomplete filename once and
  was corrected to `speckit.delivery.explore.md`.
- The first custom source-identity probe included upstream test-generated `__pycache__` (exit 1).
  Restricting enumeration to upstream Git-tracked sources corrected this verification scope.
  Its next run rejected raw PR-template hashes (exit 1); inspection confirmed LF/CRLF-only
  differences. The final probe compares normalized text, passes, and leaves the GitHub static
  template untouched; this is not reported as raw-byte identity.

## Scope and standards review

Author self-review only: vendor changes are installer-managed and must not be hand-edited;
project documents synchronize current installation identity, preserve historical evidence and
keep recommendations distinct from adopted policy. No second queue, knowledge store, approval
round or provider abstraction was introduced. Existing dependency direction and public behavior
are unchanged. No synthetic independent Review receipt or full Delivery pass is claimed.

## Limitations

- Integration customization warnings remain, identical to the pre-upgrade backup; no `--force`
  overwrite was performed. Governance also retains one historical warning for
  `harness/evidence/delivery-v022-upgrade.md`, 27 commits behind the current HEAD.
- CodeGraph has no usable index in this worktree; document/source navigation used direct fallback.
  It was not initialized or presented as correctness evidence. No project Python source changed.
- Package builds/tests and full five-package quality matrix were not run: packages are unchanged.
- Doctor, actual SD/Ralph, hosted workflows, model behavior evals, independent Review and remote CI
  were not run. A successful installation and fixture suite do not establish those outcomes.
- No commit, push, PR, merge or publication was requested or performed. HEAD remains the base;
  results apply to the current outgoing working-tree diff, not a future revision.
- Local temporary backups are retained. For rollback use the approved fixed v0.4.3 catalog/Bundle
  installation path with the backup as a preservation reference; do not edit registries to fake a downgrade.
