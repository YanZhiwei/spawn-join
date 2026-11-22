"""Strict local file profile and static policy; never creates MCP resources."""

from __future__ import annotations

import asyncio
import json
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, NoReturn
from urllib.parse import urlsplit

from spawn_join_common import FieldReader

from ._types import McpConfigurationError

if TYPE_CHECKING:
    from fastmcp.mcp_config import MCPConfig

_READER = FieldReader(
    lambda message: McpConfigurationError(
        message.split(":", 1)[0] + ": invalid configuration"
    )
)
_ENVIRONMENT_REFERENCE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


@dataclass(frozen=True, slots=True)
class _ToolSelection:
    servers: tuple[str, ...]
    tools: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True, repr=False)
class _Configuration:
    official: MCPConfig
    request_timeouts: Mapping[str, float | None]
    optional_servers: frozenset[str]
    disabled_servers: frozenset[str]
    startup_timeout: float
    toolsets: Mapping[str, _ToolSelection] | None


def _name(value: object, path: str) -> str:
    name = _READER.as_str(value, path)
    if not name or name != name.strip():
        _READER.fail(path + ": invalid identifier")
    return name


def _expanded_mapping(
    value: object, path: str, environ: Mapping[str, str]
) -> dict[str, str]:
    def replacement(match: re.Match[str]) -> str:
        try:
            return environ[match[1]]
        except KeyError as exc:
            raise McpConfigurationError(
                path + ": missing environment variable"
            ) from exc

    values = _READER.as_string_mapping(value, path)
    for key, text in values.items():
        if "${" in _ENVIRONMENT_REFERENCE.sub("", text):
            _READER.fail(path + ": malformed environment reference")
        values[key] = _ENVIRONMENT_REFERENCE.sub(replacement, text)
    return values


def _resolved_cwd(value: str, directory: Path) -> str:
    try:
        return str((directory / value).resolve())
    except (OSError, ValueError, RuntimeError) as exc:
        raise McpConfigurationError("mcpServers.cwd: invalid directory") from exc


def _number(value: object, path: str) -> float:
    try:
        return _READER.as_non_negative_number(value, path)
    except OverflowError as exc:
        raise McpConfigurationError(path + ": invalid number") from exc


def _policy_servers(value: object, path: str, servers: set[str]) -> frozenset[str]:
    names = _READER.as_string_tuple(value, path, indexed_errors=False)
    if len(names) != len(set(names)) or set(names) - servers:
        _READER.fail(path + ": duplicate or unknown server")
    return frozenset(names)


def _toolsets(value: object, available: set[str]) -> Mapping[str, _ToolSelection]:
    selections: dict[str, _ToolSelection] = {}
    for label, raw in _READER.as_mapping(value, "spawnJoin.toolsets").items():
        _name(label, "spawnJoin.toolsets.name")
        selection = _READER.as_fields(
            raw,
            "spawnJoin.toolsets.selection",
            optional=frozenset({"servers", "tools"}),
        )
        servers = _READER.as_string_tuple(
            selection.get("servers", []),
            "spawnJoin.toolsets.servers",
            indexed_errors=False,
        )
        references: list[tuple[str, str]] = []
        for raw_ref in _READER.as_list(
            selection.get("tools", []), "spawnJoin.toolsets.tools"
        ):
            ref = _READER.as_fields(
                raw_ref,
                "spawnJoin.toolsets.tools",
                required=frozenset({"server", "name"}),
            )
            server = _READER.as_str(ref["server"], "spawnJoin.toolsets.tools.server")
            name = _READER.as_str(ref["name"], "spawnJoin.toolsets.tools.name")
            if server not in available or not name:
                _READER.fail("spawnJoin.toolsets.tools: invalid reference")
            references.append((server, name))
        if set(servers) - available:
            _READER.fail("spawnJoin.toolsets.servers: invalid reference")
        selections[label] = _ToolSelection(servers, tuple(references))
    return MappingProxyType(selections)


