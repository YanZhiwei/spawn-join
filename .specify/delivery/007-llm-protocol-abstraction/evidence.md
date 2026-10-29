# Evidence — LLM protocol abstraction implementation

## Identity and scope

- **feature_id**: `007-llm-protocol-abstraction`
- **phase_id**: `llm-protocol-abstraction`
- **base_revision**: `3fe0cf0fe2e70b19ef65e73570b0d20e3e5311db`
- **head_revision**: `aa7292f3c6f0b8f4b0c5733a75d5f1b0309dd1d8`
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-29
- **result**: pass for scoped package quality and repository documentation/governance/static checks; user code review and real-service validation remain pending

Route: **Feature**. The public contracts, three protocol providers, factory, validation, mapping,
fake-model tests, READMEs and ADR are implemented. The branch is a code-review candidate; no
merge, publication or release is claimed.

## Changed paths and ownership

- `packages/core/llm-provider/src/spawn_join_llm_provider/**`: public messages, requests,
  responses, protocol-native options, capabilities, channel contracts, errors, `LLMProvider`.
- `packages/infra/llm-provider-langchain/src/spawn_join_llm_provider_langchain/**`: configuration,
  credential resolution, mapping, validation, base flow, three protocol providers, factory.
- `packages/infra/llm-provider-langchain/tests/**`: offline fake-model and contract tests.
- `packages/core/llm-provider/README.md`, `packages/infra/llm-provider-langchain/README.md`,
  `docs/architecture/package-boundaries.md`, `docs/decisions/llm-provider/0005-*.md`,
  `harness/build-log.md`, `.specify/delivery/007-llm-protocol-abstraction/**`.

## Actual checks

Commands ran from the working directory above.

| Command/check | Exit | Observed result |
|---|---:|---|
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider` | 0 | 61 tests; Pyright strict 0 errors; build/isolated install passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` | 0 | 56 tests; Pyright strict 0 errors; build/isolated install passed |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check static` | 0 | 0 failing checks |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | 75 files / 192 local targets (before final docs commit) |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors / 0 warnings (before final evidence commit) |
| `git diff --check` | 0 | no whitespace errors; LF/CRLF notices only |

## Compatibility and limitations

- No real OpenAI/Anthropic/DeepSeek/Azure request was executed; default tests use LangChain fake
  models and require no credentials or external network.
- Python 3.11 and 3.14 were not executed locally; the package venv is CPython 3.13.5. CI matrix
  remains the cross-version evidence source.
- Six protocol mapping/validation functions retain `# noqa: C901` to keep linear protocol dispatch;
  this is a review follow-up, not a claimed complexity pass.
- Azure-specific authentication/deployment and real channel `ping()`/`list_models()` HTTP are not
  implemented.
- Independent adapter code review was not performed in this session; the branch is intentionally
  opened as a PR for maintainer review.
- The ADR remains `Proposed`; it must not be promoted to `Accepted` until reviewed HEAD and
  implementation evidence are confirmed.
