"""Read explicit .env files for model catalog credentials."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Literal

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
    env_file: str | Path | None | Literal["auto"],
    referenced: set[str],
) -> tuple[Path | None, Mapping[str, str]]:
    """Read an env file, keeping only referenced variables.

    ``"auto"`` reads the current directory's ``.env`` when it exists and
    silently skips it otherwise. ``None`` disables env-file reading. An
    explicit path must exist.
    """
    if env_file is None:
        return None, {}
    if env_file == "auto":
        candidate = Path(".env")
        if not candidate.is_file():
            return None, {}
        return candidate, _read_env_file(candidate, referenced)
    env_path = Path(env_file)
    return env_path, _read_env_file(env_path, referenced)
