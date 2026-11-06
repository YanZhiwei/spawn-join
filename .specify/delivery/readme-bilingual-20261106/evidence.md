<!-- DELIVERY_CURRENT_OUTCOME_BEGIN -->
## Current delivery outcome

- **delivery_run**: readme-bilingual-20261106
- **lane**: lightweight
- **status**: delivered
- **outcome**: merged
- **provider**: github
- **repository**: yanzhiwei/spawn-join
- **number**: 41
- **pull_request**: https://github.com/yanzhiwei/spawn-join/pull/41
- **reviewed_head**: 6aa0968ee301534ffcb6548b982deac2f25fb654
- **original_pr_head**: 6aa0968ee301534ffcb6548b982deac2f25fb654
- **published_head_proof**: tracker-head-mapped
- **base_revision**: 4a7f9c9d7fd93e34f5c3f4ed3fb539bb73d0d1f0
- **merged_revision**: e4f12734936c5ed0b3089d66da460b0de85292c8
- **effective_head**: e4f12734936c5ed0b3089d66da460b0de85292c8
- **merged_at**: 2026-11-06T15:31:27Z
- **observed_at**: 2026-11-06T15:31:23.8902858+00:00
- **outcome_recorded_at**: 2026-11-06T15:31:23.8902858+00:00
- **verification_file**: .specify/delivery/readme-bilingual-20261106/runtime/observed-pr.json
- **merge_proof**: diff-equivalent
<!-- DELIVERY_CURRENT_OUTCOME_END -->

## Historical validation snapshots

<!-- Existing validation, review, CI, and limitation content below is retained verbatim as historical evidence. -->

# Bilingual README delivery evidence

## Historical validation snapshot — local review

- **observed_at**: 2026-11-06T15:12:43.103504+00:00 (last package check; independent review and human approval followed)
- **delivery_run**: readme-bilingual-20261106
- **lane**: lightweight
- **feature_id**: readme-bilingual-20261106 (Lightweight run label; no Feature created)
- **phase_id**: outgoing-diff
- **head_revision**: 6aa0968ee301534ffcb6548b982deac2f25fb654
- **working_directory**: C:/Users/YanZh/.local/share/opencode/worktree/86e56b/witty-island-2
- **recorded_at**: 2026-11-06
- **result**: pass for local checks and independent review at the historical reviewed head
- **evidence_path**: .specify/delivery/readme-bilingual-20261106/evidence.md
- **base_revision**: 4a7f9c9d7fd93e34f5c3f4ed3fb539bb73d0d1f0
- **reviewed_head**: 6aa0968ee301534ffcb6548b982deac2f25fb654
- **original_pr_head**: pending
- **pull_request**: pending
- **merge_base**: 4a7f9c9d7fd93e34f5c3f4ed3fb539bb73d0d1f0
- **content_fingerprint**: SHA256 3da44ffd258ddadd72df4c884a226f7db07f37598983bde5a56194bda4f88891
- **requirements_fingerprint**: SHA256 30de0d85d99760f9ebe88d525c3b6ff3643792701f9f7d4346d3d8f8d7335d8c
- **method_identity**: builtin installed Review; instructions-only; independent reviewer session ses_e4e9ec627ffe2dJY5z9JkExXF7
- **bug_slug**: not-applicable

This immutable snapshot describes the local reviewed change, not a later publication or merge.
The Close-owned current outcome block, when present, supplies the terminal result.

## Scope, requirements and design

The user requested separate complete English and Simplified Chinese READMEs, an
updated ongoing documentation rule, and usable GitHub-project documentation.
The user separately authorized PR creation, CI monitoring, merge after success,
and SD Close. After seeing the final six-dimensional review and check summary,
the user selected “批准并继续 (Recommended)” at the final human review gate.
Runtime recorded that actual decision against the presented review/result bytes.

Lightweight is appropriate: 13 documentation entry points are split by language,
with exact-filename governance compatibility and regression coverage. No runtime
API, package ownership, dependency, persistence, permission or architecture
contract changes. Feature Spec/Plan/Tasks are not required for this bounded work.

