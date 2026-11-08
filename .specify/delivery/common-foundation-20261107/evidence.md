# Evidence — Common package planning

## Identity

- **delivery_run**: common-foundation-20261107
- **lane**: feature
- **feature_id**: 014-common-foundation
- **phase_id**: implementation
- **base_revision**: 10b905d46af547330f815498b6f24cfc24449f69
- **head_revision**: 7dbc714e8d575ae326da81c92eca7459807a241d (main after squash merge of #48); pre-merge feature head ea2c9e7; reviewed product content 4454f22
- **pull_request**: #48 merged to main (`7dbc714`); prerequisite #45 merged to main (`6906acc`); earlier stacked #47 closed as superseded
- **status**: delivered
- **merge_revision**: 7dbc714e8d575ae326da81c92eca7459807a241d
- **working_directory**: C:\Users\YanZh\.local\share\opencode\worktree\86e56b\common-foundation
- **recorded_at**: 2026-11-08
- **result**: pass — Feature 014 and prerequisite PR #45 squash-merged to main; required checks green; no release

## Authorized scope and proposed design

用户在公共包命名、目录和按职责扩展提案后明确回复“建立”。Scope 为建立独立 spawn-join-common，首批迁移已有复用的校验机制；时间转换等留给有具体契约的后续需求。

Proposed design: packages/core/common，默认零运行时依赖的 FieldReader；optional Pydantic validation extra 提供 typed validate_with(operation, *, error, message)。common 不依赖领域包，Core 保持零依赖；协议旧导入/default 由薄兼容入口保持；adapter FileInput/strict null 与 metadata/Sync 策略留在各自包。

长期边界写入 [Proposed ADR-0011](../../../docs/decisions/engineering/0011-common-helper-package.md)，索引同步更新。ADR 没有被标记 Accepted。本记录不链接被忽略的本地 Spec 工件作为长期契约的唯一来源。

## Historical planning artifacts and state

本地 Feature 为 specs/014-common-foundation，已有 spec.md、plan.md、research.md、data-model.md、quickstart.md、contracts/python-api.md、checklists/requirements.md。旧 YAML Feature 文件未修改；原 feature.json 内容在该 run runtime/previous-feature.json 备份，当前本地指针显式切到新 Feature。

Runtime init/bind 与 Core setup-plan 已真实执行成功；不是完整 Delivery/Ralph 运行。
设计仍待用户对展示的准确内容批准；Tasks、正式 Slice、Analyze 与任务执行/关闭均未开始，未伪造批准、原生评审或提交凭证。

## Executed checks

CWD 如上；Windows，Python 3.13.5，使用各 Distribution 既有独立环境。

| Exact command | Exit | Actual result |
|---|---:|---|
| `git status --short --branch` / `git rev-parse HEAD` | 0 | 基准分支 fix/llm-langchain-boundaries，HEAD 如上；起始 tracked 干净，原有 untracked 退休 evidence 保留 |
| `codegraph status` | 0 | Index up to date；实际源码定位使用 explore，不代替测试 |
| `uv run --locked --no-sync --project packages/core/llm-provider pytest -c pyproject.toml packages/core/llm-provider/tests -q --tb=short` | 0 | 迁移前协议基线 154 passed |
| `uv run --locked --no-sync --project packages/infra/llm-provider-langchain pytest -c pyproject.toml packages/infra/llm-provider-langchain/tests -q --tb=short` | 0 | 迁移前适配基线 240 passed |
| `uv run --locked --no-sync --project packages/infra/llm-model-sync pytest -c pyproject.toml packages/infra/llm-model-sync/tests -q --tb=short` | 0 | 迁移前 Sync 基线 55 passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 初轮新规划与 ADR 文档：132 files / 338 local targets；非源码实现验证 |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 1 | 原有退休 evidence 缺 head_revision，1 error；另有历史 evidence freshness warning。没有新增 ADR 或本 Feature schema 错误 |
| `git diff --check` | 0 | 当前 tracked diff 空白检查通过；新文件另做结构/路径核对 |

只读子代理 ses_e4e131aecffejhRImLnAtEcQmu 调查实际复用点，建议仅公开两项机制；不是实现 Review 或批准。原始建议/日志/展示指纹保存在本 run runtime，不提交为产品源码。

## Historical planning changes and limitations

当前 tracked change: docs/decisions/README.md；新增 Proposed ADR 与本 evidence；其他新运行工件按 ephemeral 策略留本地。尚未创建 packages/core/common 或变更任何 Python、manifest、lock、CI、质量 Profile。

新包测试、消费者迁移、两种隔离安装、构建、静态/工具回归、独立六维 Review、任务提交和远端 CI 均未执行；上述原包测试仅为迁移前基线。
原工作区无关未跟踪 .specify/delivery/readme-governance-package-retirement-20261105/ 原样保留，不纳入本 Feature，也不把其治理失败写成通过。
无 commit、push、新 PR、旧 PR 修改、merge 或发布。后续执行需实际设计与切片门及项目 Git 授权；本记录不代替这些门。

## Standalone implementation — T001 accepted, T002 implemented

The installed SD checkpoint rejected the project-required nested ADR and the ADR authority index (real-state read-only probe exit 1). The unchanged helper, config and source were not patched. The user then explicitly selected standalone Core Implement for this Feature only; see runtime/standalone-exception.md. No RALPH task gate, slice approval, task receipt or SD checkpoint is claimed.

Later the user explicitly requested “合并main最新代码”. Because T001 was uncommitted, the coordinator created one local checkpoint commit 8b1aaf6 and merged origin/main 5021b18 (Delivery v0.4.5) as 65c688f. The merge auto-resolved; Common product files remained byte-identical and AGENTS/repository-map/spec-kit-delivery retain both main's v0.4.5 text and the Common/six-package/nine-profile statements. No push, PR edit, merge-to-main or publication. See runtime/merge-main-authorization.md.

T001 (fresh package + tooling/docs) was independently reviewed twice in fresh context: a pre-merge pass after fixing 4 findings, then a merged-snapshot delta pass on 65c688f with content fingerprint 654ba25d... and requirements fingerprint 75260905..., verdict pass, coverage complete. Findings T001-ARCH-001/TEST-001/TEST-002/DOC-001 resolved; T001-EVID-001 dismissed under the recorded user-owned CodeGraph no-index limitation with an AST import-scan substitute and required T002 rescan. T001 checkbox is checked based on that acceptance.

T002 migrated the consumers: protocol FieldReader is a thin compatibility dataclass with the original default ConfigurationError; protocol metadata delegates mapping and top-level Pydantic conversion to common while preserving formatter/order/cause; adapter delegates only its foreign ValidationError conversion while keeping FileInput/annotations/null/first-error semantics; Sync uses common FieldReader with its own ConfigurationError/SourcePayloadError and keeps metadata projection plus models.dev null-as-absent. Manifests add common[validation] to protocol/adapter and common base to Sync; agent only received a transitive lock update; lock diffs are additions only (+112 lines across four locks, no third-party version changes). quality.ps1 consumer build graphs include common.

Executed on the merged tree (logs are run-local):

| Command / check | Exit | Result |
|---|---:|---|
| `pytest packages/core/llm-provider/tests` | 0 | 158 passed (4 new compatibility tests) |
| `pytest packages/infra/llm-model-sync/tests` | 0 | 58 passed (3 new strict-reader tests) |
| `pytest packages/infra/llm-provider-langchain/tests` | 0 | 240 passed |
| `pwsh scripts/quality.ps1 -Package <each of six distributions>` | 0 | all six package gates passed (format/lint/type/tests/build/isolated install) |
| frozen protocol metadata comparison | 0 | 8 cases, 0 mismatches; reference SHA256 3ed9b6b9... unchanged |
| frozen 1536 parser differential | 0 | 0 mismatches; interim reference SHA256 8fa9427a... unchanged |
| AST navigation rescan | 0 | CodeGraph unavailable (no CLI/DB); importers listed; required suites enumerated |
| docs / governance / static | 0 | 72 files/333 targets; 0 governance errors (1 historical warning); 0 static failures |
| quality/governance/static regression | 0 | 15 / 26 / 3 scenarios |

T002 checkbox is checked on that acceptance. Per the user's “继续完成当前任务”, T002 was then committed locally as 19930b2 (26 files, 342 insertions/135 deletions) after scoped staging and whitespace checks; no push, PR edit, merge-to-main or publication. See runtime/t002-commit-authorization.md. A final integrated outgoing-diff review of the T001+T002 feature delta is the remaining local gate.

T002 independent review is now complete: pass on content fingerprint `5d8225bc9ba9037724d51b33111d5659729dc122e1cef85237e78a16d85654aa` and requirements fingerprint `7b8165b1b2996c61bd87be49db3a6b19572c2ce6ebc08b5e17981c0f5f091bce`, all six dimensions pass, coverage complete. The reviewer initially blocked on T002-DOC-001 (Sync README still pointed maintainers to the protocol reader) plus five minor findings; all were fixed and re-verified: bilingual Sync guidance now points to Common with the protocol reader labeled compatibility-only; the boundary table lists all Common local sources; the protocol shim has frozen/slotted tests; exact metadata messages and cause types are committed tests; the AST scan resolves package-relative imports correctly; the dependency test is renamed. The final review records only the T002 checkbox as post-review bookkeeping, excluded from the product identity.

T002 is committed as 19930b2; the branch contains T001 8b1aaf6, the authorized main merge 65c688f and T002 19930b2. No push, PR edit, merge-to-main or publication was performed. Remote CI, other Python platforms and real Provider calls remain unexecuted.

## Publication — 2026-11-08

The user objective then required creating a PR after completion. The branch `feat/common-foundation` was pushed (remote head 19930b26f8140f599046ff708b576a43e80532f1) and draft PR #47 was created:

- URL: https://github.com/YanZhiwei/spawn-join/pull/47
- base: `fix/llm-langchain-boundaries` at 10b905d (the unmerged PR #45 layer); head: `feat/common-foundation` at 19930b2
- metadata verified by `gh pr view 47`: OPEN, draft, exact base/head SHAs above
- `gh pr checks 47`: 18 package jobs + governance are pending at creation; no result yet
- PR body: `.specify/delivery/common-foundation-20261107/pull-request.md`

Deviation from the historical slices.md publication groups: the approved slice plan proposed two stacked publication groups P1/P2, but the explicit user request was singular (“创建pr”) and execution used the standalone exception. One stacked draft PR was therefore created containing both T001 and T002; slices.md remains the historical proposal and is not rewritten. Retargeting to main and marking ready remain separate decisions after #45 merges.

No merge, release or ready-for-review transition was performed.

## Final integrated review and CI — 2026-11-08

The final integrated fresh-context review returned **pass**, coverage complete, with content fingerprint `1d10f3593609e5de66c6308a37f934f9bd3fa0a108bfcc68523751dd599dde14` and requirements fingerprint `054795a27a64a764f6d65280dc842d96c80cb7b50c742fe82b616a42fe464d39`. It re-accounted for all T001/T002 findings as resolved/dismissed and found one non-blocking documentation finding:

- F-001: ADR-0011's implementation-status paragraph still said “尚未实现，尚未获设计批准” and cited only the pre-migration 154/240/55 baseline.

F-001 was fixed in local commit `4454f2205904e04f1ab44d149743f6cd05fb4806` by replacing the stale status with the actual implementation, verification, CI and publication state while keeping Status: Proposed. Docs and governance were re-run after the change: docs 72 files/333 targets exit 0; governance 0 errors/1 historical warning exit 0. The same final reviewer verified the fix and returned pass at 4454f22 with product-code fingerprint `cb5cb89122bed7162a8b5d03e8ca5d9533b10a3c26e79cd8f800d5f56ad02318` unchanged from 19930b2.

Remote CI for PR #47 at head 4454f22 was verified with `gh pr checks 47`: all 18 package jobs (six distributions × Linux 3.11/3.14, Windows 3.11), governance, and the required `Quality Gate` are success (20/20 pass); `mergeStateStatus` is CLEAN and the PR remains draft. No real Provider call, macOS/other Python matrix, merge, ready-for-review or release was performed.

Final verdict: pass. PR #47 is stacked on the still-open, behind draft PR #45; retargeting to main and merge order remain human release decisions. ADR-0011 remains Proposed pending decision-owner acceptance.

## Merge outcome — 2026-11-08

The user requested “帮我合并pr”. The stacked order was executed and verified with `gh`:

1. PR #45 (`fix/llm-langchain-boundaries`): marked ready, updated from main to `3469cce`, all 17 checks plus required `Quality Gate` passed, squashed to main as `6906acca67070e55b3153654d8a7addbee64f4b8` at 2026-11-08T08:40:34Z.
2. Deleting the #45 base branch caused GitHub to close the stacked #47; closed PRs cannot be reopened or retargeted, so #47 is recorded as superseded.
3. `feat/common-foundation` merged the new main (`6906acc`) as `ea2c9e7`; conflict resolution kept the already-reviewed T002 versions, and `git diff 4454f22 ea2c9e7` was empty (product content byte-identical).
4. New PR #48 was created directly against main, all checks passed (`mergeStateStatus: CLEAN`), and it was squashed to main as `7dbc714e8d575ae326da81c92eca7459807a241d` at 2026-11-08T08:44:50Z. `origin/main` now equals `7dbc714`.

Post-merge state: #45 MERGED, #48 MERGED, #47 CLOSED (superseded), remote feature/base branches deleted. Local worktree branch remains checked out; no release or registry publication. ADR-0011 remains Proposed pending decision-owner acceptance.

Post-merge main CI for `7dbc714` ran: all 18 package jobs succeeded; the governance job failed only in `actionlint` static analysis because the runner could not download `actionlint_1.7.12_linux_amd64.tar.gz` from GitHub (`HTTP 504 Gateway Time-out`). Two reruns of the failed job reproduced the same external download failure; the package matrix remained green. This is recorded as an external infrastructure limitation, not a code or quality-gate pass, and no pinned-tool or workflow change was made during wrap-up.

## Workspace closeout — 2026-11-08

- The final run directory was copied to the primary workspace `D:\Repos\Github\spawn-join\.specify\delivery\common-foundation-20261107\` so the durable record survives independent of the isolated worktree.
- The primary workspace was moved off the merged `fix/llm-langchain-boundaries` branch to detached HEAD `origin/main` = `7dbc714` (the `main` branch itself is checked out in another worktree). It is clean except the two local delivery record directories.
- The stale untracked pre-implementation ADR-0011 duplicate in the primary workspace was archived as `runtime/archived-stale-adr-0011.md`; the tracked ADR on main contains the corrected status and remains Proposed.
- Remote `fix/llm-langchain-boundaries` and `feat/common-foundation` branches were deleted by the merges. The local worktree/branch remain for local evidence; removal is a manual optional cleanup:
  `git worktree remove C:/Users/YanZh/.local/share/opencode/worktree/86e56b/common-foundation` (requires force only because of the untracked run directory already copied here) and `git branch -D feat/common-foundation`.

PR body: `.specify/delivery/common-foundation-20261107/pull-request.md`; URL https://github.com/YanZhiwei/spawn-join/pull/47.

Current tracked T002 scope is 23 modified files plus new protocol tests/test_parsing.py; locks counted separately; no unrelated paths. The original workspace remains untouched with its existing retirement-evidence governance failure; this isolated worktree governance check passes.
