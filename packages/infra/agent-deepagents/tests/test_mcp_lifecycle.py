"""Actual local protocols and OS process observations for the private loader."""

import asyncio
import csv
import json
import os
import signal
import subprocess
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from types import TracebackType
from typing import Literal

import pytest
from fastmcp import Client
from fastmcp.client.group import ClientGroup
from fastmcp.client.transports import StdioTransport
from fastmcp.mcp_config import StdioMCPServer
from httpx2 import ConnectError, ReadError
from langchain.mcp import MCPAdapter
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool
from mcp.types import Tool
from spawn_join_agent_deepagents.mcp import (
    McpCleanupError,
    McpConfigurationError,
    McpLoadError,
)
from spawn_join_agent_deepagents.mcp._config import read_configuration
from spawn_join_agent_deepagents.mcp._session import create_adapter, open_catalog

_SERVER = (Path(__file__).parent / "fixtures" / "mcp_server.py").resolve()


def _configuration(
    directory: Path,
    names: tuple[str, ...],
    *,
    arguments: dict[str, list[str]] | None = None,
    disabled: tuple[str, ...] = (),
    optional: tuple[str, ...] = (),
    remote_port: int | None = None,
) -> Path:
    arguments = arguments or {}
    servers: dict[str, dict[str, object]] = {
        name: {
            "command": sys.executable,
            "args": [
                str(_SERVER),
                str(directory / f"{name}.pids"),
                name,
                *arguments.get(name, []),
            ],
        }
        for name in names
    }
    if remote_port is not None:
        servers["remote"] = {
            "url": f"http://127.0.0.1:{remote_port}/mcp",
            "headers": {"X-Fixture": "synthetic"},
        }
    path = directory / "mcp.json"
    path.write_text(
        json.dumps(
            {
                "mcpServers": servers,
                "spawnJoin": {"disabledServers": disabled, "optionalServers": optional},
            }
        ),
        encoding="utf-8",
    )
    return path


async def _pids(directory: Path, name: str) -> tuple[int, ...]:
    try:
        content = await asyncio.to_thread((directory / f"{name}.pids").read_text)
    except FileNotFoundError:
        return ()
    if not content.endswith("\n"):
        return ()
    return tuple(int(line) for line in content.split())


def _any_alive(pids: tuple[int, ...]) -> bool:
    if sys.platform == "win32":
        processes = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH"],
            check=True,
            capture_output=True,
            text=True,
        )
        wanted = {str(pid) for pid in pids}
        return any(
            len(row) > 1 and row[1] in wanted
            for row in csv.reader(processes.stdout.splitlines())
        )
    for pid in pids:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            continue
        return True
    return False


async def _assert_stopped(pids: tuple[int, ...]) -> None:
    try:
        async with asyncio.timeout(10):
            while await asyncio.to_thread(_any_alive, pids):
                await asyncio.sleep(0.05)
    except TimeoutError:
        # A failing leak regression must still clean its own fixture processes.
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        raise


