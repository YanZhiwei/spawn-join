# Delivery evidence: Native reasoning parameter documentation

- **feature_id**: `lightweight-native-reasoning-docs`
- **phase_id**: `documentation`
- **lane**: Lightweight
- **base_revision**: `0f34357e1aebcb9ccc1ec2e0f067d001b1c26a81`
- **head_revision**: `0f34357e1aebcb9ccc1ec2e0f067d001b1c26a81` plus the documented working-tree changes
- **working_directory**: `C:\Users\YanZh\.local\share\opencode\worktree\86e56b\calm-nebula`
- **recorded_at**: 2026-11-01
- **status**: active
- **result**: pass for the local documentation diff, affected package quality, offline examples and independent review; not published

## Request, route and scope

Document the existing LangChain-native inference controls instead of extending
the project's protocol options. This is a documentation-only Lightweight change:
no Spec/Plan/Tasks, Python source, dependency, public API, architecture decision,
credential, permission or runtime data-flow change is required.

Changed paths:

- `packages/core/llm-provider/README.md`: distinguish the partial constructor
  option surface from LangChain's native per-invocation parameters; link to the
  adapter-owned examples.
- `packages/infra/llm-provider-langchain/README.md`: provide complete async setup,
  per-call reasoning effort, Anthropic thinking modes, model/version limitations
  and service-error ownership.
- `harness/build-log.md`: append the verification entry for this change.
- `.specify/delivery/lightweight-native-reasoning-docs/evidence.md`: this durable
  execution record.
- `.specify/delivery/lightweight-native-reasoning-docs/.gitignore`: keep receipts,
  review reports and the PR body local under the configured ephemeral policy.

The initial worktree was clean and detached at the base revision. Documentation
preparation did not commit, push or create a PR. On 2026-11-01 the user separately
authorized branch creation, committing, pushing and opening a PR for this exact
change. Publication uses `docs/native-reasoning-usage` against `main`; merge,
release and real Provider requests remain unauthorized. The record remains
`active` until the observed PR outcome is recorded; it is not a delivered release.

## Governing context and readiness

- ADR-0006 remains Accepted: protocol options describe constructor defaults;
  per-invocation overrides use LangChain native parameters. ADR-0001/0002 retain
  the distinction between local execution artifacts and durable documentation.
- OpenCode is the configured integration; extension registrations, command
  files, the Lightweight workflow, review/package-README templates and configured
  PR template were inspected. The PR template matches its static GitHub copy.
- PowerShell 7.6.9, uv 0.7.13, Node 22.17.0 and PSScriptAnalyzer 1.25.0 were
  found. This availability is not a quality pass. Hooks remain disabled.
- The legacy installation record under `006-delivery-release-install` is already
  marked superseded and points to `harness/evidence/delivery-release-installation.md`;
  it is not reused as evidence for this run or edited here. No full historical
  delivery/remote-state audit is claimed.
- CodeGraph reports an uninitialized index; current source/tests and the pinned
  SDK source were inspected directly. No index was installed or rebuilt.

## Verification

All commands run from the recorded working directory. Package checks used
PowerShell 7.6.9, uv 0.7.13, Node 22.17.0, package-local CPython 3.13.5 and the
unchanged package lock files. Build staging used the approved parent directory
`C:\Users\YanZh\AppData\Local\Temp\opencode`; package environments were synced
independently, not as a root workspace.

