# Delivery evidence — ADR-0014 P1 review fixes

- **delivery_run**: `adr-0014-p1-fix-20261126`
- **lane**: `bugfix`
- **evidence_path**: `.specify/delivery/adr-0014-p1-fix-20261126/evidence.md`
- **base_revision**: `be26baeb4148445f1c486531844aa90eadfd3ed4`
- **reviewed_head**: `8880a6d9281e8cfde6a5828aff28e78cbdc17ce9`
- **original_pr_head**: `pending`
- **content_fingerprint**: `sha256:66074f5eee97b06c3b8bd09f1da6dbd13da847b914671224d6077472e62f1e88`
- **requirements_fingerprint**: `sha256:c7a26da49c4e69e84c020fba98c5c8ed3d354db82afd708b6bb1c27db03933b2`
- **method_identity**: `builtin independent six-dimensional review; ADR-0014 F1-F8 regression repair`
- **pull_request**: `pending`
- **working_directory**: `D:\Repos\spawn-join`
- **recorded_at**: 2026-11-26
- **result**: pass

## Scope

修复 ADR-0014 独立 Review 的 F1-F8：

- 原生 `RubricMiddleware` 在 supervisor、workers、worker overrides 和 declarative
  subagent middleware 的 beta gate 与排他校验；
- 原生 rubric `_tools` 的 `tool_count` 报告；
- `SupervisorSpec` 既有位置参数兼容性；
- `ResourceReport`/`AssemblyReport` 迁移说明；
- generic `BaseSandbox` 分类；
- rubric 未配置、非法 callback、多作用域、工具计数和兼容性回归测试；
- ADR-0014 的当前契约和复评状态说明。

## Verification

| Command | Exit/result |
|---|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-deepagents` | 0；lock/sync、Black/isort、Ruff、Pyright、315 tests、build、isolated install、pip check、MCP probe 全部通过 |
| `uv run --locked --directory packages/infra/agent-deepagents pytest -q tests/test_rubric.py tests/test_backends.py tests/test_supervisor.py` | 50 passed |
| `uv run ... ruff check ...` | pass |
| `uv run ... pyright ...` | 0 errors, 0 warnings |
| `git diff --check` | pass |

独立复评在 `9e21d91` 上为 `REVIEW_VERDICT: pass`；随后仅有仓库格式/导入排序
修正，未改变产品行为。复评确认 F1-F8 无新问题。

## Findings disposition

| Finding | Disposition |
|---|---|
| F1 | Fixed: all public middleware scopes are scanned and gated |
| F2 | Fixed: native `_tools` is reported with a public accessor fallback |
| F3 | Fixed: rubric fields are keyword-only after legacy positional fields |
| F4 | Fixed: report migration text now matches appended fields |
| F5 | Fixed: all `BaseSandbox` implementations classify as `sandbox` |
| F6 | Fixed: targeted regression tests added |
| F7 | Fixed: evidence is bound to the reviewed repair head and full package gate |
| F8 | Fixed: disabled `RubricReport.model_source="none"` and coverage documented |

## Limitations

- 真实 provider structured-output rubric 执行仍不在离线测试范围内。
- 远端 CI、合并前的最终 GitHub checks 由 PR #（待创建）提供。
- 本次不接受 ADR-0014；接受动作必须在 PR 合并后的 reviewed HEAD 上另行完成。

