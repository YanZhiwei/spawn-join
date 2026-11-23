"""运行本地 MCP 服务与离线 Agent 图示例。"""

import argparse
import asyncio
import json
import socket
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import cast

from fake_model import FakeChatModel
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from langchain_core.messages import AIMessage, HumanMessage
from spawn_join_agent_deepagents import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    SubAgentDefinition,
    SupervisorSpec,
    build_supervisor,
)
from spawn_join_agent_deepagents.mcp import McpTools, open_mcp_tools


def _server(name: str) -> FastMCP:
    server = FastMCP(name)

    @server.tool()
    def echo(value: str) -> str:
        """返回示例服务标识和输入。"""
        suffix = ":" + get_http_headers()["x-demo"] if name == "remote" else ""
        return f"{name}:{value}{suffix}"

    return server


def _call(name: str, arguments: dict[str, object], identifier: str) -> AIMessage:
    return AIMessage(
        content="", tool_calls=[{"name": name, "args": arguments, "id": identifier}]
    )


async def _graph(tools: McpTools) -> None:
    supervisor = FakeChatModel(
        responses=[
            _call("local_echo", {"value": "supervisor"}, "local"),
            _call(
                "task",
                {"subagent_type": "researcher", "description": "Use remote"},
                "task",
            ),
            AIMessage(content="offline workflow finished"),
        ]
    )
    worker = FakeChatModel(
        responses=[
            _call("remote_echo", {"value": "researcher"}, "remote"),
            AIMessage(content="researcher finished"),
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
    assembly = build_supervisor(
        SupervisorSpec(
            models=bindings,
            tools=tools.tools_for("supervisor"),
            subagents=(
                SubAgentDefinition(
                    name="researcher",
                    description="Use remote tools.",
                    tools=tools.tools_for("researcher"),
                ),
            ),
            control_default_subagent=False,
        )
    )
    await assembly.graph.ainvoke({"messages": [HumanMessage(content="Run the demo")]})
    sys.stdout.write("offline native graph completed\n")


async def _port(path: Path) -> int:
    async with asyncio.timeout(30):
        while True:
            try:
                value = await asyncio.to_thread(path.read_text, encoding="utf-8")
            except FileNotFoundError:
                value = ""
            if value.endswith("\n"):
                return int(value)
            await asyncio.sleep(0.02)


def _http(path: Path) -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        path.write_text(f"{port}\n", encoding="utf-8")
        asyncio.run(
            _server("remote").run_http_async(
                host="127.0.0.1", port=port, sockets=[listener], show_banner=False
            )
        )


async def main() -> None:
    script = Path(__file__).resolve()
    configuration: dict[str, object] = json.loads(
        await asyncio.to_thread(
            script.with_name("mcp.example.json").read_text, encoding="utf-8"
        )
    )
    # 示例模板来自仓库；加载器仍会在启动服务前校验生成的完整配置。
    servers = cast(dict[str, dict[str, object]], configuration["mcpServers"])
    servers["local"].update(command=sys.executable, args=[str(script), "--stdio"])
    servers["unavailable"]["command"] = sys.executable
    with TemporaryDirectory() as directory:
        ready = Path(directory) / "http.port"
        remote = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script),
            "--http-ready",
            str(ready),
            stdout=asyncio.subprocess.DEVNULL,
        )
        try:
            port = await _port(ready)
            servers["remote"]["url"] = f"http://127.0.0.1:{port}/mcp"
            path = Path(directory) / "mcp.json"
            await asyncio.to_thread(
                path.write_text, json.dumps(configuration), encoding="utf-8"
            )
            async with open_mcp_tools(
                path, environ={"MCP_DEMO_LABEL": "offline"}
            ) as tools:
                assert (
                    tools.report.status == "degraded" and tools.report.tool_count == 2
                )
                assert tools.tools_for("empty") == ()
                sys.stdout.write(f"{tools.report}\n")
                for role in ("supervisor", "researcher"):
                    response = await tools.tools_for(role)[0].ainvoke(
                        {"value": "direct"}
                    )
                    assert (
                        "local:direct"
                        if role == "supervisor"
                        else "remote:direct:offline"
                    ) in str(response)
                    sys.stdout.write(f"{role} {response}\n")
                await _graph(tools)
            assert remote.returncode is None, "helper stopped a host-owned HTTP server"
        finally:
            if remote.returncode is None:
                remote.terminate()
            await remote.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--stdio", action="store_true", help="Run the local demo peer.")
    mode.add_argument(
        "--http-ready", type=Path, help="Run the host-owned HTTP demo peer."
    )
    arguments = parser.parse_args()
    if arguments.stdio:
        _server("local").run(transport="stdio", show_banner=False)
    elif arguments.http_ready:
        _http(arguments.http_ready)
    else:
        asyncio.run(main())
