# Evidence — Role-aware context and learning navigation

## Identity and scope

- **feature_id**: `governance-context-optimization` (Lightweight label, not a new Feature)
- **phase_id**: `governance-context-optimization`
- **route**: Lightweight; documentation/navigation clarification of existing SD/Harness contracts
- **base_revision**: `e292f0e3b746fec266e71dca142fc20356841978`
- **head_revision**: `working-tree`
- **working_directory**: `C:\Users\YanZh\.local\share\opencode\worktree\86e56b\mighty-harbor`
- **recorded_at**: `2026-11-07`
- **result**: pass for documentation, governance structure, navigation and incremental-scope checks; actual role behavior remains unverified

The user authorized optimizing the preceding Delivery/Harness reference findings. The worktree
already contained the uncommitted v0.4.4 installation and reference analysis from the previous
request; those changes are retained, not attributed to this incremental documentation task.
HEAD remains detached at the base above. No Spec/Plan/Tasks is needed because this does not add
product behavior, durable data, runtime enforcement, a scheduling system or an architectural owner.

## Blueprint and authority

- Keep stable permissions, workflow gates and source-of-truth boundaries in AGENTS; replace its
  duplicated Release chronology with the existing installation guide and ADR-0004 links.
- Extend the existing repository map with task/role navigation: relevant minimum sources,
  conditional reading and expected returns. Roles do not authorize subagents or parallel writes.
- Clarify investigation continuity and native handoffs in the existing bilingual Context guide;
  material summaries point to Explore/Bug/owner outputs, not a second report/state machine.
- Clarify consumer verification and reusable learning in the bilingual Review guide. Verified
  guidance returns to its existing package/architecture/development owner; only a qualifying
  long-term decision enters the existing ADR lifecycle. No lesson quota or new approval is added.
- Update the reference analysis/adoption status without relabeling historical installation evidence
  or claiming real model-level effectiveness.

## Incremental changed paths

1. `AGENTS.md`
2. `docs/architecture/repository-map.md`
3. `harness/context/README.md`
4. `harness/context/README.en.md`
5. `harness/code_review/README.md`
6. `harness/code_review/README.en.md`
7. `docs/development/delivery-harness-reference-review.md`
8. `docs/development/spec-kit-delivery.md`
9. `harness/build-log.md`
10. `harness/evidence/governance-context-optimization.md` (new)

The complete outgoing diff still includes the preceding installation; its provenance is
[v0.4.4 installation evidence](delivery-v044-upgrade.md). Its historical checks are not presented
as freshly executed checks of the newly edited documentation. Current project checks inspect the
full current worktree; the incremental preservation audit distinguishes this task's ten paths.

## Baseline and commands

Before edits, the current project docs check passed (61 files / 290 local targets, exit 0).
The current governance check passed with 0 errors / 1 historical freshness warning (exit 0).
Both commands were run from the project root, not inferred from the prior session:

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Check docs
pwsh -NoProfile -File scripts/quality.ps1 -Check governance
```

The baseline snapshot of 558 tracked/untracked non-ignored files and the outgoing Git diff are
stored outside the repository in
`C:\Users\YanZh\AppData\Local\Temp\opencode\spawn-join-governance-context-20261107`.
SHA-256 comparison against this pre-edit snapshot checks preservation of all paths outside the
incremental allowlist, including installer-managed files, project config, packages and scripts.

## Post-edit verification

All commands ran from the working directory above; the temporary audit was explicitly invoked
with PowerShell 7. Its source and logs remain in the temporary directory, not as new project tools.

| Command | Exit | Actual result |
|---|---:|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 62 files / 320 local targets checked; no missing target or whitespace error |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors / 1 unchanged historical freshness warning |
| `pwsh -NoProfile -File scripts/test-governance.ps1` | 0 | 26 scenarios passed, including rejecting unsafe Delivery configuration/automatic hooks and validating bilingual README links |
| `pwsh -NoProfile -File <temporary-root>/audit.ps1 -Project <project-root>` | 0 | Exactly ten incremental allowed paths, 549 baseline files unchanged, no deletion/unauthorized addition; AGENTS sections 0.1 onward unchanged; 13 referenced headings exist |
| `git -c core.safecrlf=false diff --check` | 0 | No whitespace error in the complete current outgoing diff |

The first audit invocation failed (exit 1) because native Git output decoding did not find the
Chinese section marker. The temporary helper was corrected to use explicit UTF-8 native output
and the ASCII section prefix, then the complete rule-text comparison passed. No project rule
was changed to make the audit pass. Line-ending normalization applies only to that text comparison;
the 549-file preservation comparison uses raw SHA-256 hashes.

Semantic self-review confirmed the permission/gate/ownership rules, equivalent bilingual guidance,
and references to actual installed owners. These documentation conventions remain instructions,
not newly machine-enforced semantic checks; neither this audit nor the regression suite proves
that an agent read or understood context. No independent Review pass is claimed.

## Standards and compatibility review

Author self-review, not an independent native Review receipt. The navigation references existing
owners and packets, does not weaken mandatory reading, freshness, task gates, authorization or
the Constitution. Bilingual guides preserve equivalent meaning and examples. Requirements,
observations, recommendations and actual approvals remain distinct. No new dependencies,
permissions, credentials, data flow, public API, execution queue, runtime state or hook is added.

Documentation tests establish structural correctness, not that an agent understood sources or
that the revised guidance improves actual delivery outcomes.

## Limitations

- One pre-existing governance freshness warning concerns `delivery-v022-upgrade.md`, 27 commits
  behind HEAD. This task neither hides the warning nor rewrites that historical evidence.
- Real SD/Ralph, role delegation, model behavior evals, real-host handoffs, remote CI and independent
  Review were not run. No example defect or invented successful handoff is claimed.
- Package builds/tests, static analysis and upstream runtime/distribution suites are not rerun
  for this docs-only increment; their unchanged files are checked by the preservation audit.
- No source-relation exploration is needed for these documentation edits; no CodeGraph index was
  initialized, no generated command/vendor file was edited, and no automatic Hook was enabled.
- No commit, push, PR, merge or publication was performed. Future revisions/scope changes require
  evidence reconfirmation; the user-authorized optimization is not publication authorization.
