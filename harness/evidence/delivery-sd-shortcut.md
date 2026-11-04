# Evidence — OpenCode /sd shortcut

## Identity and scope

- **feature_id**: `delivery-sd-shortcut` (Lightweight installation repair; no Feature created)
- **phase_id**: `delivery-sd-shortcut`
- **base_revision**: `5e8eb7e4029d5a2ae4835e59ef3759c2abc26d82`
- **head_revision**: `working-tree`
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-11-04
- **result**: pass for shortcut discovery, changed-document links, and governance; full documentation check blocked by an existing ignored Spec link

Route: **Lightweight**. The existing delivery router remains authoritative. This
repair adds a host command that reads that installed router and uses the request
as its input, plus documentation and this operational record. It changes no
Python Distribution, dependency, API, quality profile, or workflow policy, so no
Feature Spec/Plan/Tasks or Ralph queue is required.

The project started on `main` with a clean worktree. HEAD remains the base revision.

## Cause and implementation

Bundle v0.3.1 installed 38 `speckit.*` commands, including
`speckit.delivery.route`, but did not declare an `sd` alias. Earlier manually
copied `sd` skills had been removed. Before repair, the running OpenCode API
reported one full router and zero `sd` commands for this project.

Project-owned `.opencode/commands/sd.md` reads
`.opencode/commands/speckit.delivery.route.md` from the active project and follows
its instructions with the request as input. A missing router is reported as an
installation gap. This command does not depend on global skills or an adjacent
source checkout and does not contain another copy of the delivery lifecycle.

Changed paths:

- `.opencode/commands/sd.md`
- `AGENTS.md`
- `docs/development/spec-kit-delivery.md`
- `harness/build-log.md`
- `harness/evidence/delivery-sd-shortcut.md`

The distribution repository separately prepares v0.3.3 with `aliases: [sd]` on
`speckit.delivery.route`. That installer-managed alias will replace the need for
this compatibility command after publication and a normal Bundle upgrade.
This project remains on released Bundle v0.3.1; its manifests, registry, catalogs,
configuration, generated `speckit.*` commands, and workflows were not upgraded.

## Verification

All project checks below use the working directory recorded above.

| Check | Exit | Observed result |
| --- | --- | --- |
| `opencode api get '/api/command?location[directory]=D%3A%2FRepos%2FGithub%2Fspawn-join'` before repair | 0 | Full router: 1; `sd`: 0; `speckit.*`: 38 |
| Same API request after saving the shortcut | 0 | Full router: 1; `sd`: 1; `speckit.*`: 38; automatic reload confirmed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 1 | Existing ignored `specs/007-llm-protocol-abstraction/plan.md` links to missing `docs/decisions/llm-provider/0005-protocol-native-llm-contracts.md` |
| Scoped equivalent Markdown checks over the five changed files | 0 | Five documents and 54 local link targets verified |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | Zero errors; one existing freshness warning for `delivery-v022-upgrade.md` |
| `git diff --check` | 0 | No whitespace errors |

PowerShell's native-process output encoding was set to UTF-8 before parsing the
API JSON. Its default decoding initially made Chinese descriptions invalid JSON;
that failed parse was not counted as command-discovery evidence.

Separately, from `D:\Repos\Github\speckit-delivery`, real clean-project Bundle
installation checks passed for OpenCode and Codex using Specify CLI 1.2.3. They
verify the packaged alias body/input, installation registry ownership, reinstall
restoration, removal, and preservation of project configuration. The distribution
validator, 46 contract tests, 5 release-stamping tests, Markdown link check, and
v0.3.3 metadata check passed. These are local source checks, not publication proof.

## Limitations

- No delivery request or real model execution was submitted through `/sd`; the
  confirmed behavior is host discovery and delegation to the installed command.
- Doctor, independent project Review, Feature/Bugfix/Ralph workflows, and Python
  package builds/tests were not run for this host-configuration-only repair.
- The local compatibility command is project-owned until the published Bundle
  supplies the manifest alias. No release was published or installed here.
- The full documentation check is not a pass: it scans an existing Git-ignored
  historical Spec with a missing ADR link. That local Spec was not edited; the
  scoped link check and governance check cover the actual outgoing diff.
- This record covers the listed working-tree paths, not later material changes.
