"""Recovery identity, resource ownership, and native interrupt/resume tests."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, cast

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command, interrupt
from spawn_join_agent_deepagents.errors import RecoveryConfigurationError
from spawn_join_agent_deepagents.models import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
)
from spawn_join_agent_deepagents.recovery import (
    RecoveryContext,
    validate_interrupt_checkpointer,
)
from spawn_join_agent_deepagents.supervisor import (
    SupervisorSpec,
    build_supervisor,
)


def _bindings(supervisor: BaseChatModel) -> ModelBindings:
    return ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )


@tool
def approval_tool(value: str) -> str:
    """Pause for a host decision and return it."""

    decision = interrupt({"value": value})
    return f"approved:{decision}"


@tool
def strict_approval_tool(value: str) -> str:
    """Reject a resume decision other than ``yes``."""

    decision = interrupt({"value": value})
    if decision != "yes":
        raise ValueError("invalid decision")
    return "approved"


def test_recovery_context_builds_native_config() -> None:
    config = cast(
        dict[str, Any],
        RecoveryContext("thread-1").to_graph_config(
            tags=["test"],
            configurable={"checkpoint_ns": "ns"},
        ),
    )

    assert config["configurable"]["thread_id"] == "thread-1"
    assert config["configurable"]["checkpoint_ns"] == "ns"
    assert config["tags"] == ["test"]


def test_blank_thread_id_is_rejected() -> None:
    with pytest.raises(RecoveryConfigurationError, match="thread_id"):
        RecoveryContext("   ")


def test_interrupt_requires_a_checkpointer() -> None:
    with pytest.raises(RecoveryConfigurationError, match="checkpointer"):
        validate_interrupt_checkpointer(None, True)

    with pytest.raises(RecoveryConfigurationError, match="checkpointer"):
        validate_interrupt_checkpointer(False, True)

    validate_interrupt_checkpointer(object(), True)
    validate_interrupt_checkpointer(None, False)
    validate_interrupt_checkpointer(False, False)


def test_native_interrupt_and_resume_with_host_checkpointer(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "approval_tool",
                        "args": {"value": "x"},
                        "id": "call-approval",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="final answer"),
        ]
    )
    checkpointer = InMemorySaver()
    store = InMemoryStore()
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor),
            tools=(approval_tool,),
            checkpointer=checkpointer,
            store=store,
            name="coordinator",
        )
    )
    config = RecoveryContext("thread-1").to_graph_config()

    first = cast(
        dict[str, Any],
        asyncio.run(
            assembly.graph.ainvoke(
                {"messages": [HumanMessage(content="start")]},
                config=config,
            )
        ),
    )
    assert "__interrupt__" in first

    resumed = cast(
        dict[str, Any],
        asyncio.run(assembly.graph.ainvoke(Command(resume="yes"), config=config)),
    )
    contents = [
        str(getattr(message, "content", ""))
        for message in cast(list[Any], resumed["messages"])
    ]

    assert any("approved:yes" in content for content in contents)
    assert any("final answer" in content for content in contents)
    assert assembly.report.resources.checkpointer == "host"
    assert assembly.report.resources.store == "host"
    assert assembly.report.resources.thread_id_required is False

    state = asyncio.run(assembly.graph.aget_state(config))
    assert state.values


def test_invalid_resume_surfaces_a_native_error(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    supervisor = make_sequence_model(
        [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "strict_approval_tool",
                        "args": {"value": "x"},
                        "id": "call-strict",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="final answer"),
        ]
    )
    assembly = build_supervisor(
        SupervisorSpec(
            models=_bindings(supervisor),
            tools=(strict_approval_tool,),
            checkpointer=InMemorySaver(),
            name="coordinator",
        )
    )
    config = RecoveryContext("thread-strict").to_graph_config()

    first = cast(
        dict[str, Any],
        asyncio.run(
            assembly.graph.ainvoke(
                {"messages": [HumanMessage(content="start")]},
                config=config,
            )
        ),
    )
    assert "__interrupt__" in first

    with pytest.raises(ValueError, match="invalid decision"):
        asyncio.run(assembly.graph.ainvoke(Command(resume="no"), config=config))
