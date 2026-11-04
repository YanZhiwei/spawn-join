"""Run governed delegation with redacted lifecycle diagnostics offline."""

from __future__ import annotations

import asyncio
from typing import Any, cast

from fake_model import FakeChatModel
from langchain_core.messages import AIMessage, HumanMessage

from spawn_join_agent_deepagents import (
    DelegationConfiguration,
    DelegationPolicy,
    DiagnosticEvent,
    DiagnosticsConfig,
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    SubAgentDefinition,
    SupervisorSpec,
    build_supervisor,
)


def _task_call() -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "task",
                "args": {
                    "description": "Research the topic.",
                    "subagent_type": "researcher",
                },
                "id": "call-researcher",
                "type": "tool_call",
            }
        ],
    )


async def main() -> None:
    events: list[str] = []

    def on_event(event: DiagnosticEvent) -> None:
        events.append(
            f"{event.event_type.value}:{event.subagent_name}:"
            f"{event.outcome}"
        )

    supervisor = FakeChatModel(
        responses=[
            _task_call(),
            AIMessage(content="The supervisor's final answer."),
        ]
    )
    worker = FakeChatModel(responses=[AIMessage(content="research result")])
    models = ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor),
            ModelBinding(ModelPurpose.WORKER, model=worker),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )
    assembly = build_supervisor(
        SupervisorSpec(
            models=models,
            name="coordinator",
            subagents=(
                SubAgentDefinition(
                    name="researcher",
                    description="Research a bounded question.",
                ),
            ),
            delegation=DelegationConfiguration(
                policy=DelegationPolicy(
                    max_concurrency=1,
                    max_queue=1,
                    deadline_seconds=30,
                )
            ),
            diagnostics=DiagnosticsConfig(sync_callback=on_event),
        )
    )

    result = cast(
        dict[str, Any],
        await assembly.graph.ainvoke(
            {"messages": [HumanMessage(content="Start the research.")]}
        ),
    )
    print("Report:", assembly.report)
    print("Events:", events)
    print(
        "Final:",
        [
            getattr(message, "content", "")
            for message in cast(list[Any], result["messages"])
        ],
    )


if __name__ == "__main__":
    asyncio.run(main())
