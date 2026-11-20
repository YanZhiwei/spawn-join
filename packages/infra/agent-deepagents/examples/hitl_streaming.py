"""Stream a batched HITL request and resume with offline demo decisions."""

from __future__ import annotations

import asyncio
from typing import Any, cast

from fake_model import FakeChatModel
from langchain.agents.middleware.human_in_the_loop import HITLRequest
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from spawn_join_agent_deepagents import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    PendingInterrupt,
    RecoveryContext,
    SupervisorSpec,
    approve_decision,
    build_supervisor,
    pending_interrupts,
    reject_decision,
    resume_batched,
)


async def main() -> None:
    executed_values: list[str] = []

    @tool
    def record_value(value: str) -> str:
        """Record a value in memory for this example."""
        executed_values.append(value)
        return f"Recorded {value}."

    model = FakeChatModel(
        responses=[
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
    assembly = build_supervisor(
        SupervisorSpec(
            models=ModelBindings(
                catalog=None,
                bindings=(
                    ModelBinding(ModelPurpose.SUPERVISOR, model=model),
                    ModelBinding(
                        ModelPurpose.SUMMARIZATION,
                        inherit_from=ModelPurpose.SUPERVISOR,
                    ),
                ),
            ),
            control_default_subagent=False,
            tools=(record_value,),
            interrupt_on={"record_value": True},
            checkpointer=InMemorySaver(),
        )
    )
    config = RecoveryContext("hitl-demo").to_graph_config()

    pending: list[PendingInterrupt] = []
    async for update in assembly.graph.astream(
        {"messages": [HumanMessage(content="Review two values.")]},
        config=config,
        stream_mode="updates",
        version="v1",
    ):
        pending.extend(pending_interrupts(update))

    (interruption,) = pending
    requests = cast(HITLRequest, interruption.value)["action_requests"]
    values = [request["args"]["value"] for request in requests]
    print("Pending actions:", values)
    print("Executed before review:", executed_values)

    # The two fixed decisions stand in for a reviewer's response in this demo.
    decisions = {
        "keep": approve_decision(),
        "skip": reject_decision("Skip this value."),
    }
    command = resume_batched([decisions[value] for value in values])
    result = cast(dict[str, Any], await assembly.graph.ainvoke(command, config=config))
    print("Executed after resume:", executed_values)
    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
