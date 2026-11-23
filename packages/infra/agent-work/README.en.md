# spawn-join-agent-work

[简体中文](README.md) | [English](README.en.md)

Reusable desktop durable-work runtime: SQLite persistence, leases/fencing, retry/backoff,
ZeroMQ wake-ups, and a long-running runner. The desktop default needs no external service;
storage and notification are ports so a Postgres/MQ service tier can be added later.

> Status: Phase 1, version `0.1.0`, Python `>=3.11`; not yet published to PyPI. See
> [ADR-0018](../../../docs/decisions/engineering/0018-agent-work-package-boundary.md) for the boundary decision.

## When to use it

Use it when:

- a desktop app needs durable background work that survives restarts;
- the host wants SQLite + local wake-ups instead of Temporal/Celery;
- replaceable storage/notification interfaces are required for a future service tier.

Do not use it for:

- exactly-once side effects (this package promises at-least-once only);
- multi-host scheduling, multi-tenancy, auth, quotas, or billing;
- a built-in Web UI, MCP server, or remote sandbox.

## Installation

Not published yet. In-repo development:

```powershell
uv lock --check --directory packages/infra/agent-work
uv sync --locked --directory packages/infra/agent-work
```

Hosts can use a local path dependency during development:

```toml
dependencies = ["spawn-join-agent-work>=0.1.0,<0.2.0"]
[tool.uv.sources]
spawn-join-agent-work = { path = "../../infra/agent-work", editable = true }
```

The only runtime dependency is `pyzmq>=27.3.0,<28` (BSD-3-Clause; bundled libzmq is
MPL-2.0). SQLite is from the standard library.

## Minimal example

```python
import asyncio
from pathlib import Path

from spawn_join_agent_work import (
    SqliteWorkStore, WorkOutcome, WorkResult, WorkRunner, WorkSpec,
)


async def main() -> None:
    store = SqliteWorkStore(Path("work.db"))
    await store.enqueue(
        WorkSpec(kind="report", payload=b"hello", idempotency_key="demo-1")
    )

    async def executor(item):
        return WorkResult(outcome=WorkOutcome.SUCCESS, summary="done")

    runner = WorkRunner(store, executor, owner="desktop-1")
    print(await runner.run_once())  # 1


asyncio.run(main())
```

Continuous mode:

```python
runner = WorkRunner(store, executor, owner="desktop-1")
stop = asyncio.Event()
task = asyncio.create_task(runner.serve(stop))
# ...
await runner.astop()   # stop claiming, release in-flight leases, close notifier, <=10s
```

`WorkRunner.serve()` is a one-shot lifecycle: after `astop()` the same runner will not start
another loop; create a new runner for a new continuous session.

`run_once()` claims and executes items serially, processing at most `limit` items,
or `claim_batch` when omitted. Cancelling it propagates cancellation and leaves
the current item `running` until lease expiry allows recovery. `serve()/astop()`
instead cancel in-flight tasks and release recoverable leases.

## Public API

| Kind | Name | Purpose |
|---|---|---|
| Models | `WorkSpec` | Enqueue definition: `kind`, `payload: bytes`, `idempotency_key`, queue/namespace/priority, available_at, deadline, max_attempts |
| Models | `WorkItem` | Persisted item: state, attempts, lease, last_error, result, timestamps |
| Models | `WorkState` / `WorkOutcome` | `queued/running/waiting/completed/failed/dead/cancelled`; executor `success/retry/fail/defer` |
| Models | `WorkLease` / `WorkResult` / `WorkEvent` | Ownership window / result / wake-up event (no business payload) |
| Policies | `RetryPolicy` / `LeasePolicy` / `ConcurrencyPolicy` | Exponential backoff, lease/heartbeat, concurrency/batch/poll |
| Ports | `WorkStore` / `Notifier` / `Clock` / `WorkExecutor` | Storage, wake-up, clock, executor |
| Adapters | `SqliteWorkStore` / `InMemoryWorkStore` / `ZmqNotifier` | Desktop default, contract-test second implementation, PUB/SUB wake-up |
| Runtime | `WorkRunner` | `run_once()` for one batch; `serve()/astop()` for continuous mode |
| Errors | `WorkError` and subclasses | Configuration, not found, conflict, lease lost, store, notifier |

