# Evidence — Delivery Bundle v0.2.1 upgrade

## Identity and scope

- **feature_id**: `delivery-v021-upgrade` (Lightweight run label; no Feature created)
- **phase_id**: `delivery-v021-upgrade`
- **base_revision**: `9cdb10a334acf9100ae822f7220cb67fa7a25650`
- **head_revision**: working-tree
- **working_directory**: `C:\Users\YanZh\.local\share\opencode\worktree\86e56b\stellar-engine`
- **recorded_at**: 2026-10-30
- **result**: pass for scoped installation consistency and generated-command checks; Workflows and independent Doctor prompt not run

Route: **Lightweight**. This is an upstream minor-release upgrade of development tooling.
It does not change Python behavior, package dependencies, public APIs, architecture or durable
data, so no Spec/Plan/Tasks, delivery Workflow run or Ralph queue is required.

The starting worktree was clean at detached `HEAD` `9cdb10a`; this upgrade is applied as an
uncommitted working-tree change. No content was staged; no commit, push, merge or release
action was made.

## Changed paths and ownership

- Installer-owned `.opencode/commands/speckit.delivery.*` and
  `.specify/extensions/**`, `.specify/workflows/**`: refreshed from the release; one new
  command `speckit.delivery.slice` and templates `slices.md` were added.
- `.specify/{extension,workflow,bundle}-catalogs.yml`, `bundle-records.json`,
  `extensions/.registry`: pinned v0.2.1 catalogs and versions.
- Project-owned `.specify/extensions/delivery/delivery-config.yml`: intentional policy update
  for `pr_slicing`, slice budgets, `stack_provider`, `merge_policy`, `code_context` and
  `install_pull_request_template`; installer itself preserved all 14 protected files before
  this edit.
- `README.md`, `AGENTS.md`, `harness/README.md`,
  `docs/development/spec-kit-delivery.md`,
  `docs/decisions/engineering/0004-release-managed-delivery-installation.md`: current version,
  Slice/Handoff contract and upgrade guidance.
- This evidence and `harness/build-log.md`.

Project-owned extension configs, Constitution, core tasks skill/template and integration
selection are byte-preserved by the installer (14 protected files). No `packages/`, `scripts/`,
CI, runtime dependency, global configuration, historical Specs, remote metadata or user skill
changes. Vendor files are not hand-edited or patched to fake a passing state.

## Source, permissions and reproducibility

Source: [v0.2.1 Release](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.2.1),
MIT-licensed tooling. Specify CLI remains 1.2.3 / Python 3.13.5; Bug remains the CLI-bundled
1.0.1. Ten Delivery extensions and three workflows are 0.2.1, for 13 Bundle components.
No new runtime dependency, global CLI install, configuration format break or remote write.

Public GitHub downloads are read-only. Only the local project and owned temporary directories
were written; no private content was uploaded. No staging, commit, push, merge, publication,
hooks or autonomous workflow execution.

Owned temporary root (assets, catalogs, fixture, driver, backups and verification records):
`C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-v021-0fd4705853fe4ee9a88c1052a00841f4`.
`fixture/` is a file-level copy of the pre-upgrade worktree (excluding `.git`, `.venv`,
`.codegraph` and caches) so the upgrade could be exercised before the target. `target-backup/`
holds the pre-upgrade `.specify`, `.opencode` and project skills. Backups are retained for
inspection, not committed or deleted.

The temporary driver `upgrade_v021.py` was executed with
`C:\Users\YanZh\AppData\Roaming\uv\tools\specify-cli\Scripts\python.exe` and records each
command and exit code. It is a run-scoped audit helper, not a new project quality tool.

Both fixture and target followed these exact commands, individually exiting 0:

