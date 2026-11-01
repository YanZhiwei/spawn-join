# Delivery evidence: 009-model-file-config

- **feature_id**: `009-model-file-config`
- **phase_id**: `final-verification`
- **branch**: `ralph/009-model-file-config`
- **base_revision**: `392aa909bcfe57f47d84d3d5e782ffd5fed4ae1f` (`main` at kickoff)
- **branch_base**: `9dcc51a632fba7be05f5ef72df11133789ce050c` (planning artifacts commit)
- **head_revision**: `aa96a5763cff10cf6d74fa6bb1d1cf36c4a6cc40` (code + review fixes; evidence/PR body commit follows)
- **working_directory**: `C:\Users\YanZh\.local\share\opencode\worktree\86e56b\witty-island`
- **recorded_at**: 2026-11-01
- **status**: active
- **result**: pass for the full local quality gate, target package quality, docs, governance, quickstart, and final independent review; PR CI and user Code Review pending

## Commits

| Task | Commit | Summary |
| --- | --- | --- |
| planning | `9dcc51a` | exploration, decision context, slices, ADR-0008 |
| T001 | `6a42876` | add PyYAML/python-dotenv and refresh lock |
| T002 | `6a5bbe8` | add model file fixtures |
| T003 | `9678cce` | YAML document boundary, duplicate/recursive alias checks |
| T004 | `7b88523` | load catalog and create models |
| T005 | `925665c` | protocol options and thinking |
| T006 | `f50e5e2` | model summaries and display names |
| T007 | `0a0cf99` | `.env` support and key precedence |
| T008 | `1c805fa` | adapter README |
| T009 | `d711a7b` | core README, package boundaries, `.gitignore` |
| T010 | `04369c9` | final verification record |
| review fixes | `aa96a57` | extra failure-path tests, contract/ADR consistency, slice deviations |

## Verification

| Check | Command | Result |
| --- | --- | --- |
| Full repository quality | `pwsh -NoProfile -File scripts/quality.ps1` | exit 0（core 129, adapter 105 at that snapshot, observability 7; builds/isolated installs pass） |
| Target package quality (after review fixes) | `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` | exit 0；110 tests passed；Pyright strict 0 errors；Black/isort/Ruff/build/install pass |
| Targeted tests | `pytest tests/test_model_file.py tests/test_public_api.py -q` | 75 passed |
| Docs | `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | exit 0；55 files，191 local targets |
| Governance | `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | exit 0；0 errors，1 pre-existing warning（`harness/evidence/delivery-v022-upgrade.md` 落后 HEAD） |
| Quickstart | temporary script loading `tests/fixtures/model.yaml` and creating both protocols | exit 0；`QUICKSTART_OK` |
| Diff hygiene | `git diff --check` | exit 0 |
| Final independent review | fresh-context subagent over `main...HEAD` | `FINAL_REVIEW_VERDICT: pass`；findings addressed or recorded |

## Scope and deviations

- Implemented: schema v1 `model.yaml`, strict parsing, three protocol options, `thinking`, display names, 5-name public API, explicit `.env` with process-env precedence, READMEs, ADR-0008 (Proposed), package boundary note.
- **Delivery deviation**: the approved slice plan describes 5 stacked PRs; this handoff uses **one feature PR** for user review. Stacked delivery is not claimed; merge method is pending user review.
- **Slice budget exception**: S2 (`9678cce..925665c`) added 1,031 lines (493 source), above `slice_warn_lines: 400`; recorded in `slices.md`.
- **ADR status**: ADR-0008 remains `Proposed`; ADR-0006 carries a dated note that its adapter public surface is extended. Acceptance follows the user's review.
- Out of scope: channel config, multi-file merge, auto-discovery, hot reload, interpolation, provider routing/pool, real Provider requests.

## Limitations and residual risks

- Remote CI is the first check on the actual GitHub runner; local full quality passed.
- No real Provider request was executed; model construction is offline by design.
- `reportUnusedFunction`/PyYAML stub/white-box test suppressions are narrow and documented in the code/tests.
- The pre-existing governance warning is unrelated to this feature and was not silently rewritten.

## Next

Push `ralph/009-model-file-config`, open the PR with `pull-request.md`, monitor CI, fix failures, and wait for user Code Review. Do not merge without separate authorization.
