# Delivery Evidence — channels-closure-20261108

- feature_id: 015-llm-channel-closure
- phase_id: final-review-and-handoff
- base_revision: 8044db5d3b1430c17f9d6fa0f5c77ef9e3be0a8d
- head_revision: 2d1733745d02ade21666a824a55be890bc86ecef
- reviewed_head: 550ba93b990df737d7dfefd459bc047252ec7ebd
- original_pr_head: 7d3a1df64b8d8304bcf6656e3964c56b2fe51880
- working_directory: C:\Users\YanZh\AppData\Local\Temp\opencode\sj-pr58
- recorded_at: 2026-11-15T21:06:16+08:00
- outcome_recorded_at: 2026-11-15
- status: delivered
- merged_revision: 2d1733745d02ade21666a824a55be890bc86ecef
- pull_request: 58 (https://github.com/YanZhiwei/spawn-join/pull/58)
- result: pass for merged outcome; PR #58 squash-merged as `2d17337` after all 21 CI checks and the required `Quality Gate` passed.
- bookkeeping_commit: the commit immediately after `550ba93` updates only this evidence, the
  persisted PR body, and documentation-only wording/counts (ADR verification text, protocol
  README status pointer). It changes no product source or test and is excluded from the
  reviewed content.

## Outcome

Implemented the library-level channel closure requested by the user:

`ChannelConfig -> ping/list_models -> ModelInfo -> ChatModelConfig.from_channel
-> create_chat_model -> native BaseChatModel`

The user explicitly removed the CLI from scope at the design gate. No routing, pool,
health selection, `channels.yaml`, hot reload, or Agent assembly change was added.

Final continuation work: merged current `main` (`8044db5`) into the branch, re-ran the
seven-package quality gate on the merged content, resolved the final review findings,
and finalized ADR-0013 as `Accepted` against the reviewed head.

## Commits

| Commit | Purpose |
|---|---|
| `685b468` | Approved planning packet and checkpoint baseline |
| `24a8ded` | Channel package, protocol additions, adapter bridge, docs/quality/CI |
| `78c9694` | Reject empty Anthropic cursor IDs and clarify bridge ownership docs |
| `44a32f0` | Merge earlier `main` into the feature branch |
| `3eef412` | Renumber the channel ADR from 0012 to 0013 after the main sync |
| `5c4cf2c` | Merge current `main` (`8044db5`) into the feature branch |
| `550ba93` | Address final review findings; finalize ADR-0013 as Accepted; broaden tests |

`9b674c1` is the original Proposed ADR planning baseline (created as ADR-0012, later
renumbered to 0013 by `3eef412`).

## Commands and results

All commands ran in `C:\Users\YanZh\AppData\Local\Temp\opencode\sj-pr58` at substantive
head `550ba93`, on Windows with Python 3.13.5 and uv 0.12.3.

| Command | Exit | Result |
|---|---|---|
| `pwsh -NoProfile -File scripts/quality.ps1` | 0 | Seven Distributions passed format/isort/Ruff/Pyright/tests/build/isolated install: core 7, common 18, llm-provider 187, llm-provider-langchain 309, llm-channel 104 passed + 2 skipped, llm-model-sync 58, agent-deepagents 146 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 68 files, 345 local targets checked |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors, 1 historical warning (`delivery-v022-upgrade.md` freshness) |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | 0 | actionlint and PSScriptAnalyzer 0 failing checks |
| `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | 15 gate-regression scenarios passed; no root project artifacts |
| `uv lock --check --directory packages/infra/llm-channel` | 0 | Lock consistent after adding the explicit `httpx2` dev dependency |
| `git diff --check` | 0 | No whitespace errors |
| `git status --short --branch --untracked-files=all` | 0 | Clean before the bookkeeping commit |

PSScriptAnalyzer 1.25.0 was installed locally as the documented quality prerequisite
(`Install-Module PSScriptAnalyzer -RequiredVersion 1.25.0 -Scope CurrentUser`).
Remote GitHub Actions were not observed for this local evidence; CI must be re-run after
the branch is pushed.

## Review evidence

Two fresh read-only subagent reviews were performed; the reviewer did not implement this
Feature and did not modify the worktree.

- Round 1 at `5c4cf2c` verified the runtime contract with real SDK `httpx2.MockTransport`
  probes and found no code BLOCKER. It found one evidence BLOCKER (stale
  `base_revision`/`head_revision` and a full-gate result that predated the declared head),
  two MAJOR documentation gaps (ADR verification section still planned; protocol README
  did not point to the new transport), and bounded MINOR/NIT findings.
- Round 2 at `550ba93` confirmed the repairs: `REVIEW_VERDICT: pass`, conditional on this
  bookkeeping commit syncing the evidence, ADR counts/dates, and persisted PR body. It
  independently reproduced the seven package test counts, docs, governance, static,
  gate-regression, and lock results above.
- Findings fixed at `550ba93`: added 404/405/400 mapping tests, an Anthropic empty-page
  success test, and a `sk-sentinel-secret` leakage assertion; declared `httpx2` as a dev
  dependency; documented client-side `limit` truncation, `ValueError` argument semantics,
  the 404/405 endpoint-path diagnostic, `ModelSummary` value semantics, and endpoint
  display/privacy; synchronized the protocol package READMEs and AGENTS command lists.

## Limitations and unexecuted checks

- Real Provider live tests were skipped because no live credentials are available. They
  are opt-in and are **not** reported as passed.
- Remote CI run 43718001688 passed all 21 checks (seven Distributions across Ubuntu
  Python 3.11/3.14 plus Windows 3.11, Governance and gate regression, and the required
  `Quality Gate`) before the squash merge.
- This is a legacy Delivery run: it has no `.specify/delivery/.../runtime/` state,
  receipts, or local Spec/Plan/Tasks (the project keeps `specs/` ignored). Runtime task
  closures and Ralph per-task receipts cannot be reconstructed without inventing passes;
  this packet is the durable record.
- The implementation was committed as feature commits rather than one Ralph task commit.

## Residual risks

- Provider SDK behavior is validated with fake clients and real SDK `httpx2.MockTransport`;
  real endpoint behavior still needs opt-in live validation.
- `uv.lock` also recalculated some transitive markers (`h11`/`truststore`) while adding
  the dev dependency; the local lock/sync/full gate passed and CI's pinned uv confirmed it
  before merge.
- `_page.next_cursor` still returns a cursor when `has_more` is absent but `last_id` is
  present; Anthropic's contract always sends the boolean, so this remains a known NIT.
- `ModelSummary.endpoint` can carry query/fragment data; ADR-0013 now records that it must
  not be written to logs without redaction.
- ADR-0013 is `Accepted` at reviewed head `550ba93`; any later transport, error-mapping,
  credential, or bridge change reopens the decision.
