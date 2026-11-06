# Evidence — Anthropic native default budget repair

## Identity

- **delivery_run**: bugfix-anthropic-budget-20261106
- **lane**: bugfix
- **feature_id**: bugfix-anthropic-budget-20261106
- **phase_id**: handoff
- **evidence_path**: .specify/delivery/bugfix-anthropic-budget-20261106/evidence.md
- **exploration_path**: .specify/delivery/bugfix-anthropic-budget-20261106/exploration.md
- **bug_slug**: anthropic-default-token-budget
- **assessment_path**: .specify/bugs/anthropic-default-token-budget/assessment.md
- **assessment_hash**: SHA256 df1d02124da62a44883023e83e5636c90391380046b8bac069e2198726434d46
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

## Requirements, root cause and ownership

Bugfix route: two executable failures established the bounded constructor-alias defect. The adapter passed max_tokens_to_sample=None, overriding the default supplied by LangChain and omitting the required SDK max_tokens. Omit that alias when the budget is unspecified; preserve explicit budgets and native per-call overrides. Do not hardcode 4096 or duplicate native model profiles. Private optional-key TypedDict owns the omission in the existing adapter factory.

This run shares one integrated five-file verification/review snapshot with the metadata error-boundary repair, whose durable record is [here](../bugfix-metadata-source-20261106/evidence.md). Its frozen assessment SHA256 is 68840965a69071c4e24aace353d6411cc23b85aa452ff2cb89d2dfdd2fd86ee4. Both assessments were approved before implementation. Official local reports are fix.md/test.md under each assessment's directory; both test results are verified. Feature Spec/Plan/Tasks are not applicable to these approved bounded Bugfixes.

Accepted constraints: native LangChain model/call semantics (ADR-0006), adapter-owned file/default/error boundary (ADR-0008), existing Agent catalog consumer (ADR-0010). No new public API, protocol field, DTO validator, dependency, credential source, network permission, persistence or lifecycle mechanism. YAML reasoning defaults remain a separate unapproved Feature scope.

## Reviewed content manifest

Paths below are relative to packages/infra/llm-provider-langchain/. Each is a modified regular file, stat mode 438, Git tracked mode 100644. No staged changes, product additions/deletions or outgoing commits.

| Path | SHA256 |
|---|---|
| README.md | 4beb4e366342cab2a4410c7529d4f023b8087bd4288660df995c2decfed825fb |
| src/spawn_join_llm_provider_langchain/factory.py | b4d9cf2b51e00ab0b4494a62c7e1150101391643b523892ef5c9acdb672565a2 |
| src/spawn_join_llm_provider_langchain/model_file/_schema.py | 997d22374df45099b86cfa71045927e27a77bf2c854d5ddebe62f0ffa112c39f |
| tests/test_factory.py | 6f9b6c8a92937d7b9d11e2b65f532e6b98c449549d974469d257d04fa5ec30b7 |
| tests/test_model_metadata.py | 466cc9147c25ffb2bdf61387309a4ec48fbc070e7003a46b761b630091d6eb5f |

Canonical JSON uses sorted keys, ensure_ascii=False, separators=(",", ":"), UTF-8. The requirements manifest binds both assessments/fix/test reports, both exploration/decision contexts, actual governance-scope decision, global/root instructions, Constitution, package/quality rules, review method/templates/config, and applicable ADRs. Full manifest is preserved in reviews/outgoing-diff/review.yml. Runtime's broader 483-file/index snapshot fingerprint is 2738347f221d05e35df52e8a7a8404d9f64823aeb1c25794e136384e41a1198e.

Exclusions: generated same-run runtime/reviews/receipts/evidence/PR bodies, workflow ledgers and unrelated historical Delivery records. No product files or assessments are excluded. The two new evidence files are delivery bookkeeping, outside the product fingerprint. Local ephemeral reports are trace references, not the only description of the durable requirements/results.

## Historical validation snapshot — 2026-11-06

All commands ran from the working directory above; package Python 3.13.5 on Windows, locked dependencies: langchain-anthropic 1.7.7, langchain-openai 1.7.3, langchain-core 1.7.0, anthropic 2.3.0, pydantic 2.14.1. Build staging used SPAWN_JOIN_TEMP_DIR=C:\Users\YanZh\AppData\Local\Temp\opencode; no root uv project was created.

