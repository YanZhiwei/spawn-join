# spawn-join-core

[简体中文](README.md) | [English](README.en.md)

Stable contracts and foundational primitives shared across the SpawnJoin ecosystem.

**Contents**

- [Status and compatibility](#status-and-compatibility)
- [Installation and shortest use](#installation-and-shortest-use)
- [Boundaries and non-goals](#boundaries-and-non-goals)
- [Layout, development, and quality](#layout-development-and-quality)
- [Maintenance, versioning, and license](#maintenance-versioning-and-license)

## Status and compatibility

`0.1.0` scaffold, requiring Python `>=3.11`. `config`, `exceptions`, `protocols`, and
`types` currently contain module contracts only, with no implementation or public
exports; the package root exposes only `__version__`. Interfaces may still change in
documented ways during `0.x`.

## Installation and shortest use

This package belongs to the SpawnJoin monorepo and is not published to PyPI. Use the
Distribution's own environment:

```powershell
uv sync --locked --directory packages/core/spawn-join-core
```

The shortest currently valid import:

```python
import spawn_join_core

print(spawn_join_core.__version__)
```

Alternatively, run directly from the repository root without creating a script:

```powershell
uv run --locked --directory packages/core/spawn-join-core python -c "import spawn_join_core; print(spawn_join_core.__version__)"
```

Expected output: `0.1.0`. No credentials or network requests are needed.

There is no callable public API, CLI, or configuration surface; do not infer runtime
capabilities that are not implemented.

## Boundaries and non-goals

- Must not depend on another SpawnJoin package.
- Must not introduce third-party runtime dependencies.
- Must not host single-domain helpers, Provider adapters, or side effects.
- Add capabilities to Core only after at least two components have a stable reuse need.

## Layout, development, and quality

- `src/spawn_join_core/`: runtime source; currently contract documentation only.
- `tests/`: import, identity, and zero-runtime-dependency boundary tests.
- Independent `pyproject.toml`, `uv.lock`, and `.venv/`; never create a root uv workspace.

```powershell
uv lock --check --directory packages/core/spawn-join-core
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-core
```

The quality command runs Black, isort, Ruff, Pyright strict, pytest, wheel/sdist, isolated
installation, `pip check`, and an isolated import check.

## Maintenance, versioning, and license

Public capabilities must first pass the Feature delivery route with a documented reuse
rationale, dependency direction, and verification method; synchronize tests, package
boundaries, and repository docs when adding or removing modules. This package uses an
independent version and is not published; publication requires separate authorization.
See [LICENSE](LICENSE).
