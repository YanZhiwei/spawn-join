# spawn-join-llm-model-sync

Manual model metadata synchronization for SpawnJoin LLM catalogs.

The package fetches metadata from an explicitly selected source, translates only the
models referenced by `model.yaml`, validates the result, and writes a deterministic
`model-metadata.json` snapshot. It never modifies `model.yaml`, never registers models
automatically, and never runs on a schedule.

## Status

This package is part of the SpawnJoin monorepo and is not published to PyPI. It is an
infrastructure tool, not a runtime dependency of the LangChain adapter.

## Install

```powershell
uv sync --locked --directory packages/infra/llm-model-sync
```

## Commands

```powershell
model-sync sources
model-sync sync --source models.dev
model-sync sync --source models.dev --apply
model-sync sync --source models.dev --check
```

`sync` defaults to a dry run. `--apply` writes the snapshot atomically; `--check`
returns exit code `2` when the snapshot differs. Exit code `3` means the source was
unreachable, malformed, truncated, or failed validation.

## Storage

- Snapshot: next to `model.yaml` by default, or explicit `--output`.
- Cache/state/reports: platform user cache directory, or explicit `--cache-dir`.

The runtime library never reads these directories; the application passes an explicit
`metadata_file` path.

## Adding a source

Implement `MetadataSource`, provide fixture-based translation tests, and register the
source explicitly:

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

The runner, snapshot schema, and runtime loader do not change. `model-sync sources`
lists registered sources.

See
[ADR-0009](../../../docs/decisions/llm-provider/0009-model-metadata-and-sync.md) for the
long-term boundary.
