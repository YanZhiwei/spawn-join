# Delivery evidence: 010-model-metadata-sync

- **feature_id**: `010-model-metadata-sync`
- **phase_id**: `implementation-working-tree`
- **base_revision**: `f717f71b5360b1c4e8b421301359787b0e41db9e`
- **head_revision**: `working-tree`（用户要求不创建本地 commit）
- **working_directory**: `C:\Users\YanZh\.local\share\opencode\worktree\86e56b\tidy-canyon`
- **recorded_at**: 2026-11-02
- **status**: active
- **result**: pass for the available local implementation checks; independent code review and final Delivery review pending

## Scope implemented in the working tree

- 元数据契约、快照文档解析和覆盖合并（`spawn-join-llm-provider`）。
- `model.yaml` v2 解析、可选快照读取和多渠道元数据解析（`spawn-join-llm-provider-langchain`）。
- 新 Distribution `spawn-join-llm-model-sync`：源注册表、models.dev adapter、确定性快照、
  缓存/报告、手动 CLI。
- 文档、ADR-0009（Proposed）、包边界、仓库地图、质量 profile 和 CI matrix。

## Commands and results

| Command | Working directory | Exit code | Result |
|---|---|---|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider` | repo root | 0 | format/lint/type/test/build/isolated install pass |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` | repo root | 0 | pass（含新增元数据测试） |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-model-sync` | repo root | 0 | pass（含新增 26 tests、build、isolated import） |
| `pwsh -NoProfile -File scripts/quality.ps1` | repo root | 0 | full repository quality gate pass |
| `pwsh -NoProfile -File scripts/test-quality.ps1` | repo root | 0 | 10 gate-regression scenarios pass，含新 Distribution 注册断言 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | repo root | 0 | actionlint/PSScriptAnalyzer 0 failing checks |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | repo root | 0 | 58 files / 194 local targets pass |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | repo root | 0 | 0 errors; 1 pre-existing stale-evidence warning |
| `uv run --locked --directory packages/infra/llm-model-sync model-sync sync --source models.dev --model-file <temp>/model.yaml --output <temp>/model-metadata.json --cache-dir <temp>/cache --apply --json` | repo root | 0 | live models.dev sync; matched `openai/gpt-5`; 606 ignored upstream models |
| Adapter load of the live snapshot | repo root | 0 | `metadata_ref=openai/gpt-5`; metadata name `GPT-5`; pricing and reasoning resolved |
| Snapshot backup/restore hash comparison | temp live directory | 0 | rollback byte-identical |

The live sync command was run against a temporary directory under the approved
`C:\Users\YanZh\AppData\Local\Temp\opencode` location; it did not write into the repository.

## Evidence limitations and residual risk

- **No local Git commits** by explicit user request; `head_revision` is `working-tree`.
  Consequently, Ralph per-task commit gates and `ALL_TASKS_DONE` are not used, and task
  checkboxes remain open pending code review.
- ADR-0009 remains **Proposed**; finalization must run after an independent review whose
  reviewed HEAD matches the accepted design.
- The live models.dev check exercised one model and one provider; fixture tests cover
  missing, empty, duplicate and multi-channel cases, but not every upstream provider.
- The source registry currently has one real source (models.dev); the extension seam is
  covered by a fake source and contract tests, not a second production source.
- No scheduler, automatic PR, background refresh or model auto-registration was implemented.
- The repository governance check reports one pre-existing warning for
  `harness/evidence/delivery-v022-upgrade.md`; it is not caused by this change and remains
  unmodified.

## Working-tree paths

Source and tests:

- `packages/core/llm-provider/src/spawn_join_llm_provider/metadata.py`
- `packages/core/llm-provider/src/spawn_join_llm_provider/__init__.py`
- `packages/core/llm-provider/tests/test_metadata.py`
- `packages/core/llm-provider/tests/test_public_api.py`
- `packages/infra/llm-provider-langchain/src/.../model_file/{_schema,_catalog,_metadata,__init__}.py`
- `packages/infra/llm-provider-langchain/tests/test_model_metadata.py`
- `packages/infra/llm-provider-langchain/tests/test_model_file.py`
- `packages/infra/llm-model-sync/`（新 Distribution）

Governance and documentation:

- `docs/decisions/llm-provider/0009-model-metadata-and-sync.md`（Proposed）
- `docs/decisions/README.md`
- `docs/architecture/package-boundaries.md`
- `docs/architecture/repository-map.md`
- `docs/development/quality-gates.md`
- `README.md`、`AGENTS.md`
- `scripts/quality.ps1`、`.specify/extensions/quality/quality-config.yml`
- `.github/workflows/quality.yml`

## Next required gates

1. User code review of the working tree.
2. Independent `speckit.review.run` / Standards review against the reviewed contents.
3. `speckit.decision.finalize` for ADR-0009 after reviewed HEAD matches.
4. Re-run the applicable quality gates on the reviewed contents.
5. Fresh `speckit.evidence.collect` and `speckit.delivery.handoff`; no push, PR or merge
   without separate authorization.
