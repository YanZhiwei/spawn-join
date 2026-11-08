"""Build and run an offline supervisor with the three official P0 capabilities.

The example uses a temporary filesystem backend for memory/skills, a fake model
for deterministic output, and declares a remote async subagent without invoking
it. No network, credentials, or real model provider is required.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Any, cast

from deepagents import HarnessProfile
from deepagents.backends import FilesystemBackend
from fake_model import FakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from spawn_join_agent_deepagents import (
    AsyncSubAgentDefinition,
    HarnessProfileBinding,
    MemoryConfiguration,
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    ProfilesConfiguration,
    SkillsConfiguration,
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
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root)
        (root / "AGENTS.md").write_text(
            "# Agent memory\n\nReturn concise answers.\n",
            encoding="utf-8",
        )
        skill = root / "skills" / "web-research"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\n"
            "name: web-research\n"
            "description: Research a bounded question.\n"
            "---\n\n"
            "Use the available research tools and cite the result.\n",
            encoding="utf-8",
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
                backend=FilesystemBackend(root_dir=root),
                memory=MemoryConfiguration(
                    sources=("/AGENTS.md",),
                    cache_memory_prefix=False,
                ),
                skills=SkillsConfiguration(sources=("/skills",)),
                profiles=ProfilesConfiguration(
                    harness=(
                        HarnessProfileBinding(
                            "example:fake-model",
                            HarnessProfile(system_prompt_suffix="Be concise."),
                        ),
                    )
                ),
                allow_experimental_profiles=True,
                subagents=(
                    SubAgentDefinition(
                        name="researcher",
                        description="Research a bounded question.",
                        system_prompt="Return a concise result.",
                    ),
                    AsyncSubAgentDefinition(
                        name="remote-researcher",
                        description="A remote Agent Protocol worker.",
                        graph_id="research_agent",
                        url="https://example.invalid",
                    ),
                ),
                allow_experimental_async_subagents=True,
                name="coordinator",
            )
        )

        result = cast(
            dict[str, Any],
            await assembly.graph.ainvoke(
                {"messages": [HumanMessage(content="Start the research.")]}
            ),
        )

        print("Report:", assembly.report)
        print("Context:", assembly.report.context)
        print("Profiles:", assembly.report.profiles)
        print(
            "Subagents:", [(item.name, item.kind) for item in assembly.report.subagents]
        )
        for message in cast(list[Any], result["messages"]):
            print(type(message).__name__, getattr(message, "content", ""))


if __name__ == "__main__":
    asyncio.run(main())
