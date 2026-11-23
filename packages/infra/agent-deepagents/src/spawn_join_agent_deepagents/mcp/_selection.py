"""基于启动快照选择原生工具，不产生外部副作用。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from langchain_core.tools import BaseTool
from spawn_join_agent_deepagents.mcp._types import (
    McpConfigurationError,
    McpLoadError,
    McpLoadReport,
    McpTools,
)

if TYPE_CHECKING:
    # 复用内部配置记录，避免新增公共类型。
    from spawn_join_agent_deepagents.mcp._config import (
        _Configuration,  # pyright: ignore[reportPrivateUsage]
    )

_Identity = tuple[str, str]


def select_tools(
    configuration: _Configuration,
    catalog: Mapping[_Identity, BaseTool],
    report: McpLoadReport,
    failures: Mapping[str, McpLoadError],
) -> McpTools:
    """按原始服务和工具身份选择，不调用工具或分配宿主角色。"""
    positions = {
        name: index for index, name in enumerate(configuration.official.mcpServers)
    }
    ordered = sorted(
        catalog, key=lambda origin: (positions[origin[0]], catalog[origin].name)
    )
    tools = tuple(catalog[origin] for origin in ordered)
    if len({tool.name for tool in tools}) != len(tools):
        raise McpConfigurationError("MCP selection: duplicate public tool name")

    toolsets: dict[str, tuple[BaseTool, ...]] = {"supervisor": tools}
    if configuration.toolsets is not None:
        toolsets = {}
        failed_optional = {
            row.name
            for row in report.servers
            if row.status == "failed" and not row.required
        }
        for label, selection in configuration.toolsets.items():
            requested = set(selection.tools)
            requested.update(
                origin for origin in ordered if origin[0] in selection.servers
            )
            if any(
                origin not in catalog and origin[0] not in failed_optional
                for origin in requested
            ):
                raise McpConfigurationError("MCP selection: unknown tool reference")
            toolsets[label] = tuple(
                catalog[origin] for origin in ordered if origin in requested
            )
    return McpTools(tools, toolsets, report, failures)
