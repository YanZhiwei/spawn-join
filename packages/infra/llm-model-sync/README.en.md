# spawn-join-llm-model-sync

[简体中文](README.md) | [English](README.en.md)

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
`spawn-join-llm-provider`, `spawn-join-common`, `platformdirs`, and `PyYAML`.

This package belongs to the SpawnJoin monorepo and is not published to PyPI. It is a maintenance
tool, not a runtime dependency of the LangChain adapter package. See
[ADR-0009](../../../docs/decisions/llm-provider/0009-model-metadata-and-sync.md) for the long-term
boundary.

## Users: installation and daily operations

```powershell
uv sync --locked --directory packages/infra/llm-model-sync
```

First verify the CLI from the repository root without network access:

```powershell
uv run --locked --directory packages/infra/llm-model-sync spawn-join-model-sync --help
uv run --locked --directory packages/infra/llm-model-sync spawn-join-model-sync sources
```

Both exit successfully (`0`); `sources` includes the built-in `models.dev`. The `sync` commands
below contact the selected metadata source. The built-in public source needs no `OPENAI_API_KEY`;
that variable name in the model file is for the inference application.

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

After `--apply`, save this as `read_snapshot.py` beside `model.yaml` and run there:
`uv run --locked --project <repo>/packages/infra/llm-model-sync python read_snapshot.py`.
It uses the sync package's existing protocol dependency: no additional LangChain installation,
inference credentials or network access. It prints each snapshot model's key, display name and
context size (`None` when unknown):

```python
from pathlib import Path

from spawn_join_llm_provider import decode_metadata_document

document = decode_metadata_document(
    Path("model-metadata.json").read_text(encoding="utf-8")
)
for key, metadata in document.models.items():
    print(key, metadata.name, metadata.limits.context)
```

To merge metadata with inference configuration, use `ModelCatalog.from_file(..., metadata_file=...)`
in the [LangChain adapter environment](../llm-provider-langchain/README.en.md#model-metadata-snapshot).
The application owns that environment and its credential configuration.

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

- `spawn-join-llm-provider`: framework-independent metadata types and snapshot parsing.
- `spawn-join-common`: shared strict field reading; the sync tool injects its own error type.
- `spawn-join-llm-provider-langchain`: full `model.yaml` parsing and runtime catalog reading; a
  test/dev dependency only, not a CLI runtime dependency.
- `spawn-join-llm-model-sync`: network fetching, source registration, raw DTOs, metadata projection,
  snapshot generation, cache, and CLI.

The sync tool depends on `llm-provider` and `common`; the full model-file parser still
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

Implement `MetadataSource`, responsible only for `fetch` and `translate`. Save this complete offline
example as `source_demo.py` at the repository root and run
`uv run --locked --project packages/infra/llm-model-sync python source_demo.py`.
Fixed bytes demonstrate registration, fetching and typed projection. It sends no requests, writes no
snapshot and cleans up its temporary directory. A real source must fetch and parse its own payload
instead of using this fixed response.

```python
from pathlib import Path
from tempfile import TemporaryDirectory

from spawn_join_llm_model_sync import (
    SourceCatalog,
    SourceInfo,
    SourceRegistry,
    SourceRequest,
    SyncContext,
    SyncError,
)
from spawn_join_llm_provider import Modality, ModelMetadata, ModelModalities, ModelType


class DemoSource:
    info = SourceInfo(
        id="demo",
        display_name="Offline Demo",
        homepage="https://example.com",
        license="Example data only",
        default_url="https://example.com/catalog.json",
    )

    def fetch(self, context: SyncContext) -> bytes:
        return b"demo/chat"

    def translate(self, payload: bytes, request: SourceRequest) -> SourceCatalog:
        if payload != b"demo/chat" or request.hosts:
            raise SyncError("DemoSource supports only its fixed model payload")
        model = ModelMetadata(
            key="demo/chat",
            name="Demo Chat",
            type=ModelType.CHAT,
            modalities=ModelModalities(input=(Modality.TEXT,), output=(Modality.TEXT,)),
        )
        selected = model.key in request.refs
        return SourceCatalog(
            models={model.key: model} if selected else {},
            hosts={},
            total_models=1,
            total_providers=1,
            unreferenced_models=() if selected else (model.key,),
        )


def main() -> None:
    registry = SourceRegistry.with_builtins()
    registry.register(DemoSource())
    source = registry.get("demo")
    with TemporaryDirectory() as directory:
        payload = source.fetch(SyncContext(cache_dir=Path(directory)))
        catalog = source.translate(payload, SourceRequest(refs=("demo/chat",)))
    print("source registered:", source.info.id)
    for key, model in catalog.models.items():
        print(key, model.name)


if __name__ == "__main__":
    main()
```

Expected output:

```text
source registered: demo
demo/chat Demo Chat
```

Registration affects only this `SourceRegistry` instance; another CLI process will not automatically
discover it. To write a snapshot, the host calls this registry's `sync()` method with explicit
model-file/output paths, `SourceConfig` and `SyncContext`.

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
- When changing shared parsing rules, reuse `spawn_join_common.FieldReader` rather than
  duplicating field-reading code across adapters; `spawn_join_llm_provider.parsing.FieldReader`
  is only the protocol package's compatibility entry for its own callers.
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
