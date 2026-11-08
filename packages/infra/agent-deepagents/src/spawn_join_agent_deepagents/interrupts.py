"""Small HITL helpers around native LangGraph interrupts and resume commands.

These helpers do not approve anything themselves. They only normalize the
native interrupt shape and build the exact payload LangChain's
``HumanInTheLoopMiddleware`` expects.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, cast

from langgraph.types import Command


@dataclass(frozen=True, slots=True)
class PendingInterrupt:
    """One native interrupt, reduced to its safe identity and value."""

    id: str | None
    value: Any


def pending_interrupts(state: Mapping[str, Any]) -> tuple[PendingInterrupt, ...]:
    """Return the interrupts from a native state/result mapping."""

    raw = state.get("__interrupt__", ())
    result: list[PendingInterrupt] = []
    for item in raw:
        if isinstance(item, Mapping):
            data = cast("Mapping[str, Any]", item)
            identifier = data.get("id")
            value = data.get("value")
        else:
            identifier = getattr(item, "id", None)
            value = getattr(item, "value", item)
        result.append(
            PendingInterrupt(
                id=str(identifier) if identifier is not None else None,
                value=value,
            )
        )
    return tuple(result)


def approve_decision() -> dict[str, Any]:
    """Build a native HITL approve decision."""

    return {"type": "approve"}


def edit_decision(name: str, args: Mapping[str, Any]) -> dict[str, Any]:
    """Build a native HITL edit decision for one tool call."""

    return {
        "type": "edit",
        "edited_action": {"name": name, "args": dict(args)},
    }


def reject_decision(message: str | None = None) -> dict[str, Any]:
    """Build a native HITL reject decision."""

    decision: dict[str, Any] = {"type": "reject"}
    if message is not None:
        decision["message"] = message
    return decision


def respond_decision(message: str) -> dict[str, Any]:
    """Build a native HITL respond decision (skip execution, return text)."""

    return {"type": "respond", "message": message}


def resume_batched(
    decisions: Sequence[Mapping[str, Any]],
) -> Command[Any]:
    """Resume a batched interrupt with one decision per action request."""

    return Command(resume={"decisions": [dict(item) for item in decisions]})


def resume_per_call(
    answers: Mapping[str, Mapping[str, Any]],
) -> Command[Any]:
    """Resume per-call interrupts keyed by the native interrupt id."""

    return Command(resume={key: dict(value) for key, value in answers.items()})


def resume_with(payload: Any) -> Command[Any]:
    """Resume with an already-built native payload."""

    return Command(resume=payload)