`README.md` stays the English packaging/GitHub entry; `README.zh-CN.md` is the
complete Chinese peer. Both link to each other. Landing pages prioritize purpose,
package choice, installation, runnable examples and navigation. Long guides have
contents lists. `AGENTS.md` section 4.4 defines the ongoing bilingual standard.
The ADR machine index remains uniquely owned by `docs/decisions/README.md`.
Existing proprietary licensing and unpublished distribution status remain accurate.
No new dependency or credential is introduced. Rollback is a revert of the PR.

### Reviewed paths

All 31 paths have Git mode `100644`. The fingerprint hashes UTF-8 canonical JSON
of Git-ordered rows `{path, mode, sha256}` using sorted keys, compact separators
and `ensure_ascii=False`. `sha256` is the raw working-file byte digest. Original
manifest: `runtime/repair1-changed-paths.json`, SHA256
`c11b931e7982dd5e4205902306ad4cdfd45fbdac3968d2aa1479cff9095afc0d`.
Git retains the exact reviewed versions at `reviewed_head`.

```text
.specify/delivery/README.md
.specify/delivery/README.zh-CN.md
.specify/extensions/quality/quality-config.yml
AGENTS.md
README.md
README.zh-CN.md
docs/decisions/README.md
docs/decisions/README.zh-CN.md
docs/development/quality-gates.md
harness/README.md
harness/README.zh-CN.md
harness/build/README.md
harness/build/README.zh-CN.md
harness/code_review/README.md
harness/code_review/README.zh-CN.md
harness/context/README.md
harness/context/README.zh-CN.md
harness/evidence/README.md
harness/evidence/README.zh-CN.md
packages/core/llm-provider/README.md
packages/core/llm-provider/README.zh-CN.md
packages/core/spawn-join-core/README.md
packages/core/spawn-join-core/README.zh-CN.md
packages/infra/agent-deepagents/README.md
packages/infra/agent-deepagents/README.zh-CN.md
packages/infra/llm-model-sync/README.md
packages/infra/llm-model-sync/README.zh-CN.md
packages/infra/llm-provider-langchain/README.md
packages/infra/llm-provider-langchain/README.zh-CN.md
scripts/check-governance.ps1
scripts/test-governance.ps1
```

Requirements identity covers the bounded user request/authorization, intake,
Constitution, AGENTS, package boundaries, ADR index, quality-gates, delivery and
quality configuration, and builtin review contracts. Native runtime fingerprint:
`2d90cf983b23c662fe9b7ed826fd98d21bbdc57b885c6d43b9f4af2edb94ffee`.
Its snapshot omits the two Delivery READMEs; the explicit 31-path identity above
and every check manifest include both. Only run-local operational reports,
receipts/logs and this evidence/PR bookkeeping are excluded from product scope.

## Mechanical checks

Working directory for all commands:
`C:/Users/YanZh/.local/share/opencode/worktree/86e56b/witty-island-2`.
Environment: Windows, PowerShell, uv, CPython 3.13.5, independent package locks
and environments. The explicit interpreter is
`C:/Users/YanZh/AppData/Roaming/uv/python/cpython-3.13.5-windows-x86_64-none/python.exe`.
Original repair checks ran on 2026-11-06 from 15:09:00Z through 15:12:43Z at the
reviewed head. Before/after input manifests remained identical for all checks.

| Command | Exit | Result |
| --- | --- | --- |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core` | 0 | Package gate passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider` | 0 | Package gate passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` | 0 | Package gate passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-model-sync` | 0 | Package gate passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents` | 0 | Package gate passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | Documentation links passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | Evidence/ADR checks passed; historical warning below |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | 0 | PowerShell/workflow static checks passed |
| `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | 11 scenarios passed |
| `pwsh -NoProfile -File scripts/test-governance.ps1` | 0 | 26 scenarios passed |
| `pwsh -NoProfile -File scripts/test-static.ps1` | 0 | 3 scenarios passed |
| Explicit interpreter + `.specify/delivery/readme-bilingual-20261106/runtime/readme_navigation.py` | 0 | 13 pairs, 396 local links/anchors, language navigation and fences passed |
| `git diff --check` | 0 | No whitespace errors |

