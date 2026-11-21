"""Strict local configuration validation must precede external effects."""

import asyncio
import json
from pathlib import Path
from typing import NoReturn

import pytest
from fastmcp import Client
from fastmcp.mcp_config import MCPConfig
from spawn_join_agent_deepagents.mcp import McpConfigurationError
from spawn_join_agent_deepagents.mcp._config import read_configuration


@pytest.fixture(autouse=True)
def no_external_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("configuration created external resources")

    monkeypatch.setattr(Client, "__init__", forbidden)
    monkeypatch.setattr("subprocess.Popen", forbidden)
    monkeypatch.setattr("socket.create_connection", forbidden)


def test_official_models_defaults_and_fractional_request_timeout(
    tmp_path: Path,
) -> None:
    path = tmp_path / "mcp.json"
    path.write_text(
        '{"mcpServers":{"local":{"command":"python","timeout":1.5},'
        '"remote":{"url":"https://example.com/mcp"}}}',
        encoding="utf-8-sig",
    )
    configuration = asyncio.run(read_configuration(path))
    assert isinstance(configuration.official, MCPConfig)
    assert list(configuration.official.mcpServers) == ["local", "remote"]
    assert configuration.request_timeouts["local"] == 1.5
    assert configuration.startup_timeout == 30
    assert not configuration.optional_servers and not configuration.disabled_servers
    assert configuration.toolsets is None
    assert "example.com" not in repr(configuration)


@pytest.mark.parametrize(
    "payload",
    [
        "[]",
        '{"local":{"command":"python"}}',
        '{"mcpServers":{},"mcpServers":{}}',
        '{"mcpServers":{}} // comment',
        '{"mcpServers":{},"spawnJoin":{"startupTimeoutSeconds":NaN}}',
        '{"mcpServers":{},"spawnJoin":{"startupTimeoutSeconds":0}}',
        '{"mcpServers":{},"spawnJoin":{"optionalServers":["missing"]}}',
        '{"mcpServers":{},"spawnJoin":{"unknown":true}}',
    ],
)
def test_invalid_file_shell_and_policy_fail_safely(
    tmp_path: Path, payload: str
) -> None:
    path = tmp_path / "mcp.json"
    path.write_text(payload, encoding="utf-8")
    with pytest.raises(McpConfigurationError):
        asyncio.run(read_configuration(path))


@pytest.mark.parametrize(
    "server",
    [
        {"command": "python", "url": "https://private.example/mcp"},
        {"command": "python", "args": [1]},
        {"command": "python", "timeout": True},
        {"command": "python", "timeout": -1},
        {"command": "python", "env": {"TOKEN": 1}},
        {"url": "ssh://private.example/mcp"},
        {"url": "https://private.example/sse"},
        {"url": "https://private.example/mcp", "headers": {"Token": 1}},
        {"url": "https://private.example/mcp", "transport": {}},
        {"url": "https://private.example:invalid/mcp"},
        {"command": "python", "secret-unknown-field": "secret-value"},
    ],
)
def test_optional_and_disabled_entries_are_statically_validated(
    tmp_path: Path, server: dict[str, object]
) -> None:
    path = tmp_path / "mcp.json"
    for policy in ({"optionalServers": ["bad"]}, {"disabledServers": ["bad"]}):
        path.write_text(
            json.dumps({"mcpServers": {"bad": server}, "spawnJoin": policy})
        )
        with pytest.raises(McpConfigurationError) as caught:
            asyncio.run(read_configuration(path))
        assert "private.example" not in str(caught.value)
        assert "secret-" not in repr(caught.value)


def test_missing_file_is_a_safe_configuration_error_with_cause(tmp_path: Path) -> None:
    with pytest.raises(McpConfigurationError) as caught:
        asyncio.run(read_configuration(tmp_path / "missing.json"))
    assert isinstance(caught.value.__cause__, OSError)


@pytest.mark.parametrize(
    "policy",
    [
        {"optionalServers": ["s", "s"]},
        {"optionalServers": ["s"], "disabledServers": ["s"]},
        {"startupTimeoutSeconds": True},
        {"toolsets": {"x": {"servers": ["missing"]}}},
        {"toolsets": {"x": {"tools": [{"server": "missing", "name": "echo"}]}}},
        {"disabledServers": ["s"], "toolsets": {"x": {"servers": ["s"]}}},
    ],
)
def test_static_reference_conflicts_fail_before_effects(
    tmp_path: Path, policy: dict[str, object]
) -> None:
    path = tmp_path / "mcp.json"
    path.write_text(
        json.dumps({"mcpServers": {"s": {"command": "python"}}, "spawnJoin": policy})
    )
    with pytest.raises(McpConfigurationError):
        asyncio.run(read_configuration(path))
