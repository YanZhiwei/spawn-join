"""Application configuration for the personal assistant host.

`AppConfig` is the public boundary object for host-side configuration. It
validates paths and scheduler bounds eagerly so later stages receive only
narrowed, typed inputs. Credentials are never part of configuration: model
authentication stays in the environment and is resolved by
`spawn-join-llm-provider-langchain` (ADR-0008 boundary).

Validation helpers accept ``object`` on purpose: they narrow untyped dynamic
input at the boundary (Constitution IV) without making the type checker
report statically provable isinstance calls.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import HostConfigError

_MIN_CONCURRENCY = 1


def _require_path(label: str, value: object) -> None:
    """Reject non-Path input with a stable, assertable error."""

    if not isinstance(value, Path):
        raise HostConfigError(f"{label}: must be a pathlib.Path")


def _require_positive_int(label: str, value: object) -> None:
    """Reject non-int, bool, or below-minimum concurrency input."""

    if not isinstance(value, int) or isinstance(value, bool):
        raise HostConfigError(f"{label}: must be an int")
    if value < _MIN_CONCURRENCY:
        raise HostConfigError(f"{label}: must be at least {_MIN_CONCURRENCY}")


def _require_positive_number_or_none(label: str, value: object) -> None:
    """Reject non-numeric (or non-positive) deadline input; None disables it."""

    if value is None:
        return
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise HostConfigError(f"{label}: must be a number or None")
    if value <= 0:
        raise HostConfigError(f"{label}: must be greater than 0")


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Validated host-application configuration.

    Attributes:
        data_dir: Directory for host-owned persistence (SQLite database).
        workspace_root: The only directory tree where agent file side
            effects are allowed.
        model_catalog_path: Path to the model catalog file consumed via
            ``ModelCatalog``; credentials come from the environment.
        max_concurrency: Maximum number of work items running at once.
        work_deadline_seconds: Optional total deadline for one work item
            run; ``None`` disables the deadline.
    """

    data_dir: Path
    workspace_root: Path
    model_catalog_path: Path
    max_concurrency: int = 2
    work_deadline_seconds: float | None = None

    def __post_init__(self) -> None:
        for label, value in (
            ("data_dir", self.data_dir),
            ("workspace_root", self.workspace_root),
            ("model_catalog_path", self.model_catalog_path),
        ):
            _require_path(label, value)
        if not self.model_catalog_path.is_file():
            raise HostConfigError(
                f"model_catalog_path: file does not exist: "
                f"{self.model_catalog_path}"
            )
        _require_positive_int("max_concurrency", self.max_concurrency)
        _require_positive_number_or_none(
            "work_deadline_seconds", self.work_deadline_seconds
        )
