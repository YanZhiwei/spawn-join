# Delivery evidence: 009-model-file-config

- **feature_id**: `009-model-file-config`
- **phase_id**: `final-verification`
- **branch**: `ralph/009-model-file-config`
- **base_revision**: `392aa909bcfe57f47d84d3d5e782ffd5fed4ae1f` (`main` at kickoff)
- **branch_base**: `9dcc51a632fba7be05f5ef72df11133789ce050c` (planning artifacts commit)
- **head_revision**: `50cf425d91bcd4bac8c2ee23df919c25dfc17f84` (code HEAD; evidence commit follows)
- **working_directory**: `C:\Users\YanZh\.local\share\opencode\worktree\86e56b\witty-island`
- **recorded_at**: 2026-11-01
- **status**: active
- **result**: pass for the full local quality gate, target package quality, docs, governance, quickstart, and final independent review; PR CI and user Code Review pending

## Commits

| Task | Commit | Summary |
| --- | --- | --- |
| planning | `9dcc51a` | exploration, decision context, slices, ADR-0008 |
| T001 | `6a42876` | add PyYAML/python-dotenv and refresh lock |
| T002 | `6a5bbe8` | add model file fixtures |
| T003 | `9678cce` | YAML document boundary, duplicate/recursive alias checks |
| T004 | `7b88523` | load catalog and create models |
| T005 | `925665c` | protocol options and thinking |
| T006 | `f50e5e2` | model summaries and display names |
| T007 | `0a0cf99` | `.env` support and key precedence |
| T008 | `1c805fa` | adapter README |
| T009 | `d711a7b` | core README, package boundaries, `.gitignore` |
| T010 | `04369c9` | final verification record |
| review fixes | `aa96a57` | extra failure-path tests, contract/ADR consistency, slice deviations |
| review refactor | `0711cf1` | simplify repeated parsing helpers; keep strict boundary |
| readability refactor | `02fe638` | split long parsers into named steps; rename `_CatalogEntry`; section navigation |
| OOP constructor | `0635d25` | add `ModelCatalog.from_file`; keep `load_model_catalog` wrapper |
| file split | `7199c6b` | thin facade + focused private modules |
| package move | `fd58558` | move implementation into `model_file/` package |
| default path | `50cf425` | default to cwd `model.yaml`; keep `.env` explicit |

## Verification

| Check | Command | Result |
| --- | --- | --- |
| Full repository quality | `pwsh -NoProfile -File scripts/quality.ps1` | exit 0（core 129, adapter 105 at that snapshot, observability 7; builds/isolated installs pass） |
| Target package quality (after review fixes) | `pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-provider-langchain` | exit 0；110 tests passed；Pyright strict 0 errors；Black/isort/Ruff/build/install pass |
| Targeted tests | `pytest tests/test_model_file.py tests/test_public_api.py -q` | 75 passed |
| Docs | `pwsh -NoProfile -File scripts/quality.ps1 -Check docs` | exit 0；55 files，191 local targets |
| Governance | `pwsh -NoProfile -File scripts/quality.ps1 -Check governance` | exit 0；0 errors，1 pre-existing warning（`harness/evidence/delivery-v022-upgrade.md` 落后 HEAD） |
| Quickstart | temporary script loading `tests/fixtures/model.yaml` and creating both protocols | exit 0；`QUICKSTART_OK` |
| Diff hygiene | `git diff --check` | exit 0 |
| Final independent review | fresh-context subagent over `main...HEAD` | `FINAL_REVIEW_VERDICT: pass`；findings addressed or recorded |

## Scope and deviations

- Implemented: schema v1 `model.yaml`, strict parsing, three protocol options, `thinking`, display names, 5-name public API, explicit `.env` with process-env precedence, READMEs, ADR-0008 (Proposed), package boundary note.
- **Delivery deviation**: the approved slice plan describes 5 stacked PRs; this handoff uses **one feature PR** for user review. Stacked delivery is not claimed; merge method is pending user review.
- **Slice budget exception**: S2 (`9678cce..925665c`) added 1,031 lines (493 source), above `slice_warn_lines: 400`; recorded in `slices.md`.
- **ADR status**: ADR-0008 remains `Proposed`; ADR-0006 carries a dated note that its adapter public surface is extended. Acceptance follows the user's review.
- Out of scope: channel config, multi-file merge, auto-discovery, hot reload, interpolation, provider routing/pool, real Provider requests.

