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
  - [1. Run the full offline example](#1-run-the-full-offline-example)
  - [2. Connect your own model service](#2-connect-your-own-model-service)
- [Work items](#work-items)
  - [WorkItem fields](#workitem-fields)
  - [State machine](#state-machine)
- [Scheduling](#scheduling)
- [Approvals](#approvals)
  - [ApprovalRecord fields](#approvalrecord-fields)
  - [Approval flow](#approval-flow)
- [Assembly](#assembly)
- [CLI](#cli)
- [Public API](#public-api)
- [Errors and failure behavior](#errors-and-failure-behavior)
- [Compatibility and limitations](#compatibility-and-limitations)
- [Development and verification](#development-and-verification)
- [Release and versioning](#release-and-versioning)
- [Maintenance and contributing](#maintenance-and-contributing)
- [Related documentation](#related-documentation)
- [License](#license)

## Status and compatibility

- Version and stability: `0.1.0`, preview; the public API may still change
  as documented during `0.x`.
- Runtime: Python `>=3.11`; DeepAgents `0.7.x`; LangChain/LangGraph 1.x.
- Release status: local repository development only; not published to PyPI
  or a private registry yet.

## Provided capabilities

- Six-state work-item machine
  (`queued/running/waiting_approval/completed/failed/cancelled`) with a
  unique idempotency-key constraint: replaying the same key never creates a
  second item or side effect;
- asyncio due scheduler: concurrency bound, deadline (expiry lands as
  `failed` with category `deadline`), cancellation propagation (requeue +
  re-raise), and exactly-once interrupted-rerun recovery after restart;
- Confined workspace assembly: `FilesystemBackend` path guardrails
  (rejecting `..`, `~`, and absolute paths outside the root), explicit
  `FilesystemPermission` policy, and no shell execution tools by default;
- Strict-msgpack `AsyncSqliteSaver`: thread state survives process
  restarts with a strict deserialization whitelist enabled by default
  (equivalent to the documented `LANGGRAPH_STRICT_MSGPACK` switch without
  mutating process environment);
- HITL approval persistence: action lists, decisions, and timestamps in an
  own SQLite table; decided records are immutable; resume commands are
  structurally aligned with the action count;
- Five CLI subcommands (`accept/due/run/report/approve`): stable exit
  codes 0/1; credentials only via the `LLM_API_KEY` environment variable;
- 60 offline tests (including e2e) plus a runnable example, independent
  wheel/sdist, `py.typed`, and a quality profile.

## Installation

Use this Distribution's own environment from the repository root:

```powershell
uv lock --check --directory packages/apps/personal-assistant
uv sync --locked --directory packages/apps/personal-assistant
```

Runtime dependencies:

- `spawn-join-agent-deepagents>=0.1.0,<0.2.0`
- `spawn-join-llm-provider-langchain>=0.1.0,<0.2.0`
- `langgraph-checkpoint-sqlite>=3.1.3,<4`

This package does not re-parse `model.yaml`, `.env`, or Provider SDKs;
configured models are created by
[`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/README.en.md)
and agent assembly is owned by
[`spawn-join-agent-deepagents`](../../infra/agent-deepagents/README.en.md).

## Quick start

### 1. Run the full offline example

From the repository root — no model file or credentials needed:

```powershell
uv run --locked --directory packages/apps/personal-assistant python examples/offline_run.py
```

Full source: [offline_run.py](examples/offline_run.py). It uses
[`fake_model.py`](examples/fake_model.py) in the same directory for
deterministic responses: the model first requests to write a note (which
pauses for approval), then the script approves, resumes, and reports.
Actual output:

```text
accepted <id> key=notes-1
waiting_approval <id>: needs human decision
run: 1 item(s) processed
approved <id>: completed
completed <id>: note written to workspace.
report: 1 item(s)
notes.txt exists: True
```

### 2. Connect your own model service

Prepare `model.yaml` (both purposes share the `LLM_API_KEY` credential):

```yaml
schema_version: 1
default: supervisor
models:
  supervisor:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: your-supervisor-model
    api_key_env: LLM_API_KEY
  worker:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: your-worker-model
    api_key_env: LLM_API_KEY
```

Models must support tool calling. Then set `LLM_API_KEY` in the process
environment and drive the full loop with the CLI:

```powershell
$env:LLM_API_KEY = "<your-key>"
spawn-join-personal-assistant --root <data-dir> --model-catalog <path-to-model.yaml> accept "organize this week's invoices" --key invoices-week-47
spawn-join-personal-assistant --root <data-dir> --model-catalog <path-to-model.yaml> run --supervisor-model supervisor --worker-model worker
spawn-join-personal-assistant --root <data-dir> report
spawn-join-personal-assistant --root <data-dir> approve --list
spawn-join-personal-assistant --root <data-dir> approve --record <record-id>
```

## Work items

### WorkItem fields

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | `str` | Store-assigned unique identifier (UUID hex) |
| `idempotency_key` | `str` | Caller-supplied, unique across items; replaying the same key is rejected |
| `goal` | `str` | Non-empty natural-language goal |
| `status` | `WorkStatus` | Current lifecycle state |
| `created_at` / `updated_at` | `str` | ISO-8601 UTC timestamps |
| `due_at` | `str \| None` | Optional runnable-from time; `run_due` only picks items past it |
| `deadline_seconds` | `float \| None` | Total runtime budget per attempt |
| `attempts` | `int` | Started runs; incremented on every `queued -> running` |
| `result_summary` | `str \| None` | Final reply summary on completion (truncated to 200 chars) |
| `failure_category` | `str \| None` | Stable failure category (`deadline`, exception class name, `rejected`) |
| `thread_id` | `str \| None` | Associated checkpointer thread |

### State machine

```text
queued ──→ running ──→ completed
   │           │  ↖       │
   │           ↓  │       ↓
   ↓       waiting_approval → failed
cancel ←──┘  │       │
             ↓       ↓
          cancel ←──┘
```

- `transition_allowed(current, target)` is the single transition authority;
- Illegal moves raise `WorkTransitionError` with zero side effects
  (`queued -> completed` is rejected outright);
- Terminal states (`completed/failed/cancelled`) reject every transition;
- The `running -> queued` recovery edge is for interrupted reruns only: a
  hard-killed process leaves the item RUNNING, and
  `Scheduler.recover_interrupted()` requeues it exactly once at next start.

Code example:

```python
from spawn_join_personal_assistant import WorkStatus, WorkStore
from pathlib import Path

with WorkStore(Path("data/work.db")) as store:
    item = store.accept("organize invoices", idempotency_key="invoices-001")

    running = store.mark(item.id, WorkStatus.RUNNING, increment_attempt=True)
    assert running.attempts == 1

    done = store.mark(
        running.id, WorkStatus.COMPLETED, result_summary="12 invoices filed"
    )
    assert done.result_summary == "12 invoices filed"
```

## Scheduling

`Scheduler` picks every due queued item in one `run_due` cycle, bounds
concurrency with a semaphore, and enforces the deadline via
`asyncio.timeout`:

| Transition | Behavior |
| --- | --- |
| Due pickup | `queued` items where `due_at is None or due_at <= now` |
| Concurrency bound | `asyncio.Semaphore(max_concurrency)`; excess items wait |
| Deadline expiry | Lands as `failed` with category `deadline`; slot released immediately |
| Executor exception | Lands as `failed` with the exception class name; **sibling items keep running** (the store is the record) |
| Executor incomplete | Lands as `failed` with category `executor_incomplete` (contract backstop) |
| Parent cancellation | Running item is requeued (`running -> queued`) and `CancelledError` propagates |
| Restart recovery | `recover_interrupted()` requeues RUNNING items exactly once |

The executor contract (`WorkExecutor`): an async callable receiving the
RUNNING item that **persists its own final state**; the scheduler verifies
the contract by reading back the stored outcome. In production the CLI's
`_drive_to_outcome` is the reference implementation: it consumes the astream
update stream fully, detects interrupts, and persists the final-state
summary from `aget_state` when no interrupt fired.

Code example:

```python
import asyncio
from pathlib import Path
from spawn_join_personal_assistant import Scheduler, WorkStatus, WorkStore

async def scenario() -> None:
    with WorkStore(Path("data/work.db")) as store:
        async def execute(item) -> None:
            store.mark(item.id, WorkStatus.COMPLETED, result_summary="done")

        scheduler = Scheduler(store, max_concurrency=2, deadline_seconds=120)
        recovered = await scheduler.recover_interrupted()
        outcomes = await scheduler.run_due(execute)
        print(f"{len(outcomes)} item(s) processed")

asyncio.run(scenario())
```

## Approvals

### ApprovalRecord fields

| Field | Type | Meaning |
| --- | --- | --- |
| `id` | `str` | Book-assigned unique identifier (UUID hex) |
| `work_item_id` | `str` | Associated work item |
| `thread_id` | `str` | Associated checkpointer thread |
| `interrupt_id` | `str \| None` | Native interrupt id when present |
| `actions` | `tuple[dict, ...]` | Requested actions, in order; decisions must align one-to-one |
| `decision` | `str` | `pending` / `approved` / `rejected` |
| `created_at` / `decided_at` | `str` | ISO-8601 UTC timestamps |

### Approval flow

1. `pause_for_approval(store, book, ...)`: extracts the action list from the
   native interrupt, persists it, and moves the work item to
   `waiting_approval` (with the `thread_id` association);
2. `apply_decision(..., approve=True)`: records the decision, returns the
   work item to `running`, and returns the aligned `resume_batched` command
   (approved actions execute on resume);
3. `apply_decision(..., approve=False, message="...")`: records the decision,
   lands the work item as `failed(rejected)`, and returns the aligned reject
   command (**refused actions are never executed**);
4. Decided records are immutable: a second decision raises
   `HostApprovalError`.

Code example (the fully runnable version is in `tests/test_approvals.py`):

```python
# After the run_due executor detects an interrupt:
record = pause_for_approval(
    store, book, work_item_id=item.id, thread_id="t-1", interrupt=found
)

# After the user approves:
command = apply_decision(
    store, book, record_id=record.id, work_item_id=item.id, approve=True
)
await graph.ainvoke(command, {"configurable": {"thread_id": "t-1"}})
```

**Two runtime facts verified by probe before landing** (recorded in this
package's tests):

1. Callers must **fully consume** `astream(stream_mode="updates")` before
   resuming — breaking early interrupts the underlying run's checkpoint and
   approved tools will not execute;
2. The deepagents `write_file` tool parameter is named `file_path`, not
   `path`.

The CLI already follows this pattern internally; library callers must honor
rule 1.

## Assembly

`open_host_session(config, models=...)` assembles the native supervisor:

```python
import asyncio
from pathlib import Path
from spawn_join_personal_assistant import AppConfig, HostSession
from spawn_join_personal_assistant.host import open_host_session

config = AppConfig(
    data_dir=Path("~/.spawn-join-personal-assistant/data").expanduser(),
    workspace_root=Path("~/.spawn-join-personal-assistant/workspace").expanduser(),
    model_catalog_path=Path("model.yaml"),
)

async def main() -> None:
    session = await open_host_session(
        config, models=models, interrupt_on={"write_file": True}
    )
    try:
        result = await session.assembly.graph.ainvoke(
            {"messages": [HumanMessage(content="hello")]},
            {"configurable": {"thread_id": "greeting"}},
        )
        print(result["messages"][-1].content)
    finally:
        await session.aclose()  # idempotently closes the host-owned connection

asyncio.run(main())
```

- All four `HostSession.spec/backend/checkpointer/connection` fields are
  assertable: tests directly verify `spec.tools == ()`,
  `backend.cwd == workspace_root`, and that `checkpointer.serde` is
  behaviorally equivalent to the strict serializer;
- Assembly only validates configuration and creates the graph; it **does not
  execute the graph or open external model connections** (models are
  consumed at runtime);
- To change which tools are approval-gated, pass a different `interrupt_on`
  Mapping.

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

| Subcommand | Behavior | Exit codes |
| --- | --- | --- |
| `accept` | Insert with unique idempotency key | 0 / 1 on duplicate key or blank goal |
| `due` | List unfinished items with due status | 0 |
| `run` | Recover interrupted items, then one due cycle | 0 / 1 on missing catalog |
| `report` | List all history (filterable by status) | 0 |
| `approve --list` | List pending approval records | 0 |
| `approve --record ID` | Approve and resume execution | 0 / 1 on unknown or decided record |
| `approve --record ID --reject` | Reject (action never executes) | 0 |

- Output goes through `sys.stdout.write` (no `print`, no runtime log
  mixing);
- Errors are prefixed `personal-assistant:` on stderr;
- v1 approval policy: `write_file` tool calls require human approval.

## Public API

Public exports are defined by `spawn_join_personal_assistant.__all__`,
mainly:

- `main`, `AppConfig`;
- `ApprovalBook`, `ApprovalRecord`, `apply_decision`, `interrupt_actions`,
  `pause_for_approval`, `resume_approved`, `resume_rejected`;
- `HostSession`, `open_host_session`;
- `Scheduler`, `WorkExecutor`;
- `WorkItem`, `WorkStatus`, `WorkStore`;
- Stable error types (`HostError` base plus `HostConfigError`,
  `HostStoreError`, `HostSchedulingError`, `HostApprovalError`,
  `WorkTransitionError`).

Internal modules (`work/`, `scheduler`, `approvals`, `host`, `cli`) do not
become public contracts just because they are importable.

## Errors and failure behavior

- All host-side failures surface as `HostError` subclasses; the CLI maps
  them to stable exit code 1.
- Executor exceptions never abort sibling items: they land as `failed`
  with the exception class name; the store is the record.
- `WorkTransitionError` (a `HostStoreError` subclass): illegal state
  transitions fail with zero side effects.
- Decided approval records are immutable: a second decision raises
  `HostApprovalError`.
- Model and framework exceptions keep their own taxonomy and cause chains;
  cross-package errors are converted with the original cause preserved
  (`ConfigurationError -> HostError`).
- Upstream `LLMCallError` normalization is owned by the assembly package's
  middleware (enabled by default); this package does not swallow it.

## Compatibility and limitations

- Python `>=3.11`; the DeepAgents lock is owned by the assembly package
  (`>=0.7.32,<0.8`).
- **Memory (langmem, `BaseStore`, embeddings, memory files) is out of scope
  for v1**; the `SupervisorSpec.store`/`memory` pass-through seam is
  reserved for a later discussion (ADR-0015).
- Single-writer assumption: one host process per data directory at a time;
  concurrent multi-process access to the same SQLite is unsupported.
- Callers must consume `astream(stream_mode="updates")` to completion before
  resuming with `ainvoke(command)` on the same thread (the CLI follows this
  internally; breaking early interrupts the underlying run's checkpointing).
- No multi-tenancy/auth/billing, IM channels, web UI, MCP server,
  container/remote sandbox, or Postgres deployment; production migration is
  documented as seams only (ADR-0015).

## Development and verification

```powershell
uv lock --check --directory packages/apps/personal-assistant
uv sync --locked --directory packages/apps/personal-assistant
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-personal-assistant
```

- Layout: `src/spawn_join_personal_assistant/` holds runtime sources;
  `tests/` holds offline tests (60 cases); `examples/` holds runnable
  examples; the package carries its own `uv.lock`, `py.typed`, and
  `LICENSE`.
- Required tools: uv `>=0.7.13`, PowerShell 7, Git, Node.js 22+ (Pyright
  wrapper).
- The package quality gate runs Black/isort, Ruff, Pyright strict, pytest,
  wheel/sdist, isolated installation, `pip check`, and isolated import.
  Offline tests never read real credentials or contact external services.
- e2e coverage: the accept→run→approve→report loop including escape-write
  guardrails and hard-kill recovery (side effects counted via controlled
  file writes).

## Release and versioning

This package uses an independent version and independent wheel/sdist; it is
not implicitly released with other Distributions. Current version `0.1.0`,
not yet published; release requires the repository quality gate, independent
review, and separate release authorization. Breaking public-API changes must
update the version, documentation, and compatibility notes, and re-run the
package-level and repository-level gates.

## Maintenance and contributing

This package is owned by the SpawnJoin repository maintainers; changes
follow `AGENTS.md`, the
[package boundaries](../../../docs/architecture/package-boundaries.md), and
[ADR-0015](../../../docs/decisions/agent/0015-personal-assistant-host-boundary.md).
New capabilities or public-contract changes take the Feature delivery route;
defects take Bugfix; documentation-only or mechanical changes take
Lightweight. Commits must carry quality, standards, and review evidence
bound to the current diff.

## Related documentation

- [ADR-0015: personal assistant host boundary and persistence baseline](../../../docs/decisions/agent/0015-personal-assistant-host-boundary.md)
- [ADR-0010: DeepAgents product boundary](../../../docs/decisions/agent/0010-deepagents-product-boundary.md) (assembly-package contract)
- [Package boundaries](../../../docs/architecture/package-boundaries.md)
- [Repository map](../../../docs/architecture/repository-map.md)
- [Quality gates](../../../docs/development/quality-gates.md)

## License

This package is proprietary software. All rights reserved. See
[LICENSE](LICENSE).
