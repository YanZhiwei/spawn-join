# Evidence — Release-managed Delivery installation

## Identity and scope

- **feature_id**: `006-delivery-release-install`
- **phase_id**: `delivery-release-installation`
- **base_revision**: `fdd0c072186ef3cea7f4b3261acd1d82b358ef56`
- **head_revision**: `2b8b70db080096a5d12ee399409e3cd4c40dfa2f` (PR #8 merge commit)
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-28
- **result**: pass for v0.1.1 Bundle installation and the declared verification environment; merged main CI passed; default-environment Doctor remains blocked

Route: Feature, manual installation bootstrap. Local Spec/Plan/Tasks remain Git-ignored.
No branch switch, staging, commit, push, merge, publication or Ralph iteration is performed.

## Changed paths

- Remove exactly seven files under `.agents/skills/sd/` and `.agents/skills/speckit-delivery/`.
- CLI-owned `.opencode/commands/`, `.specify/integrations/`, integration/init state,
  shared script/template command-surface rendering, extension manifests/registry and workflows.
- Project-owned `.specify/extensions/*/*-config.yml`, `.specify/extensions.yml`,
  `.specify/{extension,workflow,bundle}-catalogs.yml`, `.specify/bundle-records.json`
  and `.specify/.gitignore`.
- `.specify/extensions/quality/quality-config.yml`: seven profiles, including a separate
  shared `pyproject.toml` gate so root tool policy does not run four package gates.
- `scripts/check-governance.ps1`, `scripts/test-governance.ps1`: quoted valid YAML gate
  support/rejection, Delivery evidence/truncated-revision checks, safety settings and
  installer-owned Markdown link boundary, with failing tests first.
- Historical Harness evidence head fields that used truncated SHAs were normalized to
  explicit `working-tree (...)` metadata without changing their conclusions; the Delivery
  lightweight evidence received the required `phase_id`.
- README, AGENTS, architecture/Harness/quality navigation; Delivery installation guide;
  Proposed ADR-0004 and index; this evidence, review and build-log.
- `.specify/delivery/006-delivery-release-install/evidence.md` points to this durable record.

No changes to `packages/`, root tool policy, runtime dependencies, existing core task
customizations, historical Specs, user-level shared skill files or remote settings.
Final scope audit: 132 changed/new/deleted paths (7 removed facades, 31 native commands,
Bundle records/catalogs, project installer state, 2 root documents, docs, Harness records
and 2 scripts).
The target Git index is untouched and base/head are unchanged.

## v0.1.1 Bundle migration

The published [v0.1.1 Release](https://github.com/YanZhiwei/speckit-delivery/releases/tag/v0.1.1)
was verified from its public catalogs before changing the project:

| Actual command/check | Exit | Result |
|---|---:|---|
| Tag inspection | 0 | annotated `v0.1.1` points to `27b2e73` |
| Release asset audit | 0 | 9 ZIPs; SHA-256 matches Release API |
| Published Catalog audit | 0 | extensions/workflows/bundle all `0.1.1`; URLs pinned to `v0.1.1` |
| Isolated published-Catalog Bundle install | 0 | 12 components; Bundle `0.1.1`; Bug `1.0.1` |
| Isolated v0.1.0 → v0.1.1 migration | 0 | `--keep-config` removal and Bundle reinstall; configs preserved |
| Target migration | 0 | 9 extensions + 3 workflows replaced by Bundle-owned `0.1.1` |
| `specify bundle list --json` | 0 | Bundle `0.1.1`, 12 contributed/required components |
| `specify extension list` / `workflow list` | 0 | eight `0.1.1` extensions, Bug `1.0.1`, three `0.1.1` workflows |
| Protected file comparison | 0 | core tasks skill, tasks template and six extension configs byte-identical |
| `.specify/extensions.yml` semantic check | 0 | same installed IDs, `auto_execute_hooks: false`, empty hooks; line endings differed only |
| OpenCode API command discovery | 0 | 31 native commands (21 extension + 10 core) |
| `specify integration status` | 0 | OpenCode default, Codex retained; expected managed-file warnings |
| `pwsh -NoProfile -File scripts/quality.ps1` | 0 | complete four-package, docs, governance and static gate; `quality-v011.log` |
| `scripts/test-quality.ps1` | 0 | 9 gate scenarios |
| `scripts/test-governance.ps1` | 0 | 20 governance scenarios |
| `scripts/test-static.ps1` | 0 | 3 static scenarios |
| `quality.ps1 -Check docs` / `-Check governance` | 0 each | 62 files / 157 targets; 0 errors / 0 warnings |
| Clean checkout without local Specs | 0 | 346 files; docs 35 files / 133 targets and governance pass |

Migration details: remove old components with `specify extension remove <id> --keep-config --force`;
remove the three workflows; replace the v0.1.0 extension catalog with v0.1.1; add v0.1.1 workflow
and Bundle catalogs; run `specify bundle install speckit-delivery --version 0.1.1`. Bundle ownership
is recorded in `.specify/bundle-records.json`; catalog sources are in
`.specify/{extension,workflow,bundle}-catalogs.yml`. The v0.1.0 component installation below is
historical bootstrap and is no longer the current state.

## Release installation (v0.1.0 bootstrap)

- Public Release: v0.1.0, published 2026-10-25; eight owned extension ZIPs plus Bundle asset.
- CLI stays 1.2.3. Active OpenCode installed alongside retained Codex; no force reinitialization.
- Eight extensions installed from the v0.1.0 catalog using `specify extension add <id> --version 0.1.0`.
- Bug 1.0.1 installed from the CLI's bundled core through its v1.2.3 catalog.
- Three workflows installed using `specify workflow add <v0.1.0-tag-workflow-url>`.
- Bundle is **not installed**. Both tested Bundle paths failed before completing installation;
  no Bundle receipt is fabricated and no release files are edited to hide the mismatch.

## Observed checks

| Actual command/check | Exit | Result |
|---|---:|---|
| `specify version` | 0 | CLI 1.2.3; isolated 0.16.4 trial did not replace it |
| `quality.ps1 -Check governance` / `-Check docs` before migration | 0 each | baseline 0/0; 52 files / 124 local targets |
| Release component install in isolated Codex + OpenCode project | 0 | nine extensions, three delivery workflows; custom tasks/config preserved |
| `specify integration install opencode --script ps`; `specify integration use opencode` | 0 each | project default OpenCode; Codex retained; tasks template preserved |
| Target release extension and workflow commands | 0 each | nine components and three workflows registered |
| `specify extension list`; `specify workflow list` | 0 each | expected versions present, zero hooks |
| Python/PyYAML audit using existing Specify tool interpreter | 0 | eight project YAML configs parse; all active extension commands exist |
| Workflow command closure audit | 0 | Feature 21, Bugfix 13, Lightweight 8 unique commands resolve |
| `gh release download v0.1.0 --repo YanZhiwei/speckit-delivery --pattern '*-0.1.0.zip' --dir <owned-temp>/release-assets` and SHA-256 audit | 0 | all nine asset digests match Release API; 41 installed files across eight extensions byte-identical |
| Protected file comparison against pre-install backup | 0 | core tasks skill and tasks template byte-identical |
| `pwsh -NoProfile -File scripts/test-governance.ps1` after fixes | 0 | 16 fixture scenarios pass |
| `git diff --name-only -- packages`; `git ls-files specs` | 0 each | both empty; old facade files absent |
| Release Tag workflow comparison | 0 | all three installed Workflow files byte-identical to v0.1.0 Tag sources |
| Native Release prompt comparison | 0 | 18 Release command bodies retained; bundled Bug commands have expected native command-token substitution |
| OpenCode API `GET /api/command` with explicit project location | 0 | live service discovers all 31 dot-separated project-native commands |
| Tracked clean-checkout simulation | 0 | 332 files, no local Specs; cached diff check, docs and governance all pass; target index untouched |
| `codegraph sync` | 0 | up to date; navigation only, not quality proof |

## Quality Profile execution

Every command below ran from the stated working directory, with `SPAWN_JOIN_TEMP_DIR` set to
the approved temp parent and the fixed PSScriptAnalyzer 1.25.0 directory prepended to **process-local**
`PSModulePath`. The profile runner wrote exact command/exit/log records to
`quality-profile-results.json` under the owned temp directory. No profile command was invented.

| Exact command | Exit | Result |
|---|---:|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core` | 0 | format/lint/type, 7 tests, build and isolated installation |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider` | 0 | format/lint/type, 4 tests, build and isolated installation |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` | 0 | format/lint/type, 6 tests, build and isolated installation |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-observability` | 0 | format/lint/type, 3 tests, build and isolated installation |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | 0 | actionlint and PSScriptAnalyzer, zero failing checks |
| `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | 9 regression scenarios |
| `pwsh -NoProfile -File scripts/test-governance.ps1` | 0 | 16 regression scenarios |
| `pwsh -NoProfile -File scripts/test-static.ps1` | 0 | 3 regression scenarios |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | project documentation and local targets; rerun after final records |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | zero errors/warnings; rerun after final records |
| `pwsh -NoProfile -File scripts/quality.ps1` | 0 | final complete four-package gate plus docs, governance and static checks; `quality-final.log` |

All 11 configured Profile commands pass (the shared `pyproject.toml` profile invokes the same
complete entry point), including the final full quality run. Package/source build/dist,
egg-info and root `.venv`/`uv.lock` checks found no generated project artifacts.
Existing package README/sdist, empty exported runtime-requirements and LF/CRLF warnings remain
non-blocking; no package metadata or global Git settings were changed to suppress them.

## Re-audit and governance hardening — 2026-10-28

The follow-up audit found that `scripts/check-governance.ps1` scanned only
`harness/evidence`, not `.specify/delivery`, and silently skipped truncated
revisions. It also did not validate upstream `artifact_policy` or automatic hook
settings. The checker now validates both evidence trees, rejects truncated
revisions, checks Delivery safety fields, and fails on automatic hooks.

| Actual command/check | Exit | Result |
|---|---:|---|
| `pwsh -NoProfile -File scripts/test-governance.ps1` | 0 | 20 scenarios, including Delivery evidence, truncated SHA, unsafe policy and automatic-hook rejection |
| `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | 9 real-tool gate scenarios; no root project artifacts |
| `pwsh -NoProfile -File scripts/test-static.ps1` | 0 | 3 static-analysis scenarios |
| `pwsh -NoProfile -File scripts/quality.ps1` | 0 | complete four-package, docs, governance and static gate; `quality-reaudit.log` |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors / 0 warnings after evidence metadata migration |
| Tracked+untracked clean-checkout simulation (no `specs/`) | 0 | 341 files; cached diff check, docs (35 files / 131 targets) and governance all pass |
| Quality profile structural audit | 0 | seven profiles; shared root `pyproject.toml` maps to one full gate instead of four package gates |
| Upstream `python scripts/validate_distribution.py` (local checkout) | 0 | catalogs, manifests, workflow requirements and bundle agree |
| Upstream `python scripts/test_validate_distribution.py` | 0 | 4 contract regression tests pass |
| Upstream `python scripts/test_bundle_install.py` | 0 | clean project installed all 12 Bundle components through local release-shaped catalogs on CLI 1.2.3 |

The upstream Bundle test uses local HTTP catalogs and locally built release assets;
it does not publish a release. It proves the source fix, not the immutable v0.1.0
Tag. The published v0.1.0 limitation remains as described below.

## Post-merge closure — 2026-10-28

PR [#8](https://github.com/YanZhiwei/spawn-join/pull/8) was merged as
`2b8b70db080096a5d12ee399409e3cd4c40dfa2f`. The main Quality run
[40699123377](https://github.com/YanZhiwei/spawn-join/actions/runs/40699123377)
completed 14/14 jobs successfully, including all package/platform matrix jobs,
Governance and gate regression, and the required Quality Gate. ADR-0004 is now
Accepted; no Ralph loop or task commit receipt is claimed.

## Readiness and Standards

- Scoped mechanical result: `QUALITY_VERDICT: pass` for the declared verification environment
  and installation working tree, **not** an immutable task receipt.
- [Standards Review](../code_review/review-delivery-release-installation.md): `STANDARDS_VERDICT: pass`
  for the scoped local implementation, with explicit environment/upstream/closure follow-ups.
- [Doctor](../../.specify/delivery/006-delivery-release-install/doctor.md): `SD_DOCTOR_VERDICT: blocked`
  in the default local environment because the static module is not permanently available there.
- Installation/source/native command coherence passed; full autonomous delivery readiness is not claimed.

## Failed attempts and corrections

- CLI 1.2.3 `specify bundle install speckit-delivery --version 0.1.0 --integration opencode`
  in the isolated fixture: exit 1, workflow catalog/YAML requirements mismatch; rollback left no extensions.
- Isolated `uv tool run --from specify-cli==0.16.4 specify bundle install speckit-delivery --integration opencode`:
  exit 1, `--dev source must be a workflow YAML file ... feature-delivery`.
- Existing config was invalid YAML at its unquoted gate/verdict scalars. Before checker adaptation,
  a valid quoted gate fixture failed (exit 1); after adaptation both quote styles pass and unquoted fails.
- Before the vendor boundary fix, a fixture with upstream-relative prompt/README links failed
  (exit 1); after the fix it passes without editing vendor content. Project links remain checked.
- Initial `quality.ps1 -Check static`: exit 1 because PSScriptAnalyzer was absent. Save the required
  1.25.0 module to the owned temp directory and use only process-local `PSModulePath`; no global install.
- One-off live-API JSON parsing through Windows PowerShell string decoding failed on CJK text;
  capturing UTF-8 bytes through the installed PowerShell launcher confirmed the 31 native commands.
  A raw Bug prompt comparison also encountered expected CLI command-token rendering; this is not
  release drift, and byte-exact prompt-body claims are limited to the 18 Release commands.

## Environment and reproducibility

Windows, PowerShell 7, Specify CLI 1.2.3/Python 3.13.5; existing per-package locked environments.
The exact backup, fixture, Release assets and logs are under
`C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-delivery-release-c56b011ad6964caab875c2b1213970bb`.
The v0.1.1 migration backup is
`C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-v011-backup-u98xwyrs`;
the full gate log is `quality-v011.log` in the release-run directory.
This directory is owned by this run, outside the project. No credentials or private content are uploaded.
Installation/upgrade reproduction is in [the Delivery guide](../../docs/development/spec-kit-delivery.md).

## Limitations and blockers

- The default local environment still needs PSScriptAnalyzer 1.25.0; passing tests with an explicit
  temporary module path do not make the default Doctor result pass or authorize a global install.
- The published **v0.1.0** Bundle remains historical and unusable; it predates the Workflow
  `requires` fix. Current state is v0.1.1 Bundle, verified from the published fixed Tag.
  Do not fall back to the v0.1.0 catalog or component instructions.
- Global old skills/commands are deliberately not deleted. Use project dot-separated native commands.
- Integration status reports preserved customizations; do not force overwrite them to remove warnings.
- Generated/vendor Markdown keeps upstream context links and is explicitly outside project link validation.
- No real Feature/Ralph loop, task commit receipt, remote CI, merge protection update or publication is tested here.
- ADR-0004 is Accepted after PR #8; local tasks T001–T009 are marked complete for this delivery.
- This evidence now anchors the merged PR #8 commit and its main CI run; later code changes require renewed confirmation.
