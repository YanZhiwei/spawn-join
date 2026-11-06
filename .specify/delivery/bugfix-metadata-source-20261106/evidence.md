# Evidence — Metadata source error-boundary repair

## Identity

- **delivery_run**: bugfix-metadata-source-20261106
- **lane**: bugfix
- **feature_id**: bugfix-metadata-source-20261106
- **phase_id**: handoff
- **evidence_path**: .specify/delivery/bugfix-metadata-source-20261106/evidence.md
- **exploration_path**: .specify/delivery/bugfix-metadata-source-20261106/exploration.md
- **bug_slug**: metadata-source-error-boundary
- **assessment_path**: .specify/bugs/metadata-source-error-boundary/assessment.md
- **assessment_hash**: SHA256 68840965a69071c4e24aace353d6411cc23b85aa452ff2cb89d2dfdd2fd86ee4
- **base_revision**: 4a7f9c9d7fd93e34f5c3f4ed3fb539bb73d0d1f0
- **head_revision**: 4a7f9c9d7fd93e34f5c3f4ed3fb539bb73d0d1f0
- **reviewed_head**: 4a7f9c9d7fd93e34f5c3f4ed3fb539bb73d0d1f0
- **merge_base**: 4a7f9c9d7fd93e34f5c3f4ed3fb539bb73d0d1f0
- **original_pr_head**: not-yet-published
- **pull_request**: pending
- **scope**: outgoing-diff; five uncommitted package files against local main
- **content_fingerprint**: SHA256 62cf712faf647efffce79ac9712f9a1341724fd7659be147f054e6c6af561e65; canonical JSON of sorted path/kind/stat-mode/raw-byte-hash manifest below
- **requirements_fingerprint**: SHA256 a3716494e170fbc376866b691f4fa284f2edddb9f96c1c686e92ca183eef6657; canonical JSON of builtin method and reviewed requirement/policy input hash manifest in native report
- **method_identity**: builtin six-dimensional review; fresh-context, instructions-only read-only; report SHA256 30083a90520fce810000a2517fe2fe47c287cc0e6d16c99c528a77ee446ef43b
- **working_directory**: D:\Repos\Github\spawn-join
- **recorded_at**: 2026-11-06T23:43:21+08:00
- **result**: blocked — repository governance failed; local package-scope verification and approved independent Review passed; unpublished

## Requirements and repair

Bugfix route: original public-loader tests reproduced escaping Pydantic ValidationError instead of ConfigurationError. Translate that exception only where YAML parsing constructs ModelSourceRef, report a safe YAML field location, omit invalid source keys/coordinate values from the translated public string, and preserve __cause__. Scalar/schema errors must retain a single path prefix. Keep existing validation, valid mappings and internal whitespace compatibility; do not modify protocol DTOs or the independent sync reader.

This run shares an integrated review with the [Anthropic default-budget repair](../bugfix-anthropic-budget-20261106/evidence.md). Its approved assessment SHA256 is df1d02124da62a44883023e83e5636c90391380046b8bac069e2198726434d46. Both assessments were frozen and approved before implementation. Local official fix.md/test.md reports remain under their respective assessment directories; both tests report verified. No Feature queue is needed for these bounded defects; YAML reasoning-default planning is separate.

Ownership: existing LangChain adapter YAML parser and factory. Accepted ADR-0008 controls safe parsing errors and credentials, ADR-0006 controls native model/default/call semantics, ADR-0010 controls the catalog consumer. No new public export, schema field, dependency, permission, persistence, retry or resource lifecycle. Preserved cause may contain original input in a complete traceback; the public safe-message contract applies to str(ConfigurationError).

## Reviewed content manifest

All paths relative to packages/infra/llm-provider-langchain/; modified regular files, stat mode 438 and Git mode 100644. No staged/product-untracked/deleted files or outgoing commits.

