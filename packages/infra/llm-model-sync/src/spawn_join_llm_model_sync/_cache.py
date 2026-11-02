"""Cache, state, and report helpers for the manual sync tool."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from platformdirs import user_cache_dir

from ._source import SyncResult


def default_cache_dir() -> Path:
    """Return the platform user cache directory for SpawnJoin model sync."""
    return Path(user_cache_dir("SpawnJoin"))


def write_raw_payload(cache_dir: Path, source_id: str, payload: bytes) -> Path:
    """Persist the raw upstream response for audit and debugging."""
    directory = cache_dir / "cache"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{source_id}.json"
    path.write_bytes(payload)
    return path


def write_state(cache_dir: Path, result: SyncResult, revision: str) -> Path:
    """Persist the last successful sync state."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / "state.json"
    state = {
        "source_id": result.source_id,
        "revision": revision,
        "last_sync": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "output_path": str(result.output_path),
        "changed": result.changed,
        "written": result.written,
    }
    path.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def write_report(cache_dir: Path, result: SyncResult) -> Path:
    """Write a human-readable sync report under the cache directory."""
    directory = cache_dir / "reports"
    directory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = directory / f"{stamp}-{result.source_id}.md"
    lines = [
        f"# Model sync report: {result.source_id}",
        "",
        f"- output: `{result.output_path}`",
        f"- changed: {result.changed}",
        f"- written: {result.written}",
        f"- matched: {len(result.matched)}",
        f"- unmatched: {len(result.unmatched)}",
        f"- ignored_upstream_models: {result.ignored_models}",
        f"- exit_code: {result.exit_code}",
        "",
        "## Matched",
        "",
        *[f"- `{item}`" for item in result.matched],
        "",
        "## Unmatched",
        "",
        *[f"- `{item}`" for item in result.unmatched],
        "",
        "## Warnings",
        "",
        *[f"- {item}" for item in result.warnings],
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
