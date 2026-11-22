"""按配置加载 MCP 工具，由宿主上下文管理资源。"""

from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager
from importlib import import_module
from pathlib import Path

from ._types import (
    McpCleanupError,
    McpConfigurationError,
    McpLoadError,
    McpLoadReport,
    McpServerReport,
    McpTools,
)

__all__ = [
    "McpCleanupError",
    "McpConfigurationError",
    "McpLoadError",
    "McpLoadReport",
    "McpServerReport",
    "McpTools",
    "open_mcp_tools",
]


@asynccontextmanager
async def open_mcp_tools(
    path: str | Path, *, environ: Mapping[str, str] | None = None
) -> AsyncGenerator[McpTools, None]:
    """加载原生工具，并在宿主上下文内持有资源。

    使用前安装 ``mcp`` extra；工具调用和图执行须在上下文内完成。
    命名工具集由宿主显式分配。
    """
    try:
        from spawn_join_agent_deepagents.mcp._config import read_configuration
        from spawn_join_agent_deepagents.mcp._selection import select_tools
        from spawn_join_agent_deepagents.mcp._session import open_catalog

        import_module("langchain.mcp")
    except ModuleNotFoundError as exc:
        raise McpConfigurationError(
            "MCP support: install spawn-join-agent-deepagents[mcp]"
        ) from exc
    configuration = await read_configuration(path, environ=environ)
    async with open_catalog(configuration) as catalog:
        yield select_tools(
            configuration, catalog.tools, catalog.report, catalog.failures
        )
