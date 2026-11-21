"""Shared validation and clock helpers for store adapters."""

from __future__ import annotations

from datetime import UTC, datetime

from ..errors import WorkConfigurationError


def require_aware(label: str, value: datetime) -> None:
    """Reject naive datetimes at the adapter boundary."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise WorkConfigurationError(f"{label}: must be timezone-aware")


def require_positive_seconds(label: str, value: float) -> None:
    """Reject non-positive durations at the adapter boundary."""

    if value <= 0:
        raise WorkConfigurationError(f"{label}: must be > 0")


class SystemClock:
    """UTC wall clock used when the host does not inject one."""

    def now(self) -> datetime:
        return datetime.now(UTC)
