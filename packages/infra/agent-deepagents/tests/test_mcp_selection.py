"""验证工具选择保留原生身份、严格引用与空集语义。"""

import asyncio
import json
import sys
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import cast

import pytest
from langchain_core.tools import BaseTool, tool
from spawn_join_agent_deepagents.mcp import (
    McpConfigurationError,
    McpLoadError,
    McpLoadReport,
    McpServerReport,
    McpTools,
)
from spawn_join_agent_deepagents.mcp._config import read_configuration
from spawn_join_agent_deepagents.mcp._selection import select_tools


def _native(public_name: str) -> BaseTool:
    @tool(public_name)
    def forbidden(value: str) -> str:
        """private-tool-description：选择工具时不得读取或执行。"""
        raise AssertionError("selection called a tool")

    return forbidden


@pytest.fixture
def catalog() -> dict[tuple[str, str], BaseTool]:
    return {
        ("a", "echo_value"): _native("a_echo_value"),
        ("z", "zeta"): _native("z_zeta"),
        ("z", "alpha"): _native("z_alpha"),
    }


def _select(
    directory: Path,
    catalog: Mapping[tuple[str, str], BaseTool],
    toolsets: dict[str, object] | None = None,
    *,
    servers: tuple[str, ...] = ("z", "a"),
    optional: tuple[str, ...] = (),
    disabled: tuple[str, ...] = (),
    failed: tuple[str, ...] = (),
) -> McpTools:
    policy: dict[str, object] = {
        "optionalServers": optional,
        "disabledServers": disabled,
    }
    if toolsets is not None:
        policy["toolsets"] = toolsets
    path = directory / "mcp.json"
    path.write_text(
        json.dumps(
            {
                "mcpServers": {name: {"command": sys.executable} for name in servers},
                "spawnJoin": policy,
            }
        ),
        encoding="utf-8",
    )
    configuration = asyncio.run(read_configuration(path))
    rows: list[McpServerReport] = []
    for name in servers:
        if name in failed:
            rows.append(
                McpServerReport(name, False, "failed", 0, "connect", "upstream_error")
            )
        else:
            rows.append(
                McpServerReport(
                    name,
                    name not in optional,
                    "loaded",
                    sum(server == name for server, _ in catalog),
                )
            )
    report = McpLoadReport("degraded" if failed else "ready", tuple(rows), len(catalog))
    failures = {
        name: McpLoadError(name, "connect", "upstream_error", report) for name in failed
    }
    return select_tools(configuration, catalog, report, failures)


def test_default_union_and_canonical_order_keep_native_objects(
    tmp_path: Path, catalog: dict[tuple[str, str], BaseTool]
) -> None:
    expected = (
        catalog[("z", "alpha")],
        catalog[("z", "zeta")],
        catalog[("a", "echo_value")],
    )
    default = _select(tmp_path, catalog)
    assert default.tools == expected and default.tools_for("supervisor") == expected
    selected = _select(
        tmp_path,
        catalog,
        {
            "role": {
                "servers": ["a", "z"],
                "tools": [
                    {"server": "z", "name": "alpha"},
                    {"server": "z", "name": "alpha"},
                ],
            }
        },
    )
    assert selected.tools_for("role") == expected
    assert all(
        actual is original
        for actual, original in zip(selected.tools, expected, strict=True)
    )
    assert "private-tool-description" not in repr(selected)


def test_omitted_explicit_empty_and_named_empty_are_distinct(
    tmp_path: Path, catalog: dict[tuple[str, str], BaseTool]
) -> None:
    none = _select(tmp_path, catalog, {})
    assert none.tools and not none.toolsets
    with pytest.raises(McpConfigurationError, match="unknown toolset"):
        none.tools_for("supervisor")
    empty = _select(tmp_path, catalog, {"empty": {}})
    assert empty.tools_for("empty") == () and empty.tools == none.tools
    with pytest.raises(TypeError):
        cast(MutableMapping[str, tuple[BaseTool, ...]], empty.toolsets)["other"] = ()


def test_original_underscore_identity_selects_without_parsing_prefix(
    tmp_path: Path,
) -> None:
    native = _native("first_server_echo_value")
    selected = _select(
        tmp_path,
        {("first_server", "echo_value"): native},
        {"researcher": {"tools": [{"server": "first_server", "name": "echo_value"}]}},
        servers=("first_server",),
    )
    assert selected.tools_for("researcher") == (native,)


@pytest.mark.parametrize("optional", [(), ("a",)])
def test_unknown_tool_in_healthy_directory_is_global_configuration_error(
    tmp_path: Path, catalog: dict[tuple[str, str], BaseTool], optional: tuple[str, ...]
) -> None:
    with pytest.raises(McpConfigurationError, match="tool") as caught:
        _select(
            tmp_path,
            catalog,
            {"role": {"tools": [{"server": "a", "name": "secret-missing"}]}},
            optional=optional,
        )
    assert "secret-missing" not in str(caught.value)


def test_only_actually_failed_optional_service_can_be_absent(tmp_path: Path) -> None:
    native = _native("z_alpha")
    selected = _select(
        tmp_path,
        {("z", "alpha"): native},
        {
            "role": {
                "servers": ["a"],
                "tools": [
                    {"server": "a", "name": "absent"},
                    {"server": "z", "name": "alpha"},
                ],
            }
        },
        optional=("a",),
        failed=("a",),
    )
    assert (
        selected.tools_for("role") == (native,) and selected.report.status == "degraded"
    )
    assert selected.failures["a"].report is selected.report
    with pytest.raises(TypeError):
        cast(MutableMapping[str, McpLoadError], selected.failures)["z"] = (
            selected.failures["a"]
        )


@pytest.mark.parametrize("disabled,server", [((), "unknown"), (("a",), "a")])
def test_unknown_and_disabled_references_fail_static_validation(
    tmp_path: Path,
    catalog: dict[tuple[str, str], BaseTool],
    disabled: tuple[str, ...],
    server: str,
) -> None:
    with pytest.raises(McpConfigurationError):
        _select(tmp_path, catalog, {"role": {"servers": [server]}}, disabled=disabled)


@pytest.mark.parametrize("toolsets", [None, {}, {"empty": {}}])
def test_public_name_collision_checks_even_unselected_tools(
    tmp_path: Path, toolsets: dict[str, object] | None
) -> None:
    collision = _native("a_b_c")
    with pytest.raises(McpConfigurationError, match="collision|duplicate"):
        _select(
            tmp_path,
            {("a_b", "c"): collision, ("a", "b_c"): _native("a_b_c")},
            toolsets,
            servers=("a_b", "a"),
        )


def test_empty_success_and_failed_optional_default_sets(tmp_path: Path) -> None:
    ready = _select(tmp_path, {})
    assert ready.tools_for("supervisor") == () and ready.report.status == "ready"
    degraded = _select(tmp_path, {}, optional=("z", "a"), failed=("z", "a"))
    assert (
        degraded.tools_for("supervisor") == () and degraded.report.status == "degraded"
    )
