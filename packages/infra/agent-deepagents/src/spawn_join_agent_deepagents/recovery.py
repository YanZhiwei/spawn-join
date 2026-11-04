"""Native recovery context and boundary validation.

The package does not create or close checkpointers, stores, MCP sessions, or
sandbox resources; it only validates the identity/interrupt inputs and passes
the host's resources to the native graph.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from langchain_core.runnables import RunnableConfig

from .errors import RecoveryConfigurationError


def checkpointer_present(checkpointer: object | None) -> bool:
    """Return whether a host checkpointer is enabled."""

    return (
        checkpointer is not None
        and checkpointer is not False
        and checkpointer is not True
    )


def validate_checkpointer_value(checkpointer: object | None) -> None:
    """Reject the boolean checkpointer form unsupported by a root graph."""

    if checkpointer is True:
        raise RecoveryConfigurationError(
            "recovery: checkpointer=True is not valid for a root graph; "
            "provide a BaseCheckpointSaver"
        )


def validate_interrupt_checkpointer(
    checkpointer: object | None,
    interrupt_configured: bool,
) -> None:
    """Reject an interrupt configuration without a host checkpointer."""

    if interrupt_configured and not checkpointer_present(checkpointer):
        raise RecoveryConfigurationError(
            "recovery: interrupt_on requires a host-provided checkpointer"
        )


@dataclass(frozen=True, slots=True)
class RecoveryContext:
    """A validated thread identity that produces native LangGraph config."""

    thread_id: str

    def __post_init__(self) -> None:
        if not self.thread_id.strip():
            raise RecoveryConfigurationError("recovery.thread_id: must not be blank")

    def to_graph_config(self, **config: Any) -> RunnableConfig:
        """Return native ``configurable.thread_id`` config without invoking a graph."""

        merged: dict[str, Any] = dict(config)
        configurable = dict(cast(Mapping[str, Any], merged.get("configurable", {})))
        configurable["thread_id"] = self.thread_id
        merged["configurable"] = configurable
        return cast(RunnableConfig, merged)