def test_stdio_catalog_uses_original_identity_and_holds_actual_adapter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _configuration(tmp_path, ("first_server", "second"))
    closed: list[str] = []
    original_exit = MCPAdapter.__aexit__

    async def observe_exit(
        adapter: MCPAdapter,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await original_exit(adapter, exc_type, exc_value, traceback)
        group = adapter.client
        assert isinstance(group, ClientGroup)
        if not any(client.is_connected() for client in group.clients.values()):
            closed.extend(group.clients)

    monkeypatch.setattr(MCPAdapter, "__aexit__", observe_exit)

    async def run() -> None:
        configuration = await read_configuration(path)
        async with open_catalog(configuration) as catalog:
            assert list(catalog.tools) == [
                ("first_server", "echo_value"),
                ("second", "echo_value"),
            ]
            first = catalog.tools[("first_server", "echo_value")]
            assert first.name == "first_server_echo_value"
            assert "first_server:hello" in str(await first.ainvoke({"value": "hello"}))
            assert "second:world" in str(
                await catalog.tools[("second", "echo_value")].ainvoke(
                    {"value": "world"}
                )
            )
            assert "first_server:again" in str(await first.ainvoke({"value": "again"}))
            assert len(await _pids(tmp_path, "first_server")) == 1
            assert len(await _pids(tmp_path, "second")) == 1
            assert catalog.report.tool_count == 2
        assert closed == ["second", "first_server"]
        await _assert_stopped(
            await _pids(tmp_path, "first_server") + await _pids(tmp_path, "second")
        )

    asyncio.run(run())


def test_empty_stdio_and_disabled_declarations(tmp_path: Path) -> None:
    path = _configuration(
        tmp_path,
        ("empty", "disabled"),
        arguments={"empty": ["--empty"], "disabled": ["--fail"]},
        disabled=("disabled",),
    )

    async def run() -> None:
        async with open_catalog(await read_configuration(path)) as catalog:
            assert not catalog.tools and catalog.report.tool_count == 0
            assert [item.status for item in catalog.report.servers] == [
                "loaded",
                "disabled",
            ]
            assert not await asyncio.to_thread((tmp_path / "disabled.pids").exists)
        await _assert_stopped(await _pids(tmp_path, "empty"))

    asyncio.run(run())


def test_later_stdio_startup_failure_closes_earlier_service(tmp_path: Path) -> None:
    path = _configuration(
        tmp_path, ("healthy", "failing", "later"), arguments={"failing": ["--fail"]}
    )

    async def run() -> None:
        with pytest.raises(McpLoadError, match="connect/upstream_error") as caught:
            async with open_catalog(await read_configuration(path)):
                pytest.fail("failed initialization produced a catalog")
        assert [item.status for item in caught.value.report.servers] == [
            "loaded",
            "failed",
            "not_attempted",
        ]
        assert (
            caught.value.report.tool_count == 1 and caught.value.__cause__ is not None
        )
        assert not await _pids(tmp_path, "later")
        await _assert_stopped(
            await _pids(tmp_path, "healthy") + await _pids(tmp_path, "failing")
        )

    asyncio.run(run())


def _inject_startup_failure(
    monkeypatch: pytest.MonkeyPatch,
    stage: Literal["connect", "discover", "convert"],
    failure: Exception | None = None,
) -> None:
    from langchain import mcp

    failure = failure or ValueError("synthetic secret-token")
    original_list = ClientGroup.list_tools
    original_convert = mcp.as_langchain_tool

    async def discover(
        group: ClientGroup,
        *,
        cache_mode: Literal["use", "refresh", "bypass"] = "refresh",
    ) -> list[Tool]:
        if "failing" in group.clients:
            raise failure
        return await original_list(group, cache_mode=cache_mode)

    async def convert(tool: Tool, group: ClientGroup) -> BaseTool:
        if tool.name.startswith("failing_"):
            raise failure
        return await original_convert(tool, group)

    if stage == "discover":
        monkeypatch.setattr(ClientGroup, "list_tools", discover)
    elif stage == "convert":
        monkeypatch.setattr(mcp, "as_langchain_tool", convert)


@pytest.mark.parametrize("stage", ["connect", "discover", "convert"])
def test_optional_failure_releases_member_and_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: Literal["connect", "discover", "convert"],
) -> None:
    path = _configuration(
        tmp_path,
        ("failing", "healthy"),
        optional=("failing",),
        arguments={"failing": ["--fail"]} if stage == "connect" else None,
    )
    _inject_startup_failure(monkeypatch, stage)

    async def run() -> None:
        async with open_catalog(await read_configuration(path)) as catalog:
            assert (
                catalog.report.status == "degraded" and catalog.report.tool_count == 1
            )
            assert [item.status for item in catalog.report.servers] == [
                "failed",
                "loaded",
            ]
            assert catalog.report.servers[0].error_stage == stage
            failure = catalog.failures["failing"]
            assert failure.report is catalog.report and failure.__cause__ is not None
            assert "secret-token" not in repr(catalog.report) + repr(catalog) + str(
                failure
            )
            await _assert_stopped(await _pids(tmp_path, "failing"))
            assert "healthy:ok" in str(
                await catalog.tools[("healthy", "echo_value")].ainvoke({"value": "ok"})
            )
        await _assert_stopped(await _pids(tmp_path, "healthy"))

    asyncio.run(run())


