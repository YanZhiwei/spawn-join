<!-- DELIVERY_CURRENT_OUTCOME_BEGIN -->
## Current delivery outcome

- **delivery_run**: agent-middleware-package
- **lane**: feature
- **status**: delivered
- **outcome**: merged
- **provider**: github
- **repository**: yanzhiwei/spawn-join
- **number**: 59
- **pull_request**: https://github.com/yanzhiwei/spawn-join/pull/59
- **reviewed_head**: 4559db3a85f19cc0e8152326a4545b5e5dbabae0
- **original_pr_head**: f593064723483ad34827f1c74a791d77aae5c4c5
- **published_head_proof**: published-evidence-archive
- **base_revision**: 2271860c70a54cdb8703d54617c1550b5a4b0901
- **merged_revision**: b3521d2b976354e0bcc03843d31dc8e4be068738
- **effective_head**: b3521d2b976354e0bcc03843d31dc8e4be068738
- **merged_at**: 2026-11-19T13:32:42Z
- **observed_at**: 2026-11-19T13:44:23Z
- **outcome_recorded_at**: 2026-11-19T13:44:23Z
- **verification_file**: .specify/delivery/agent-middleware-package/runtime/observed-pr.json
- **merge_proof**: evidence-archive
<!-- DELIVERY_CURRENT_OUTCOME_END -->

## Historical validation snapshots

<!-- Existing validation, review, CI, and limitation content below is retained verbatim as historical evidence. -->

# Delivery evidence: agent-middleware-package

- feature_id: agent-middleware-package
- phase_id: close
- base_revision: 2271860c70a54cdb8703d54617c1550b5a4b0901
- head_revision: b3521d2b976354e0bcc03843d31dc8e4be068738
- working_directory: D:/Repos/Github/spawn-join
- recorded_at: 2026-11-19
- result: pass

- delivery_run: agent-middleware-package
- lane: feature
- feature: specs/001-middleware-subpackage
- base_revision: 2271860c70a54cdb8703d54617c1550b5a4b0901
- reviewed_head: 4559db3a85f19cc0e8152326a4545b5e5dbabae0
- published_head: f593064723483ad34827f1c74a791d77aae5c4c5
- pull_request: 59
- reviewed_diff_archive: runtime/reviewed-diff-archive.patch
- reviewed_diff_archive_sha256: b722942877a65cd111b36c22d99f28292601eb6878300f753c28acecf7edaac1
- reviewed_diff_archive_base: 2271860c70a54cdb8703d54617c1550b5a4b0901
- reviewed_diff_archive_head: f593064723483ad34827f1c74a791d77aae5c4c5
- reviewed_diff_archive_reviewed_head: 4559db3a85f19cc0e8152326a4545b5e5dbabae0

## Historical snapshot (recorded before Close)

- Scope: move middleware scopes and the model-call hook into the
  `middleware/` subpackage, keep `llm_errors.py` and `middleware/__init__.py`
  as explicit compatibility entries, and leave classification rules in
  `_llm_error_policy.py`.
- Verification executed on the committed tree:
  - `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents`
    exit 0; 177 tests; Pyright 0 errors; isolated wheel build, install and
    `python -I` import passed.
  - focused tests: 78 passed.
  - `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` exit 0.
  - `git diff --check` exit 0.
- Independent review: outgoing-diff Standards `pass`; six-dimension Review
  `pass` (requirements, code_quality, architecture, correctness,
  security_compatibility, test_effectiveness). Non-blocking findings:
  REV-001 identity-test strength, REV-002 docstring completeness.
- Archive note: the native review ran at 4559db3a85f19cc0e8152326a4545b5e5dbabae0 (temporary execution branch).
  The published head f593064723483ad34827f1c74a791d77aae5c4c5 is that change cherry-picked onto the P1 branch;
  `git diff 4559db3 f593064 -- packages/infra/agent-deepagents` is
  empty, so the reviewed change bytes equal the published change bytes. The
  archived binary patch is `base..published_head`, bound to the reviewed head
  via `reviewed_diff_archive_reviewed_head`.

## Limitations

- Base drift between the temporary execution base (2d4fffb) and the merge base
  (2271860) means whole-tree diffs differ; equivalence is asserted and
  archived over the changed package paths and the published patch.
- The binary review archive stays in the local run workspace at
  `runtime/reviewed-diff-archive.patch`; it is reproducible with
  `git diff --binary --full-index 2271860 f593064 --`.
- Known baseline defect reserved for a separate Bugfix: passing an
  already-normalized `LLMCallError` through the hook sets `__cause__` to
  itself.
