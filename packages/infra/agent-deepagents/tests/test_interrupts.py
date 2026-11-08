"""HITL interrupt and resume helper contracts."""

from __future__ import annotations

from dataclasses import dataclass

from spawn_join_agent_deepagents.interrupts import (
    PendingInterrupt,
    approve_decision,
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
