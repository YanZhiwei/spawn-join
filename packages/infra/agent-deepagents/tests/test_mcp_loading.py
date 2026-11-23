"""无需真实服务的 MCP 公开快照契约测试。"""

from collections.abc import MutableMapping
from dataclasses import FrozenInstanceError, fields
from typing import cast

import pytest
from langchain_core.tools import BaseTool, tool
from spawn_join_agent_deepagents import AgentConfigurationError
from spawn_join_agent_deepagents.mcp import (
    McpCleanupError,
    McpConfigurationError,
    McpLoadError,
    McpLoadReport,
    McpServerReport,
    McpTools,
)


@tool
def hidden_tool(value: str) -> str:
    """secret-tool-description：用于检查私有工具描述的脱敏。"""
    return value


def test_reports_and_outer_collections_are_immutable_snapshots() -> None:
    report = McpLoadReport("ready", (McpServerReport("local", True, "loaded", 1),), 1)
    selected: dict[str, tuple[BaseTool, ...]] = {"supervisor": (hidden_tool,)}
    snapshot = McpTools((hidden_tool,), selected, report)
    selected.clear()
    assert snapshot.tools_for("supervisor") == (hidden_tool,)
    assert snapshot.tools == (hidden_tool,)
    assert snapshot.report.servers[0].tool_count == 1
    for attribute in fields(snapshot.report):
        with pytest.raises(FrozenInstanceError):
            setattr(snapshot.report, attribute.name, None)
    with pytest.raises(TypeError):
        # 故意写入只读映射，验证公开契约。
        cast(MutableMapping[str, tuple[BaseTool, ...]], snapshot.toolsets)["other"] = ()


def test_sensitive_tools_and_failure_causes_stay_out_of_representations() -> None:
    report = McpLoadReport(
        "degraded",
        (
            McpServerReport("healthy", True, "loaded", 1),
            McpServerReport(
                "optional", False, "failed", 0, "discover", "upstream_error"
            ),
        ),
        1,
    )
    failure = McpLoadError("optional", "discover", "upstream_error", report)
    failure.__cause__ = RuntimeError("secret-token https://private.example/mcp")
    failures = {"optional": failure}
    snapshot = McpTools((hidden_tool,), {}, report, failures)
    failures.clear()
    assert snapshot.failures["optional"] is failure
    assert failure.report is report
    assert isinstance(failure, AgentConfigurationError)
    for rendered in (str(failure), repr(failure), repr(snapshot), repr(report)):
        assert "secret-" not in rendered
        assert "private.example" not in rendered
    assert "secret-token" in str(failure.__cause__)


def test_empty_reports_and_unknown_toolsets_have_distinct_results() -> None:
    report = McpLoadReport("ready", (), 0)
    snapshot = McpTools((), {"empty": ()}, report)
    assert snapshot.tools_for("empty") == ()
    with pytest.raises(McpConfigurationError, match="unknown toolset") as caught:
        snapshot.tools_for("secret-token")
    assert "secret-token" not in str(caught.value)
    assert issubclass(McpConfigurationError, AgentConfigurationError)
    assert issubclass(McpCleanupError, AgentConfigurationError)


def test_reports_preserve_empty_success_disabled_and_unattempted_states() -> None:
    servers = (
        McpServerReport("empty", True, "loaded", 0),
        McpServerReport("disabled", True, "disabled", 0),
        McpServerReport("later", True, "not_attempted", 0),
    )
    assert tuple(item.status for item in servers) == (
        "loaded",
        "disabled",
        "not_attempted",
    )
    assert all(item.error_code is None and item.error_stage is None for item in servers)
