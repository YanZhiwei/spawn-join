# Evidence — Delivery Bundle v0.2.2 upgrade

## Identity and scope

- **feature_id**: `delivery-v022-upgrade` (Lightweight run label; no Feature created)
- **phase_id**: `delivery-v022-upgrade`
- **base_revision**: `035979d6f345899119adc5ad830217f193af7fe8`
- **head_revision**: `079ccc2e4991b26e8bdd7113a46df00e1a1803ce`
- **working_directory**: `C:\Users\YanZh\.local\share\opencode\worktree\86e56b\stellar-engine`
- **recorded_at**: 2026-10-30
- **result**: pass for scoped installation consistency and generated-command checks; Workflows and independent Doctor prompt not run

Route: **Lightweight**. v0.2.2 is a patch release of development tooling. It changes the
packaged Delivery PR-template fallback to Chinese; it does not change Python behavior,
package dependencies, public APIs, architecture or durable data, so no Spec/Plan/Tasks,
delivery Workflow run or Ralph queue is required.

The starting worktree was clean at branch head `035979d`; this upgrade was committed as
`079ccc2e4991b26e8bdd7113a46df00e1a1803ce` on `chore/delivery-v021-upgrade`. This evidence
is re-anchored in a docs-only follow-up commit. No merge or release action is made by the
installation.

## Changed paths and ownership

- Installer-owned `.opencode/commands/speckit.delivery.*`,
  `.specify/extensions/**` and `.specify/workflows/**`: refreshed to `0.2.2`; the packaged
  `templates/pull-request.md` is now Chinese.
- `.specify/{extension,workflow,bundle}-catalogs.yml`, `bundle-records.json`,
  `extensions/.registry`: pinned to v0.2.2 catalogs and versions.
- Project-owned `.specify/extensions/delivery/delivery-config.yml`: uses the packaged Chinese
  fallback via `pull_request_template` and records `install_pull_request_template: true`.
- `.github/pull_request_template.md`: byte-identical static copy of the packaged Chinese
  fallback for GitHub UI; the previous project template remains in Git history.
- `README.md`, `AGENTS.md`, `harness/README.md`,
  `docs/development/spec-kit-delivery.md`,
  `docs/decisions/engineering/0004-release-managed-delivery-installation.md`: current version,
  template policy and upgrade guidance.
- This evidence; the v0.2.1 evidence is marked superseded.

Project-owned extension configs, Constitution, core tasks skill/template and integration
selection are byte-preserved by the installer (14 protected files). No `packages/`, `scripts/`,
CI, runtime dependency, global configuration, historical Specs, remote metadata or user skill
changes.

## Source, permissions and reproducibility

Source: [v0.2.2 Release](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.2.2),
MIT-licensed tooling. Specify CLI remains 1.2.3 / Python 3.13.5; Bug remains the CLI-bundled
1.0.1. Ten Delivery extensions and three workflows are 0.2.2, for 13 Bundle components.
No new runtime dependency, global CLI install, configuration format break or remote write.

Public GitHub downloads are read-only. Only the local project and owned temporary directories
were written; no private content was uploaded. No staging, commit, push, merge, publication,
hooks or autonomous workflow execution.

Owned temporary root (assets, catalogs, fixture, driver, backups and verification records):
`C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-v022-f99d97ffc6fc4d0ba97e6b84c0356bea`.
`fixture/` is a file-level copy of the pre-upgrade worktree (excluding `.git`, `.venv`,
`.codegraph` and caches) so the upgrade was exercised before the target. `target-backup/`
holds the pre-upgrade `.specify`, `.opencode` and project skills. Backups are retained for
inspection, not committed or deleted.

Both fixture and target followed these exact commands, individually exiting 0:

```powershell
$base = 'https://raw.githubusercontent.com/YanZhiwei/speckit-delivery/v0.2.2/catalogs'
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

| Command/check | Exit | Observed result |
|---|---:|---|
| `gh release view v0.2.2 --repo YanZhiwei/speckit-delivery --json ...` | 0 | published, not draft/prerelease; 10 ZIP assets |
| `gh release download v0.2.2 --pattern '*-0.2.2.zip' --dir <owned-temp>/assets` | 0 | all 10 assets downloaded |
| Temporary driver `audit` | 0 | all 10 SHA-256 digests match Release API; catalogs pinned to v0.2.2 and parse; Bundle declares 10 extensions + 3 workflows |
| Temporary driver `upgrade <fixture> fixture` | 0 | 0.2.1 → 0.2.2 on a copy of the live worktree; 14 protected files unchanged |
| Temporary driver `upgrade <worktree> target` | 0 | target at 0.2.2; 13 components; 14 protected files unchanged by installer |
| Fixture/target verification | 0 each | 36 native commands; 26 extension commands; Feature 25 / Bugfix 16 / Lightweight 9 unique commands resolve; 55 non-config extension files and 3 workflows byte-identical to Release |
| `specify bundle list --json` | 0 | Bundle 0.2.2; all 13 components at expected versions (Bug 1.0.1) |
| Packaged PR template | 0 | `templates/pull-request.md` is Chinese; SHA-256 `ee175915a0d390937fec3279087097719656c6fbbb4489584b43caff2bfccad8` |
| Project PR template copy | 0 | `.github/pull_request_template.md` SHA-256 matches the packaged template; `install_pull_request_template: true` |
| Generated Doctor assertion | 0 | references `.specify/extensions/review/templates/reviewer.md`; stale Delivery path absent |
| Generated Handoff assertion | 0 | contains `PR_BODY_PATH`, `PR_CREATE_HINT: gh pr create`, and `--body-file` |
| `specify integration status --json` | 0 | OpenCode default, Codex retained; 0 missing managed files; 0 invalid manifest paths; warning: 32 project-modified managed files (expected customizations) |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | documentation links and structure pass |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors / 0 warnings |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | 0 | 0 failing checks |
| `pwsh -NoProfile -File scripts/quality.ps1` | 0 | full four-package format/lint/type/test/build matrix passed |
| `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | 9 gate regression scenarios passed |
| `pwsh -NoProfile -File scripts/test-governance.ps1` | 0 | 23 governance regression scenarios passed |
| `pwsh -NoProfile -File scripts/test-static.ps1` | 0 | 3 static regression scenarios passed |
| `git diff --check` | 0 | no whitespace errors; LF/CRLF notices only |
| `git diff --name-only -- packages scripts .github pyproject.toml` | 0 | only `.github/pull_request_template.md`; no runtime, automation or shared-tool source changes |

## Doctor and standards assessment

```text
SD_DOCTOR_VERDICT: not-run
INTEGRATION: opencode (Codex retained)
COMPONENTS: all 13 Bundle components installed at their expected versions
WORKFLOWS: all three at 0.2.2; installed command closure passed
POLICY_COVERAGE: seven existing profiles unchanged; Quality owns mechanical checks;
  Review/Simplify/ADR own semantic standards; repair budget remains 2
MANUAL CONTRACT CHECKS: Slice command/template/gate, merge policy, Chinese PR template,
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

- v0.2.2 changes only the packaged Delivery PR-template fallback to Chinese. Command surface,
  workflow inputs, review dimensions, snapshots, repair budget and runtime dependencies are
  unchanged from v0.2.1.
- The project config points at the packaged Chinese fallback and copies the same bytes to
  `.github/pull_request_template.md`. The `.github` copy is a static snapshot; Init does not
  overwrite an existing template, so a future packaged-template change needs a deliberate
  refresh. The previous project template is recoverable from Git history.
- Task closure still requires current content/requirements-bound Quality, Standards and
  independent Review; no earlier receipt is promoted to the new contract.
- Direct Workflow execution, independent Review, Doctor agent run and real
  Feature/Bugfix/Ralph delivery were not run for this tooling-only patch.
- LF/CRLF warnings are existing platform behavior; installer-refreshed files may appear in
  `git status` as line-ending-only entries even when their content hash matches the index.
  `git diff --name-only` remains the content diff.
- Evidence covers material change commit `079ccc2e4991b26e8bdd7113a46df00e1a1803ce`; the
  evidence re-anchor commit changes only `harness/` records. Later material changes require
  renewed confirmation rather than reuse of this record.