def _server(
    value: object, directory: Path, environ: Mapping[str, str]
) -> tuple[dict[str, object], float | None]:
    from fastmcp.mcp_config import infer_transport_type_from_url

    server = _READER.as_mapping(value, "mcpServers.entry")
    local = "command" in server
    allowed = (
        ("args", "env", "cwd", "timeout")
        if local
        else ("headers", "timeout", "transport")
    )
    server = _READER.as_fields(
        server,
        "mcpServers.entry",
        required=frozenset({"command" if local else "url"}),
        optional=frozenset(allowed),
    )
    timeout = (
        _number(server.pop("timeout"), "mcpServers.timeout")
        if "timeout" in server
        else None
    )
    if local:
        _name(server["command"], "mcpServers.command")
        server["args"] = list(
            _READER.as_string_tuple(
                server.get("args", []), "mcpServers.args", indexed_errors=False
            )
        )
        server["env"] = _expanded_mapping(
            server.get("env", {}), "mcpServers.env", environ
        )
        if "cwd" in server:
            server["cwd"] = _resolved_cwd(
                _READER.as_str(server["cwd"], "mcpServers.cwd"), directory
            )
        server["keep_alive"] = False
    else:
        url = _READER.as_str(server["url"], "mcpServers.url")
        try:
            parsed = urlsplit(url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("unsupported HTTP URL")
            _ = parsed.port  # Validate malformed/out-of-range ports before effects.
            transport = (
                _READER.as_str(server["transport"], "mcpServers.transport")
                if "transport" in server
                else infer_transport_type_from_url(url)
            )
        except ValueError as exc:
            raise McpConfigurationError("mcpServers.url: invalid HTTP URL") from exc
        if transport not in {"http", "streamable-http"}:
            _READER.fail("mcpServers.transport: unsupported transport")
        server["headers"] = _expanded_mapping(
            server.get("headers", {}), "mcpServers.headers", environ
        )
    # Official server models accept only integer milliseconds. Public Client accepts
    # fractional seconds; preserve the validated numeric option outside that model.
    return server, timeout


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise McpConfigurationError("MCP JSON: duplicate key")
        result[key] = value
    return result


def _reject_constant(_: str) -> NoReturn:
    raise McpConfigurationError("MCP JSON: non-finite number")


def _read(path: Path, environ: Mapping[str, str]) -> _Configuration:
    try:
        raw: object = json.loads(
            path.read_text(encoding="utf-8-sig"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        raise McpConfigurationError("MCP file: cannot read strict JSON") from exc
    root = _READER.as_fields(
        raw,
        "MCP root",
        required=frozenset({"mcpServers"}),
        optional=frozenset({"spawnJoin"}),
    )
    servers = _READER.as_mapping(root["mcpServers"], "mcpServers")
    policy = _READER.as_fields(
        root.get("spawnJoin", {}),
        "spawnJoin",
        optional=frozenset(
            {"optionalServers", "disabledServers", "startupTimeoutSeconds", "toolsets"}
        ),
    )
    optional = _policy_servers(
        policy.get("optionalServers", []), "spawnJoin.optionalServers", set(servers)
    )
    disabled = _policy_servers(
        policy.get("disabledServers", []), "spawnJoin.disabledServers", set(servers)
    )
    if optional & disabled:
        _READER.fail("spawnJoin: optional and disabled overlap")
    startup = _number(
        policy.get("startupTimeoutSeconds", 30), "spawnJoin.startupTimeoutSeconds"
    )
    if startup == 0:
        _READER.fail("spawnJoin.startupTimeoutSeconds: must be positive")
    selections = (
        _toolsets(policy["toolsets"], set(servers) - disabled)
        if "toolsets" in policy
        else None
    )
    try:
        from fastmcp.mcp_config import MCPConfig
    except ModuleNotFoundError as exc:
        raise McpConfigurationError(
            "MCP support: install spawn-join-agent-deepagents[mcp]"
        ) from exc
    normalized: dict[str, object] = {}
    timeouts: dict[str, float | None] = {}
    for name, definition in servers.items():
        _name(name, "mcpServers.name")
        normalized[name], timeouts[name] = _server(definition, path.parent, environ)
    try:
        official = MCPConfig.from_dict({"mcpServers": normalized})
    except ValueError as exc:
        raise McpConfigurationError(
            "mcpServers: invalid official configuration"
        ) from exc
    return _Configuration(
        official, MappingProxyType(timeouts), optional, disabled, startup, selections
    )


async def read_configuration(
    path: str | Path, *, environ: Mapping[str, str] | None = None
) -> _Configuration:
    """Validate a local file off the event loop without opening clients or processes."""
    snapshot = _READER.as_string_mapping(
        os.environ if environ is None else environ, "MCP environment"
    )
    return await asyncio.to_thread(_read, Path(path), snapshot)