| Path | SHA256 |
|---|---|
| README.md | 4beb4e366342cab2a4410c7529d4f023b8087bd4288660df995c2decfed825fb |
| src/spawn_join_llm_provider_langchain/factory.py | b4d9cf2b51e00ab0b4494a62c7e1150101391643b523892ef5c9acdb672565a2 |
| src/spawn_join_llm_provider_langchain/model_file/_schema.py | 997d22374df45099b86cfa71045927e27a77bf2c854d5ddebe62f0ffa112c39f |
| tests/test_factory.py | 6f9b6c8a92937d7b9d11e2b65f532e6b98c449549d974469d257d04fa5ec30b7 |
| tests/test_model_metadata.py | 466cc9147c25ffb2bdf61387309a4ec48fbc070e7003a46b761b630091d6eb5f |

Canonical serialization: UTF-8, sorted keys, ensure_ascii=False, separators=(",", ":"). Native report reviews/outgoing-diff/review.yml retains the full reviewed requirements manifest: both assessments/fix/test reports, exploration/decision contexts, actual governance decision, global/root instructions, Constitution, package/quality policy, review/config resources and relevant ADRs. Runtime broader 483-file/index fingerprint: 597a92e8674c0d8b786dc269efd2b5cb4477a20f324256f4b933e6b4ba898591.

Only generated run runtime/reviews/receipts/evidence/PR bodies, workflow ledgers and unrelated historical Delivery records are bookkeeping exclusions. No source/test/assessment is excluded. The new durable evidence files are outside the five-file product fingerprint. This self-contained requirement/result summary remains available independently of local ephemeral reports.

## Historical validation snapshot — 2026-11-06

CWD above; Windows / package Python 3.13.5. Locked LangChain Anthropic 1.7.7, OpenAI 1.7.3, Core 1.7.0; Anthropic SDK 2.3.0, Pydantic 2.14.1. Temporary builds under C:\Users\YanZh\AppData\Local\Temp\opencode using SPAWN_JOIN_TEMP_DIR. No root uv environment created.

