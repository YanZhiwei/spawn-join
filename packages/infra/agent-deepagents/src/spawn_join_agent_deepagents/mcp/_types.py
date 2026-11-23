"""原生工具及启动结果的安全只读快照。"""

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
    """MCP 配置或选择无效，错误仅包含安全字段信息。"""


class McpCleanupError(AgentConfigurationError):
    """当前 MCP 上下文持有的资源释放失败。"""


@dataclass(frozen=True, slots=True)
class McpServerReport:
    """单个服务的安全启动结果；零工具也可表示成功。"""

    name: str
    required: bool
    status: Literal["loaded", "failed", "disabled", "not_attempted"]
    tool_count: int
    error_stage: _ErrorStage | None = None
    error_code: _ErrorCode | None = None


@dataclass(frozen=True, slots=True)
class McpLoadReport:
    """按配置顺序记录启动结果；ready 允许零工具，不表示持续健康。"""

    status: Literal["ready", "degraded"]
    servers: tuple[McpServerReport, ...]
    tool_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "servers", tuple(self.servers))


class McpLoadError(AgentConfigurationError):
    """安全的服务失败信息，附只读报告并单独保留原始原因。"""

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
    """工具集合外层只读；原生工具可变且仅在上下文内有效。"""

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
        """返回已有工具集，不建立连接、刷新工具或调用模型。"""
        try:
            return self.toolsets[name]
        except KeyError:
            raise McpConfigurationError("MCP selection: unknown toolset") from None
