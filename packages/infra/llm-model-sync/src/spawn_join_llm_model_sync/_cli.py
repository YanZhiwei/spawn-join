"""Command-line interface for manual model metadata synchronization."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn

from spawn_join_llm_provider import ConfigurationError

from ._cache import default_cache_dir
from ._registry import SourceRegistry
from ._source import SourceConfig, SyncContext, SyncError, SyncResult


class _ArgumentParser(argparse.ArgumentParser):
    """Argparse parser that reserves exit code 2 for snapshot drift."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="model-sync")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sources = subparsers.add_parser("sources", help="List registered sources")
    sources.add_argument("--json", action="store_true", dest="as_json")

    sync = subparsers.add_parser("sync", help="Synchronize model metadata")
    sync.add_argument("--source", required=True, help="Registered source ID")
    sync.add_argument(
        "--model-file",
        default=Path("model.yaml"),
        type=Path,
        help="Explicit model.yaml path",
    )
    sync.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Snapshot path; defaults to model-metadata.json next to model.yaml",
    )
    sync.add_argument("--cache-dir", type=Path, default=None)
    sync.add_argument("--timeout", type=float, default=30.0)
    sync.add_argument("--url", default=None, help="Override the source URL")
    mode = sync.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="Write the snapshot")
    mode.add_argument(
        "--check",
        action="store_true",
        help="Exit 2 when the snapshot differs; never write",
    )
    sync.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "sources":
        return _list_sources(
            registry=SourceRegistry.with_builtins(), as_json=args.as_json
        )
    return _sync(args)


def _write(text: str, *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    stream.write(text if text.endswith("\n") else text + "\n")


def _list_sources(*, registry: SourceRegistry, as_json: bool) -> int:
    infos = registry.list()
    if as_json:
        _write(
            json.dumps(
                [
                    {
                        "id": info.id,
                        "display_name": info.display_name,
                        "homepage": info.homepage,
                        "license": info.license,
                        "requires_auth": info.requires_auth,
                        "default_url": info.default_url,
                        "min_models": info.min_models,
                    }
                    for info in infos
                ],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    _write("ID\tNAME\tAUTH\tLICENSE\tHOMEPAGE")
    for info in infos:
        auth = "yes" if info.requires_auth else "no"
        _write(
            f"{info.id}\t{info.display_name}\t{auth}\t{info.license}\t{info.homepage}"
        )
    return 0


def _sync(args: argparse.Namespace) -> int:
    model_file = Path(args.model_file)
    output = (
        Path(args.output)
        if args.output is not None
        else model_file.with_name("model-metadata.json")
    )
    cache_dir = (
        Path(args.cache_dir) if args.cache_dir is not None else default_cache_dir()
    )
    registry = SourceRegistry.with_builtins()
    try:
        result = registry.sync(
            source_id=args.source,
            model_file=model_file,
            output=output,
            config=SourceConfig(
                url=args.url,
                timeout_seconds=args.timeout,
            ),
            context=SyncContext(cache_dir=cache_dir, timeout_seconds=args.timeout),
            apply=args.apply,
            check=args.check,
        )
    except ConfigurationError as exc:
        _write(f"model-sync: {exc}", error=True)
        return 1
    except SyncError as exc:
        _write(f"model-sync: {exc}", error=True)
        return 3
    _print_result(result, as_json=args.as_json)
    return result.exit_code


def _print_result(result: SyncResult, *, as_json: bool) -> None:
    if as_json:
        _write(
            json.dumps(
                {
                    "source_id": result.source_id,
                    "changed": result.changed,
                    "written": result.written,
                    "output_path": str(result.output_path),
                    "matched": list(result.matched),
                    "unmatched": list(result.unmatched),
                    "ignored_upstream_models": result.ignored_models,
                    "warnings": list(result.warnings),
                    "exit_code": result.exit_code,
                    "report_path": (
                        None if result.report_path is None else str(result.report_path)
                    ),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return
    _write(f"source: {result.source_id}")
    _write(f"output: {result.output_path}")
    _write(f"matched: {len(result.matched)}")
    _write(f"unmatched: {len(result.unmatched)}")
    _write(f"ignored_upstream_models: {result.ignored_models}")
    _write(f"changed: {result.changed}")
    _write(f"written: {result.written}")
    if result.warnings:
        _write("warnings:")
        for warning in result.warnings:
            _write(f"- {warning}")
    if result.report_path is not None:
        _write(f"report: {result.report_path}")


if __name__ == "__main__":
    raise SystemExit(main())
