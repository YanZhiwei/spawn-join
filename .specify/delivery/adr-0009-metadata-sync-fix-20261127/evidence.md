# Delivery evidence — ADR-0009 metadata sync review fixes

- **delivery_run**: `adr-0009-metadata-sync-fix-20261127`
- **lane**: `bugfix`
- **bug_slug**: `adr-0009-metadata-sync-review-fixes`
- **evidence_path**: `.specify/delivery/adr-0009-metadata-sync-fix-20261127/evidence.md`
- **exploration_path**: `.specify/delivery/adr-lifecycle-closure-20261126/reviews/adr-0009-review.md`
- **assessment_path**: `.specify/delivery/adr-lifecycle-closure-20261126/reviews/adr-0009-review.md`
- **assessment_hash**: `sha256:56c29c684bb8582a38f417101ccbdea7438c0dd6872c4eb8ec483ec985b44251`
- **base_revision**: `b867b68c8aaa8f93bc02afe838f9ce2a248dd040`
- **reviewed_head**: `139c7cb4d0a8fbdc6e72f6e8cde0b6c6c5d58f00`
- **original_pr_head**: `pending`
- **content_fingerprint**: `sha256:04e60e728e594bffab1dc39f9a73b59fa32b0388bebe7f8295a80c01827f5f96`
- **requirements_fingerprint**: `sha256:fb5c34e25ac18c73ca654c172f249f79dcd63a9e670bf7a073f4fd4384a1fce8`
- **method_identity**: `builtin independent review plus configured package quality gate`
- **pull_request**: `pending`
- **working_directory**: `D:\Repos\spawn-join`
- **recorded_at**: 2026-11-27
- **result**: pass

## Scope

修复 ADR-0009 独立 Review 的 F1-F8：

- 上游和 model.yaml 校验错误转换为稳定错误；
- 默认 dry-run 不写快照、缓存或报告；
- 修正 Windows 默认缓存路径；
- 渠道只保留与共享事实不同的覆盖；
- 更新 common 依赖、reader 边界和实际 summary 字段文档；
- 严格校验 metadata_ref/source ID/inline metadata；
- 拒绝非法日期、未知模型类型和无法识别的模态事实；
- 补充 CLI、dry-run、渠道差异、malformed payload 和边界回归测试。

## Verification

| Command | Result |
|---|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-model-sync` | pass：lock/sync、Black/isort、Ruff、Pyright、62 tests、build、isolated install、pip check、import |
| `uv run --locked --directory packages/infra/llm-model-sync pytest -q` | 62 passed |
| Ruff | pass |
| Pyright | 0 errors, 0 warnings |
| `git diff --check` | pass |

独立复评在此前 HEAD `649d2c2` 确认 F1-F6 已修复，并指出 F7 residual；
本次继续修复 F7，且补充严格 modality/provenance 边界。最终远端 CI 将验证完整 PR 树。

## Limitations

- 真实 models.dev live sync 未执行。
- Snapshot provenance 的统一 URL 校验仍属于后续增强；当前 runner 生成的来源 URL 已经过 fetch URL 校验和脱敏。
- ADR-0009 保持 `Proposed`，需要 PR 合并后在最终 reviewed HEAD 上完成接受决策。
