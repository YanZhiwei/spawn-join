# Evidence — Phase 01 Python Quality Gates

## Identity and scope

- **feature_id**: `002-python-quality-gates`
- **phase_id**: `phase-01-python-quality-gates`
- **task_id**: T001–T009 (manual local acceptance; no Ralph receipts)
- **base_revision**: `bd497d72e928f596e79cdbe5b1466eba4c75ec39`
- **head_revision**: `83628acb287a0c3cf74e92530d...`（PR #2 squash 合并提交）
- **reconfirmed_at**: 2026-10-27
- **working_directory**: `D:\Repos\Github\spawn-join`
- **recorded_at**: 2026-10-26T04:19:52Z (final documentation reconfirmed after this entry)
- **environment**: Windows; PowerShell 7.6.8; uv 0.7.13 and isolated uv 0.13.5;
  Node 22.17.0; original package Python 3.13.5; temporary verification Python 3.11.13
- **artifact_policy**: tracked Spec/Plan/Tasks and Harness; no configured Delivery/Ralph
- **result**: pass for the explicitly selected local checks below; remote CI confirmed at `475ab4c` (see Reconfirmation)

## Changed paths and attribution

This Feature owns root tool-only pyproject; four Distribution pyproject/uv.lock/test files;
Core `__init__.py` trailing blank-line removal; scripts/quality.ps1 and scripts/test-quality.ps1;
quality workflow; quality documentation; README/AGENTS/architecture/Harness navigation;
test-generation template/skill alignment; specs/002-python-quality-gates and this phase's records.

Pre-existing user changes are `specs/001-harness-foundation/spec.md` and the earlier
reconfirmation entry in `harness/build-log.md`; they are preserved, not attributed to this Feature.
Only a new phase entry will be appended to that shared log. No branch, commit, stage, push,
remote settings, runtime dependency or public API change is authorized/performed.

`git ls-files --modified --others --exclude-standard` reports 37 paths: 36 Feature-owned/shared
paths below, plus the preserved user-only `specs/001-harness-foundation/spec.md`.

```text
.agents/skills/speckit-tasks/SKILL.md
.github/workflows/quality.yml
.specify/templates/tasks-template.md
AGENTS.md
README.md
docs/architecture/package-boundaries.md
docs/architecture/repository-map.md
docs/development/quality-gates.md
harness/README.md
harness/build-log.md
harness/build/phase-01-python-quality-gates.md
harness/code_review/review-phase-01-python-quality-gates.md
harness/context/phase-01-python-quality-gates-context.md
harness/evidence/phase-01-python-quality-gates.md
packages/core/spawn-join-core/pyproject.toml
packages/core/spawn-join-core/uv.lock
packages/core/spawn-join-core/src/spawn_join_core/__init__.py
packages/core/spawn-join-core/tests/test_package.py
packages/core/llm-provider/pyproject.toml
packages/core/llm-provider/uv.lock
packages/core/llm-provider/tests/test_package.py
packages/infra/llm-provider-langchain/pyproject.toml
packages/infra/llm-provider-langchain/uv.lock
packages/infra/llm-provider-langchain/tests/test_package.py
packages/infra/spawn-join-observability/pyproject.toml
packages/infra/spawn-join-observability/uv.lock
packages/infra/spawn-join-observability/tests/test_package.py
pyproject.toml
scripts/quality.ps1
scripts/test-quality.ps1
specs/002-python-quality-gates/checklists/requirements.md
specs/002-python-quality-gates/plan.md
specs/002-python-quality-gates/quickstart.md
specs/002-python-quality-gates/research.md
specs/002-python-quality-gates/spec.md
specs/002-python-quality-gates/tasks.md
```

## Observed commands

All relative commands run at the working directory above; native checks are fail-fast.

| Command | Exit | Observed result |
|---|---|---|
| `git status --short --branch`; `git rev-parse HEAD` | 0 each | main @ base; two pre-existing edits |
| `codegraph status` | 0 | Baseline index up to date; navigation only |
| `uv lock --check --directory <package>` × four | 0 each | Baseline locks valid |
| `uv sync --locked --directory <package>` × four | 0 each | Baseline independent environments usable |
| `uv build <package> --out-dir <unique-temp>/<package>` × four | 0 each | Baseline 8 artifacts; existing README warnings |
| `uv lock --directory <package>` then `uv sync --locked --directory <package>` × four | 0 each | Dev tools added and independently locked |
| `uv run --locked --directory <package> pytest -c ../../../pyproject.toml tests -q` × four | 0 each | 7 + 4 + 6 + 3 = 20 package tests |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check format` | 0 after correction | Black/isort four packages |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check lint` | 0 | Ruff four packages |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check type` | 0 | Pyright four packages; zero errors/warnings |
| `pwsh -NoProfile -File scripts/test-quality.ps1` | 0 | Nine real-tool fixture scenarios; eight expected rejects |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check build` | 0 | Four target chains built, isolated installed, dependency/import checks passed |

Here `<package>` means each of `packages/core/spawn-join-core`, `packages/core/llm-provider`,
`packages/infra/llm-provider-langchain`, `packages/infra/spawn-join-observability`.
For reproducible final acceptance use the committed runner below instead of the one-off baseline loop.
Temporary output parent was `C:\Users\YanZh\AppData\Local\Temp\opencode`.
Build command expansion/output was captured locally in `spawn-join-quality-build.log` there;
that machine-local log is not a committed artifact or a substitute for the recorded outcomes.

## Failed attempts and corrections

- Initial Black gate returned 1 on Core `__init__.py`'s extra final blank line; removed only that line.
- Initial formatter preview also found one newly written test expression needing Black's line split;
  corrected the test formatting without changing the assertion.
