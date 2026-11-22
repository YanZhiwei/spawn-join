"""Minimal offline runner example.

Run from the package environment:

    uv run --directory packages/infra/agent-work python examples/minimal_runner.py

No network, database file, or external service is required.
"""

from __future__ import annotations

import asyncio

from spawn_join_agent_work import (
    InMemoryWorkStore,
    WorkItem,
    WorkOutcome,
    WorkResult,
    WorkRunner,
    WorkSpec,
)


async def executor(item: WorkItem) -> WorkResult:
    goal = item.spec.payload.decode("utf-8")
    print(f"executing {item.id}: {goal}")
    return WorkResult(outcome=WorkOutcome.SUCCESS, summary=f"handled {goal!r}")


async def main() -> None:
    store = InMemoryWorkStore()
    await store.enqueue(
        WorkSpec(
            kind="example",
            payload=b"hello from spawn-join-agent-work",
            idempotency_key="example-1",
        )
    )

    runner = WorkRunner(store, executor, owner="example-runner")
    processed = await runner.run_once()
    print(f"processed={processed}")


if __name__ == "__main__":
    asyncio.run(main())
