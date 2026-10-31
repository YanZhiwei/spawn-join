# Delivery evidence: LangChain-first LLM Runtime

- **feature_id**: `008-langchain-first-llm-runtime`
- **phase_id**: `s0-default-slice-delivery`
- **base_revision**: `353af49cf9db6014b7af0437a3f9dc0dd651437c`
- **head_revision**: `working-tree` (update to the S0 commit SHA after commit)
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-31
- **result**: pass for S0 policy/docs/governance checks; runtime slices are not executed and no remote action was taken

**Feature**: `008-langchain-first-llm-runtime`

**Branch**: `ralph/008-langchain-first-llm-runtime`

**Base HEAD**: `353af49cf9db6014b7af0437a3f9dc0dd651437c` (`origin/main`)

**Evidence updated**: 2026-10-31

**Working directory**: `D:\Repos\Github\spawn-join`

## S0 — Default Slice delivery policy (T001–T002)

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

## S1–S3

Not executed yet. Evidence will be appended at each slice boundary. Do not read this section as a
pass for S1–S3.