- A one-off `uv --directory ... black` diagnostic used root-relative input after uv changed cwd and
  returned 2; reran with explicit root config and package-relative targets. The runner uses absolute paths.
- Global `python --version` failed because of a Windows alias; package interpreters work. An initial
  multi-command environment probe ended successfully on Node, so it was not treated as Python success.
- Expected fixture failures return gate exit 1, including pytest's underlying exit 5 for zero tests;
  fixture assertions verify diagnostic text, not merely any nonzero exit.

## Final acceptance

| Actual command / environment | Exit | Observed result |
|---|---|---|
| `pwsh -NoProfile -File scripts/quality.ps1` / uv 0.7.13, Windows Python 3.13.5 | 0 | Full four-package gate, including 20 tests and isolated install/import |
| Same full command with uv 0.13.5 prepended to process PATH | 0 | CI's pinned uv accepts locks and passes full gate; no global uv upgrade |
| Same full command in a temporary copy of current files, `UV_PYTHON=3.11` | 0 | Windows Python 3.11.13, all four packages and isolated installs pass; real environments untouched |
| `pwsh -NoProfile -File scripts/test-quality.ps1` / uv 0.7.13 and 0.13.5 | 0 each | Nine scenarios each; all eight intended rejects verified |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check test` after generated metadata cleanup | 0 | 20 tests still pass from installed distribution metadata |
| `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | 0 | Final 28 Markdown files and 59 local targets; diff check succeeds |
| `codegraph sync` | 0 | Up to date after watcher sync |
| `codegraph affected packages/core/spawn-join-core/src/spawn_join_core/__init__.py` | 0 | No affected tests inferred; did not rely on this to skip any package tests |
| PowerShell AST parse of both scripts | 0 | No syntax errors |
| `uv run --locked --directory packages/infra/llm-provider-langchain python C:/Users/YanZh/AppData/Local/Temp/opencode/validate_spawn_join_quality.py D:/Repos/Github/spawn-join` | 0 | Supplemental static check: tool-only root; unchanged four project metadata and pre-existing locked runtime versions/sources; 12 matrix combinations; pinned Actions; read-only permissions |
| Aggregate run block executed by supplemental check for all 16 success/failure/cancelled/skipped pairs | 0 for assertion script | Only success/success yields 0; every other pair yields 1 |
| Whitespace scan of all 37 modified/untracked paths | 0 | No trailing whitespace |

Reproduction: from root set `SPAWN_JOIN_TEMP_DIR` to an existing directory, then run the two committed
scripts above. Python selection can be set by `UV_PYTHON`; a clean temporary copy preserves the original
package environments when testing another interpreter. Current uv was obtained with
`uv tool run --from uv==0.13.5 python -c "import uv; print(uv.find_uv_bin())"`, then only its Scripts
directory was prepended to the verification process PATH. The one-off Python/YAML diagnostic is
machine-local, not an additional CI gate or a workflow-schema validator; regular reproduction uses the
committed runner and direct inspection of the workflow.

The temporary copy used `git ls-files --cached --others --exclude-standard`, copied only those files,
initialized a temporary local Git repository, and ran the unchanged runner with `UV_PYTHON=3.11`.
Its exact unique directory was deleted in finally. Supplemental local logs are
`spawn-join-quality-full.log`, `spawn-join-quality-uv0135.log` and `spawn-join-quality-python311.log`
under the approved temp parent. No log or binary was added to Git.

Cleanup checked exact four package paths: no source build/dist; removed only recognized generated
setuptools `.egg-info` files from the four known directories. Original package venvs remain, root
`.venv`/uv.lock/build/dist do not exist. The exact baseline output directory was also removed.
Final `git rev-parse HEAD` still matches base; `git status --short --branch` confirms main and only the
declared worktree paths, with no commit/stage/push. Scoped static Standards review is recorded in
[review](../code_review/review-phase-01-python-quality-gates.md).

This is working-tree evidence, not an immutable commit receipt. Do not reuse results after changing
their implementation, revision or scope without renewed confirmation.

## Limitations and blockers

- GitHub workflow execution, Linux and Python 3.14 checks are not-run in this local Windows session.
- Required status check/Ruleset is not configured remotely; no external write or push performed.
- No full dependency vulnerability scan, workflow-specific linter, release, or Spec Kit hook run.
- Delivery config, ADR root, Ralph receipts and full Delivery handoff are not enabled/claimed.
- Existing README and hardlink/copy warnings remain; global Python alias is unchanged.
- A new commit, changed paths or implementation change requires renewed evidence confirmation.

## Reconfirmation — 2026-10-27

After PR #1 merged, the original Feature gates were re-run at `475ab4c` to confirm later
governance/CI changes did not invalidate the recorded outcome. PR #2 is squash-merged as
`83628ac`; its branch commits are not main ancestors, so this record is anchored to the
squash commit.

- **HEAD**: `83628acb287a0c3cf74e92530d...`（PR #2 squash 合并提交）
- **Working directory**: `D:\Repos\Github\spawn-join`
- `pwsh -NoProfile -File scripts/quality.ps1`: exit 0; four packages (format/lint/type/test/build)
  plus docs and governance.
- `pwsh -NoProfile -File scripts/test-quality.ps1`: exit 0; 9 scenarios.
- `pwsh -NoProfile -File scripts/quality.ps1 -Check docs`: exit 0; 41 Markdown files / 105 targets.
- `pwsh -NoProfile -File scripts/check-governance.ps1`: 0 errors / 0 warnings.

The original verification was bound to `bd497d7` plus an uncommitted worktree (before the
quality-gate implementation was committed). This reconfirmation only re-verifies that the
implementation still passes; it does not rewrite the original commands, failed attempts or
environment limits. Windows Python 3.13.5 was executed locally; Linux and Python 3.14 remain
covered by remote CI.
