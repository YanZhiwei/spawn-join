"""Contracts for governed async delegation."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, cast

import pytest
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from spawn_join_agent_deepagents.errors import (
    AgentConfigurationError,
    DelegationQueueFullError,
    DelegationTimeoutError,
    UnsupportedSyncDelegationError,
)
from spawn_join_agent_deepagents.execution import (
    DelegationConfiguration,
    DelegationController,
    DelegationPolicy,
    DelegationPolicyMiddleware,
)


async def _wait_until(predicate: Callable[[], bool]) -> None:
    for _ in range(200):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("condition was not reached")


def test_policy_validation() -> None:
    with pytest.raises(AgentConfigurationError, match="max_concurrency"):
        DelegationPolicy(max_concurrency=0, max_queue=0)

    with pytest.raises(AgentConfigurationError, match="max_queue"):
        DelegationPolicy(max_concurrency=1, max_queue=-1)

    with pytest.raises(AgentConfigurationError, match="deadline_seconds"):
        DelegationPolicy(max_concurrency=1, max_queue=0, deadline_seconds=0)


def test_concurrency_ceiling_and_fifo_queue() -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(max_concurrency=2, max_queue=2)
        )
        release = asyncio.Event()
        started: list[str] = []

        async def operation(name: str) -> str:
            started.append(name)
            await release.wait()
            return name

        async def run_one(name: str) -> str:
            return await controller.run(
                lambda: operation(name),
                subagent_name=name,
            )

        tasks = [asyncio.create_task(run_one(name)) for name in ("a", "b", "c")]
        await _wait_until(lambda: len(started) == 2)
        assert controller.active_count == 2
        assert controller.waiting_count == 1

        release.set()
        results = await asyncio.gather(*tasks)

        assert results == ["a", "b", "c"]
        assert started == ["a", "b", "c"]
        assert controller.active_count == 0
        assert controller.waiting_count == 0

    asyncio.run(scenario())


def test_queue_full_is_rejected() -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(max_concurrency=1, max_queue=0)
        )
        release = asyncio.Event()

        async def blocker() -> None:
            await release.wait()

        first = asyncio.create_task(controller.run(blocker, subagent_name="first"))
        await _wait_until(lambda: controller.active_count == 1)

        with pytest.raises(DelegationQueueFullError):
            await controller.run(blocker, subagent_name="second")

        release.set()
        await first
        assert controller.active_count == 0

    asyncio.run(scenario())


def test_deadline_covers_queue_wait() -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(
                max_concurrency=1,
                max_queue=1,
                deadline_seconds=0.02,
            )
        )
        # Simulate an occupied slot without a cooperative active operation so
        # the queued deadline path is deterministic.
        cast(Any, controller)._available = 0

        async def quick() -> None:
            return None

        with pytest.raises(DelegationTimeoutError, match="queued"):
            await controller.run(quick, subagent_name="queued")

        assert controller.waiting_count == 0

    asyncio.run(scenario())


def test_deadline_covers_execution() -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(
                max_concurrency=1,
                max_queue=0,
                deadline_seconds=0.02,
            )
        )

        async def slow() -> None:
            await asyncio.sleep(2)

        with pytest.raises(DelegationTimeoutError, match="deadline"):
            await controller.run(slow, subagent_name="slow")

        assert controller.active_count == 0
        assert controller.waiting_count == 0

    asyncio.run(scenario())


def test_parent_cancellation_while_queued_and_running() -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(max_concurrency=1, max_queue=1)
        )
        release = asyncio.Event()
        started = asyncio.Event()

        async def blocker() -> None:
            started.set()
            await release.wait()

        first = asyncio.create_task(controller.run(blocker, subagent_name="first"))
        await started.wait()

        queued = asyncio.create_task(
            controller.run(
                lambda: asyncio.sleep(0),
                subagent_name="queued",
            )
        )
        await _wait_until(lambda: controller.waiting_count == 1)
        queued.cancel()
        with pytest.raises(asyncio.CancelledError):
            await queued
        assert controller.waiting_count == 0

        release.set()
        await first
        assert controller.active_count == 0

        running_started = asyncio.Event()

        async def slow() -> None:
            running_started.set()
            await asyncio.sleep(10)

        running = asyncio.create_task(controller.run(slow, subagent_name="running"))
        await running_started.wait()
        running.cancel()
        with pytest.raises(asyncio.CancelledError):
            await running
        assert controller.active_count == 0

    asyncio.run(scenario())


def test_worker_failure_propagates_and_releases_slot() -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(max_concurrency=1, max_queue=0)
        )

        async def failure() -> None:
            raise ValueError("worker failed")

        with pytest.raises(ValueError, match="worker failed"):
            await controller.run(failure, subagent_name="worker")

        assert controller.active_count == 0

    asyncio.run(scenario())


def test_controller_can_be_reused_in_one_loop() -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(max_concurrency=2, max_queue=1)
        )

        async def value(number: int) -> int:
            return number

        first = await controller.run(
            lambda: value(1),
            subagent_name="first",
        )
        second = await controller.run(
            lambda: value(2),
            subagent_name="second",
        )

        assert (first, second) == (1, 2)
        assert controller.active_count == 0

    asyncio.run(scenario())


def test_controller_rejects_a_different_event_loop() -> None:
    controller = DelegationController(DelegationPolicy(max_concurrency=1, max_queue=0))

    async def value(number: int) -> int:
        return number

    assert asyncio.run(controller.run(lambda: value(1), subagent_name="first")) == 1

    with pytest.raises(RuntimeError, match="one event loop"):
        asyncio.run(controller.run(lambda: value(2), subagent_name="second"))


def test_queue_and_started_callbacks_are_ordered() -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(max_concurrency=1, max_queue=1)
        )
        release = asyncio.Event()
        events: list[str] = []

        async def blocker() -> None:
            await release.wait()

        async def queued() -> None:
            events.append("queued")

        async def started() -> None:
            events.append("started")

        first = asyncio.create_task(controller.run(blocker, subagent_name="first"))
        await _wait_until(lambda: controller.active_count == 1)

        second = asyncio.create_task(
            controller.run(
                lambda: asyncio.sleep(0),
                subagent_name="second",
                on_queued=queued,
                on_started=started,
            )
        )
        await _wait_until(lambda: controller.waiting_count == 1)
        assert events == ["queued"]

        release.set()
        await asyncio.gather(first, second)
        assert events == ["queued", "started"]

    asyncio.run(scenario())


def test_slow_queue_callback_does_not_leak_a_slot() -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(
                max_concurrency=1,
                max_queue=1,
                deadline_seconds=0.05,
            )
        )

        async def blocker() -> None:
            await asyncio.sleep(0.01)

        async def slow_queue_callback() -> None:
            await asyncio.sleep(0.1)

        async def quick() -> str:
            return "ok"

        first = asyncio.create_task(controller.run(blocker, subagent_name="first"))
        await _wait_until(lambda: controller.active_count == 1)

        with pytest.raises(DelegationTimeoutError, match="queued"):
            await controller.run(
                quick,
                subagent_name="queued",
                on_queued=slow_queue_callback,
            )

        await first
        assert controller.active_count == 0
        assert controller.waiting_count == 0
        assert await controller.run(quick, subagent_name="next") == "ok"

    asyncio.run(scenario())


def test_controller_configuration_mismatch_is_rejected() -> None:
    controller = DelegationController(DelegationPolicy(max_concurrency=1, max_queue=0))

    with pytest.raises(AgentConfigurationError, match="does not match"):
        DelegationConfiguration(
            policy=DelegationPolicy(max_concurrency=2, max_queue=0),
            controller=controller,
        )


def _request(name: str) -> ToolCallRequest:
    return cast(
        ToolCallRequest,
        SimpleNamespace(
            tool_call={
                "name": name,
                "args": {"subagent_type": "researcher"},
                "id": "call-1",
            }
        ),
    )


def _sync_handler(request: ToolCallRequest) -> ToolMessage:
    del request
    return ToolMessage(content="ok", tool_call_id="call-1")


async def _async_handler(request: ToolCallRequest) -> ToolMessage:
    return _sync_handler(request)


def test_policy_middleware_rejects_sync_task_calls() -> None:
    controller = DelegationController(DelegationPolicy(max_concurrency=1, max_queue=0))
    middleware = DelegationPolicyMiddleware(controller)

    with pytest.raises(UnsupportedSyncDelegationError, match="ainvoke"):
        middleware.wrap_tool_call(_request("task"), _sync_handler)

    message = cast(
        ToolMessage,
        middleware.wrap_tool_call(_request("other"), _sync_handler),
    )
    assert message.text == "ok"


def test_policy_middleware_async_and_non_task_paths() -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(max_concurrency=1, max_queue=0)
        )
        middleware = DelegationPolicyMiddleware(controller)

        result = await middleware.awrap_tool_call(
            _request("task"),
            _async_handler,
        )
        assert cast(ToolMessage, result).text == "ok"

        other = await middleware.awrap_tool_call(
            _request("other"),
            _async_handler,
        )
        assert cast(ToolMessage, other).text == "ok"
        assert controller.active_count == 0

    asyncio.run(scenario())
