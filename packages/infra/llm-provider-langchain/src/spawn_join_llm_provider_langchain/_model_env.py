"""Read explicit .env files for model catalog credentials."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from dotenv import dotenv_values

from spawn_join_llm_provider import ConfigurationError


def _read_env_file(path: Path, referenced: set[str]) -> Mapping[str, str]:
    if not path.is_file():
        raise ConfigurationError(f"Env file not found: {path}")
    try:
        values = dotenv_values(path, encoding="utf-8-sig", interpolate=False)
    except (OSError, UnicodeError) as exc:
        raise ConfigurationError(f"Env file could not be read: {path}") from exc
    return {
        key: value
        for key, value in values.items()
        if key in referenced and value is not None
    }


def load_env_snapshot(
    env_file: str | Path | None,
    referenced: set[str],
) -> tuple[Path | None, Mapping[str, str]]:
    """Read an explicit env file, keeping only referenced variables."""
    if env_file is None:
        return None, {}
    env_path = Path(env_file)
    return env_path, _read_env_file(env_path, referenced)
