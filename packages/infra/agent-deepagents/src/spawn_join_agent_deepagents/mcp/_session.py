"""Private, sequential official MCP resource composition; no public loader yet."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Mapping
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from langchain_core.tools import BaseTool
from spawn_join_agent_deepagents.mcp._types import (
    McpConfigurationError,
    McpLoadReport,
    McpServerReport,
)

if TYPE_CHECKING:
    from fastmcp.mcp_config import StdioMCPServer
    from langchain.mcp import MCPAdapter

    # Companion modules share this precise record without making it a public DTO.
    from spawn_join_agent_deepagents.mcp._config import (
        _Configuration,  # pyright: ignore[reportPrivateUsage]
    )


@dataclass(frozen=True, slots=True, repr=False)
class _Catalog:
    tools: Mapping[tuple[str, str], BaseTool]
    report: McpLoadReport


def create_adapter(
    name: str, server: StdioMCPServer, timeout_ms: float | None
) -> MCPAdapter:
    from fastmcp import Client
    from fastmcp.client.group import ClientGroup
    from langchain.mcp import MCPAdapter

    # Explicit Client preserves fractional milliseconds and the zero-disable option
    # on supported FastMCP versions whose Group.from_config omits timeout.
    timeout = None if timeout_ms is None else timeout_ms / 1000
    client = Client(server.to_transport(), timeout=timeout)
    return MCPAdapter(ClientGroup({name: client}))


@asynccontextmanager
async def open_catalog(configuration: _Configuration) -> AsyncGenerator[_Catalog, None]:
    """Hold each adapter's actual context and yield original-identity native tools."""
    from fastmcp.client.group import ClientGroup
    from fastmcp.mcp_config import StdioMCPServer

    # This independently usable prefix implements only stdio; HTTP is the next task.
    for name, server in configuration.official.mcpServers.items():
        if name not in configuration.disabled_servers and not isinstance(
            server, StdioMCPServer
        ):
            raise McpConfigurationError("MCP transport: stdio required by this prefix")

    tools: dict[tuple[str, str], BaseTool] = {}
    reports: list[McpServerReport] = []
    async with AsyncExitStack() as resources:
        for name, server in configuration.official.mcpServers.items():
            required = name not in configuration.optional_servers
            if name in configuration.disabled_servers:
                reports.append(McpServerReport(name, required, "disabled", 0))
                continue
            assert isinstance(server, StdioMCPServer)
            adapter = create_adapter(name, server, configuration.request_timeouts[name])
            # The adapter may clone the Client. Hold its own context, not the input
            # Client/Group, so tool callbacks reenter the same live singleton group.
            await resources.enter_async_context(adapter)
            converted = await adapter.list_tools()
            group = adapter.client
            assert isinstance(group, ClientGroup)
            for tool in converted:
                route = await group.resolve_tool(tool.name)
                tools[(name, route.upstream_name)] = tool
            reports.append(McpServerReport(name, required, "loaded", len(converted)))
        yield _Catalog(
            MappingProxyType(tools), McpLoadReport("ready", tuple(reports), len(tools))
        )
