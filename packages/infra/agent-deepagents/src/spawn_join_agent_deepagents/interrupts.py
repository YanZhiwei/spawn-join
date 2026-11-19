"""Small HITL helpers around native LangGraph interrupts and resume commands.

These helpers do not approve anything themselves. They only normalize the
native interrupt shape and build the exact payload LangChain's
``HumanInTheLoopMiddleware`` expects.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, cast, runtime_checkable

from langgraph.types import Command


@dataclass(frozen=True, slots=True)
class PendingInterrupt:
    """One native interrupt, reduced to its identity and host-owned value.

    ``value`` is the raw native payload and may contain tool arguments or paths.
    Treat it as host-owned data and do not write it to logs unredacted.
    """

    id: str | None
    value: Any


@runtime_checkable
class _InterruptLike(Protocol):
    """Duck-typed native interrupt surface.

    Native LangGraph interrupts expose ``id`` and ``value`` as attributes; the
    runtime-checkable protocol keeps that shape checkable without ``getattr``.
    """

    id: object
    value: object


def _interrupt_parts(item: object) -> tuple[object, object] | None:
    """Return ``(id, value)`` for one interrupt payload, or ``None``."""

    if isinstance(item, Mapping):
        # The native payload is JSON-like host data. Narrow it explicitly so no
        # partially unknown type leaks into the normalized result.
        mapping = cast(Mapping[str, object], item)
        if "value" not in mapping:
            return None
        return mapping.get("id"), mapping["value"]
    if isinstance(item, _InterruptLike):
        return item.id, item.value
    return None


def _interrupt_items(raw: object) -> Sequence[object]:
    """Normalize a native ``__interrupt__`` value into one sequence of items."""

    if isinstance(raw, Mapping):
        return (cast(Mapping[str, object], raw),)
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
        return (raw,)
    return cast(Sequence[object], raw)


def pending_interrupts(state: Mapping[str, Any]) -> tuple[PendingInterrupt, ...]:
    """Return the interrupts from a native state/result mapping.

    Accepts a native sequence of interrupt mappings/objects, a single interrupt
    mapping/object, or no interrupts. Malformed or non-interrupt values yield an
    empty tuple instead of fabricating entries or raising.
    """

    raw: object = state.get("__interrupt__")
    if raw is None:
        return ()

    result: list[PendingInterrupt] = []
    for item in _interrupt_items(raw):
        parts = _interrupt_parts(item)
        if parts is None:
            continue
        identifier, value = parts
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
