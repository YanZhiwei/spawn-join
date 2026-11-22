"""Local stdio protocol fixture; process records make lifecycle effects observable."""

import argparse
import os
import time
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    parser.add_argument("source")
    parser.add_argument("--empty", action="store_true")
    parser.add_argument("--delay", type=float, default=0)
    parser.add_argument("--fail", action="store_true")
    options = parser.parse_args()
    with options.record.open("a", encoding="utf-8") as record:
        record.write(f"{os.getpid()}\n")
    if options.fail:
        raise RuntimeError("controlled startup failure")
    time.sleep(options.delay)

    from fastmcp import FastMCP

    server = FastMCP(options.source)
    if not options.empty:

        @server.tool(name="echo_value")
        def echo(value: str) -> str:
            """携带夹具来源标识回显输入。"""
            return f"{options.source}:{value}"

    server.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
