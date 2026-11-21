"""Optional configuration-driven MCP tools, held by an explicit host context."""

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
    """Load native tools and keep owned resources valid throughout the host body.

    Install the ``mcp`` extra before activation. Call tools and agent graphs inside
    this context; the host explicitly assigns each named toolset to its consumer.
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