@pytest.mark.parametrize("mode", ["empty", "disabled", "no_tools", "all_failed"])
def test_empty_catalog_readiness_is_distinct_from_optional_failure(
    tmp_path: Path, mode: str
) -> None:
    names = () if mode == "empty" else ("one", "two")
    path = _configuration(
        tmp_path,
        names,
        disabled=names if mode == "disabled" else (),
        optional=names if mode == "all_failed" else (),
        arguments={
            name: ["--fail" if mode == "all_failed" else "--empty"] for name in names
        },
    )

    async def run() -> None:
        async with open_catalog(await read_configuration(path)) as catalog:
            assert not catalog.tools and catalog.report.tool_count == 0
            assert catalog.report.status == (
                "degraded" if mode == "all_failed" else "ready"
            )
            assert tuple(catalog.failures) == (names if mode == "all_failed" else ())
            assert tuple(item.name for item in catalog.report.servers) == names
        for name in names:
            await _assert_stopped(await _pids(tmp_path, name))

    asyncio.run(run())


def test_optional_configuration_and_cleanup_errors_are_not_degraded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _configuration(tmp_path, ("failing", "later"), optional=("failing",))
    original_exit = MCPAdapter.__aexit__

    async def fail_exit(
        adapter: MCPAdapter,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await original_exit(adapter, exc_type, exc_value, traceback)
        if (
            isinstance(adapter.client, ClientGroup)
            and "failing" in adapter.client.clients
        ):
            raise RuntimeError("synthetic cleanup failure")

    async def run() -> None:
        _inject_startup_failure(
            monkeypatch, "convert", McpConfigurationError("safe config")
        )
        with pytest.raises(McpConfigurationError, match="safe config"):
            async with open_catalog(await read_configuration(path)):
                pytest.fail("configuration error was downgraded")
        _inject_startup_failure(monkeypatch, "convert")
        monkeypatch.setattr(MCPAdapter, "__aexit__", fail_exit)
        with pytest.raises(McpCleanupError) as caught:
            async with open_catalog(await read_configuration(path)):
                pytest.fail("cleanup error was downgraded")
        assert isinstance(caught.value.__cause__, RuntimeError)
        assert not await _pids(tmp_path, "later")
        await _assert_stopped(await _pids(tmp_path, "failing"))

    asyncio.run(run())


@pytest.mark.parametrize("during_startup", [True, False])
@pytest.mark.parametrize("optional", [True, False])
def test_parent_cancellation_releases_stdio(
    tmp_path: Path, during_startup: bool, optional: bool
) -> None:
    path = _configuration(
        tmp_path,
        ("cancelled",),
        arguments={"cancelled": ["--delay", "30"]} if during_startup else None,
        optional=("cancelled",) if optional else (),
    )

    async def run() -> None:
        entered = asyncio.Event()

        async def hold() -> None:
            async with open_catalog(await read_configuration(path)):
                entered.set()
                await asyncio.Event().wait()

        parent = asyncio.create_task(hold())
        try:
            async with asyncio.timeout(20):
                if during_startup:
                    while not await _pids(tmp_path, "cancelled"):
                        await asyncio.sleep(0.02)
                else:
                    await entered.wait()
        finally:
            parent.cancel()
            with pytest.raises(asyncio.CancelledError):
                await parent
            await _assert_stopped(await _pids(tmp_path, "cancelled"))

    asyncio.run(run())


@pytest.mark.parametrize(
    ("timeout_ms", "seconds"), [(None, None), (0, 0), (1.5, 0.0015), (1500, 1.5)]
)
def test_explicit_client_timeout_units_and_stdio_process_ownership(
    timeout_ms: float | None, seconds: float | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: list[float | None] = []

    def observe_client(
        transport: StdioTransport,
        *,
        timeout: float | None,
    ) -> Client[StdioTransport]:
        observed.append(timeout)
        return Client(transport, timeout=timeout)

    monkeypatch.setattr("fastmcp.Client", observe_client)
    server = StdioMCPServer(command=sys.executable, keep_alive=False)
    adapter = create_adapter("local", server, timeout_ms)
    assert observed == [seconds]
    assert isinstance(adapter.client, ClientGroup)
    transport = adapter.client.clients["local"].transport
    assert isinstance(transport, StdioTransport) and not transport.keep_alive


async def _wait_text(path: Path) -> str:
    async with asyncio.timeout(20):
        while True:
            try:
                content = await asyncio.to_thread(path.read_text)
            except FileNotFoundError:
                content = ""
            if content.endswith("\n"):
                return content
            await asyncio.sleep(0.02)


@asynccontextmanager
async def _http_service(
    directory: Path,
) -> AsyncGenerator[tuple[asyncio.subprocess.Process, int], None]:
    record = directory / "remote.pids"
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        str(_SERVER),
        str(record),
        "remote",
        "--http",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        port = int(await _wait_text(record.with_suffix(".port")))
        yield process, port
    finally:
        if process.returncode is None:
            process.terminate()
        await process.wait()


def test_mixed_three_service_routing_headers_and_http_ownership(tmp_path: Path) -> None:
    async def run() -> None:
        async with _http_service(tmp_path) as (remote, port):
            path = await asyncio.to_thread(
                _configuration, tmp_path, ("first", "second"), remote_port=port
            )
            async with open_catalog(await read_configuration(path)) as catalog:
                assert len(catalog.tools) == catalog.report.tool_count == 3
                for source in ("first", "second", "remote"):
                    tool = catalog.tools[(source, "echo_value")]
                    assert tool.name == f"{source}_echo_value"
                    assert f"{source}:hello" in str(
                        await tool.ainvoke({"value": "hello"})
                    )
                assert "remote:header:synthetic" in str(
                    await catalog.tools[("remote", "echo_value")].ainvoke(
                        {"value": "header"}
                    )
                )
                assert len(await _pids(tmp_path, "remote")) == 1
            await _assert_stopped(
                await _pids(tmp_path, "first") + await _pids(tmp_path, "second")
            )
            assert remote.returncode is None
            async with Client(f"http://127.0.0.1:{port}/mcp") as probe:
                assert "remote:after" in str(
                    await probe.call_tool("echo_value", {"value": "after"})
                )

    asyncio.run(run())


def test_http_business_error_and_lost_transport_remain_distinct(tmp_path: Path) -> None:
    async def run() -> None:
        async with _http_service(tmp_path) as (remote, port):
            path = await asyncio.to_thread(
                _configuration, tmp_path, ("local",), remote_port=port
            )
            observed_call_failure = False
            try:
                async with open_catalog(await read_configuration(path)) as catalog:
                    tool = catalog.tools[("remote", "echo_value")]
                    failed = await tool.ainvoke(
                        {
                            "type": "tool_call",
                            "name": tool.name,
                            "id": "failed",
                            "args": {"value": "fail"},
                        }
                    )
                    assert isinstance(failed, ToolMessage) and failed.status == "error"
                    remote.terminate()
                    await remote.wait()
                    with pytest.raises(Exception, match="(?i)connect|closed|transport"):
                        await tool.ainvoke({"value": "transport-lost"})
                    observed_call_failure = True
            except* (ConnectError, ReadError):
                # The SDK may also surface its failed HTTP session on exit.
                pass
            assert observed_call_failure
            await _assert_stopped(await _pids(tmp_path, "local"))

    asyncio.run(run())


def test_http_request_cancellation_keeps_remote_server_alive(tmp_path: Path) -> None:
    async def run() -> None:
        async with _http_service(tmp_path) as (remote, port):
            path = await asyncio.to_thread(
                _configuration, tmp_path, ("local",), remote_port=port
            )

            async def call() -> None:
                async with open_catalog(await read_configuration(path)) as catalog:
                    await catalog.tools[("remote", "echo_value")].ainvoke(
                        {"value": "wait"}
                    )

            parent = asyncio.create_task(call())
            try:
                assert await _wait_text(tmp_path / "remote.calls") == "wait\n"
            finally:
                parent.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await parent
                await _assert_stopped(await _pids(tmp_path, "local"))
            assert remote.returncode is None

    asyncio.run(run())
