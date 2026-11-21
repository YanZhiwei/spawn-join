# spawn-join-agent-work

[简体中文](README.md) | [English](README.en.md)

> Status: Phase 1 skeleton (T001). Full API, examples, installation, and limitations
> are completed in later tasks.

Reusable durable work lifecycle runtime: desktop default SQLite + ZeroMQ wake-up;
public contracts can be replaced with server-side storage and message queues via
ports. Not yet released; see ADR-0017 (Proposed).

## Current scope

- Not yet wired into any host;
- Store/queue/runner are implemented in later tasks;
- The default desktop profile requires no external service;
- The service profile (Postgres/MQ) is out of Phase 1.

## Dependencies

- `pyzmq>=27.3.0,<28` is the desktop wake-up dependency; pyzmq is BSD-3-Clause and
  bundles libzmq under MPL-2.0. Supply-chain and platform-wheel assessment is
  recorded; full notes are completed by T016.

## Verification

```powershell
uv lock --check --directory packages/infra/agent-work
uv sync --locked --directory packages/infra/agent-work
uv run --directory packages/infra/agent-work pytest -q
```
