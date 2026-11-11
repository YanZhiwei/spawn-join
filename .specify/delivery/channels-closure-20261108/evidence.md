# Delivery Evidence — channels-closure-20261108

- feature_id: 015-llm-channel-closure
- phase_id: implementation-verification
- base_revision: 9f8cb1c78cc254450e2a7557eb88013bc7cdb302
- head_revision: 44a32f0b87bc6b460261000fb866a05954ce654b
- working_directory: D:\Repos\Github\spawn-join
- recorded_at: 2026-11-09T00:13:34+08:00
- result: pass

## Outcome

Implemented the library-level channel closure requested by the user:

`ChannelConfig -> ping/list_models -> ModelInfo -> ChatModelConfig.from_channel
-> create_chat_model -> native BaseChatModel`

The user explicitly removed the CLI from scope at the design gate. No routing,
pool, health selection, `channels.yaml`, hot reload, or Agent assembly change was
added.

## Commits

| Commit | Purpose |
|---|---|
| `685b468` | Approved planning packet and checkpoint baseline |
| `24a8ded` | Channel package, protocol additions, adapter bridge, docs/quality/CI |
| `78c9694` | Reject empty Anthropic cursor IDs and clarify bridge ownership docs |

`9b674c1` is the Proposed ADR-0013 planning baseline.

## Commands and results

| Working directory | Command | Exit | Result |
|---|---|---|---|
| repo root | `uv run --locked --project packages/core/llm-provider pytest packages/core/llm-provider/tests -q -p no:cacheprovider` | 0 | 187 passed |
| repo root | `uv run --locked --project packages/infra/llm-provider-langchain pytest packages/infra/llm-provider-langchain/tests -q -p no:cacheprovider` | 0 | 309 passed |
| repo root | `uv run --locked --project packages/infra/llm-channel pytest packages/infra/llm-channel/tests -q -p no:cacheprovider` | 0 | 99 passed, 2 skipped |
| repo root | `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider` | 0 | format, isort, Ruff, Pyright, 187 tests, build, isolated install |
| repo root | `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-channel` | 0 | format, isort, Ruff, Pyright, 99 passed/2 skipped, build, isolated install |
| repo root | `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` | 0 | format, isort, Ruff, Pyright, 309 tests, build, isolated install |
| repo root | `pwsh -NoProfile -File scripts/quality.ps1` | 0 | all seven packages, docs, governance, static, gate regressions passed |
| repo root | `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 147 files, 401 local targets checked |
| repo root | `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors, 1 historical warning (`delivery-v022-upgrade.md` stale) |
| repo root | `git diff --check` | 0 | no whitespace errors |

The full `scripts/quality.ps1` result was produced at implementation head
`78c9694` after the malformed-response and cursor fixes.

## Review evidence

Fresh read-only subagent review of `24a8ded`/`78c9694` verified:

- malformed 200 responses (`{}`, `data: null`, non-list data, non-JSON body)
  produce `INVALID_RESPONSE` / `ChannelResponseError`, not `OK` or raw SDK
  `TypeError`/`AttributeError`;
- 401/403/404/405/429/400/5xx, connect failure, and timeout map to the stable
  contract;
- no sentinel key appears in public messages;
- credential priority and explicit key validation are correct;
- adapter public exports and `create_chat_model` behavior remain unchanged.

The first review found a blocker (malformed 200 handling), a minor cursor bug,
and a docs ownership wording issue. All three were fixed before the final
quality run. A second fresh review reported `NO_BLOCKER`.

## Limitations and unexecuted checks

- Real Provider live tests were skipped because no live credentials are
  available. They are opt-in and are **not** reported as passed.
- No remote CI result is recorded in this local evidence; the PR CI run is
  monitored separately after publication.
- Independent runtime Review/Standards/Simplify receipts and Ralph per-task
  closure receipts were not recorded; the run remains in execution state.

## Residual risks

- Provider SDK behavior is validated with fake clients and real SDK
  `httpx2.MockTransport`; real endpoint behavior still needs opt-in live
  validation.
- ADR-0013 remains `Proposed` until the reviewed repository HEAD matches it.
- The implementation was committed as a single feature commit rather than one
  Ralph task commit; task-closure receipts are incomplete.
