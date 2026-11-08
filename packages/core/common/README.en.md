# spawn-join-common

[简体中文](README.md) | [English](README.en.md)

A standalone package for domain-independent helper capabilities in SpawnJoin. The current release provides a strict standard-library field reader and an optional Pydantic validation-error conversion helper.

## Contents

- [Status and boundaries](#status-and-boundaries)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Public API](#public-api)
- [Development and verification](#development-and-verification)
- [Maintenance and license](#maintenance-and-license)

## Status and boundaries

The current version is `0.1.0` and requires Python `>=3.11`. The base installation has no runtime dependencies and does not depend on any SpawnJoin domain package, model framework, or Provider SDK.

There are only two deliberate public entry points in this release:

- `spawn_join_common.FieldReader`: uses only the Python standard library to read untrusted scalars, lists, and mappings strictly. The caller owns the error factory; the default is `ValueError`.
- `spawn_join_common.validation.validate_with`: available through the optional `validation` extra, converts Pydantic `ValidationError` using caller-owned messages and exception types.

Datetime conversion, serialization, networking, files, caching, retries, and concurrency are outside this release. No placeholder API is created for them. A future capability should have a stable reuse need in at least two components before it is added to the appropriate responsibility-focused module.

## Installation

This package belongs to the SpawnJoin monorepo and is not published to PyPI. Each Distribution is an independent uv project.

For the standard-library reader only, without the development group or Pydantic:

```powershell
uv sync --locked --no-dev --directory packages/core/common
```

To install the Pydantic conversion capability without the development group:

```powershell
uv sync --locked --no-dev --extra validation --directory packages/core/common
```

For development and tests, install the dev group, which includes Pydantic as a test dependency:

```powershell
uv sync --locked --directory packages/core/common
```

The base package can be imported without Pydantic:

```powershell
uv run --locked --no-dev --directory packages/core/common python -c "from spawn_join_common import FieldReader; print(FieldReader().as_int(3, 'count'))"
```

## Quick start

### Read external fields strictly

`FieldReader` rejects numeric strings and does not treat booleans as integers. `as_number` accepts an integer or float and returns a `float`; separate methods enforce finite, non-negative values. A mapping is copied into a new `dict` while preserving source iteration order. `optional` skips only an absent field; an explicit `None` is still passed to the caller's parser so each consumer can retain its own null policy.

```python
from spawn_join_common import FieldReader

reader = FieldReader()
fields = reader.as_mapping({"name": "demo", "limit": 3}, "config")
reader.require_keys(
    fields,
    required=frozenset({"name"}),
    optional=frozenset({"limit"}),
    path="config",
)

name = reader.as_str(fields["name"], "config.name")
limit = reader.optional(fields, "limit", reader.as_non_negative_int, "config")
print(name, limit)
```

Invalid values raise a path-bearing `ValueError`; callers can inject their own `Callable[[str], Exception]` error factory.

### Convert Pydantic validation errors

`validate_with` catches only Pydantic `ValidationError`. The caller supplies the safe message and exception type, and the original validation exception is preserved as `__cause__`; all other exceptions propagate unchanged.

```python
from pydantic import TypeAdapter, ValidationError

from spawn_join_common.validation import validate_with

adapter = TypeAdapter(int)

try:
    value = validate_with(
        lambda: adapter.validate_python("not-an-integer"),
        error=ValueError,
        message=lambda exc: "config.limit: invalid integer",
    )
except ValueError as exc:
    assert isinstance(exc.__cause__, ValidationError)
    print(exc)
```

The public helper never renders validation input itself; message formatting remains the caller's responsibility.

## Public API

### `spawn_join_common`

- `FieldReader`
- `__version__` (currently `"0.1.0"`)

`FieldReader` provides `fail`, `as_mapping`, `require_keys`, `as_str`, `as_int`, `as_non_negative_int`, `as_number`, `as_non_negative_number`, `as_bool`, `as_list`, and `optional`. It is a frozen/slotted dataclass with no I/O, logging, global registration, or in-place mutation of the supplied mapping.

### `spawn_join_common.validation`

- `validate_with(operation, *, error, message)`

This subpackage is the only optional Pydantic entry point; importing `spawn_join_common` itself does not load Pydantic.

## Development and verification

Run these independent-package checks from the repository root:

```powershell
uv lock --check --directory packages/core/common
uv sync --locked --directory packages/core/common
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-common
```

The shared entry point explicitly uses the repository tool policy for Black/isort, Ruff, Pyright strict, pytest, builds, and isolated installation of both the base package and validation extra.

The package uses a `src/` layout, with runtime code under `src/spawn_join_common/` and tests under `tests/`. Runtime dependencies remain empty for the base package; Pydantic is declared only for the `validation` extra and development tests.

## Maintenance and license

Public capabilities must remain domain-independent with one-way dependencies. Adding an API requires synchronized tests, bilingual documentation, and independent installation evidence. The package version is managed independently; publication requires separate authorization.

This package is proprietary software. Use and distribution require authorization under [LICENSE](LICENSE).