## Review follow-up: simpler deserialization?

Review feedback suggested replacing the manual parser with YAML → entity
serialization/deserialization. A Pydantic `TypeAdapter` spike on the existing
dataclasses showed regressions:

- `timeout_seconds: true` and `max_retries: true` were silently coerced to
  `1.0` / `1` (violates strict type checks);
- unknown keys were ignored (violates unknown-field rejection);
- `ValidationError` text echoed input values (secret-leak risk);
- a full Pydantic schema would duplicate `ChatModelConfig` / `ProtocolOptions`,
  violating FR-017 and ADR-0008.

The accepted behavior-preserving change removes six `_optional_*` helpers and
the separate string-key helper, replacing them with one generic `_optional`
and string-key-enforcing `_as_mapping`; protocol field sets are constants.
Public API, schema, error messages and 110 tests are unchanged.

## Review follow-up: readability

Review feedback also called out readability. The parser was reorganised into
named steps without changing the public contract:

- `load_model_catalog` → `_parse_root` / `_parse_models` /
  `_resolve_default_name` / `_load_env_snapshot`;
- `_parse_entry` → `_parse_model_config` / `_parse_display_name` /
  `_parse_api_key_env` / `_parse_entry_options`;
- `_parse_options` → one small function per protocol;
- `_ModelEntry` renamed to `_CatalogEntry`, with YAML/schema/catalog/env
  section markers for navigation.

The file is slightly longer (604 → 676 lines) because of docstrings and split
function boundaries, but each function now has one named responsibility.
Public API, schema, error messages and 110 tests are unchanged.

## Review follow-up: OOP boundary

Constitution II reserves objects for state, invariants and lifecycle, and allows
stateless transformations to remain functions. The runtime already follows that:
`ModelCatalog` owns entries/default/env snapshot and `create_chat_model`;
`ModelSummary` and `_CatalogEntry` are frozen value objects. Parsing stays
functional because it is stateless validation.

To make construction available on the object itself, `ModelCatalog.from_file`
was added as the OOP entry point; `load_model_catalog` remains as the equivalent
function wrapper for the existing public contract.

## Review follow-up: file split

The public module is now a thin facade; implementation is split by
responsibility:

| Module | Lines | Responsibility |
| --- | ---: | --- |
| `model_file/__init__.py` | 18 | public `load_model_catalog` and re-exports |
| `model_file/_yaml.py` | 85 | YAML boundary, duplicate keys, recursive aliases |
| `model_file/_schema.py` | 452 | document/entry/options schema parsing |
| `model_file/_catalog.py` | 130 | `ModelCatalog` runtime and key resolution |
| `model_file/_env.py` | 35 | explicit `.env` reading |

`from spawn_join_llm_provider_langchain.model_file import ...` and
`ModelCatalog.from_file` remain unchanged; 111 tests pass.

## Review follow-up: default model file

`ModelCatalog.from_file()` and `load_model_catalog()` now default `path` to the
current working directory's `model.yaml`; an explicit path still overrides it.
`env_file` remains `None` by default: automatically reading `.env` would change
FR-018/ADR-0008's explicit credential boundary. A regression test changes into a
temporary directory and loads the default file.

## Limitations and residual risks

- Remote CI is the first check on the actual GitHub runner; local full quality passed.
- No real Provider request was executed; model construction is offline by design.
- `reportUnusedFunction`/PyYAML stub/white-box test suppressions are narrow and documented in the code/tests.
- The pre-existing governance warning is unrelated to this feature and was not silently rewritten.

## Next

Push `ralph/009-model-file-config`, open the PR with `pull-request.md`, monitor CI, fix failures, and wait for user Code Review. Do not merge without separate authorization.
