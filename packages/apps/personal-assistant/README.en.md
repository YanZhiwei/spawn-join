# spawn-join-personal-assistant

[简体中文](README.md) | [English](README.en.md)

`spawn-join-personal-assistant` is the SpawnJoin personal assistant host
application: it composes `spawn-join-agent-deepagents` and
`spawn-join-llm-provider-langchain` into a testable local product that accepts
work, executes it inside a confined workspace, pauses for approvals, reports
results, and recovers after restarts. It owns the work-item store, the
scheduler loop, HITL approval persistence, and the CLI. **Memory is out of
scope for v1** (the seam is reserved; see
[ADR-0015](../../../docs/decisions/agent/0015-personal-assistant-host-boundary.md)).

**Contents**

- [Status and compatibility](#status-and-compatibility)
- [Provided capabilities](#provided-capabilities)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [CLI](#cli)
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
- Release status: local repository development only; not published to PyPI
  or a private registry yet.

## Provided capabilities

- **Configuration boundary**: `AppConfig` eagerly validates the data
  directory, workspace root, model catalog file, and scheduler
  bounds/deadline. Credentials never enter configuration (environment only,
  ADR-0008).
- **Stable error taxonomy**: `HostError` with `HostConfigError`,
  `HostStoreError`, `HostSchedulingError`, `HostApprovalError`, and
  `WorkTransitionError` subclasses.
- **Work-item persistence** (`WorkStore`): single-writer sqlite3 — `accept`
  inserts with a unique idempotency key (replays are rejected), `mark`
  applies state-machine transitions (`queued/running/waiting_approval/
  completed/failed/cancelled`; illegal moves raise `WorkTransitionError`
  with zero side effects), `pending_recovery` scans unfinished items after
  restart, and `list_all` reports history; `WorkItem`/`WorkStatus` are the
  public data types.
- **Host assembly** (`open_host_session`): a
  `FilesystemBackend(workspace_root, virtual_mode=True)` with path
  guardrails (rejecting `..`, `~`, and absolute paths outside the root), an
  explicit `FilesystemPermission` workspace policy, `tools=()` so no shell
  execution tools are exposed by default, and an `AsyncSqliteSaver` that
  persists thread state with a strict deserialization whitelist by default
  (equivalent to the documented `LANGGRAPH_STRICT_MSGPACK` switch without
  mutating process environment). It returns a `HostSession` whose idempotent
  `aclose` closes the host-owned connection.
- **Due scheduler** (`Scheduler`): `run_due` picks due queued items for one
  cycle, bounds concurrency with a semaphore, enforces an optional deadline
  via `asyncio.timeout` (expiry lands as `failed` with category `deadline`
  and releases the slot), converts executor exceptions into `failed` items
  (category = exception class name; the store is the record and sibling
  items keep running), re-queues the running item on parent cancellation
  (`RUNNING -> QUEUED`) while propagating `CancelledError`, and re-queues
  interrupted runs exactly once after a restart via `recover_interrupted`.
  `WorkExecutor` is the executor contract type (receives the RUNNING item
  and persists its final state itself).
- **HITL approvals** (`ApprovalBook`/`ApprovalRecord`): persisted approval
  requests (own SQLite table with the action list, decision, and
  timestamps; decided records are immutable). `pause_for_approval` saves
  the request and moves the work item to `waiting_approval`;
  `apply_decision` records the human decision and returns the **aligned**
  native resume command (`resume_batched`, one decision per recorded
  action, in order; approve returns the item to `running`, reject records
  `failed(rejected)` without executing the refused actions).
- **CLI** (`main`): the `accept`/`due`/`run`/`report`/`approve`
  subcommands with stable exit codes 0/1; `main(bindings=...)` is the
  model-binding injection seam (production via `ModelCatalog`, offline via
  a constructed `BaseChatModel`).

## Installation

Use this Distribution's own environment from the repository root:

```powershell
uv lock --check --directory packages/apps/personal-assistant
uv sync --locked --directory packages/apps/personal-assistant
```

## Quick start

Run the full offline example first (no model file or credentials needed):

```powershell
uv run --locked --directory packages/apps/personal-assistant python examples/offline_run.py
```

The example uses [`fake_model.py`](examples/fake_model.py) for deterministic
responses and prints the accept → run (paused for approval) → approve →
report loop. After installation the console entry
`spawn-join-personal-assistant` invokes the CLI.

## Configuration

`AppConfig` fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `data_dir` | `pathlib.Path` | Host persistence directory (work/approval SQLite plus threads.db) |
| `workspace_root` | `pathlib.Path` | The only legal root for agent file side effects |
| `model_catalog_path` | `pathlib.Path` | Model catalog file; consumed via `ModelCatalog`, must exist |
| `max_concurrency` | `int = 2` | Maximum simultaneously running work items (at least 1) |
| `work_deadline_seconds` | `float \| None = None` | Total deadline per work-item run; `None` disables it |

The CLI defaults its root to `~/.spawn-join-personal-assistant`
(overridable with `--root`) and its model catalog to `<root>/model.yaml`
(overridable with `--model-catalog`).

## CLI

```text
spawn-join-personal-assistant [--root DIR] [--model-catalog PATH]
    accept GOAL [--key KEY] [--due ISO]
    due
    run [--max-concurrency N] [--deadline SECONDS]
        [--supervisor-model NAME] [--worker-model NAME]
    report [--status STATUS]
    approve --list | approve --record ID [--reject] [--message MSG]
```

`run` recovers interrupted items before executing one due cycle. v1
approval policy: `write_file` tool calls require human approval
(`approve --list` to inspect, `approve --record ID` to approve, or
`--record ID --reject` to reject). Exit codes: 0 success, 1 host error
(stderr prefix `personal-assistant:`) or usage error.

## Errors and failure behavior

- Host-side failures surface as `HostError` subclasses; the CLI maps them
  to stable exit code 1.
- Executor exceptions never abort sibling items: they land as `failed`
  with the exception class name; the store is the record.
- Model and framework exceptions keep their own taxonomy and cause chains;
  cross-package errors are converted with the original cause preserved
  (`ConfigurationError -> HostError`).

## Compatibility and limitations

- Python `>=3.11`; the DeepAgents lock is owned by the assembly package
  (`>=0.7.32,<0.8`).
- Memory (langmem, `BaseStore`, embeddings, memory files) is out of scope
  for v1; the `SupervisorSpec.store`/`memory` pass-through seam is
  reserved, see ADR-0015.
- Single-writer assumption: one host process per data directory at a time;
  concurrent multi-process access to the same SQLite is unsupported.
- Callers must consume `astream(stream_mode="updates")` to completion
  before resuming with `ainvoke(command)` on the same thread (breaking
  early interrupts the underlying run's checkpointing); the CLI already
  follows this pattern internally.
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
  `tests/` holds offline tests (60 cases); `examples/` holds runnable
  examples.
- Offline tests never read real credentials or contact external services;
  the e2e covers the accept→run→approve→report loop including escape-write
  guardrails and hard-kill recovery.

## Related documentation

- [ADR-0015: personal assistant host boundary and persistence baseline](../../../docs/decisions/agent/0015-personal-assistant-host-boundary.md)
- [Package boundaries](../../../docs/architecture/package-boundaries.md)
- [Repository map](../../../docs/architecture/repository-map.md)
- [Quality gates](../../../docs/development/quality-gates.md)

## License

This package is proprietary software. All rights reserved. See
[LICENSE](LICENSE).
