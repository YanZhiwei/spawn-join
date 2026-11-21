"""Private, sequential official MCP resource composition; no public loader yet."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Mapping
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal

from langchain_core.tools import BaseTool
from spawn_join_agent_deepagents.errors import AgentConfigurationError
from spawn_join_agent_deepagents.mcp._types import (
    McpCleanupError,
    McpLoadError,
    McpLoadReport,
    McpServerReport,
)

if TYPE_CHECKING:
    from fastmcp.mcp_config import RemoteMCPServer, StdioMCPServer
    from langchain.mcp import MCPAdapter

    # Companion modules share this precise record without making it a public DTO.
    from spawn_join_agent_deepagents.mcp._config import (
        _Configuration,  # pyright: ignore[reportPrivateUsage]
    )


@dataclass(frozen=True, slots=True, repr=False)
class _Catalog:
    tools: Mapping[tuple[str, str], BaseTool]
    report: McpLoadReport
    failures: Mapping[str, McpLoadError]


@dataclass(frozen=True, slots=True, repr=False)
class _Failure:
    report: McpServerReport
    cause: Exception


def create_adapter(
    name: str, server: StdioMCPServer | RemoteMCPServer, timeout_ms: float | None
) -> MCPAdapter:
    from fastmcp import Client
    from fastmcp.client.group import ClientGroup
    from langchain.mcp import MCPAdapter

    # Explicit Client preserves fractional milliseconds and the zero-disable option
    # on supported FastMCP versions whose Group.from_config omits timeout.
    timeout = None if timeout_ms is None else timeout_ms / 1000
    client = Client(server.to_transport(), timeout=timeout)
    return MCPAdapter(ClientGroup({name: client}))


async def _initialize(
    name: str, required: bool, adapter: MCPAdapter, member: AsyncExitStack
) -> dict[str, BaseTool] | _Failure:
    from fastmcp.client.group import ClientGroup
    from langchain.mcp import as_langchain_tool

    group = adapter.client
    assert isinstance(group, ClientGroup)
    stage: Literal["connect", "discover", "convert"] = "connect"
    try:
        await member.enter_async_context(adapter)
        stage = "discover"
        discovered = await group.list_tools(cache_mode="use")
        stage = "convert"
        tools: dict[str, BaseTool] = {}
        for remote in discovered:
            tool = await as_langchain_tool(remote, group)
            route = await group.resolve_tool(tool.name)
            tools[route.upstream_name] = tool
        return tools
    except AgentConfigurationError:
        raise
    except Exception as exc:
        return _Failure(
            McpServerReport(name, required, "failed", 0, stage, "upstream_error"), exc
        )


def _load_report(reports: list[McpServerReport]) -> McpLoadReport:
    return McpLoadReport(
        "degraded" if any(item.status == "failed" for item in reports) else "ready",
        tuple(reports),
        sum(item.tool_count for item in reports),
    )


def _load_error(failure: _Failure, report: McpLoadReport) -> McpLoadError:
    server = failure.report
    assert server.error_stage is not None and server.error_code is not None
    error = McpLoadError(server.name, server.error_stage, server.error_code, report)
    error.__cause__ = failure.cause
    return error


async def _close_failed(member: AsyncExitStack, cause: BaseException) -> None:
    try:
        await member.aclose()
    except Exception as cleanup:
        # Keep both original SDK failures available only through controlled causes.
        cleanup.__context__ = cause
        raise McpCleanupError("MCP service cleanup failed") from cleanup


@asynccontextmanager
async def open_catalog(configuration: _Configuration) -> AsyncGenerator[_Catalog, None]:
    """Hold each adapter's actual context and yield original-identity native tools."""
    tools: dict[tuple[str, str], BaseTool] = {}
    failures: dict[str, _Failure] = {}
    reports = [
        McpServerReport(
            name, name not in configuration.optional_servers, "not_attempted", 0
        )
        for name in configuration.official.mcpServers
    ]
    async with AsyncExitStack() as resources:
        for index, (name, server) in enumerate(
            configuration.official.mcpServers.items()
        ):
            required = reports[index].required
            if name in configuration.disabled_servers:
                reports[index] = McpServerReport(name, required, "disabled", 0)
                continue
            adapter = create_adapter(name, server, configuration.request_timeouts[name])
            member = AsyncExitStack()
            try:
                initialized = await _initialize(name, required, adapter, member)
            except BaseException as exc:
                await _close_failed(member, exc)
                raise
            if isinstance(initialized, _Failure):
                reports[index] = initialized.report
                await _close_failed(member, initialized.cause)
                if required:
                    raise _load_error(initialized, _load_report(reports))
                failures[name] = initialized
                continue
            # Transfer only complete members; the Adapter owns its actual clone.
            resources.push_async_exit(member.pop_all())
            tools.update(
                ((name, original), tool) for original, tool in initialized.items()
            )
            reports[index] = McpServerReport(name, required, "loaded", len(initialized))
        report = _load_report(reports)
        yield _Catalog(
            MappingProxyType(tools),
            report,
            MappingProxyType(
                {
                    name: _load_error(failure, report)
                    for name, failure in failures.items()
                }
            ),
        )
