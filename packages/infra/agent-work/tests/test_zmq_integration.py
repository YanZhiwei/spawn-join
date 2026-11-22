"""ZeroMQ wake-up integration tests."""

from __future__ import annotations

import asyncio
import sys
import threading
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
import zmq.asyncio

from spawn_join_agent_work import (
    InMemoryWorkStore,
    NotifierError,
    WorkEvent,
    WorkItem,
    WorkOutcome,
    WorkResult,
    WorkRunner,
    WorkSpec,
    WorkState,
    ZmqNotifier,
)

NOW = datetime(2026, 11, 22, tzinfo=UTC)
ENDPOINT = "inproc://agent-work-t012"


def _event(work_id: str, queue: str = "default") -> WorkEvent:
    return WorkEvent(
        work_id=work_id,
        queue=queue,
        namespace="default",
        type="enqueued",
        occurred_at=NOW,
    )


def _notifier_pair() -> tuple[zmq.asyncio.Context, ZmqNotifier, ZmqNotifier]:
    context = zmq.asyncio.Context()
    return (
        context,
        ZmqNotifier(ENDPOINT, context=context),
        ZmqNotifier(ENDPOINT, context=context),
    )


def test_publish_wakes_subscriber_with_id_and_queue() -> None:
    context, publisher, subscriber = _notifier_pair()

    async def scenario() -> WorkEvent:
        await publisher.publish(_event("w1"))  # bind before inproc connect
        stream: AsyncIterator[WorkEvent] = subscriber.subscribe(["default"])
        pending = asyncio.ensure_future(anext(stream))
        await asyncio.sleep(0.05)
        await publisher.publish(_event("w1"))
        received = await asyncio.wait_for(pending, timeout=2)
        await publisher.aclose()
        await subscriber.aclose()
        return received

    try:
        with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
            received = runner.run(scenario())
    finally:
        context.destroy(linger=0)

    assert received.work_id == "w1"
    assert received.queue == "default"
    assert received.type == "wakeup"


def test_subscribe_filters_queues() -> None:
    context, publisher, subscriber = _notifier_pair()

    async def scenario() -> WorkEvent:
        await publisher.publish(_event("bind"))
        stream = subscriber.subscribe(["wanted"])
        pending = asyncio.ensure_future(anext(stream))
        await asyncio.sleep(0.05)
        await publisher.publish(_event("ignored", queue="other"))
        await publisher.publish(_event("wanted-id", queue="wanted"))
        received = await asyncio.wait_for(pending, timeout=2)
        await publisher.aclose()
        await subscriber.aclose()
        return received

    try:
        with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
            received = runner.run(scenario())
    finally:
        context.destroy(linger=0)

    assert received.work_id == "wanted-id"
    assert received.queue == "wanted"


def test_duplicate_wakeups_do_not_duplicate_execution() -> None:
    store = InMemoryWorkStore()
    item = asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    async def executor(item: WorkItem) -> WorkResult:
        return WorkResult(outcome=WorkOutcome.SUCCESS, summary="once")

    runner = WorkRunner(store, executor)

    async def scenario() -> int:
        return await runner.run_once() + await runner.run_once()

    assert asyncio.run(scenario()) == 1
    finished = asyncio.run(store.get(item.id))
    assert finished is not None
    assert finished.state is WorkState.COMPLETED


def test_two_workers_compete_for_one_item() -> None:
    store = InMemoryWorkStore()
    asyncio.run(
        store.enqueue(WorkSpec(kind="report", payload=b"{}", idempotency_key="k1"))
    )

    async def executor(item: WorkItem) -> WorkResult:
        await asyncio.sleep(0.02)
        return WorkResult(outcome=WorkOutcome.SUCCESS, summary="winner")

    first = WorkRunner(store, executor, owner="worker-1")
    second = WorkRunner(store, executor, owner="worker-2")

    async def scenario() -> int:
        processed = await asyncio.gather(first.run_once(), second.run_once())
        return sum(processed)

    assert asyncio.run(scenario()) == 1


def test_aclose_is_idempotent() -> None:
    context = zmq.asyncio.Context()
    notifier = ZmqNotifier(ENDPOINT, context=context)
    try:
        with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
            runner.run(notifier.publish(_event("w1")))
            runner.run(notifier.aclose())
            runner.run(notifier.aclose())
            with pytest.raises(NotifierError):
                runner.run(notifier.publish(_event("w2")))
            stream = notifier.subscribe(["default"])

            async def read_one() -> WorkEvent:
                return await anext(stream)

            with pytest.raises(NotifierError):
                runner.run(read_one())
    finally:
        context.destroy(linger=0)


def test_close_while_subscribed_ends_stream_without_cancelling_host() -> None:
    context, publisher, subscriber = _notifier_pair()

    async def scenario() -> None:
        await publisher.publish(_event("bind"))
        stream = subscriber.subscribe(["default"])
        pending = asyncio.ensure_future(anext(stream))
        await asyncio.sleep(0.05)
        await subscriber.aclose()
        with pytest.raises(StopAsyncIteration):
            await asyncio.wait_for(pending, timeout=2)
        await publisher.aclose()

    try:
        with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
            runner.run(scenario())
    finally:
        context.destroy(linger=0)


def test_proactor_aclose_terminates() -> None:
    if sys.platform != "win32":
        pytest.skip("Proactor loop only exists on Windows")
    notifier = ZmqNotifier("inproc://agent-work-proactor")

    async def setup() -> None:
        stream = notifier.subscribe(["default"])
        with pytest.raises(NotifierError):
            await anext(stream)

    asyncio.run(setup())

    thread = threading.Thread(
        target=lambda: asyncio.run(notifier.aclose()), daemon=True
    )
    thread.start()
    thread.join(timeout=5)
    assert not thread.is_alive()


def test_random_port_endpoint_is_reusable_by_peers() -> None:
    publisher = ZmqNotifier("tcp://127.0.0.1:0")

    async def scenario() -> str:
        await publisher.publish(_event("bind"))
        endpoint = publisher.endpoint
        subscriber = ZmqNotifier(endpoint)
        stream = subscriber.subscribe(["default"])
        pending = asyncio.ensure_future(anext(stream))
        await asyncio.sleep(0.1)
        await publisher.publish(_event("w-port"))
        received = await asyncio.wait_for(pending, timeout=2)
        await subscriber.aclose()
        await publisher.aclose()
        return received.work_id

    with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
        work_id = runner.run(scenario())

    assert work_id == "w-port"


def test_subscribe_with_empty_queue_set_ends_immediately() -> None:
    context = zmq.asyncio.Context()
    notifier = ZmqNotifier(ENDPOINT, context=context)

    async def scenario() -> None:
        stream = notifier.subscribe([])
        with pytest.raises(StopAsyncIteration):
            await anext(stream)
        await notifier.aclose()

    try:
        with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
            runner.run(scenario())
    finally:
        context.destroy(linger=0)