| Exact command | Exit | Result |
|---|---:|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` | 0 | 171 tests; lock/sync, Black/isort/Ruff/Pyright, sdist/wheel, isolated install/pip check/import passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 110 files / 322 local targets; git diff --check passed |
| `uv run --locked --no-sync --project packages/infra/llm-provider-langchain pytest -c pyproject.toml .specify/bugs/metadata-source-error-boundary/test_reproduction.py -q --tb=short` | 0 | 2 passed; original red had 2 failures |
| `uv run --locked --no-sync --project packages/infra/llm-provider-langchain pytest -c pyproject.toml .specify/bugs/metadata-source-error-boundary/test_reproduction.py packages/infra/llm-provider-langchain/tests/test_model_metadata.py -q --tb=short` | 0 | 33 passed |
| `uv run --locked --no-sync --project packages/infra/llm-provider-langchain pytest -c pyproject.toml .specify/bugs/anthropic-default-token-budget/test_reproduction.py -q --tb=short` | 0 | 2 passed; original red had 2 failures |
| `uv run --locked --no-sync --project packages/infra/llm-model-sync pytest -c pyproject.toml packages/infra/llm-model-sync/tests/test_model_file.py -q --tb=short` | 0 | 3 passed |
| `uv run --locked --no-sync --project packages/infra/agent-deepagents pytest -c pyproject.toml packages/infra/agent-deepagents/tests/test_models.py -q --tb=short` | 0 | 13 passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 1 | Unrelated original evidence missing head_revision; historical freshness warning retained |
| `codegraph sync` | 0 | Up to date after source changes |

The current package/docs/governance logs are byte-for-byte copies from the paired run's same-snapshot execution, not independent reruns. Package log SHA256: 6d6a0647e85989c14cf0094a49a013fe0262a957ed0791ee4e23d444ac4ccf74. Docs log SHA256: 5c7a3d905bb407c03cf94119d9058a146bbafa93c6668bf20eb4bad741e050ad. Earlier failed fixture drafts/type checks are preserved separately, not counted as passes.

Regression asserts both public YAML loader paths, safe exact messages, Pydantic cause, invalid IDs/coordinates, integer/bool/null and missing/unknown fields. Valid mapping and internal whitespace tests prevent inadvertent validation tightening. The factory's 24-case real invoke/ainvoke conversion suite checks omitted/default/explicit/call-time budgets with a mocked network boundary and actual SDK signature binding.

## Gates and user decisions

- Simplify: none; Docs Sync: updated bilingual README, historical auto-policy maintenance/release gaps disclosed.
- Quality: pass, ticket a5315990f9b0476d928d785283dbe386; Standards: pass, ticket 3ea95b06790d4d1ea99f6882936a4af2.
- Independent Review: pass, ticket 03553cebcec844678f4d44daf3d7105f; all six dimensions pass, complete coverage, no findings. Report preserved unchanged in reviews/outgoing-diff/review.yml.
- User approved both Review presentations and actual fresh-context instructions-only independence. Runtime approval verifies exact displayed report/assessment bytes. Approval does not authorize Git or publication actions.
- Decision Check: applicable ADR relationships and implementation delta pass. ADR-0009 remains Proposed; no decision record changed. Detail: runtime/decision-check.md.
- Runtime owner-result/record/require-review completed with exit 0; no repair loop required.

## Limitations, reproduction and rollback

At this snapshot, user explicitly accepted package-scope continuation while leaving the unrelated repository governance failure unchanged. Whole-repository Quality Gate has not passed. Remote CI, real Provider requests, minimum-dependency/runtime matrices, commit/push/PR/merge remain unexecuted. CI configuration includes Linux 3.11/3.14 and Windows 3.11; configuration is not execution evidence. Hooks are empty/disabled. LF→CRLF warnings were non-failing.

Local main was two commits behind origin/main at Review approval; reviewed local HEAD/bytes stayed unchanged. Remote integration requires fresh scope/evidence checks. To reproduce, sync the package-local uv project and run the package/consumer commands above. Local reproduction scripts are assessment artifacts; package tests permanently carry the behavior regressions.

Rollback reverses only the reviewed patch or its later authorized commit, preserving unrelated work. No data migration is required; the original two defects would return. Neither this record nor the PR body asserts a delivered terminal outcome.

## Handoff artifact verification

After writing both evidence records and PR bodies, the docs command exited 0 (runtime/handoff-docs.log, identical copy of the paired execution). Its tracked-document count remains 110/322 and does not cover new untracked evidence. A separate package-interpreter `python.exe -B -` stdin verification exited 0: parsed both native YAML reports, checked identical bytes and all six axes, rehashed every reviewed product/requirement input, and checked both evidence identities, local Markdown targets, trailing whitespace and body existence. Shared raw output is runtime/handoff-artifact-check.log. Product/requirement bytes stayed unchanged.

PR_BODY_PATH: .specify/delivery/bugfix-metadata-source-20261106/pull-request.md

Both run-local PR bodies cover the same integrated diff. Actual publication head branch is unresolved (checkout remains main), so an exact runnable `gh pr create --body-file` hint awaits separately authorized branch creation. GitHub target is main. Handoff is waiting-for-publication, not a delivered outcome.

## Authorized local commit preparation — 2026-11-07

The user authorized one integrated local Bugfix commit on `fix/llm-langchain-boundaries`,
limited to the five reviewed product files and the two paired evidence records. Main was not
synchronized; push, PR creation and merge remain unauthorized. Earlier sections retain the
actual pre-commit validation snapshot and its reviewed_head/head_revision.

Before staging, original report bytes, all five product hashes and 29 reviewed requirement
inputs matched the approved review. The package quality command was rerun: 171 tests and
format/lint/type/build/isolated-install checks passed; docs validation passed. These are new
coordinator checks, not another independent review. Original review and quality reports remain.

The first new governance command exposed missing feature_id/phase_id and an unsupported result
word in both newly produced evidence records. Only these authorized records were corrected;
feature_id is the Bugfix run identifier for governance compatibility, not a claim that a Feature
Spec exists, and phase_id is handoff. result=blocked preserves the actual repository-governance
failure while retaining the separate local package successes. Original evidence bytes and the
failed output are preserved under runtime. Product and reviewed requirement bytes did not change.
The unrelated historical record missing head_revision remains unmodified and not waived anew.

After commit, runtime/local-commit-association.json records the real SHA/tree and its association
with the approved five-file content, without restamping the original independent review or
claiming remote delivery. No terminal delivered outcome is recorded by this local operation.
