"""按服务顺序装配官方 MCP 客户端并管理资源。"""

from __future__ import annotations

import asyncio
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

    # 内部模块共享配置记录，避免新增公共类型。
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

    # 显式创建 Client，保留小数毫秒和零值禁用超时的语义。
    # 部分受支持版本的 Group.from_config 不传递 timeout。
    timeout = None if timeout_ms is None else timeout_ms / 1000
    client = Client(server.to_transport(), timeout=timeout)
    return MCPAdapter(ClientGroup({name: client}))


async def _initialize(
    name: str,
    required: bool,
    adapter: MCPAdapter,
    member: AsyncExitStack,
    startup_timeout: float,
) -> dict[str, BaseTool] | _Failure:
    from fastmcp.client.group import ClientGroup
    from langchain.mcp import as_langchain_tool

    group = adapter.client
    assert isinstance(group, ClientGroup)
    stage: Literal["connect", "discover", "convert"] = "connect"
    try:
        async with asyncio.timeout(startup_timeout):
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
        code: Literal["timeout", "upstream_error"] = (
            "timeout" if isinstance(exc, TimeoutError) else "upstream_error"
        )
        return _Failure(McpServerReport(name, required, "failed", 0, stage, code), exc)


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
        # 原始 SDK 异常仅通过原因链供受控诊断。
        cleanup.__context__ = cause
        raise McpCleanupError("MCP service cleanup failed") from cleanup


@asynccontextmanager
async def _owned_stack() -> AsyncGenerator[AsyncExitStack, None]:
    """释放所有自有资源，保留主异常身份与原因链。"""
    resources = AsyncExitStack()
    primary: BaseException | None = None
    try:
        yield resources
    except BaseException as exc:
        primary = exc
    try:
        await resources.aclose()
    except Exception as cause:
        cleanup = McpCleanupError("MCP resource cleanup failed")
        cleanup.__cause__ = cause
        if primary is None:
            raise cleanup from cause
        # 保留加载与清理异常，避免覆盖 SDK 的多重清理异常链。
        cleanup.__context__ = primary.__cause__
        primary.__cause__ = cleanup
    if primary is not None:
        raise primary


@asynccontextmanager
async def open_catalog(configuration: _Configuration) -> AsyncGenerator[_Catalog, None]:
    """持有适配器上下文，提供保留原始身份的原生工具。"""
    tools: dict[tuple[str, str], BaseTool] = {}
    failures: dict[str, _Failure] = {}
    reports = [
        McpServerReport(
            name, name not in configuration.optional_servers, "not_attempted", 0
        )
        for name in configuration.official.mcpServers
    ]
    async with _owned_stack() as resources:
        for index, (name, server) in enumerate(
            configuration.official.mcpServers.items()
        ):
            required = reports[index].required
            if name in configuration.disabled_servers:
                reports[index] = McpServerReport(name, required, "disabled", 0)
                continue
            adapter = create_adapter(name, server, configuration.request_timeouts[name])
            async with _owned_stack() as member:
                initialized = await _initialize(
                    name, required, adapter, member, configuration.startup_timeout
                )
                if isinstance(initialized, _Failure):
                    reports[index] = initialized.report
                    if required:
                        raise _load_error(initialized, _load_report(reports))
                    await _close_failed(member, initialized.cause)
                    failures[name] = initialized
                    continue
                # 仅移交初始化完成的资源；适配器负责其内部克隆。
                resources.push_async_exit(member.pop_all())
                tools.update(
                    ((name, original), tool) for original, tool in initialized.items()
                )
                reports[index] = McpServerReport(
                    name, required, "loaded", len(initialized)
                )
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
