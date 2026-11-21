"""Exercise governed delegation through the native graph and task tool."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, cast

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from spawn_join_agent_deepagents import (
    CompiledSubAgentDefinition,
    DelegationConfiguration,
    DelegationController,
    DelegationPolicy,
    DiagnosticEvent,
    DiagnosticEventType,
    DiagnosticsConfig,
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    SupervisorAssembly,
    SupervisorSpec,
    build_supervisor,
)
from spawn_join_agent_deepagents.errors import (
    DelegationQueueFullError,
    DelegationTimeoutError,
)

# Compiled host runnables use native, extensible LangGraph state dictionaries.
GraphState = dict[str, Any]
ModelFactory = Callable[[list[AIMessage]], BaseChatModel]
Worker = Callable[[GraphState], Awaitable[GraphState]]
EventCallback = Callable[[DiagnosticEvent], None]

WAIT_SECONDS = 5
PRIVATE_DETAIL = "private-worker-detail-sk-not-a-real-key"


def _assembly(
    make_model: ModelFactory,
    controller: DelegationController,
    worker: Worker,
    on_event: EventCallback,
    call_id: str,
) -> SupervisorAssembly:
    supervisor = make_model(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "task",
                        "args": {
                            "description": "Run the bounded host worker.",
                            "subagent_type": "worker",
                        },
                        "id": call_id,
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="supervisor finished"),
        ]
    )
    return build_supervisor(
        SupervisorSpec(
            models=ModelBindings(
                catalog=None,
                bindings=(
                    ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor),
                    ModelBinding(
                        ModelPurpose.SUMMARIZATION,
                        inherit_from=ModelPurpose.SUPERVISOR,
                    ),
                ),
            ),
            control_default_subagent=False,
            subagents=(
                CompiledSubAgentDefinition(
                    name="worker",
                    description="A host-owned offline worker.",
                    runnable=RunnableLambda(worker),
                ),
            ),
            delegation=DelegationConfiguration(
                policy=controller.policy, controller=controller
            ),
            diagnostics=DiagnosticsConfig(sync_callback=on_event),
        )
    )


async def _invoke(assembly: SupervisorAssembly) -> GraphState:
    async with asyncio.timeout(WAIT_SECONDS):
        return cast(
            GraphState,
            await assembly.graph.ainvoke(
                {"messages": [HumanMessage(content="Start the bounded task.")]}
            ),
        )


def _result() -> GraphState:
    return {"messages": [AIMessage(content="host worker finished")]}


def _assert_trace(
    events: list[DiagnosticEvent],
    call_id: str,
    expected: list[DiagnosticEventType],
    *,
    error_category: str | None = None,
) -> None:
    trace = [event for event in events if event.tool_call_id == call_id]
    assert [event.event_type for event in trace] == expected
    assert all(event.subagent_name == "worker" for event in trace)
    # Native execution_info is optional; tool_call_id is the correlation key here.
    assert len({event.run_id for event in trace}) == 1
    assert trace[-1].error_category == error_category
    assert PRIVATE_DETAIL not in repr(events)


async def _assert_reusable(
    make_model: ModelFactory,
    controller: DelegationController,
) -> None:
    assert controller.active_count == controller.waiting_count == 0
    events: list[DiagnosticEvent] = []

    async def worker(_: GraphState) -> GraphState:
        return _result()

    result = await _invoke(
        _assembly(make_model, controller, worker, events.append, "call-reuse")
    )
    messages = cast(list[object], result["messages"])
    assert any(
        isinstance(message, ToolMessage)
        and message.tool_call_id == "call-reuse"
        and message.content == "host worker finished"
        for message in messages
    )
    assert isinstance(messages[-1], AIMessage)
    assert messages[-1].content == "supervisor finished"
    assert controller.active_count == controller.waiting_count == 0
    _assert_trace(
        events,
        "call-reuse",
        [
            DiagnosticEventType.DELEGATION_SELECTED,
            DiagnosticEventType.DELEGATION_STARTED,
            DiagnosticEventType.DELEGATION_COMPLETED,
        ],
    )


def test_graph_queue_rejection_preserves_the_queued_worker(
    make_sequence_model: ModelFactory,
) -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(max_concurrency=1, max_queue=1)
        )
        events: list[DiagnosticEvent] = []
        started = asyncio.Event()
        queued = asyncio.Event()
        release = asyncio.Event()
        executed: list[str] = []

        def record(event: DiagnosticEvent) -> None:
            events.append(event)
            if event.event_type == DiagnosticEventType.DELEGATION_QUEUED:
                queued.set()

        async def first(_: GraphState) -> GraphState:
            executed.append("first")
            started.set()
            await release.wait()
            return _result()

        async def waiting(_: GraphState) -> GraphState:
            executed.append("waiting")
            return _result()

        async def rejected(_: GraphState) -> GraphState:
            executed.append("rejected")
            return _result()

        first_task = asyncio.create_task(
            _invoke(_assembly(make_sequence_model, controller, first, record, "first"))
        )
        waiting_task: asyncio.Task[GraphState] | None = None
        try:
            await asyncio.wait_for(started.wait(), WAIT_SECONDS)
            waiting_task = asyncio.create_task(
                _invoke(
                    _assembly(
                        make_sequence_model, controller, waiting, record, "waiting"
                    )
                )
            )
            await asyncio.wait_for(queued.wait(), WAIT_SECONDS)
            with pytest.raises(DelegationQueueFullError):
                await _invoke(
                    _assembly(
                        make_sequence_model, controller, rejected, record, "rejected"
                    )
                )
            assert executed == ["first"]
            assert controller.active_count == controller.waiting_count == 1
            _assert_trace(
                events,
                "rejected",
                [
                    DiagnosticEventType.DELEGATION_SELECTED,
                    DiagnosticEventType.DELEGATION_REJECTED,
                ],
                error_category="delegation_queue_full",
            )
        finally:
            release.set()
            tasks = [first_task]
            if waiting_task is not None:
                tasks.append(waiting_task)
            await asyncio.gather(*tasks)

        assert executed == ["first", "waiting"]
        _assert_trace(
            events,
            "waiting",
            [
                DiagnosticEventType.DELEGATION_SELECTED,
                DiagnosticEventType.DELEGATION_QUEUED,
                DiagnosticEventType.DELEGATION_STARTED,
                DiagnosticEventType.DELEGATION_COMPLETED,
            ],
        )
        await _assert_reusable(make_sequence_model, controller)

    asyncio.run(scenario())


def test_graph_execution_deadline_cancels_worker_and_releases_slot(
    make_sequence_model: ModelFactory,
) -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(max_concurrency=1, max_queue=0, deadline_seconds=0.2)
        )
        events: list[DiagnosticEvent] = []
        entered = asyncio.Event()
        cleaned = asyncio.Event()
        never_release = asyncio.Event()

        async def worker(_: GraphState) -> GraphState:
            entered.set()
            try:
                await never_release.wait()
                return _result()
            finally:
                cleaned.set()

        with pytest.raises(DelegationTimeoutError):
            await _invoke(
                _assembly(
                    make_sequence_model, controller, worker, events.append, "slow"
                )
            )
        assert entered.is_set()
        assert cleaned.is_set()
        _assert_trace(
            events,
            "slow",
            [
                DiagnosticEventType.DELEGATION_SELECTED,
                DiagnosticEventType.DELEGATION_STARTED,
                DiagnosticEventType.DELEGATION_TIMED_OUT,
            ],
            error_category="delegation_timeout",
        )
        await _assert_reusable(make_sequence_model, controller)

    asyncio.run(scenario())


def test_graph_queue_deadline_expires_while_active_worker_cleans_up(
    make_sequence_model: ModelFactory,
) -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(max_concurrency=1, max_queue=1, deadline_seconds=0.2)
        )
        events: list[DiagnosticEvent] = []
        cleaning = asyncio.Event()
        release_cleanup = asyncio.Event()
        never_release = asyncio.Event()
        waiting_executed = False

        async def active(_: GraphState) -> GraphState:
            try:
                await never_release.wait()
                return _result()
            finally:
                cleaning.set()
                await release_cleanup.wait()

        async def waiting(_: GraphState) -> GraphState:
            nonlocal waiting_executed
            waiting_executed = True
            return _result()

        active_task = asyncio.create_task(
            _invoke(
                _assembly(
                    make_sequence_model, controller, active, events.append, "active"
                )
            )
        )
        try:
            # Host cleanup legitimately holds the slot after cancellation starts.
            await asyncio.wait_for(cleaning.wait(), WAIT_SECONDS)
            with pytest.raises(DelegationTimeoutError, match="while queued"):
                await _invoke(
                    _assembly(
                        make_sequence_model,
                        controller,
                        waiting,
                        events.append,
                        "waiting",
                    )
                )
            assert not waiting_executed
            assert controller.active_count == 1
            assert controller.waiting_count == 0
            _assert_trace(
                events,
                "waiting",
                [
                    DiagnosticEventType.DELEGATION_SELECTED,
                    DiagnosticEventType.DELEGATION_QUEUED,
                    DiagnosticEventType.DELEGATION_TIMED_OUT,
                ],
                error_category="delegation_timeout",
            )
        finally:
            release_cleanup.set()
            with pytest.raises(DelegationTimeoutError):
                await active_task

        await _assert_reusable(make_sequence_model, controller)

    asyncio.run(scenario())


@pytest.mark.parametrize("cancel_queued", [False, True], ids=["running", "queued"])
def test_graph_parent_cancellation_cleans_up_and_preserves_the_other_run(
    make_sequence_model: ModelFactory, cancel_queued: bool
) -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(max_concurrency=1, max_queue=1)
        )
        events: list[DiagnosticEvent] = []
        started = asyncio.Event()
        queued = asyncio.Event()
        release = asyncio.Event()
        cleaned = asyncio.Event()
        waiting_executed = False

        def record(event: DiagnosticEvent) -> None:
            events.append(event)
            if event.event_type == DiagnosticEventType.DELEGATION_QUEUED:
                queued.set()

        async def active(_: GraphState) -> GraphState:
            started.set()
            try:
                await release.wait()
                return _result()
            finally:
                cleaned.set()

        async def waiting(_: GraphState) -> GraphState:
            nonlocal waiting_executed
            waiting_executed = True
            return _result()

        active_task = asyncio.create_task(
            _invoke(
                _assembly(make_sequence_model, controller, active, record, "active")
            )
        )
        waiting_task: asyncio.Task[GraphState] | None = None
        try:
            await asyncio.wait_for(started.wait(), WAIT_SECONDS)
            waiting_task = asyncio.create_task(
                _invoke(
                    _assembly(
                        make_sequence_model, controller, waiting, record, "waiting"
                    )
                )
            )
            await asyncio.wait_for(queued.wait(), WAIT_SECONDS)
            cancelled = waiting_task if cancel_queued else active_task
            cancelled.cancel()
            with pytest.raises(asyncio.CancelledError):
                await cancelled
            call_id = "waiting" if cancel_queued else "active"
            middle = (
                DiagnosticEventType.DELEGATION_QUEUED
                if cancel_queued
                else DiagnosticEventType.DELEGATION_STARTED
            )
            _assert_trace(
                events,
                call_id,
                [
                    DiagnosticEventType.DELEGATION_SELECTED,
                    middle,
                    DiagnosticEventType.DELEGATION_CANCELLED,
                ],
                error_category="cancelled",
            )
        finally:
            release.set()
            tasks = [active_task]
            if waiting_task is not None:
                tasks.append(waiting_task)
            await asyncio.gather(*tasks, return_exceptions=True)

        assert cleaned.is_set()
        assert waiting_executed is not cancel_queued
        survivor = active_task if cancel_queued else waiting_task
        assert survivor is not None
        assert (await survivor)["messages"][-1].content == "supervisor finished"
        await _assert_reusable(make_sequence_model, controller)

    asyncio.run(scenario())


def test_graph_worker_failure_preserves_exception_and_redacts_diagnostics(
    make_sequence_model: ModelFactory,
) -> None:
    async def scenario() -> None:
        controller = DelegationController(
            DelegationPolicy(max_concurrency=1, max_queue=0)
        )
        events: list[DiagnosticEvent] = []
        cause = ValueError(PRIVATE_DETAIL)
        failure = RuntimeError(PRIVATE_DETAIL)

        async def worker(_: GraphState) -> GraphState:
            raise failure from cause

        with pytest.raises(RuntimeError) as caught:
            await _invoke(
                _assembly(
                    make_sequence_model, controller, worker, events.append, "failure"
                )
            )
        assert caught.value is failure
        assert caught.value.__cause__ is cause
        _assert_trace(
            events,
            "failure",
            [
                DiagnosticEventType.DELEGATION_SELECTED,
                DiagnosticEventType.DELEGATION_STARTED,
                DiagnosticEventType.DELEGATION_FAILED,
            ],
            error_category="RuntimeError",
        )
        await _assert_reusable(make_sequence_model, controller)

    asyncio.run(scenario())
