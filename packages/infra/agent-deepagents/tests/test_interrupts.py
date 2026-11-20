"""HITL helper contracts and native streaming recovery."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Literal, cast

import pytest
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.agents.middleware.human_in_the_loop import (
    HITLRequest,
    InterruptOnConfig,
    ToolApprovalRequest,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from spawn_join_agent_deepagents import (
    MiddlewareConfiguration,
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    PendingInterrupt,
    RecoveryContext,
    SupervisorSpec,
    approve_decision,
    build_supervisor,
    edit_decision,
    pending_interrupts,
    reject_decision,
    respond_decision,
    resume_batched,
    resume_per_call,
    resume_with,
)


@dataclass
class _Interrupt:
    id: str
    value: object


def test_pending_interrupts_reads_mapping_and_object_shapes() -> None:
    state = {
        "__interrupt__": (
            {"id": "a", "value": {"type": "tool_approval"}},
            _Interrupt(id="b", value={"decisions": []}),
        )
    }

    values = pending_interrupts(state)

    assert values == (
        PendingInterrupt(id="a", value={"type": "tool_approval"}),
        PendingInterrupt(id="b", value={"decisions": []}),
    )


def test_pending_interrupts_accepts_single_mapping_or_object() -> None:
    mapping_state = {"__interrupt__": {"id": "a", "value": {"type": "tool_approval"}}}
    object_state = {"__interrupt__": _Interrupt(id="b", value={"decisions": []})}

    assert pending_interrupts(mapping_state) == (
        PendingInterrupt(id="a", value={"type": "tool_approval"}),
    )
    assert pending_interrupts(object_state) == (
        PendingInterrupt(id="b", value={"decisions": []}),
    )


@pytest.mark.parametrize(
    "state",
    [
        {},
        {"__interrupt__": None},
        {"__interrupt__": ()},
        {"__interrupt__": []},
        {"__interrupt__": "not-an-interrupt"},
        {"__interrupt__": ["bad", 1, {"id": "missing-value"}]},
    ],
)
def test_pending_interrupts_ignores_missing_or_malformed_shapes(
    state: dict[str, object],
) -> None:
    assert pending_interrupts(state) == ()


def test_decision_builders_match_hitl_shape() -> None:
    assert approve_decision() == {"type": "approve"}
    assert edit_decision("send_email", {"to": "a"}) == {
        "type": "edit",
        "edited_action": {"name": "send_email", "args": {"to": "a"}},
    }
    assert reject_decision("keep") == {"type": "reject", "message": "keep"}
    assert reject_decision() == {"type": "reject"}
    assert respond_decision("done") == {"type": "respond", "message": "done"}


def test_resume_helpers_build_native_commands() -> None:
    batched = resume_batched([approve_decision(), reject_decision()])
    per_call = resume_per_call({"a": approve_decision()})
    raw = resume_with({"decisions": []})

    assert batched.resume == {"decisions": [{"type": "approve"}, {"type": "reject"}]}
    assert per_call.resume == {"a": {"type": "approve"}}
    assert raw.resume == {"decisions": []}


@pytest.mark.parametrize("mode", ["batched", "per_call"])
def test_streamed_hitl_resumes_only_the_approved_tool_call(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    mode: Literal["batched", "per_call"],
) -> None:
    executed_values: list[str] = []

    @tool
    def record_value(value: str) -> str:
        """Record a value so the test can observe tool execution."""
        executed_values.append(value)
        return f"Recorded {value}."

    model = make_sequence_model(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "record_value",
                        "args": {"value": value},
                        "id": f"record-{value}",
                        "type": "tool_call",
                    }
                    for value in ("keep", "skip")
                ],
            ),
            AIMessage(content="Review complete."),
        ]
    )
    interrupt_on: dict[str, bool | InterruptOnConfig] | None = {"record_value": True}
    middleware = MiddlewareConfiguration()
    if mode == "per_call":
        middleware = MiddlewareConfiguration(
            supervisor=(
                HumanInTheLoopMiddleware(interrupt_on, interrupt_mode="per_call"),
            ),
        )
        interrupt_on = None

    assembly = build_supervisor(
        SupervisorSpec(
            models=ModelBindings(
                catalog=None,
                bindings=(
                    ModelBinding(ModelPurpose.SUPERVISOR, model=model),
                    ModelBinding(
                        ModelPurpose.SUMMARIZATION, inherit_from=ModelPurpose.SUPERVISOR
                    ),
                ),
            ),
            control_default_subagent=False,
            tools=(record_value,),
            checkpointer=InMemorySaver(),
            interrupt_on=interrupt_on,
            middleware=middleware,
        )
    )
    config = RecoveryContext("approval-stream").to_graph_config()

    async def scenario() -> None:
        pending: list[PendingInterrupt] = []
        async for update in assembly.graph.astream(
            {"messages": [HumanMessage(content="Review two values.")]},
            config=config,
            stream_mode="updates",
            version="v1",
        ):
            pending.extend(pending_interrupts(update))
        assert executed_values == []

        if mode == "batched":
            (interruption,) = pending
            requests = cast(HITLRequest, interruption.value)["action_requests"]
            requested_values = [request["args"]["value"] for request in requests]
            assert requested_values == ["keep", "skip"]
            command = resume_batched([approve_decision(), reject_decision()])
        else:
            assert len(pending) == 2
            interrupt_ids: dict[str, str] = {}
            for interruption in pending:
                assert interruption.id is not None
                request = cast(ToolApprovalRequest, interruption.value)
                interrupt_ids[request["tool_call_id"]] = interruption.id
            assert set(interrupt_ids) == {"record-keep", "record-skip"}
            assert len(set(interrupt_ids.values())) == 2
            command = resume_per_call(
                {
                    interrupt_ids["record-skip"]: reject_decision(),
                    interrupt_ids["record-keep"]: approve_decision(),
                }
            )

        result = cast(
            dict[str, Any], await assembly.graph.ainvoke(command, config=config)
        )
        assert not pending_interrupts(result)
        assert result["messages"][-1].content == "Review complete."
        assert executed_values == ["keep"]

    asyncio.run(scenario())
