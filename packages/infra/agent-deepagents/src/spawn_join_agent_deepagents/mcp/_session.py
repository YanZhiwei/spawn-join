"""按服务顺序装配官方 MCP 客户端并管理资源。"""

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

    # 内部模块共享配置记录，避免新增公共类型。
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

    # 显式创建 Client，保留小数毫秒和零值禁用超时的语义。
    # 部分受支持版本的 Group.from_config 不传递 timeout。
    timeout = None if timeout_ms is None else timeout_ms / 1000
    client = Client(server.to_transport(), timeout=timeout)
    return MCPAdapter(ClientGroup({name: client}))


@asynccontextmanager
async def open_catalog(configuration: _Configuration) -> AsyncGenerator[_Catalog, None]:
    """持有适配器上下文，提供保留原始身份的原生工具。"""
    from fastmcp.client.group import ClientGroup
    from fastmcp.mcp_config import StdioMCPServer

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
            # 适配器可能克隆 Client；持有其自身上下文，让工具复用同一活动连接。
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
