# spawn-join-llm-model-sync

[English](README.md) | [简体中文](README.zh-CN.md)

The manual model metadata synchronization tool for SpawnJoin.

It fetches a model catalog from an explicitly selected source, translates only the models referenced
by `model.yaml`, validates the result, and writes a deterministic `model-metadata.json` snapshot. It
never modifies `model.yaml`, never registers models automatically, and never runs on a schedule.

**Contents**

- [Status](#status)
- [Installation and daily operations](#users-installation-and-daily-operations)
  - [Failure protection and rollback](#failure-protection-and-rollback)
  - [Storage](#storage)
- [Architecture and extension](#maintainers-architecture-and-extension)
  - [Package boundaries](#package-boundaries)
  - [models.dev data flow](#modelsdev-data-flow)
  - [Adding a sync source](#adding-a-sync-source)
  - [Quality and maintenance](#quality-and-maintenance)
- [Maintenance and releases](#maintenance-and-releases)

## Status

Version `0.1.0`, early development; Python `>=3.11`. Runtime dependencies are
`spawn-join-llm-provider`, `platformdirs`, and `PyYAML`.

This package belongs to the SpawnJoin monorepo and is not published to PyPI. It is a maintenance
tool, not a runtime dependency of the LangChain adapter package. See
[ADR-0009](../../../docs/decisions/llm-provider/0009-model-metadata-and-sync.md) for the long-term
boundary.

## Users: installation and daily operations

```powershell
uv sync --locked --directory packages/infra/llm-model-sync
```

Declare shared models and source coordinates explicitly in `model.yaml`:

```yaml
schema_version: 2
default: fast
models:
  fast:
    protocol: chat_completions
    endpoint: https://api.openai.com/v1
    model: gpt-5
    api_key_env: OPENAI_API_KEY
    metadata_ref: openai/gpt-5
    metadata_source:
      models.dev:
        provider: openai
        model: gpt-5
```

Run from the directory containing `model.yaml` (replace `<repo>` with the repository path;
`--project` does not change the current directory):

```powershell
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sources
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --apply
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --check
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --output model-metadata.json
uv run --project <repo>/packages/infra/llm-model-sync spawn-join-model-sync sync --source models.dev --model-file model.yaml --cache-dir <path> --timeout 60
```

- Without `--apply` / `--check`, it only computes the difference and writes no snapshot; differences
  return `2`.
- `--apply` atomically replaces the snapshot; unchanged content is not rewritten.
- `--check` returns `2` on drift and writes no snapshot.
- `--apply` and `--check` are mutually exclusive.

Exit codes:

| Exit code | Meaning |
|---|---|
| `0` | success; no drift or applied successfully |
| `1` | invalid argument, configuration, or credential URL |
| `2` | drift detected (dry-run or `--check`), or snapshot missing |
| `3` | network, upstream structure, empty/shrunken response, or snapshot validation failure |

Runtime reads must pass the snapshot path explicitly; the library searches no user directory and
performs no network request:

```python
from spawn_join_llm_provider_langchain import ModelCatalog

catalog = ModelCatalog.from_file(
    "model.yaml",
    metadata_file="model-metadata.json",
)
for summary in catalog.models:
    print(summary.name, summary.metadata_ref, summary.metadata)
```

### Failure protection and rollback

- Empty responses, values below safety floors, all referenced models missing, or abnormal channel
  shrinkage block the write and leave the old snapshot unchanged.
- A single missing model or channel preserves the old entry and emits a warning.
- If cache/report/state writing fails after the snapshot was replaced, the command returns success
  and displays a `post-commit` warning.
- Rollback only requires restoring the previous `model-metadata.json`; no upstream refetch is
  needed.
- `model.yaml` is never modified by the sync command.

### Storage

- The snapshot defaults to the directory containing `model.yaml` and can be overridden with
  `--output`.
- Raw responses, state, and reports live in the platform user cache directory and can be overridden
  with `--cache-dir`.
- The runtime library reads none of these directories; applications pass `metadata_file`
  explicitly.

## Maintainers: architecture and extension

### Package boundaries

- `spawn-join-llm-provider`: framework-independent metadata types, snapshot parsing, and shared
  strict field reading.
- `spawn-join-llm-provider-langchain`: full `model.yaml` parsing and runtime catalog reading; a
  test/dev dependency only, not a CLI runtime dependency.
- `spawn-join-llm-model-sync`: network fetching, source registration, raw DTOs, metadata projection,
  snapshot generation, cache, and CLI.

The sync tool depends on `llm-provider`; the full model-file parser still
belongs to `llm-provider-langchain`, but the sync tool reads only the metadata projection and imports
no LangChain. Runtime packages must not depend on the sync tool.

### models.dev data flow

```text
catalog.json
  -> ModelsDevCatalog / ModelsDevProvider / ModelsDevModel       raw DTOs
  -> parse only requested refs / hosts
  -> ModelMetadata / ModelHostMetadata / ModelPricing unified types
  -> strict validation and write model-metadata.json
```

- Unknown upstream fields are ignored so new fields do not break synchronization.
- Tiered pricing supports both legacy `min_input_tokens` and the current
  `tier: {type: context, size: ...}` shape.
- Official models.dev, mirrors, and structurally identical sources can reuse the same adapter;
  different structures require a separate adapter.
- Source identity and URL are provided through `SourceInfo`, `SourceConfig.url` /
  `SyncContext.url`; the adapter stores no second URL, keeping the fetch address and snapshot
  provenance consistent.

### Adding a sync source

Implement `MetadataSource`, responsible only for `fetch` and `translate`:

```python
from spawn_join_llm_model_sync import MetadataSource, SourceInfo, SourceRegistry

class MySource:
    info = SourceInfo(
        id="my-source",
        display_name="My Source",
        homepage="https://example.com",
        license="MIT",
        default_url="https://example.com/catalog.json",
    )

    def fetch(self, context):
        ...

    def translate(self, payload, request):
        ...

registry = SourceRegistry.with_builtins()
registry.register(MySource())
```

Translation results must be unified types, not raw dictionaries:

- `SourceCatalog.models: Mapping[str, ModelMetadata]`
- `SourceCatalog.hosts: Mapping[provider, Mapping[model, ModelHostMetadata]]`
- `SourceCatalog.unreferenced_models` records ignored upstream model identifiers.

A new source should provide fixture-based translation tests, empty/malformed payload tests, and
failure-isolation tests, and update source descriptions and documentation; the generic runner,
snapshot schema, and runtime reading should not change for a new source.

### Quality and maintenance

```powershell
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-llm-model-sync
pwsh -NoProfile -File scripts/quality.ps1
pwsh -NoProfile -File scripts/test-quality.ps1
```

- Each Distribution uses an independent `.venv` and `uv.lock`; never create a root uv environment.
- When changing shared parsing rules, reuse `spawn_join_llm_provider.parsing.FieldReader` rather than
  duplicating field-reading code across adapters.
- Cache and reports are not committed; only a reviewed `model-metadata.json` is committed.
- ADR status is closed by independent review and `speckit.decision.finalize`; tool presence does not
  prove review completion.

See [LICENSE](LICENSE).

## Maintenance and releases

Source is in `src/spawn_join_llm_model_sync/`, adapters in its `sources/` directory, and
offline tests in `tests/`. The CLI is `spawn-join-model-sync`; use `--help` or `sources`
to inspect commands and registered sources. The public Python API is listed in
[`__init__.py`](src/spawn_join_llm_model_sync/__init__.py).

Owned by the SpawnJoin repository maintainers (author: Yan Zhiwei). Follow
[contributor rules](../../../AGENTS.md) and [quality prerequisites](../../../docs/development/quality-gates.md#prerequisites)
(PowerShell 7, uv 0.7.13+, Git, Node.js 22+). Report issues with source identity, exit code,
and a redacted model-file example. Versions are independent; no automated release or
package-specific changelog is configured. Releases require quality checks, both README
languages, compatibility notes, and separate authorization.
