# spawn-join-personal-assistant

[简体中文](README.md) | [English](README.en.md)

`spawn-join-personal-assistant` is the SpawnJoin personal assistant host
application: it composes `spawn-join-agent-deepagents` and
`spawn-join-llm-provider-langchain` into a testable local product that accepts
work, executes it inside a confined workspace, pauses for approvals, reports
results, and recovers after restarts. It owns the work-item store, the
scheduler loop, HITL approval persistence, and the CLI. **Memory is out of
scope for v1** (the seam is reserved; see ADR-0015).

> Status note: this package is delivered in slices. Currently provided:
> the configuration boundary (`AppConfig`), the stable error taxonomy,
> **work-item persistence** (sqlite3 state machine, idempotency keys,
> recovery scan), and **host assembly** (confined workspace backend,
> permission gates, strict-msgpack SQLite checkpointer); scheduling,
> approvals, and the CLI land in later slices. This document describes
> only what is implemented.

**Contents**

- [Status and compatibility](#status-and-compatibility)
- [Provided capabilities](#provided-capabilities)
- [Installation](#installation)
- [Configuration](#configuration)
- [Errors and failure behavior](#errors-and-failure-behavior)
- [Compatibility and limitations](#compatibility-and-limitations)
- [Development and verification](#development-and-verification)
- [Related documentation](#related-documentation)
- [License](#license)

## Status and compatibility

- Version and stability: `0.1.0`, preview; the public API may still change
  as documented during `0.x`.
- Runtime: Python `>=3.11`; depends on `spawn-join-agent-deepagents`,
  `spawn-join-llm-provider-langchain`, and
  `langgraph-checkpoint-sqlite>=3.1.3,<4`.
- Release status: local repository development only; not published to PyPI or
  a private registry yet.

## Provided capabilities

- `AppConfig`: the host configuration boundary object. It eagerly validates
  the data directory, workspace root, model catalog file, and scheduler
  bounds/deadline. Credentials never enter configuration (environment only,
  ADR-0008).
- Stable error taxonomy: `HostError` with `HostConfigError`,
  `HostStoreError`, `HostSchedulingError`, `HostApprovalError`, and
  `WorkTransitionError` subclasses for host-side failure categories.
- `WorkStore`: single-writer sqlite3 persistence — `accept` inserts with a
  unique idempotency key (replays are rejected), `mark` applies state-machine
  transitions (`queued/running/waiting_approval/completed/failed/cancelled`;
  illegal moves raise `WorkTransitionError` with zero side effects),
  `pending_recovery` scans unfinished items after restart, and
  `count_by_status` reports totals; `WorkItem`/`WorkStatus` are the public
  data types.
- `open_host_session`: assembles the native supervisor — a
  `FilesystemBackend(workspace_root, virtual_mode=True)` with path
  guardrails (rejecting `..`, `~`, and absolute paths outside the root),
  an explicit `FilesystemPermission` workspace policy, `tools=()` so no shell
  execution tools are exposed by default, and an `AsyncSqliteSaver` that
  persists thread state with a strict deserialization whitelist by default
  (`allowed_msgpack_modules=None`, equivalent to the documented
  `LANGGRAPH_STRICT_MSGPACK` switch without mutating process environment).
  It returns a `HostSession` whose idempotent `aclose` closes the
  host-owned connection. Credentials never pass through the assembly:
  models arrive as constructed `BaseChatModel` instances or a caller-owned
  `ModelCatalog` binding (ADR-0008).

Later slices (see the delivery queue): the asyncio due scheduler, HITL
approval persistence, and the `accept`/`due`/`run`/`report`/`approve` CLI.

## Installation

Use this Distribution's own environment from the repository root:

```powershell
uv lock --check --directory packages/apps/personal-assistant
uv sync --locked --directory packages/apps/personal-assistant
```

## Configuration

`AppConfig` fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `data_dir` | `pathlib.Path` | Host persistence directory (SQLite database) |
| `workspace_root` | `pathlib.Path` | The only legal root for agent file side effects |
| `model_catalog_path` | `pathlib.Path` | Model catalog file; consumed via `ModelCatalog`, must exist |
| `max_concurrency` | `int = 2` | Maximum simultaneously running work items (at least 1) |
| `work_deadline_seconds` | `float \| None = None` | Total deadline per work-item run; `None` disables it |

Invalid input (non-`Path` values, missing catalog file, concurrency below 1,
deadline at or below 0) raises `HostConfigError` at construction time and
never reaches later stages.

## Errors and failure behavior

- Host-side failures surface as `HostError` subclasses with stable,
  assertable messages.
- Model and framework exceptions keep their own taxonomy and cause chains;
  this package does not swallow or relabel them.

## Compatibility and limitations

- Python `>=3.11`; the DeepAgents lock is owned by the assembly package
  (`>=0.7.32,<0.8`).
- Memory (langmem, `BaseStore`, embeddings, memory files) is out of scope for
  v1; the `SupervisorSpec.store`/`memory` pass-through seam is reserved, see
  ADR-0015.
- No multi-tenancy, IM channels, web UI, MCP server, container/remote
  sandbox, or Postgres deployment; production migration is documented as
  seams only (ADR-0015).

## Development and verification

```powershell
uv lock --check --directory packages/apps/personal-assistant
uv sync --locked --directory packages/apps/personal-assistant
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-personal-assistant
```

- Layout: `src/spawn_join_personal_assistant/` holds runtime sources;
  `tests/` holds offline tests.
- Offline tests never read real credentials or contact external services.

## Related documentation

- [ADR-0015: personal assistant host boundary and persistence baseline](../../../docs/decisions/agent/0015-personal-assistant-host-boundary.md)
- [Package boundaries](../../../docs/architecture/package-boundaries.md)
- [Repository map](../../../docs/architecture/repository-map.md)
- [Quality gates](../../../docs/development/quality-gates.md)

## License

This package is proprietary software. All rights reserved. See
[LICENSE](LICENSE).
