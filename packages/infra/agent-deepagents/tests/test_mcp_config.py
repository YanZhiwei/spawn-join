"""Strict local configuration validation must precede external effects."""

import asyncio
import json
from pathlib import Path
from typing import NoReturn

import pytest
from fastmcp import Client
from fastmcp.mcp_config import MCPConfig, RemoteMCPServer, StdioMCPServer
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
        '{"mcpServers":{"local":{"command":"python","timeout":1.5,"args":[""]},'
        '"remote":{"url":"https://example.com/mcp"}}}',
        encoding="utf-8-sig",
    )
    configuration = asyncio.run(read_configuration(path))
    assert isinstance(configuration.official, MCPConfig)
    assert list(configuration.official.mcpServers) == ["local", "remote"]
    local = configuration.official.mcpServers["local"]
    assert isinstance(local, StdioMCPServer) and local.args == [""]
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
        if server.get("args") == [1]:
            assert str(caught.value) == "mcpServers.args: invalid configuration"


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


@pytest.mark.parametrize("explicit", [True, False])
def test_environment_expands_only_values_and_cwd_uses_config_parent(
    tmp_path: Path, explicit: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "mcp.json"
    path.write_text(
        """{"mcpServers":{
        "local":{"command":"${BIN}","args":["${TOKEN}"],"cwd":"data",
                 "env":{"TOKEN":"prefix-${TOKEN}"}},
        "remote":{"url":"https://private.example/${TOKEN}",
                  "headers":{"Authorization":"Bearer ${TOKEN}"}}
    }}""",
        encoding="utf-8",
    )
    monkeypatch.setenv("TOKEN", "secret-value")
    config = asyncio.run(
        read_configuration(
            path, environ={"TOKEN": "secret-value"} if explicit else None
        )
    )
    local = config.official.mcpServers["local"]
    remote = config.official.mcpServers["remote"]
    assert isinstance(local, StdioMCPServer) and isinstance(remote, RemoteMCPServer)
    assert local.env["TOKEN"] == "prefix-secret-value"
    assert local.command == "${BIN}" and local.args == ["${TOKEN}"]
    assert local.cwd == str((tmp_path / "data").resolve())
    assert remote.url == "https://private.example/${TOKEN}"
    assert remote.headers["Authorization"] == "Bearer secret-value"
    assert "secret-value" not in repr(config) and "private.example" not in repr(config)


@pytest.mark.parametrize("reference", ["${MISSING}", "${bad-name}", "${}", "${OPEN"])
def test_invalid_environment_is_global_even_for_disabled(
    tmp_path: Path, reference: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MISSING", "secret-from-process")
    path = tmp_path / "mcp.json"
    for policy in ({"optionalServers": ["s"]}, {"disabledServers": ["s"]}):
        server = {"command": "python", "env": {"TOKEN": reference}}
        path.write_text(json.dumps({"mcpServers": {"s": server}, "spawnJoin": policy}))
        with pytest.raises(McpConfigurationError) as caught:
            asyncio.run(read_configuration(path, environ={}))
        assert "secret-from-process" not in str(caught.value)


def test_interpolation_uses_one_nonrecursive_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "mcp.json"
    path.write_text('{"mcpServers":{"s":{"command":"python","env":{"X":"${TOKEN}"}}}}')
    environment = {"TOKEN": "${LITERAL}"}

    async def load() -> None:
        task = asyncio.create_task(read_configuration(path, environ=environment))
        await asyncio.sleep(0)
        environment["TOKEN"] = "changed"
        config = await task
        server = config.official.mcpServers["s"]
        assert isinstance(server, StdioMCPServer) and server.env["X"] == "${LITERAL}"

    asyncio.run(load())


def test_cwd_symlink_loop_is_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "mcp.json"
    path.write_text('{"mcpServers":{"s":{"command":"python","cwd":"loop"}}}')

    def loop(_: Path) -> NoReturn:
        raise RuntimeError("Symlink loop from private-directory")

    monkeypatch.setattr(Path, "resolve", loop)
    with pytest.raises(McpConfigurationError) as caught:
        asyncio.run(read_configuration(path))
    assert isinstance(caught.value.__cause__, RuntimeError)
    assert str(caught.value) == "mcpServers.cwd: invalid directory"
    assert "private-directory" not in str(caught.value)
    assert "private-directory" not in repr(caught.value)
