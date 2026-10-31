# Delivery evidence: LangChain-first LLM Runtime

- **feature_id**: `008-langchain-first-llm-runtime`
- **phase_id**: `s2-langchain-factory`
- **base_revision**: `60de8a01dc2c9159eaea9863cafac6f6a8fb2c74`
- **head_revision**: `working-tree`
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-31
- **result**: pass for S2 LangChain factory and package checks; real channel HTTP and provider calls are not executed

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
- `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` remains `Proposed`.
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
- `packages/core/llm-provider/src/spawn_join_llm_provider/{__init__,errors,options,channels}.py`
- `packages/core/llm-provider/src/spawn_join_llm_provider/py.typed`
- `packages/core/llm-provider/tests/{test_package,test_errors,test_options,test_channels,test_public_api}.py`
- removed `packages/core/llm-provider/src/spawn_join_llm_provider/abstractions/`
- `specs/008-langchain-first-llm-runtime/data-model.md`
- `specs/008-langchain-first-llm-runtime/contracts/llm-provider-public-api.md`

### Command receipts

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider` (S1 final) | 0 | Black/isort/Ruff/Pyright strict; 117 pytest tests; wheel/sdist build; isolated install/pip check/import |
| 2 | `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` (baseline, skeleton unchanged) | 0 | Adapter package passes before its S2 changes |
| 3 | `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors, 1 pre-existing warning |
| 4 | `git diff --check` | 0 | No whitespace errors |

### Limitations

- The adapter factory is not implemented in S1; `spawn-join-llm-provider-langchain` remains a skeleton.
- No real channel HTTP, provider request, pool or routing was implemented or executed.
- The docs/package quality run temporarily moved local ignored `specs/007-llm-protocol-abstraction`
  because it links ADR-0005 from unmerged PR #16; it was restored unchanged.
- `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` remains `Proposed`.

### Fingerprints

- `S1_CONTENT_FINGERPRINT`: `1091ee66dac4637f1627e9b9b8b906fd445fef636efc6b3d36fd274e60b5eee1`
  (SHA-256 over the S1 source/test/contract paths; updated after the final S1 fixes)

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
| 2 | `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider` | 0 | S2 prefix re-verified core package; 117 pytest tests; build/install |
| 3 | `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 79 files, 206 local links; specs/007 moved and restored |
| 4 | `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors, 1 pre-existing warning |
| 5 | `git diff --check` | 0 | No whitespace errors |

### Limitations

- No real channel HTTP, provider request, streaming call or tool execution was performed.
- `docs/decisions/llm-provider/0006-langchain-first-llm-runtime.md` remains `Proposed`.
- The docs check temporarily moved local ignored `specs/007-llm-protocol-abstraction`; it was
  restored unchanged.
- Stacked PR creation, push and merge are not executed.

### Fingerprints

- `S2_CONTENT_FINGERPRINT`: `ed7b8cf38d3c7399068ae2262edf8c8f409afc30608f78a3d167816dc3e6201b`
  (SHA-256 over the S2 source/test/docs/contract paths, updated after follow-up fixes)

### Verdicts

- `QUALITY_VERDICT`: see `task-verdicts.yml`
- `STANDARDS_VERDICT`: see `task-verdicts.yml`
- `REVIEW_VERDICT`: see `task-verdicts.yml`

## S3

Not executed yet. Do not read this section as a pass for S3.