```powershell
$base = 'https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.2.1/catalogs'
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
`{fixture,target}-protected-{before,after-install,after-config}.json`,
`{fixture,target}-verification.json`.

| Command/check | Exit | Observed result |
|---|---:|---|
| `git status --short --branch`; `git rev-parse HEAD` | 0 each | base `9cdb10a`, detached HEAD, clean worktree |
| `gh release view v0.2.1 --repo YanZhiwei/speckit-delivery --json ...` | 0 | published, not draft/prerelease; 10 ZIP assets |
| `gh release download v0.2.1 --pattern '*-0.2.1.zip' --dir <owned-temp>/assets` | 0 | all 10 assets downloaded |
| Temporary driver `audit` | 0 | all 10 SHA-256 digests match Release API; catalogs pinned to v0.2.1 and parse; Bundle declares 10 extensions + 3 workflows |
| `specify workflow catalog list` before removal | 0 | one Delivery catalog at index 0, confirmed rather than assumed |
| Temporary driver `upgrade <fixture> fixture` | 0 | 0.1.4 → 0.2.1 on a copy of the live worktree; 14 protected files unchanged |
| Temporary driver `upgrade D:\...\stellar-engine target` | 0 | target at 0.2.1; 13 components; 14 protected files unchanged by installer |
| Fixture/target verification | 0 each | 36 native commands; 26 extension commands; Feature 25 / Bugfix 16 / Lightweight 9 unique commands resolve; 55 non-config extension files and 3 workflows byte-identical to Release |
| `specify bundle list --json` | 0 | Bundle 0.2.1; delivery/decision/ralph/review/simplify/evidence/quality/docs-sync/diagram + three workflows at 0.2.1; Bug 1.0.1 |
| `specify integration status --json` | 0 | OpenCode default, Codex retained; 0 missing managed files; 0 invalid manifest paths; warning: 32 project-modified managed files (expected core skill/template customizations) |
| Installer config preservation | 0 | all `*-config.yml`, Constitution, core `speckit-tasks` skill, `tasks-template.md`, integration/init records unchanged before the intentional delivery-config edit |
| Generated Doctor assertion | 0 | references `.specify/extensions/review/templates/reviewer.md`; stale Delivery path absent; includes PR-template and Handoff checks |
| Generated Handoff assertion | 0 | contains `PR_BODY_PATH`, `PR_CREATE_HINT: gh pr create`, and `--body-file`; body path contract present |
| Slice/workflow assertion | 0 | `speckit.delivery.slice`, `templates/slices.md`, Feature `slice`/`slice-gate` before analyze; `slices.md` consumed downstream |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 40 files / 156 local targets, including this untracked evidence |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors / 0 warnings |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | 0 | 0 failing checks; PSScriptAnalyzer available in current environment |
| `pwsh -NoProfile -File scripts/quality.ps1` | 0 | full four-package format/lint/type/test/build matrix passed; isolated wheel installs and imports passed |
| `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | 9 gate regression scenarios passed; no root project artifacts |
| `pwsh -NoProfile -File scripts/test-governance.ps1` | 0 | 23 governance regression scenarios passed |
| `pwsh -NoProfile -File scripts/test-static.ps1` | 0 | 3 static regression scenarios passed |
| `git diff --check` | 0 | no whitespace errors; LF/CRLF notices only |
| `git diff --name-only -- packages scripts .github pyproject.toml` | 0 | empty; no runtime, automation or shared-tool changes |

## Doctor and standards assessment

```text
SD_DOCTOR_VERDICT: not-run
INTEGRATION: opencode (Codex retained)
COMPONENTS: all 13 Bundle components installed at their expected versions
WORKFLOWS: all three at 0.2.1; installed command closure passed
POLICY_COVERAGE: seven existing profiles unchanged; Quality owns mechanical checks;
  Review/Simplify/ADR own semantic standards; repair budget remains 2
MANUAL CONTRACT CHECKS: Slice command/template/gate, merge policy, PR template,
  Handoff body path, reviewer template and hook settings checked directly
```

The Doctor is an Agent Prompt, not a PATH executable. The read-only contract checks listed
above were performed directly, but no independent Doctor agent run is claimed. The remaining
integration-status warning is project-owned customization, not a missing installation file;
`specify integration upgrade --force` was deliberately not used.

Session-local standards assessment: installer owns resources and commands, project owns
configs; no duplicate template was created; dependency direction and Python public APIs are
unchanged; existing gates are reused; automatic hooks and remote writes stay disabled. This
is not an independent Review, a Ralph receipt, or an end-to-end semantic workflow pass.

## Compatibility and limitations

- v0.2.0 added Slice planning/gates and merge policy; v0.2.1 added durable Handoff bodies and
  PR-template opt-in. This project keeps the single-PR path with `pr_slicing: "off"`,
  `stack_provider: manual`, `use_queue: false`, and `final: squash` because `main` requires
  linear history. Stacked and integration delivery are not validated or enabled.
- Existing `.github/pull_request_template.md` is preserved; `install_pull_request_template`
  is false, so GitHub UI behavior is unchanged. Handoff still writes per-change bodies and
  requires `--body-file` when creating a PR.
- Task closure still requires current content/requirements-bound Quality, Standards and
  independent Review; no earlier receipt is promoted to the new contract.
- Scoped installation checks are not full Quality readiness. The full local
  `scripts/quality.ps1` matrix and gate regression passed for the current Python packages, but
  direct Workflow execution, independent Review, Doctor agent run and real
  Feature/Bugfix/Ralph delivery were not run for this tooling-only upgrade.
- LF/CRLF warnings are existing platform behavior; no global Git setting is changed.
  Installer-refreshed files may appear in `git status` as line-ending-only entries even when
  their content hash matches the index; `git diff --name-only` remains the content diff.
- Evidence covers the uncommitted working tree at `9cdb10a`; later material changes require
  renewed confirmation rather than reuse of this record.
