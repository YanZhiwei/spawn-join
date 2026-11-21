"""Local stdio/HTTP fixture with observable process and request boundaries."""

import argparse
import asyncio
import os
import socket
import time
from pathlib import Path


def _append(path: Path, value: str) -> None:
    with path.open("a", encoding="utf-8") as record:
        record.write(value + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    parser.add_argument("source")
    parser.add_argument("--empty", action="store_true")
    parser.add_argument("--delay", type=float, default=0)
    parser.add_argument("--fail", action="store_true")
    parser.add_argument("--http", action="store_true")
    options = parser.parse_args()
    _append(options.record, str(os.getpid()))
    if options.fail:
        raise RuntimeError("controlled startup failure")
    time.sleep(options.delay)

    from fastmcp import FastMCP
    from fastmcp.server.dependencies import get_http_headers

    server = FastMCP(options.source)
    if not options.empty:

        @server.tool(name="echo_value")
        async def echo(value: str) -> str:
            """Echo a value with this fixture's source identity."""
            await asyncio.to_thread(
                _append, options.record.with_suffix(".calls"), value
            )
            if value == "wait":
                await asyncio.sleep(30)
            if value == "fail":
                raise ValueError("controlled tool failure")
            suffix = ""
            if options.http:
                suffix = ":" + get_http_headers().get("x-fixture", "missing")
            return f"{options.source}:{value}{suffix}"

    if options.http:
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            port = listener.getsockname()[1]
            options.record.with_suffix(".port").write_text(
                f"{port}\n", encoding="utf-8"
            )
            asyncio.run(
                server.run_http_async(
                    host="127.0.0.1", port=port, sockets=[listener], show_banner=False
                )
            )
    else:
        server.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