| Command | Exit | Observed result |
| --- | --- | --- |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider` | 0 | Final README snapshot: lock/sync, Black/isort/Ruff, Pyright, 129 pytest cases, wheel/sdist build and isolated install/import checks pass |
| `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` | 0 | Final README snapshot: lock/sync, Black/isort/Ruff, Pyright, 38 pytest cases, wheel/sdist build and isolated install/import checks pass |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | Local documentation targets/whitespace checked; final record-only changes are rechecked before handoff |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | 0 | 0 errors, 1 historical evidence-freshness warning; final record-only changes are rechecked before handoff |
| `py -3 -B -` (compile the Python fenced blocks in both READMEs) | 0 | 16 blocks compile, allowing top-level await in explicitly async fragments |
| `packages/infra/llm-provider-langchain/.venv/Scripts/python.exe -B C:/Users/YanZh/AppData/Local/Temp/opencode/native-reasoning-docs-0f34357-probe.py` | 0 | Execute the published full example under all three protocols and Anthropic adaptive/enabled/disabled fragments with synthetic HTTP responses; six scenarios pass |
| `git diff --check` | 0 | No whitespace errors; Git reports normal LF/CRLF conversion warnings |

The native-call probe verifies `reasoning_effort` / `reasoning.effort` /
`output_config.effort`, the per-protocol output-token limits and all three
Anthropic thinking payloads. It patches both `httpx` and `httpx2` async send,
blocks DNS/external sockets, and allows Windows asyncio's local wake-up socket.
This proves SDK request mapping, not a real model's acceptance or reasoning output.

### Check identity and review gate

- Package receipts capture the actual command, directory, start/end timestamps,
  exit status, temporary parent, wrapper hash and input manifests. The final
  conservative manifest covers the tracked packages, scripts, tool configuration
  and applicable policies; its pre/post hash is unchanged:
  `932acad1b04a83923ee685ecf1c73f5cf468341826dc63018b4a2d28484c88d7`.
- README SHA-256: core
  `d129823e93fabaaa5edf0574fbd2c688b9f6154f2b71cf20414a9b658ebb9b4c`;
  adapter `40577c78efcc8eb65ad20a6a909525123d65ae66173ed6b3fc13b5dd2ee9aad9`.
- Review content fingerprint:
  `3277e05893d26ac940bcb010702ef440fc7bbae8dc1ba8e10adcdb9f18417fec`.
  It hashes sorted `path<TAB>100644<TAB>SHA256(raw worktree bytes)<LF>` records
  for the two READMEs, build-log and new run ignore policy. No staged changes.
- Requirements/policy fingerprint:
  `71af48118fc2b77ec6c35ac346029c5c56154c51320d98736af2d380765c2c0a`;
  policy-only fingerprint:
  `eaf0d99271aceb53715ecc13797f6f9519fab2501e8c9dcc983ac4aa5ef24e8f`.
- Evidence/result finalization, ignored receipts/review reports and PR body are
  explicitly excluded as report bookkeeping, not as unreviewed product changes.
  Local documentation/governance checks still include the durable evidence.
- `QUALITY_VERDICT: pass`; `STANDARDS_VERDICT: pass`; ADR impact: none.
  Package README outcome: both `updated`. Independent fresh-context final review
  returned `REVIEW_VERDICT: pass` across requirements, code quality, architecture,
  correctness, security/compatibility and test effectiveness, with no partial or
  unreviewed required coverage. NRDOC-001 was independently verified `resolved`,
  not waived. The reviewer re-executed all six intercepted scenarios without
  writing receipts and independently checked the content/requirements identities.
  One repair pass of the configured maximum two is retained; repair is now no-op.

### Unsuccessful attempts and corrections

1. The first package-check wrapper used Windows PowerShell 5 with terminating
   stderr handling. A normal Git LF/CRLF warning aborted the wrapper (exit 1).
   The unchanged quality commands were re-run successfully from PowerShell 7;
   their original receipts are retained separately from the final runs.
2. Initial governance rejected a nonstandard evidence `result` string (exit 1).
   The metadata was changed to the supported `blocked` vocabulary and the check
   re-ran with 0 errors. No checker was weakened.
3. Initial probe interception covered `httpx` but the locked SDK uses `httpx2`;
   the reserved example domain failed DNS resolution (exit 1), before reaching
   a Provider. Both transports are now intercepted. A following guard also
   blocked Windows asyncio's local socketpair (exit 1); the corrected guard
   allows only local wake-up sockets and rejects external connections.
4. Executing the original full/disabled Anthropic examples exposed missing
   `max_tokens` (exit 1 before request dispatch). Explicit limits were added to
   the full and fragment examples. Independent review confirmed this as
   NRDOC-001. Syntax, six probe cases and both complete package quality commands
   were then re-run on the corrected README bytes; final independent re-review
   verified closure against those exact bytes rather than dropping the finding.

### Warnings and unexecuted checks

- Governance retains the pre-existing warning that
  `harness/evidence/delivery-v022-upgrade.md` is six commits behind HEAD with
  material changes. This historical record is not modified by the current scope.
- The core isolated-install check warns that its external runtime-requirements
  export is empty; the local Core wheel is installed explicitly and pip/import
  checks succeed. Git's LF/CRLF warnings do not indicate diff errors.
- Full four-package/static/gate-regression suites and remote CI are not run:
  no Python source, automation, dependency or shared tool-policy file changed.
  Both affected package profiles and the documentation/governance profiles are
  executed rather than treating old runs as current evidence.

## Limitations

No real Provider request, stream, tool execution or remote CI has been performed.
The docs qualify the examples by the locked SDK versions and actual model/service
support; package `>=1.0` dependency lower bounds are not presented as proof that
all historical SDK versions accept every example. No unrelated validation or
metadata issue is repaired as part of this documentation change.
