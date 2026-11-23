# spawn-join-agent-work

[简体中文](README.md) | [English](README.en.md)

Reusable work lifecycle contracts and desktop adapters for SpawnJoin hosts.
Current capabilities: Models, policies and adapter ports. SQLite persistence with atomic claim and lease fencing.

## Status, scope and compatibility

Version 0.1.0, preview, Python >=3.11; not published to PyPI. Install from the repository.
Suitable for hosts composing the capabilities listed below. Desktop use needs no external service.

- Storage is available; hosts supply execution and scheduling.
- No host CLI migration, Postgres/MQ, multi-host scheduling or tenant/auth system.

## Installation and shortest example

From the repository root:

```powershell
uv lock --check --directory packages/infra/agent-work
uv sync --locked --directory packages/infra/agent-work
```

```python
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory

from spawn_join_agent_work import SqliteWorkStore, WorkSpec


async def main() -> None:
    with TemporaryDirectory() as directory:
        store = SqliteWorkStore(Path(directory) / "work.db")
        item = await store.enqueue(
            WorkSpec(kind="report", payload=b"hello", idempotency_key="demo")
        )
        assert item.spec.kind == "report"


asyncio.run(main())
```

The distribution declares pyzmq>=27.3.0,<28; SQLite uses the standard library.
No LangChain, model-provider or other SpawnJoin runtime dependency is introduced.

## Public API and defaults

Only the names in this table are exported by this version:

| Area | Exports |
| --- | --- |
| models | `WorkSpec`, `WorkItem`, `WorkState`, `WorkOutcome`, `WorkLease`, `WorkResult`, `WorkEvent` |
| policies | `RetryPolicy`, `LeasePolicy`, `ConcurrencyPolicy` |
| ports | `Clock`, `Notifier`, `WorkExecutor`, `WorkStore` |
| storage | `SqliteWorkStore` |
| errors | `WorkError`, `WorkConfigurationError`, `WorkConflictError`, `WorkNotFoundError`, `LeaseLostError`, `StoreError`, `NotifierError` |

WorkSpec accepts kind, a bytes payload and an idempotency_key. WorkState models
queued/running/waiting/completed/failed/dead/cancelled; ports define the adapter boundary.

| WorkSpec field | Type | Default |
| --- | --- | --- |
| `kind` | `str` | `required` |
| `payload` | `bytes` | `required` |
| `idempotency_key` | `str` | `required` |
| `queue` | `str` | `'default'` |
| `namespace` | `str` | `'default'` |
| `priority` | `int` | `0` |
| `available_at` | `datetime \| None` | `None` |
| `deadline_seconds` | `float \| None` | `None` |
| `max_attempts` | `int` | `3` |

WorkItem carries the spec, state, attempts, lease, last_error and result;
WorkLease carries owner/token/until. WorkResult describes the outcome with
optional summary/error/wait_until. WorkEvent is event metadata, without the business payload.
WorkStore defines enqueue/claim/heartbeat/complete/fail/defer/resume/cancel/get/prune;
Notifier defines publish/subscribe/aclose, Clock supplies now(), and WorkExecutor is async.

RetryPolicy defaults to max_attempts=3, base_seconds=1, multiplier=2, jitter=0;
LeasePolicy to seconds=60 and heartbeat_seconds=20; ConcurrencyPolicy to
max_concurrency=2, claim_batch=1 and poll_interval_seconds=1.

SQLite defaults: WAL, busy_timeout=5000ms and schema_version=1. The store owns truth; heartbeat/complete/fail/defer require the lease token. waiting is not claimed until resumed. Host control-plane resume/cancel do not require that token. No old work.db migration is provided.

## Errors and limitations

WorkConfigurationError rejects invalid contract inputs. WorkConflictError,
WorkNotFoundError and LeaseLostError identify conflict, absence and lease loss;
StoreError/NotifierError distinguish adapter failures. These all derive from WorkError.
The public ports expose no SQL, connection or filesystem path. SQLite is a
desktop adapter, unsuitable for the server tier or multi-host use.

## Ownership and architecture

Hosts depend on agent-work; agent-work owns its models, policies, ports and the
implemented adapters. Hosts own business execution and process orchestration.
Store owns truth and notifications are best effort. Boundaries are defined by
[ADR-0018](../../../docs/decisions/engineering/0018-agent-work-package-boundary.md).
[agent-deepagents](../agent-deepagents/README.en.md) owns agent assembly;
[personal-assistant](../../apps/personal-assistant/README.en.md) owns its CLI and approvals.

## Development and verification

Sources: src/spawn_join_agent_work/ (models.py / policies.py / protocols.py / errors.py / stores/); tests are in tests/.
Each distribution owns its uv.lock and .venv; the repository root is tool-only.
Use Python >=3.11, uv, PowerShell 7 and Node 22+ for the configured quality gate.

```powershell
uv run --locked --directory packages/infra/agent-work pytest -q
pwsh -NoProfile -File scripts/quality.ps1 -Package spawn-join-agent-work
```

## Versioning, maintenance and license

SpawnJoin maintainers own this package. Contributions follow [AGENTS.md](../../../AGENTS.md).
Public contracts remain preview in 0.x; publication requires package checks and
separate release authorization. Version 0.1.0 is the source version, not a release claim.
No changelog/tag is published for this unpublished package; release history belongs to repository releases.
LicenseRef-Proprietary; see [LICENSE](LICENSE).