The five package gates passed locked sync, Black/isort, Ruff, strict Pyright,
460 pytest tests in aggregate, wheel/sdist builds, isolated installation/import
and dependency checks. Temporary build outputs were kept outside the worktree.
The three new governance fixtures assert actual child-checker exits: Chinese
README accepted (0), broken Chinese README link rejected (1), and other README
prefix evidence still validated/rejected (1).

Original native Quality report `runtime/repair1-quality.md` SHA256:
`4bb4e300e91b868b31b09f6cb218956314e85eaf226fa2c97cba92d067e7124c`.
Checked-tree fingerprint: `3e79047e11c282d3e6865aeae0577b3f049c5f8f6abc230767006de3daad2355`;
configuration fingerprint: `76f2082c6943f2a6889fbf5da358c3071a8ae88896b428f00f5d15cd35a559ec`.
Original per-command hashes, timestamps, working directory and manifests remain
in local `runtime/repair1-*-receipts.json` and associated logs. Those operational
files are not required to understand this committed summary.

Additional offline examples succeeded: root quickstart constructed `ChatOpenAI`,
the supervisor example ran offline, and model-sync CLI `--help` succeeded.
No live provider inference or online metadata synchronization was performed.

## Standards and independent review

`QUALITY_VERDICT: pass`; `STANDARDS_VERDICT: pass`; `REVIEW_VERDICT: pass`.
Standards report `runtime/repair1-standards.md` SHA256:
`5989556d8a8d71683458fd9df8110ae67985ce138966f45bdefd3b5f5d36480c`.
Native independent report: `reviews/outgoing-diff/review.yml`, ticket
`2a9945a0513347ad80bbc782ce35d5ca`. Full 31-path coverage; no partial or unreviewed
material paths. Six dimensions passed: requirements, code quality, architecture,
correctness, security/compatibility, and test effectiveness.

Initial finding R001: both long model-sync guides lacked contents navigation.
Repair commit `6aa0968ee301534ffcb6548b982deac2f25fb654` added matching ten-link
contents lists. Independent reviewer verified all 20 anchors and that removing
the additions restores prior content exactly. R001 is resolved and nonblocking;
repair attempt 1 is complete. Runtime verifies current Quality/Standards
dependencies, native reports, evidence hashes and complete independent Review.
No unresolved blocker remains. Diff-scoped Simplify found no candidates.

## Limitations at this local snapshot

For reviewed head `6aa0968ee301534ffcb6548b982deac2f25fb654`, publication and remote
CI had not happened at the local validation snapshot above. Later observations
are recorded separately. Existing `harness/evidence/delivery-v022-upgrade.md`
freshness warning and Core's empty requirements export notice were non-failing.
CodeGraph was uninitialized; exact source/manifest inspection provided fallback
coverage. External bookmarks are not enumerable; repository inbound links were
checked. The final human review gate was approved before publication.

## Historical publication snapshot — 2026-11-06

GitHub `gh pr view 41 --repo YanZhiwei/spawn-join --json
number,url,state,headRefOid,baseRefOid,mergeStateStatus,statusCheckRollup` returned
OPEN, head `6aa0968ee301534ffcb6548b982deac2f25fb654`, base
`4a7f9c9d7fd93e34f5c3f4ed3fb539bb73d0d1f0`, with checks starting at
2026-11-06T15:29:05Z. This observation establishes the published head as exactly
the historical reviewed head; no content-equivalence exception is needed.

- **original_pr_head**: 6aa0968ee301534ffcb6548b982deac2f25fb654
- **pull_request**: https://github.com/YanZhiwei/spawn-join/pull/41
- **publication_commands**: authorized `git push -u origin docs/readme-bilingual-20261106` and `gh pr create --repo YanZhiwei/spawn-join --base main --head docs/readme-bilingual-20261106 --title 'docs: split and improve bilingual READMEs' --body-file .specify/delivery/readme-bilingual-20261106/pull-request.md`, both exit 0

