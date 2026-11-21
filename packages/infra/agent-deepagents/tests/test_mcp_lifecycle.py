"""Actual local protocols and OS process observations for the private loader."""

import asyncio
import csv
import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from types import TracebackType

import pytest
from fastmcp import Client
from fastmcp.client.group import ClientGroup
from fastmcp.client.transports import StdioTransport
from fastmcp.mcp_config import StdioMCPServer
from langchain.mcp import MCPAdapter
from spawn_join_agent_deepagents.mcp._config import read_configuration
from spawn_join_agent_deepagents.mcp._session import create_adapter, open_catalog

_SERVER = (Path(__file__).parent / "fixtures" / "mcp_server.py").resolve()


def _configuration(
    directory: Path,
    names: tuple[str, ...],
    *,
    arguments: dict[str, list[str]] | None = None,
    disabled: tuple[str, ...] = (),
) -> Path:
    arguments = arguments or {}
    servers = {
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
    path = directory / "mcp.json"
    path.write_text(
        json.dumps({"mcpServers": servers, "spawnJoin": {"disabledServers": disabled}}),
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
        tmp_path, ("healthy", "failing"), arguments={"failing": ["--fail"]}
    )

    async def run() -> None:
        with pytest.raises(Exception, match="connect|closed|Failed|terminated"):
            async with open_catalog(await read_configuration(path)):
                pytest.fail("failed initialization produced a catalog")
        await _assert_stopped(
            await _pids(tmp_path, "healthy") + await _pids(tmp_path, "failing")
        )

    asyncio.run(run())


@pytest.mark.parametrize("during_startup", [True, False])
def test_parent_cancellation_releases_stdio(
    tmp_path: Path, during_startup: bool
) -> None:
    path = _configuration(
        tmp_path,
        ("cancelled",),
        arguments={"cancelled": ["--delay", "30"]} if during_startup else None,
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