| Exact command | Exit | Result |
|---|---:|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` | 0 | 171 passed; lock/sync, Black/isort/Ruff/Pyright, sdist/wheel, isolated install/pip check/import passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 110 files / 322 local targets; git diff --check passed |
| `uv run --locked --no-sync --project packages/infra/llm-provider-langchain pytest -c pyproject.toml .specify/bugs/anthropic-default-token-budget/test_reproduction.py -q --tb=short` | 0 | 2 passed; before repair the same original reproduction had 2 failures |
| `uv run --locked --no-sync --project packages/infra/llm-provider-langchain pytest -c pyproject.toml .specify/bugs/metadata-source-error-boundary/test_reproduction.py -q --tb=short` | 0 | 2 passed; original red had 2 failures |
| `uv run --locked --no-sync --project packages/infra/agent-deepagents pytest -c pyproject.toml packages/infra/agent-deepagents/tests/test_models.py -q --tb=short` | 0 | 13 passed |
| `uv run --locked --no-sync --project packages/infra/llm-model-sync pytest -c pyproject.toml packages/infra/llm-model-sync/tests/test_model_file.py -q --tb=short` | 0 | 3 passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 1 | Original unrelated readme-governance-package-retirement evidence lacks head_revision; historical freshness warning also retained |
| `codegraph sync` | 0 | Index up to date after source edits |

Original current package output: runtime/quality.log, SHA256 6d6a0647e85989c14cf0094a49a013fe0262a957ed0791ee4e23d444ac4ccf74. Docs output SHA256 5c7a3d905bb407c03cf94119d9058a146bbafa93c6668bf20eb4bad741e050ad. Paired metadata run retains identical copied package/docs output, not an independently rerun suite. Earlier failed test drafts/type checks are retained separately and not counted as passing checks.

Factory regression covers 24 combinations: known/unknown model, absent/empty/explicit options, native per-call override, sync/async. It executes real invoke/ainvoke conversion, mocks the network boundary, checks response and payload, and binds the payload to the actual SDK Messages.create signature. Metadata regression verifies both public loaders, safe paths/causes and existing accepted values.

## Native gates and actual approvals

- Simplify: none; no additional candidate or task queue.
- Docs Sync: bilingual README updated; auto-policy historical maintenance/release sections remain disclosed gaps.
- Quality: pass, ticket 41600e059e8140f6b06a5fc25cc2b5bf; exact snapshot-bound original receipts.
- Standards: pass, ticket 4479d97337754180a2e0a87b74b24f59; adapter ownership, precise types, public surface and dependencies unchanged.
- Review: pass, ticket 735ab462a2204173b43a63106893d144; requirements/code_quality/architecture/correctness/security_compatibility/test_effectiveness all pass; complete coverage; no findings or unresolved IDs. Native report is reviews/outgoing-diff/review.yml.
- User approved both current Review presentations, accepting fresh-context instructions-only independence, package-scope evidence and disclosed limits. Runtime decide verified presented bytes. This is not Git/publication authorization.
- Decision Check: pass for applicable active relationships and implementation delta; ADR-0006/0008 constraints restored, ADR-0009 remains Proposed, no ADR edit needed. Native detail: runtime/decision-check.md.
- `owner-result`, `record`, and `require --kind review` completed with exit 0 for both runs; no repair reservation required.

## Limitations and reproducibility

At this snapshot, user chose “单独记录并继续（推荐）” for the unrelated governance failure. It remains failed; no claim of whole-repository Quality Gate success. Current evidence is local only: no real Provider requests, lowest-dependency matrix, remote CI, commit, push, PR or merge. CI is configured for Linux Python 3.11/3.14 and Windows 3.11; these executions are not inferred from configuration. Hooks are empty/disabled.

Local main was observed two commits behind origin/main at Review approval; local HEAD and reviewed bytes stayed unchanged. Future integration needs current diff/validation, not reuse by HEAD alone. Full exception traceback may expose intentionally preserved cause input; safe-message guarantees concern str(ConfigurationError). LF→CRLF warnings were non-failing.

To reproduce product verification, sync the package using its own uv project and run the package/consumer commands above. Original reproduction scripts are local assessment artifacts; durable package tests carry the regression coverage. Rollback is a targeted reversal of the reviewed five-file patch (or its later authorized commit); it needs no data migration and must preserve unrelated work. At this snapshot rollback would restore both known bugs.

## Handoff artifact verification

After writing both evidence records and PR bodies, `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` exited 0 (runtime/handoff-docs.log). Its tracked-document count remains 110/322; it does not claim to cover new untracked evidence. A separate package-interpreter `python.exe -B -` stdin check exited 0: parsed both native YAML reports, verified identical report bytes and all six axes, rehashed every reviewed product/requirement input, and checked both evidence identities, local Markdown link targets, trailing whitespace and PR body existence. Output: runtime/handoff-artifact-check.log. No product or requirement bytes changed.

PR_BODY_PATH: .specify/delivery/bugfix-anthropic-budget-20261106/pull-request.md

The two run-local bodies describe the same integrated diff, not two independent patches. Publication head branch is unresolved (checkout is main); the exact runnable `gh pr create --body-file` hint is deferred until a separate authorized publication branch exists. Target is main; provider is GitHub. Handoff is waiting-for-publication, not terminal delivery.

## Authorized local commit preparation — 2026-11-07

The user authorized one local integrated Bugfix commit on the new branch
`fix/llm-langchain-boundaries`, restricted to the five reviewed product paths and the two
paired evidence files. No main synchronization, push, PR or merge was authorized.
The sections above describe the original pre-commit snapshot; reviewed_head/head_revision
remain its actual revision, not a claim that a future commit was already reviewed.

Pre-commit integrity verification rehashed the original independent report, all five product
files and all 29 requirement/policy inputs: unchanged. The full package quality command was
rerun successfully (171 tests plus formatting, lint, types, build and isolated installation).
Docs validation also passed. Original reports and hashes are not replaced by those new results.

The first new governance execution found six additional schema errors in these two evidence
files (missing feature_id/phase_id and invalid result words), alongside the unrelated old
missing head_revision. Only the two authorized evidence files were corrected. feature_id is
a governance compatibility identifier equal to this Bugfix run, not an invented Feature Spec;
phase_id records the local handoff phase. result is blocked because repository governance
has not passed; package-scope successes remain explicitly separate. The pre-correction files
and failed output remain under runtime. Original reviewed content/requirements are unchanged.
This metadata correction does not resolve or waive the unrelated historical governance error.

The resulting commit/tree and unchanged reviewed-content association are recorded separately
under runtime/local-commit-association.json after the local commit exists. Historical evidence
is not relabeled as a fresh independent review or remote delivery of that later commit.