The new evidence document initially failed the repository governance checker for
six missing legacy metadata fields. Those fields were added; subsequent
`quality.ps1 -Check governance` passed with zero errors/one existing warning,
`quality.ps1 -Check docs` passed (59 files, 271 local targets), and
`git diff --check` passed. This bookkeeping correction does not alter reviewed
product bytes or their original receipts. Evidence/Handoff runtime guards passed
after the correction. At this publication observation CI was running; merge and
Close were not yet performed.

## Historical CI and Close snapshot — 2026-11-06

PR [#41](https://github.com/YanZhiwei/spawn-join/pull/41) completed all 17 checks
successfully in [Quality run 42243451313](https://github.com/YanZhiwei/spawn-join/actions/runs/42243451313),
including the required `Quality Gate`, governance/gate regression, and five
package matrices on Ubuntu Python 3.11/3.14 and Windows Python 3.11.
`gh pr checks 41 --repo YanZhiwei/spawn-join --watch --interval 10` exited 0.

`gh pr merge 41 --repo YanZhiwei/spawn-join --squash --match-head-commit
6aa0968ee301534ffcb6548b982deac2f25fb654` exited 0 under the user's authorization.
No admin bypass or branch rule change was used. GitHub reported MERGED at
2026-11-06T15:31:27Z, merge commit
`e4f12734936c5ed0b3089d66da460b0de85292c8`, retaining the original PR head
`6aa0968ee301534ffcb6548b982deac2f25fb654` and base
`4a7f9c9d7fd93e34f5c3f4ed3fb539bb73d0d1f0`.
The observation came from `gh pr view 41 --json
number,url,state,headRefOid,baseRefOid,mergeCommit,mergedAt,statusCheckRollup`
with the explicit repository. Raw response and normalized observation are local
`runtime/github-merged-pr.json` and `runtime/observed-pr.json`.
`observed_at` is the local clock; `merged_at` is GitHub's clock.

`git fetch origin main`, `git merge-base --is-ancestor
e4f12734936c5ed0b3089d66da460b0de85292c8 origin/main`, and complete-tree
`git diff --exit-code 6aa0968ee301534ffcb6548b982deac2f25fb654
e4f12734936c5ed0b3089d66da460b0de85292c8` all exited 0.
The first Close attempt, while still on the pre-squash feature branch, failed
the installed helper's local reachability guard and made no terminal write.
Creating the evidence-archive branch from the already fetched `origin/main`
put the merged revision at HEAD without resetting or rewriting any existing ref.
The same observed tracker input then passed native Close:

```text
<explicit CPython 3.13.5 interpreter> .specify/extensions/delivery/scripts/delivery_runtime.py close-record --run readme-bilingual-20261106 --outcome merged --pr https://github.com/YanZhiwei/spawn-join/pull/41 --verified --file runtime/observed-pr.json
```

Exit 0: recorded/eligible true, `delivered`, `tracker-head-mapped` publication
proof, `diff-equivalent` merge proof. The machine writer produced the current
outcome block above and refreshed its evidence observation. No run workspace
artifacts were retired for this merged outcome.

Historical precision: the supplementary example executions described above were
originally performed at `ba7132e95b7792249c709d92a310498f7eb7cf05`, not rerun at
the repaired head. The only subsequent product edits were the two model-sync
contents lists; independent review confirmed unchanged examples and valid reuse.
The evidence summary before Close was independently reviewed with no blockers
at SHA256 `25315a5e9c64cf5fd1a2229b626faf875c85e14ac200454251528e1e3ae348ff`.
That review did not claim terminal or archival completion.

## Evidence-only archival validation

Archive baseline: `e4f12734936c5ed0b3089d66da460b0de85292c8`; branch:
`docs/readme-bilingual-evidence-20261106`. Scope is only this canonical evidence
file. On 2026-11-06, in the working directory and environment recorded above,
`pwsh -NoProfile -File scripts/quality.ps1 -Check docs` exited 0 (59 files,
271 local targets), `pwsh -NoProfile -File scripts/quality.ps1 -Check governance`
exited 0 (zero errors, one pre-existing historical warning), and
`git diff --check` exited 0. The original outputs are retained locally as
`runtime/archive-docs.log` and `runtime/archive-governance.log`.
This is documentation bookkeeping; the already recorded package checks are
historical execution evidence, not new runs against an archive commit.