`WorkStore` methods: `enqueue`, `claim`, `heartbeat`, `complete`, `fail`, `defer`, `resume`,
`cancel`, `get`, `prune`. Public signatures expose no SQL, connection, or path types.

## Semantics and invariants

- The store is the source of truth; wake-ups are best-effort and polling is the fallback.
- SQLite `claim` is atomic via `BEGIN IMMEDIATE`; one valid lease per item at a time.
- Every execution write-back (heartbeat/complete/fail/defer) must carry the matching lease token;
  stale writers are rejected (fencing). `resume`/`cancel` are host control-plane operations and
  take no token.
- Retries follow `RetryPolicy`; the effective stop is
  `min(WorkSpec.max_attempts, RetryPolicy.max_attempts)`: spec exhaustion becomes `dead`,
  an earlier policy stop becomes `failed`, and non-retryable failures become `failed`.
- `waiting` is never claimed automatically; the host must call `resume`.
- Exactly-once is not promised; executors should use the idempotency key or their own key.
- Shutdown stops claiming, cancels and awaits in-flight work, requeues released items, and is idempotent.

## Configuration and defaults

- `SqliteWorkStore(path)`: WAL, `busy_timeout=5000ms`, `schema_version=1`, creates the current
  schema on first start. **No legacy `work.db` migration** (the product has not shipped).
- `LeasePolicy(seconds=60, heartbeat_seconds=20)`; heartbeats only extend.
- `RetryPolicy(max_attempts=3, base_seconds=1, multiplier=2, jitter=0)`.
- `ConcurrencyPolicy(max_concurrency=2, claim_batch=1, poll_interval_seconds=1)`.
- `ZmqNotifier(endpoint="tcp://127.0.0.1:5559")`, payload only `work_id`/`queue`, `LINGER=0`.
  On Windows, `zmq.asyncio` needs a selector event loop; Proactor hosts should set
  `WindowsSelectorEventLoopPolicy` or use `asyncio.Runner(loop_factory=asyncio.SelectorEventLoop)`.
  With `tcp://…:0`, publish once to bind, then give peers `notifier.endpoint`.

## Errors and limitations

- `WorkConflictError`: duplicate idempotency key; `LeaseLostError`: write-back no longer owns the lease.
- `StoreError`/`NotifierError` preserve the underlying cause.
- SQLite is single-writer; multi-host sharing is unsupported; the service tier must not use SQLite.
- Phase 1 does not implement Postgres/MQ, Temporal, multi-tenancy, auth, or quotas.
- If an executor swallows cancellation, the runner logs it and stops claiming new work; the lease
  is resolved by process exit or expiry.

## Relationship to adjacent packages

- `spawn-join-agent-deepagents` assembles agents and deliberately owns no database or scheduler.
- `spawn-join-personal-assistant` composes this package with agent packages; HITL approvals stay
  in the host compatibility layer.
- Dependency direction: host → `agent-work`; this package depends on no LangChain, model, or agent package.

## Development and verification

```powershell
uv lock --check --directory packages/infra/agent-work
uv sync --locked --directory packages/infra/agent-work
uv run --directory packages/infra/agent-work pytest -q
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-work
```

Contract tests are parameterized over SQLite and InMemory; ZMQ tests use temporary/`inproc` endpoints.

## Layout

```text
src/spawn_join_agent_work/
  models.py policies.py protocols.py runner.py errors.py
  stores/   sqlite.py memory.py
  notify/   zmq.py
tests/      test_contract_store.py test_runner.py test_lease_and_fencing.py
            test_retry.py test_shutdown.py test_zmq_integration.py ...
```

Storage, notification, and executor concerns are separated from the public models/ports;
`stores/` and `notify/` are adapters, not additional public contracts.

## Versioning and releases

The current version is `0.1.0` and is not published to PyPI. A release is gated by the package
`uv.lock`, quality gate, and the PR CI 9×3 matrix; change notes live in the repository release
record rather than being copied here. Phase 1 public APIs may change with feedback.

## Ownership, versioning, and license

Maintainer: the SpawnJoin repository maintainers. The package is not published yet; version and
compatibility follow the repository release record, and Phase 1 APIs may change with feedback.
License: see [LICENSE](LICENSE) (LicenseRef-Proprietary). Contributions follow the repository
root `AGENTS.md`.
