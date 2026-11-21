"""Public file-to-native-graph behavior with offline models and real MCP calls."""

import asyncio
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from spawn_join_agent_deepagents import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    SubAgentDefinition,
    SupervisorSpec,
    build_supervisor,
)
from spawn_join_agent_deepagents.mcp import open_mcp_tools


def _call(name: str, value: str, identifier: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": {"value": value}, "id": identifier}],
    )


def test_public_context_assigns_native_tools_to_supervisor_and_worker(
    tmp_path: Path,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    server = (Path(__file__).parent / "fixtures/mcp_server.py").resolve()
    path = tmp_path / "mcp.json"
    path.write_text(
        json.dumps(
            {
                "mcpServers": {
                    name: {
                        "command": sys.executable,
                        "args": [str(server), str(tmp_path / f"{name}.pids"), name],
                    }
                    for name in ("main", "worker")
                },
                "spawnJoin": {
                    "toolsets": {
                        "supervisor": {"servers": ["main"]},
                        "researcher": {"servers": ["worker"]},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    supervisor = make_sequence_model(
        [
            _call("worker_echo_value", "forbidden-root", "root-denied"),
            _call("main_echo_value", "root-input", "root-ok"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "task",
                        "args": {"subagent_type": "researcher", "description": "Run"},
                        "id": "delegate",
                    }
                ],
            ),
            AIMessage(content="finished"),
        ]
    )
    worker = make_sequence_model(
        [
            _call("main_echo_value", "forbidden-worker", "worker-denied"),
            _call("worker_echo_value", "worker-input", "worker-ok"),
            AIMessage(content="worker finished"),
        ]
    )
    bindings = ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor),
            ModelBinding(ModelPurpose.WORKER, model=worker),
            ModelBinding(
                ModelPurpose.SUMMARIZATION, inherit_from=ModelPurpose.SUPERVISOR
            ),
        ),
    )

    async def run() -> None:
        async with open_mcp_tools(path) as mcp:
            assert mcp.report.status == "ready" and len(mcp.tools) == 2
            assembly = build_supervisor(
                SupervisorSpec(
                    models=bindings,
                    tools=mcp.tools_for("supervisor"),
                    subagents=(
                        SubAgentDefinition(
                            name="researcher",
                            description="An explicitly equipped worker.",
                            tools=mcp.tools_for("researcher"),
                        ),
                    ),
                    control_default_subagent=False,
                )
            )
            outcome = await assembly.graph.ainvoke(
                {"messages": [HumanMessage(content="Run the offline workflow")]}
            )
            messages = cast(list[BaseMessage], outcome["messages"])
            calls = {
                message.tool_call_id: message
                for message in messages
                if isinstance(message, ToolMessage)
            }
            assert calls["root-denied"].status == "error"
            assert "main:root-input" in str(calls["root-ok"].content)
            assert "worker finished" in str(calls["delegate"].content)
            for source, expected in (
                ("main", "root-input\n"),
                ("worker", "worker-input\n"),
            ):
                assert (
                    await asyncio.to_thread((tmp_path / f"{source}.calls").read_text)
                    == expected
                )
            assert messages[-1].content == "finished"

    asyncio.run(run())


def test_empty_public_context_preserves_host_module_errors(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    path.write_text('{"mcpServers": {}}', encoding="utf-8")
    host_failure = ModuleNotFoundError("host-owned-module")

    async def run() -> None:
        with pytest.raises(ModuleNotFoundError) as caught:
            async with open_mcp_tools(path) as mcp:
                assert mcp.report.status == "ready" and mcp.tools == ()
                assert mcp.tools_for("supervisor") == ()
                raise host_failure
        assert caught.value is host_failure

    asyncio.run(run())
