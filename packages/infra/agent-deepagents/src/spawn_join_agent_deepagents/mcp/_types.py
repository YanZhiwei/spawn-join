"""Native tools and safe, immutable outer snapshots of one MCP startup."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal

from langchain_core.tools import BaseTool
from spawn_join_agent_deepagents.errors import AgentConfigurationError

_ErrorStage = Literal["connect", "discover", "convert"]
_ErrorCode = Literal["timeout", "upstream_error"]


class McpConfigurationError(AgentConfigurationError):
    """Invalid MCP input or selection; raisers provide only safe field context."""


class McpCleanupError(AgentConfigurationError):
    """An owned resource failed cleanup; its cause retains the raw failure.

    With a primary error, this error becomes its cause and retains the previous
    primary cause in its context, so controlled diagnostics can inspect both.
    """


@dataclass(frozen=True, slots=True)
class McpServerReport:
    """One configured service's safe startup result, including empty success."""

    name: str
    required: bool
    status: Literal["loaded", "failed", "disabled", "not_attempted"]
    tool_count: int
    error_stage: _ErrorStage | None = None
    error_code: _ErrorCode | None = None


@dataclass(frozen=True, slots=True)
class McpLoadReport:
    """Ordered startup history; ready permits zero tools and is not health monitoring."""

    status: Literal["ready", "degraded"]
    servers: tuple[McpServerReport, ...]
    tool_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "servers", tuple(self.servers))


class McpLoadError(AgentConfigurationError):
    """Safe service failure with an immutable report and separately retained cause."""

    def __init__(
        self,
        server: str,
        stage: _ErrorStage,
        code: _ErrorCode,
        report: McpLoadReport,
    ) -> None:
        super().__init__(f"MCP service {server!r}: {stage}/{code}")
        self.server = server
        self.stage = stage
        self.code = code
        self.report = report


@dataclass(frozen=True, slots=True)
class McpTools:
    """Read-only outer tool collections; native tools remain mutable and context-bound."""

    tools: tuple[BaseTool, ...] = field(repr=False)
    toolsets: Mapping[str, tuple[BaseTool, ...]] = field(repr=False)
    report: McpLoadReport
    failures: Mapping[str, McpLoadError] = field(
        default_factory=lambda: dict[str, McpLoadError](), repr=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "tools", tuple(self.tools))
        object.__setattr__(
            self,
            "toolsets",
            MappingProxyType(
                {name: tuple(tools) for name, tools in self.toolsets.items()}
            ),
        )
        object.__setattr__(self, "failures", MappingProxyType(dict(self.failures)))

    def tools_for(self, name: str) -> tuple[BaseTool, ...]:
        """Return an existing selection without connecting, refreshing or calling a model."""
        try:
            return self.toolsets[name]
        except KeyError:
            raise McpConfigurationError("MCP selection: unknown toolset") from None
