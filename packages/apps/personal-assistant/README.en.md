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

**Why you need it.** Building a "personal assistant" directly on
DeepAgents/LangGraph runs into the same host problems every time:

- The conversation dies with the process — agent thread state has no
  persistence across restarts.
- File side effects have no boundary — by default the agent can write the
  whole disk, and it should not have a shell.
- Dangerous actions have no human gate — "approve first, execute later"
  means handling interrupts, decisions, and resume-command alignment
  yourself.
- Tasks have no durable queue or idempotency — every retry repeats the side
  effect.
- Testing the loop offline is impossible without a model injection seam.

This package collapses those problems into five testable host contracts:
durable work items (idempotency key + state machine), an asyncio due
scheduler (concurrency bound + deadline + interrupted rerun), a HITL approval
book (decided records immutable + aligned resume commands), confined-workspace
assembly (path guardrails + explicit permissions + no shell by default), and a
strict-msgpack checkpointer (thread recovery across restarts).

**How to read this document.** As a package consumer, start with
[Installation](#installation) and [Quick start](#quick-start), then follow
[Work items](#work-items) → [Scheduling](#scheduling) → [Approvals](#approvals)
→ [CLI](#cli) for the domain semantics. As a maintainer, read
[Architecture and module boundaries](#architecture-and-module-boundaries-maintainer-view)
and [Development and verification](#development-and-verification) first, and
consult the per-domain examples as needed.

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
  - [Full example: accept→execute→complete](#full-example-acceptexecutecomplete)
  - [Idempotency key replay](#idempotency-key-replay)
  - [Illegal transition rejection](#illegal-transition-rejection)
  - [Data survives restart](#data-survives-restart)
- [Scheduling](#scheduling)
  - [Example 1: basic cycle](#example-1-basic-cycle)
  - [Example 2: deadline expiry](#example-2-deadline-expiry)
  - [Example 3: executor exception (siblings unaffected)](#example-3-executor-exception-siblings-unaffected)
  - [Example 4: hard-kill recovery](#example-4-hard-kill-recovery)
  - [Example 5: parent cancellation](#example-5-parent-cancellation)
- [Approvals](#approvals)
  - [ApprovalRecord fields](#approvalrecord-fields)
  - [Approval flow](#approval-flow)
  - [Full example: approve path (file written)](#full-example-approve-path-file-written)
  - [Full example: reject path (action skipped)](#full-example-reject-path-action-skipped)
  - [Full example: decided records are immutable](#full-example-decided-records-are-immutable)
  - [Full example: pending alignment after restart](#full-example-pending-alignment-after-restart)
- [Assembly](#assembly)
  - [Full example: assembly and resource cleanup](#full-example-assembly-and-resource-cleanup)
  - [Full example: custom approval gates](#full-example-custom-approval-gates)
  - [HostSession field assertions](#hostsession-field-assertions)
- [CLI](#cli)
  - [CLI full flow walkthrough](#cli-full-flow-walkthrough)
- [Public API](#public-api)
- [Errors and failure behavior](#errors-and-failure-behavior)
- [Compatibility and limitations](#compatibility-and-limitations)
- [Architecture and module boundaries (maintainer view)](#architecture-and-module-boundaries-maintainer-view)
  - [Modules and responsibilities](#modules-and-responsibilities)
  - [Dependency direction](#dependency-direction)
  - [Data flow (one run cycle)](#data-flow-one-run-cycle)
  - [Persistence layout](#persistence-layout)
  - [Extension seams](#extension-seams)
  - [Test layout](#test-layout)
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
  restarts with a strict deserialization whitelist enabled by default;
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
- Illegal moves raise `WorkTransitionError` with zero side effects;
- Terminal states (`completed/failed/cancelled`) reject every transition;
- The `running -> queued` recovery edge is for interrupted reruns only.

### Full example: accept→execute→complete

```python
from pathlib import Path

from spawn_join_personal_assistant import WorkStatus, WorkStore

with WorkStore(Path("data/work.db")) as store:
    # Accept (caller provides the idempotency key)
    item = store.accept(
        "organize this week's invoices into a table",
        idempotency_key="invoices-week-47",
        due_at="2026-11-24T09:00:00+00:00",
        deadline_seconds=120.0,
    )
    print(f"accepted: {item.id} status={item.status}")

    # Start (attempts increments)
    running = store.mark(item.id, WorkStatus.RUNNING, increment_attempt=True)
    print(f"running: attempts={running.attempts}")

    # Needs approval → pause
    waiting = store.mark(item.id, WorkStatus.WAITING_APPROVAL, thread_id="t-47")
    print(f"paused: status={waiting.status} thread={waiting.thread_id}")

    # Approved → resume
    resumed = store.mark(waiting.id, WorkStatus.RUNNING)
    print(f"resumed: status={resumed.status} attempts={resumed.attempts}")

    # Complete (persist the result summary)
    done = store.mark(
        resumed.id, WorkStatus.COMPLETED, result_summary="12 invoices filed"
    )
    print(f"done: {done.result_summary}")
```

Output:

```text
accepted: 3a8f… status=WorkStatus.QUEUED
running: attempts=1
paused: status=WorkStatus.WAITING_APPROVAL thread=t-47
resumed: status=WorkStatus.RUNNING attempts=1
done: 12 invoices filed
```

### Idempotency key replay

```python
from pathlib import Path

from spawn_join_personal_assistant import HostStoreError, WorkStore

with WorkStore(Path("data/work.db")) as store:
    first = store.accept("task A", idempotency_key="key-1")

    # Replay the same key → stable error, no second item
    try:
        store.accept("task B", idempotency_key="key-1")
    except HostStoreError as exc:
        print(f"replay rejected: {exc}")  # idempotency_key: already exists: key-1

    # The original item is untouched
    assert store.get(first.id) == first
    assert store.count_by_status(WorkStatus.QUEUED) == 1
```

### Illegal transition rejection

```python
from pathlib import Path

import pytest

from spawn_join_personal_assistant import WorkStatus, WorkStore, WorkTransitionError

with WorkStore(Path("data/work.db")) as store:
    item = store.accept("task A", idempotency_key="key-1")

    # queued -> completed is illegal (must go through running)
    with pytest.raises(WorkTransitionError, match="illegal transition"):
        store.mark(item.id, WorkStatus.COMPLETED)

    # The original item is unchanged (zero side effects)
    assert store.get(item.id) == item

    # Terminal states reject every transition
    running = store.mark(item.id, WorkStatus.RUNNING)
    failed = store.mark(running.id, WorkStatus.FAILED, failure_category="timeout")
    for target in WorkStatus:
        if target is not failed.status:
            with pytest.raises(WorkTransitionError):
                store.mark(failed.id, target)
```

### Data survives restart

```python
from pathlib import Path

from spawn_join_personal_assistant import WorkStatus, WorkStore

db_path = Path("data/work.db")

# First "process": write items
with WorkStore(db_path) as store:
    store.accept("task A", idempotency_key="key-a")
    store.accept("task B", idempotency_key="key-b")
    store.accept("task C", idempotency_key="key-c")

# Simulate a hard kill: task B left in RUNNING
with WorkStore(db_path) as store:
    item_b = store.get_by_idempotency_key("key-b")
    store.mark(item_b.id, WorkStatus.RUNNING)

# Second "process" restarts → data intact, schema idempotent
with WorkStore(db_path) as store:
    unfinished = store.pending_recovery()
    # 2 queued + 1 running = 3 unfinished
    assert len(unfinished) == 3

    # Full history is queryable
    all_items = store.list_all()
    assert len(all_items) == 3
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
| Executor exception | Lands as `failed` with the exception class name; **sibling items keep running** |
| Executor incomplete | Lands as `failed` with category `executor_incomplete` (contract backstop) |
| Parent cancellation | Running item is requeued (`running -> queued`) and `CancelledError` propagates |
| Restart recovery | `recover_interrupted()` requeues RUNNING items exactly once |

The executor contract (`WorkExecutor`): an async callable receiving the
RUNNING item that **persists its own final state**; the scheduler verifies
the contract by reading back the stored outcome.

### Example 1: basic cycle

```python
import asyncio
from pathlib import Path

from spawn_join_personal_assistant import Scheduler, WorkStatus, WorkStore

async def main() -> None:
    with WorkStore(Path("data/work.db")) as store:
        for i in range(4):
            store.accept(f"task {i}", idempotency_key=f"key-{i}")

        async def execute(item) -> None:
            store.mark(item.id, WorkStatus.COMPLETED, result_summary=f"done {item.goal}")

        scheduler = Scheduler(store, max_concurrency=2)
        outcomes = await scheduler.run_due(execute)
        print(f"{len(outcomes)} item(s) completed")

asyncio.run(main())
# Output: 4 item(s) completed
```

### Example 2: deadline expiry

```python
import asyncio
from pathlib import Path

from spawn_join_personal_assistant import Scheduler, WorkStatus, WorkStore

async def main() -> None:
    with WorkStore(Path("data/work.db")) as store:
        store.accept("slow task", idempotency_key="slow")
        store.accept("fast task", idempotency_key="fast")

        async def execute(item) -> None:
            if item.idempotency_key == "slow":
                await asyncio.sleep(10)  # exceeds the deadline
            store.mark(item.id, WorkStatus.COMPLETED)

        scheduler = Scheduler(store, max_concurrency=1, deadline_seconds=0.1)
        outcomes = await scheduler.run_due(execute)

        for o in outcomes:
            if o.status is WorkStatus.FAILED:
                print(f"{o.idempotency_key}: failed({o.failure_category})")
            else:
                print(f"{o.idempotency_key}: {o.status.value}")

asyncio.run(main())
# Output:
# slow: failed(deadline)
# fast: completed
```

### Example 3: executor exception (siblings unaffected)

```python
import asyncio
from pathlib import Path

from spawn_join_personal_assistant import Scheduler, WorkStatus, WorkStore

async def main() -> None:
    with WorkStore(Path("data/work.db")) as store:
        store.accept("crashing task", idempotency_key="bad")
        store.accept("normal task", idempotency_key="good")

        async def execute(item) -> None:
            if item.idempotency_key == "bad":
                raise ValueError("something broke")
            store.mark(item.id, WorkStatus.COMPLETED, result_summary="ok")

        scheduler = Scheduler(store, max_concurrency=2)
        outcomes = await scheduler.run_due(execute)

        # bad → failed(ValueError), good → completed, siblings unaffected
        by_key = {o.idempotency_key: o for o in outcomes}
        assert by_key["bad"].status is WorkStatus.FAILED
        assert by_key["bad"].failure_category == "ValueError"
        assert by_key["good"].status is WorkStatus.COMPLETED

asyncio.run(main())
```

### Example 4: hard-kill recovery

```python
import asyncio
from pathlib import Path

from spawn_join_personal_assistant import Scheduler, WorkStatus, WorkStore

async def main() -> None:
    db = Path("data/work.db")

    # First "process": task started then hard-killed (left RUNNING)
    with WorkStore(db) as store:
        item = store.accept("long task", idempotency_key="long")
        store.mark(item.id, WorkStatus.RUNNING, increment_attempt=True)
        # ... process killed, no further mark

    # Second "process": restart, recover, rerun
    with WorkStore(db) as store:
        scheduler = Scheduler(store, max_concurrency=1)

        # Exactly-once requeue
        requeued = await scheduler.recover_interrupted()
        print(f"requeued: {len(requeued)} item(s)")
        assert requeued[0].attempts == 1  # previous attempt preserved

        # Second call is a no-op (idempotent)
        assert await scheduler.recover_interrupted() == []

        # Rerun
        async def execute(item) -> None:
            store.mark(item.id, WorkStatus.COMPLETED, result_summary="rerun done")

        outcomes = await scheduler.run_due(execute)
        final = store.get_by_idempotency_key("long")
        assert final.status is WorkStatus.COMPLETED
        assert final.attempts == 2  # 1 interrupted + 1 rerun

asyncio.run(main())
# Output: requeued: 1 item(s)
```

### Example 5: parent cancellation

```python
import asyncio
from pathlib import Path

from spawn_join_personal_assistant import Scheduler, WorkStatus, WorkStore

async def main() -> None:
    with WorkStore(Path("data/work.db")) as store:
        item = store.accept("blocking task", idempotency_key="blocked")
        started = asyncio.Event()

        async def execute(item) -> None:
            started.set()
            await asyncio.Event().wait()  # blocks forever

        scheduler = Scheduler(store, max_concurrency=1)
        task = asyncio.create_task(scheduler.run_due(execute))
        await started.wait()

        # External cancel → running item is requeued
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("CancelledError propagated")

        # Work item back to QUEUED, attempts preserved
        recovered = store.get(item.id)
        print(f"status={recovered.status} attempts={recovered.attempts}")
        assert recovered.status is WorkStatus.QUEUED

asyncio.run(main())
# Output:
# CancelledError propagated
# status=WorkStatus.QUEUED attempts=1
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
   work item to `running`, and returns the aligned `resume_batched` command;
3. `apply_decision(..., approve=False, message="...")`: records the decision,
   lands the work item as `failed(rejected)`, and returns the aligned reject
   command (**refused actions are never executed**);
4. Decided records are immutable: a second decision raises
   `HostApprovalError`.

### Full example: approve path (file written)

```python
import asyncio
from pathlib import Path
from typing import Any, cast

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command
from spawn_join_agent_deepagents import pending_interrupts

from spawn_join_personal_assistant import (
    ApprovalBook,
    AppConfig,
    WorkStatus,
    WorkStore,
)
from spawn_join_personal_assistant.approvals import (
    apply_decision,
    interrupt_actions,
    pause_for_approval,
)
from spawn_join_personal_assistant.host import open_host_session

# Offline fake model: first requests a file write, then replies "done"
# (see tests/conftest.py for the full FakeChatModel implementation)
model = FakeChatModel(
    responses=[
        AIMessage(content="", tool_calls=[{
            "name": "write_file",
            "args": {"file_path": "/notes.txt", "content": "note"},
            "id": "call-1", "type": "tool_call",
        }]),
        AIMessage(content="note written"),
    ]
)

config = AppConfig(
    data_dir=Path("data"),
    workspace_root=Path("workspace"),
    model_catalog_path=Path("model.yaml"),
)

async def main() -> None:
    with WorkStore(Path("data/work.db")) as store, \
         ApprovalBook(Path("data/approvals.db")) as book:
        item = store.accept("write a note", idempotency_key="notes-1")
        store.mark(item.id, WorkStatus.RUNNING)

        session = await open_host_session(
            config, models=make_models(model),
            interrupt_on={"write_file": True},
        )
        try:
            thread_id = "thread-notes"
            graph_config: dict[str, Any] = {
                "configurable": {"thread_id": thread_id}
            }

            # 1. Consume the FULL astream update stream (do NOT break early!)
            interrupt_found = None
            async for update in session.assembly.graph.astream(
                {"messages": [HumanMessage(content="write a note")]},
                graph_config, stream_mode="updates", version="v1",
            ):
                found = pending_interrupts(update)
                if found:
                    interrupt_found = found[0]

            # 2. Interrupt detected → pause
            assert interrupt_found is not None
            actions = interrupt_actions(interrupt_found)
            print(f"pending action: {actions[0]['name']}")

            record = pause_for_approval(
                store, book,
                work_item_id=item.id, thread_id=thread_id,
                interrupt=interrupt_found,
            )
            print(f"work item status: {store.get(item.id).status}")
            # Output: waiting_approval

            # 3. User approves → aligned resume command
            command = apply_decision(
                store, book,
                record_id=record.id, work_item_id=item.id, approve=True,
            )
            assert isinstance(command, Command)
            resumed = cast(Any, command).resume
            print(f"resume decision count: {len(resumed['decisions'])}")
            # Output: 1 (aligned with action count)

            # 4. Execute the resume → approved write actually runs
            await session.assembly.graph.ainvoke(command, graph_config)

            # The file was written to the workspace
            assert (Path("workspace") / "notes.txt").is_file()
            print(f"file content: {(Path('workspace') / 'notes.txt').read_text()}")
            # Output: note

            # Mark complete
            store.mark(item.id, WorkStatus.COMPLETED, result_summary="note written")
        finally:
            await session.aclose()

asyncio.run(main())
```

### Full example: reject path (action skipped)

```python
# ... same setup as above ...

# User rejects → lands as failed(rejected), refused action never executes
command = apply_decision(
    store, book,
    record_id=record.id, work_item_id=item.id,
    approve=False, message="not allowed",
)

# Work item is already failed
item_after = store.get(item.id)
print(f"status={item_after.status} category={item_after.failure_category}")
# Output: status=WorkStatus.FAILED category=rejected

# The refused action never executed: no file was created
assert not (Path("workspace") / "notes.txt").exists()
```

### Full example: decided records are immutable

```python
from spawn_join_personal_assistant import ApprovalBook, HostApprovalError
from spawn_join_personal_assistant.approvals import apply_decision

# ... first approve the record ...
apply_decision(store, book, record_id=record.id,
               work_item_id=item.id, approve=True)

# Attempting a second decision → stable error
try:
    apply_decision(store, book, record_id=record.id,
                   work_item_id=item.id, approve=False)
except HostApprovalError as exc:
    print(f"immutable: {exc}")
    # Output: approval record <id>: already approved
```

### Full example: pending alignment after restart

```python
from pathlib import Path
from spawn_join_personal_assistant import ApprovalBook, WorkStatus, WorkStore
from spawn_join_personal_assistant.approvals import pause_for_approval

db = Path("data")

# First "process": pause for approval then hard-kill
with WorkStore(db / "work.db") as store, \
     ApprovalBook(db / "approvals.db") as book:
    item = store.accept("task A", idempotency_key="key-1")
    store.mark(item.id, WorkStatus.RUNNING)
    record = pause_for_approval(
        store, book,
        work_item_id=item.id, thread_id="t-1",
        interrupt=some_interrupt,
    )

# Second "process": restart → pending approvals and waiting items fully aligned
with WorkStore(db / "work.db") as store, \
     ApprovalBook(db / "approvals.db") as book:
    pending = book.pending()
    assert [r.id for r in pending] == [record.id]
    assert len(pending[0].actions) == 1

    unfinished = store.pending_recovery()
    assert unfinished[0].status is WorkStatus.WAITING_APPROVAL
    assert unfinished[0].thread_id == "t-1"
    print("pending approvals and work items fully aligned after restart")
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

### Full example: assembly and resource cleanup

```python
import asyncio
from pathlib import Path

from langchain_core.messages import HumanMessage

from spawn_join_personal_assistant import AppConfig
from spawn_join_personal_assistant.host import open_host_session

config = AppConfig(
    data_dir=Path("data"),
    workspace_root=Path("workspace"),
    model_catalog_path=Path("model.yaml"),
    max_concurrency=2,
    work_deadline_seconds=None,
)

async def main() -> None:
    session = await open_host_session(
        config, models=models,
        interrupt_on={"write_file": True},
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

### Full example: custom approval gates

```python
# Which tools need human approval? Pass a different interrupt_on Mapping.

# Gate only writes (the default policy)
session = await open_host_session(
    config, models=models,
    interrupt_on={"write_file": True},
)

# Gate all file operations (reads and writes both need approval)
session = await open_host_session(
    config, models=models,
    interrupt_on={"read_file": True, "write_file": True,
                  "edit_file": True, "delete": True},
)

# Gate nothing (everything auto-executes)
session = await open_host_session(
    config, models=models,
    interrupt_on=None,
)
```

### HostSession field assertions

```python
from spawn_join_personal_assistant.host import (
    open_host_session, workspace_permissions, strict_msgpack_serializer,
)

session = await open_host_session(config, models=models)

# All assembly parameters are assertable
assert session.backend.cwd == config.workspace_root  # workspace root
assert session.spec.tools == ()                        # no shell tools by default
assert tuple(session.spec.permissions) == workspace_permissions()
assert session.spec.checkpointer is session.checkpointer

# Serializer is behaviorally equivalent to the strict version
serde = session.checkpointer.serde
assert serde.pickle_fallback is False
sample = {"kind": "host", "count": 2}
strict = strict_msgpack_serializer()
assert serde.dumps_typed(sample) == strict.dumps_typed(sample)

# Assembly report confirms the confined workspace
report = session.assembly.report
assert report.resources.backend_kind == "filesystem"
assert report.resources.permissions.allow == 1
```

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

### CLI full flow walkthrough

```powershell
# 1. Accept two tasks
PS> spawn-join-personal-assistant --root . accept "organize invoices" --key inv-1
accepted 3a8f… key=inv-1
PS> spawn-join-personal-assistant --root . accept "write weekly report" --key wk-1
accepted 9c2d… key=wk-1

# 2. Check unfinished
PS> spawn-join-personal-assistant --root . due
[queued] 3a8f… due=- organize invoices
[queued] 9c2d… due=- write weekly report
due: 2 unfinished item(s)

# 3. Run one cycle (approval-gated write pauses)
PS> spawn-join-personal-assistant --root . run
waiting_approval 3a8f…: needs human decision
completed 9c2d…: weekly report generated
run: 2 item(s) processed

# 4. Check pending approvals
PS> spawn-join-personal-assistant --root . approve --list
record abc123 work=3a8f… thread=work-3a8f… actions=write_file
approve: 1 pending record(s)

# 5. Approve → the file is actually written
PS> spawn-join-personal-assistant --root . approve --record abc123
approved 3a8f…: completed

# 6. Check final state
PS> spawn-join-personal-assistant --root . report
completed 9c2d…: weekly report generated
completed 3a8f…: invoices organized
report: 2 item(s)

# 7. Error path: duplicate idempotency key
PS> spawn-join-personal-assistant --root . accept "duplicate task" --key inv-1
personal-assistant: idempotency_key: already exists: inv-1
# exit code 1
```

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

## Architecture and module boundaries (maintainer view)

### Modules and responsibilities

| Module | Responsibility | Key invariant |
| --- | --- | --- |
| `config.py` | `AppConfig` boundary validation (paths, concurrency, deadline) | Credentials never in config; validation completes at construction |
| `errors.py` | Stable host error taxonomy | Never wraps upstream provider/framework errors |
| `work/models.py` | `WorkItem`/`WorkStatus` state machine | `transition_allowed` is the only transition authority |
| `work/store.py` | Single-writer SQLite work-item store | UNIQUE idempotency key; illegal transitions have zero side effects |
| `scheduler.py` | asyncio due scheduler | Executor exceptions never abort siblings; parent cancellation requeues, then propagates |
| `approvals.py` | HITL approval book and resume commands | Decided records are immutable; decisions align with actions in order |
| `host.py` | Supervisor assembly and host resource ownership | `build_supervisor` is the only assembly authority; the caller closes resources |
| `cli.py` | Five-subcommand entry point | Stable exit codes; `bindings` is the explicit model injection seam |

### Dependency direction

```text
cli ─┬─ host ── spawn-join-agent-deepagents (assembly) + langgraph (checkpointer)
    ├─ scheduler ── work (store/models)
    ├─ approvals ── work + spawn-join-agent-deepagents (interrupt/resume)
    └─ config / errors (shared package-wide)
```

Dependencies stay one-way: this package sits at the end of the SpawnJoin
dependency graph (apps layer) and no SpawnJoin package depends on it in
return. Assembly and model contracts belong to
[`spawn-join-agent-deepagents`](../../infra/agent-deepagents/README.md) and
[`spawn-join-llm-provider-langchain`](../../infra/llm-provider-langchain/README.md);
this package does not re-parse `model.yaml`, `.env`, or provider SDKs.

### Data flow (one run cycle)

```text
accept(goal, key) ──────────────── work_items(queued)
run:
  recover_interrupted: RUNNING -> queued (interrupted rerun, exactly once)
  pick due queued -> RUNNING (attempts+1)
  executor: consume the full astream
    ├─ interrupt hit -> approval_records(pending) + WAITING_APPROVAL
    └─ natural end ── COMPLETED (result_summary = last assistant message)
approve:
  record_decision(approved/rejected)
    ├─ approved -> RUNNING + resume_batched -> runs to completion
    └─ rejected -> FAILED(rejected); refused actions never execute
```

### Persistence layout

- `data/work.db`: the `work_items` table (UNIQUE idempotency key;
  `CREATE TABLE IF NOT EXISTS` keeps schema setup idempotent).
- `data/approvals.db`: the `approval_records` table (decided records are
  immutable; a separate database so approvals and work items never lock each
  other).
- `data/threads.db`: LangGraph thread checkpoints (strict msgpack whitelist —
  equivalent to `LANGGRAPH_STRICT_MSGPACK` without mutating the process
  environment).
- `workspace/`: the only directory tree where agent file side effects are
  legal (virtual-mode guardrails reject `..`, `~`, and absolute paths outside
  the root).

### Extension seams

- **Approval gates**: `open_host_session(interrupt_on=...)` declares which
  tools need human approval (the CLI defaults to `{"write_file": True}` —
  writes only).
- **Model injection**: `main(bindings=...)` bypasses the catalog and injects
  offline/alternative models — every test and example runs through this seam.
- **Host tools**: `SupervisorSpec.tools` stays empty by default; adding host
  tools is this package's assembly concern and must declare their approval
  policy (`interrupt_on`) at the same time.
- **Storage migration**: the three SQLite files are the persistence interface;
  the Postgres migration is seam documentation only (ADR-0015) and the runtime
  never depends on a cloud service.

### Test layout

- Unit: `test_work_store` (state machine/idempotency/recovery),
  `test_scheduler` (pickup/bounds/cancel/hard-kill recovery),
  `test_approvals` (pause/decide/restart alignment), `test_config`
  (boundary validation).
- Assembly: `test_host_assembly` (resource ownership, path guardrails, the
  strict serializer, fake-model smoke execution).
- End to end: `test_cli` (five-subcommand smoke + stable exit codes) and
  `test_e2e_offline` (US1–US4 through the real loop; side effects asserted by
  counting files inside a controlled tmpdir).
- All 60 cases run offline: no real secrets, no external services; new
  behavior needs a failing test first (see the repository `AGENTS.md`).

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
