# Delivery evidence: LangChain-first LLM Runtime

- **feature_id**: `008-langchain-first-llm-runtime`
- **phase_id**: `s3-final-verification`
- **base_revision**: `353af49cf9db6014b7af0437a3f9dc0dd651437c` (feature base HEAD, `origin/main` at kickoff)
- **head_revision**: `468ee7f49de87921fd04b0f7256d306018d12490` (PR #18 squash-merge commit)
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-31
- **result**: pass for the full repository quality gate, gate regressions, quickstart construction, and final independent review; PR #18 squash-merged as `468ee7f` after all remote checks passed

**Feature**: `008-langchain-first-llm-runtime`

**Branch**: `ralph/008-langchain-first-llm-runtime`

**Base HEAD**: `353af49cf9db6014b7af0437a3f9dc0dd651437c` (`origin/main`)

**Evidence updated**: 2026-10-31

**Working directory**: `D:\Repos\Github\spawn-join`

## S0 — Default Slice delivery policy (T001–T002)

**S0 base HEAD**: `353af49cf9db6014b7af0437a3f9dc0dd651437c`
**S0 commit**: `a524aaf9450dc2ca5862055bfff38f4d5de2841d`

### Scope

- `.specify/extensions/delivery/delivery-config.yml`
- `docs/decisions/engineering/0007-default-slice-delivery.md` (new)
- `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` (new planning artifact)
- `.specify/delivery/008-langchain-first-llm-runtime/exploration.md` (new)
- `.specify/delivery/008-langchain-first-llm-runtime/decision-context.md` (new)
- `.specify/delivery/008-langchain-first-llm-runtime/slices.md` (new)
- `.specify/delivery/008-langchain-first-llm-runtime/evidence.md` (new)
- `.specify/delivery/008-langchain-first-llm-runtime/task-verdicts.yml` (new)
- `.specify/delivery/008-langchain-first-llm-runtime/receipts/T001.md` (new)
- `.specify/delivery/008-langchain-first-llm-runtime/receipts/T002.md` (new)
- `docs/decisions/README.md`
- `AGENTS.md`
- `docs/development/spec-kit-delivery.md`
- `docs/decisions/engineering/0004-release-managed-delivery-installation.md`

### Command receipts

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `packages/infra/llm-provider-langchain/.venv/Scripts/python.exe -c "import yaml; ... assert pr_slicing == 'auto' ..."` | 0 | `yaml_parse=ok pr_slicing=auto stack_provider=manual use_queue=false` |
| 2 | `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | `Documentation: 79 files, 206 local targets checked.` |
| 3 | `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | `Governance checks: 0 error(s), 1 warning(s).` |
| 4 | `git diff --check` | 0 | No whitespace errors |
| 5 | `git status --short --branch` | 0 | Branch `ralph/008-langchain-first-llm-runtime`; S0 paths modified/untracked as listed above |

### Limitations and workarounds

- The docs check scans local ignored `specs/`. The local `specs/007-llm-protocol-abstraction/plan.md`
  links to `docs/decisions/llm-provider/0005-protocol-native-llm-contracts.md`, which exists only on
  the unmerged PR #16 branch, not on `main`. For command 2, `specs/007-llm-protocol-abstraction` was
  temporarily moved to `C:\Users\YanZh\AppData\Local\Temp\opencode\007-llm-protocol-abstraction.backup`
  and restored unchanged immediately after the check (`restored=True`). This is a pre-existing local
  artifact issue, not an S0 outgoing-diff failure.
- The governance warning `harness/evidence/delivery-v022-upgrade.md: head_revision is not an
  ancestor of HEAD` is pre-existing and unrelated to S0.
- No remote CI, PR, push, merge, or stacked PR was executed. S0 is a local change set.
- `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` was `Proposed` at this
  boundary; accepted at final HEAD `d6cdc37`.
- `docs/decisions/engineering/0007-default-slice-delivery.md` is `Accepted` based on the user's
  2026-10-31 instruction and slice approval; its commands are the receipts above.

### Fingerprints

- `POLICY_CONTENT_FINGERPRINT`: `7d8339f5f4e3ab40203f331ee0ea20c218763d0cd0f6acd65505483175ebd818`
  (SHA-256 over sorted `path=SHA256` lines for the 10 policy/document paths under review)
- `POLICY_FINGERPRINT`: `70b2276f095ed81276dc32dbf9f00655be2a798358434327d6ca7726337627a0`
  (SHA-256 over sorted policy-source hashes)
- Bookkeeping exclusion: `evidence.md`, `task-verdicts.yml` and `receipts/{T001,T002}.md` record
  the verdict itself and are excluded from `POLICY_CONTENT_FINGERPRINT`; they are listed in Scope
  and committed with S0 but are not policy inputs.

### Verdicts

- `QUALITY_VERDICT`: see `task-verdicts.yml`
- `STANDARDS_VERDICT`: see `task-verdicts.yml`
- `REVIEW_VERDICT`: see `task-verdicts.yml`

## S1 — Core contract (T003–T010)

**S1 base HEAD**: `a524aaf9450dc2ca5862055bfff38f4d5de2841d`
**Working tree**: S1 implementation and tests; final gate below

### T003 pre-implementation baseline

- `git status --short --branch`: `## ralph/008-langchain-first-llm-runtime...origin/main [ahead 1]`
- `git rev-parse HEAD`: `a524aaf9450dc2ca5862055bfff38f4d5de2841d`
- `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider` at the baseline:
  exit 0 (skeleton package; pre-S1 test set)
- `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` at the
  baseline: exit 0 (skeleton package; adapter unchanged)
- Baseline tree identity: core `9ad42cbe5ea124fc3af9b3c09cb5a5c6e896378d`, adapter
  `21f75bf84b71be2833363b8b0df22e742dc35f1c`

### S1 final gate

### Scope

- `packages/core/llm-provider/pyproject.toml`
- `packages/core/llm-provider/README.md`
- `packages/core/llm-provider/src/spawn_join_llm_provider/{__init__,errors,options,endpoints,channels}.py`
- `packages/core/llm-provider/src/spawn_join_llm_provider/py.typed`
- `packages/core/llm-provider/tests/{test_package,test_errors,test_options,test_channels,test_public_api}.py`
- removed `packages/core/llm-provider/src/spawn_join_llm_provider/abstractions/`
- `specs/008-langchain-first-llm-runtime/data-model.md`
- `specs/008-langchain-first-llm-runtime/contracts/llm-provider-public-api.md`

### Command receipts

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider` (S1 final) | 0 | Black/isort/Ruff/Pyright strict; 129 pytest tests; wheel/sdist build; isolated install/pip check/import |
| 2 | `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` (baseline, skeleton unchanged) | 0 | Adapter package passes before its S2 changes |
| 3 | `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors, 1 pre-existing warning |
| 4 | `git diff --check` | 0 | No whitespace errors |

### Limitations

- The adapter factory is not implemented in S1; `spawn-join-llm-provider-langchain` remains a skeleton.
- No real channel HTTP, provider request, pool or routing was implemented or executed.
- The docs/package quality run temporarily moved local ignored `specs/007-llm-protocol-abstraction`
  because it links ADR-0005 from unmerged PR #16; it was restored unchanged.
- `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` was `Proposed` at this
  boundary; accepted at final HEAD `d6cdc37`.

### Fingerprints

- `S1_CONTENT_FINGERPRINT`: `0ab984b576728fc5987d62e0418b3c2dea1f9c90eb91b11c057ca12aa17bf343`
  (SHA-256 over the S1 source/test/contract paths; updated after final review hardening)

### Verdicts

- `QUALITY_VERDICT`: see `task-verdicts.yml`
- `STANDARDS_VERDICT`: see `task-verdicts.yml`
- `REVIEW_VERDICT`: see `task-verdicts.yml`

## S2 — LangChain model factory (T011–T017)

**S2 base HEAD**: `60de8a01dc2c9159eaea9863cafac6f6a8fb2c74`
**Working tree**: S2 implementation and tests; final gate below

### Scope

- `packages/infra/llm-provider-langchain/pyproject.toml`
- `packages/infra/llm-provider-langchain/README.md`
- `packages/infra/llm-provider-langchain/uv.lock`
- `packages/infra/llm-provider-langchain/src/spawn_join_llm_provider_langchain/{__init__,config,factory}.py`
- `packages/infra/llm-provider-langchain/src/spawn_join_llm_provider_langchain/py.typed`
- `packages/infra/llm-provider-langchain/tests/{test_package,test_validation,test_factory,test_public_api}.py`
- removed `packages/infra/llm-provider-langchain/src/spawn_join_llm_provider_langchain/providers/`
- `docs/architecture/package-boundaries.md`
- `AGENTS.md`
- `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md`
- `specs/008-langchain-first-llm-runtime/data-model.md`
- `specs/008-langchain-first-llm-runtime/contracts/langchain-adapter-public-api.md`

### Command receipts

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` | 0 | Black/isort/Ruff/Pyright strict; 38 pytest tests; wheel/sdist build; isolated install/pip check/import |
| 2 | `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider` | 0 | S2 prefix re-verified core package; 117 tests at the S2 boundary; final core 129 after B+A decoupling |
| 3 | `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 79 files, 206 local links; specs/007 moved and restored |
| 4 | `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors, 1 pre-existing warning |
| 5 | `git diff --check` | 0 | No whitespace errors |

### Limitations

- No real channel HTTP, provider request, streaming call or tool execution was performed.
- `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` was `Proposed` at this
  boundary; accepted at final HEAD `d6cdc37`.
- The docs check temporarily moved local ignored `specs/007-llm-protocol-abstraction`; it was
  restored unchanged.
- Stacked PR creation, push and merge are not executed.

### Fingerprints

- `S2_CONTENT_FINGERPRINT`: `2d8907d639391b4796943dbefc6ea5fd9607789a7689e02844cde80a3a3296ca`
  (SHA-256 over the S2 source/test/docs/contract paths, updated after final review hardening)

### Verdicts

- `QUALITY_VERDICT`: see `task-verdicts.yml`
- `STANDARDS_VERDICT`: see `task-verdicts.yml`
- `REVIEW_VERDICT`: see `task-verdicts.yml`

## S3 — Final verification and evidence (T018–T020)

**S3 base HEAD**: `4598eb5108b33f3b55af251ee78af405f2ad86bd`
**Review-fix HEAD**: `3088ce83cd8a5404a088fc10287709ca7dcb3a5b`
**Working tree**: final evidence/ADR bookkeeping only

### Scope

- `.specify/delivery/008-langchain-first-llm-runtime/evidence.md`
- `.specify/delivery/008-langchain-first-llm-runtime/task-verdicts.yml`
- `.specify/delivery/008-langchain-first-llm-runtime/receipts/T018.md`
- `.specify/delivery/008-langchain-first-llm-runtime/receipts/T019.md`
- `.specify/delivery/008-langchain-first-llm-runtime/receipts/T020.md`
- `specs/008-langchain-first-llm-runtime/quickstart.md` only if a command or expectation is stale

### Command receipts

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `pwsh -NoProfile -File scripts/quality.ps1` | 0 | Full repository gate: four packages, docs, governance, static, build/isolated install |
| 2 | `pwsh -NoProfile -File scripts/test-governance.ps1` | 0 | 23 governance regression scenarios passed |
| 3 | `pwsh -NoProfile -File scripts/test-static.ps1` | 0 | 3 static regression scenarios passed |
| 4 | `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | 9 gate regression scenarios passed; no root project artifacts |
| 5 | quickstart public-export commands | 0 | core `__all__` has 21 symbols; adapter `__all__` is `['ChatModelConfig', 'create_chat_model']` |
| 6 | quickstart three-model construction | 0 | `ChatOpenAI False`, `ChatOpenAI True`, `ChatAnthropic`; all `BaseChatModel` checks true; sentinel key masked |
| 7 | `git diff --check` / `git status --short --branch --untracked-files=all` | 0 | No whitespace errors; final S3 evidence/ADR bookkeeping commit contains only delivery records and ADR status |
| 8 | build artifact scan | 0 | No `build/` or `dist/`; four ignored `src/*.egg-info` editable metadata directories were present and are cleaned before handoff |

### Limitations

- The full `scripts/quality.ps1` run required temporarily moving local ignored
  `specs/007-llm-protocol-abstraction` because it links ADR-0005 from unmerged PR #16; it was
  restored unchanged.
- During S3 (before PR #18), no remote CI, push, PR creation, merge or release action was
  performed. PR #18 and its squash merge happened afterwards and are recorded in
  "Post-merge closure".
- No real channel HTTP, provider request or streaming call was executed.
- `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` was accepted at the final
  reviewed HEAD `3088ce8`; implementation and quality gates passed.
- The quickstart `ainvoke`/`astream` examples are intentionally commented because this verification
  is offline; message and streaming behavior remains LangChain-native and was not re-tested here.
- The four `src/*.egg-info` directories are ignored editable-install metadata, not tracked build
  outputs; they are removed before handoff but may be recreated by a later `uv sync`.
- Final independent review passed at `3088ce8` with no blockers; the bookkeeping commit that
  follows changes only delivery records, ADR wording and contract prose.

### Final review fixes

- R1: `stop`/`stop_sequences` now reject non-tuple and non-string elements; `thinking` rejects
  mappings and arbitrary objects in `AnthropicMessagesOptions`; factory `_thinking_payload()` raises
  on unknown values. Regression tests added.
- R2: ADR-0006 and evidence now record core 129 tests and adapter 38 tests.
- R3: root `README.md` and `docs/development/quality-gates.md` no longer claim skeleton-only state
  or a fixed 20-test suite.
- R4: `ChannelConfig.protocol` is validated as `ProtocolKind` at construction; tests cover string,
  int and None.
- B+A decoupling: `ChannelConfig` and `ChatModelConfig` now inherit shared flat
  `EndpointConfig`; `ChatModelConfig` no longer depends on `ChannelConfig`, while
  protocol/endpoint/timeout validation remains single-sourced.
- R6: slice counts/status and T003 review note reconciled.
- R8: ADR-0007 no longer claims a standalone slice CLI receipt that was not captured.
- Verification after fixes: core 129 tests, adapter 38 tests; both package gates, full
  `scripts/quality.ps1`, governance/static/quality regressions, quickstart construction, and
  `git diff --check` pass.

### Fingerprints

- `FINAL_CODE_CONTENT_FINGERPRINT`: `769a3b858dca10c0fb470a7856909b125f2fa154974df3f85bf662f47acd1f0e`
  (SHA-256 over the final tracked code/docs/spec paths; delivery bookkeeping files excluded)
- Scope note: this fingerprint binds the reviewed implementation head `3088ce8`. Commits after
  it (`c6e0df1`, `e451315`) changed only the two package READMEs, contract prose and delivery
  records, so the hash does not describe the merged tree. It is retained because
  `task-verdicts.yml` T018–T020 cite it.

### Verdicts

- `QUALITY_VERDICT`: see `task-verdicts.yml`
- `STANDARDS_VERDICT`: see `task-verdicts.yml`
- `REVIEW_VERDICT`: see `task-verdicts.yml`

## Post-merge closure

- PR #18 was squash-merged as `468ee7f49de87921fd04b0f7256d306018d12490` on 2026-10-31 after
  every configured remote check passed. `main` advanced linearly from `353af49` to `468ee7f`.
- The merged tree equals the final branch head `e451315c029469ff088c27231500698d4b4b6aef`
  (tree `89801db358068c2ffb4ab786021e1aa2ff2f84d6`), so the squash did not drop or rewrite
  content. The reviewed implementation head was `3088ce8`; later commits changed only delivery
  records, contract prose and the two package READMEs.
- `pull-request.md` remains the pre-merge PR body used for handoff; this section is the
  post-merge source of truth.
- The feature branch `ralph/008-langchain-first-llm-runtime` was deleted locally and on
  `origin` after merge, consistent with `merge_policy.delete_branch: true`.
- Re-anchoring: `base_revision` used to point at the S3 base HEAD `4598eb5`, which became
  unreachable from any ref after the merged branch was deleted. The field now points at the
  feature base `353af49`; S3 scope and results are unchanged. Branch-only SHAs in this record
  (`4598eb5`, `3088ce8`, `e451315`) are historical references and are not resolvable in a
  fresh clone; the verifiable anchors are `353af49` and `468ee7f`.
