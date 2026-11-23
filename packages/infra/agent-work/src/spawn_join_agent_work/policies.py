"""Retry, lease, and concurrency policies."""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import cast

from .errors import WorkConfigurationError


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Bounded exponential retry with optional jitter."""

    max_attempts: int = 3
    base_seconds: float = 1.0
    multiplier: float = 2.0
    jitter: float = 0.0

    def __post_init__(self) -> None:
        attempts = cast(object, self.max_attempts)
        if not isinstance(attempts, int) or isinstance(attempts, bool):
            raise WorkConfigurationError("retry.max_attempts: must be an int")
        if self.max_attempts < 1:
            raise WorkConfigurationError("retry.max_attempts: must be >= 1")
        for label, value in (
            ("retry.base_seconds", self.base_seconds),
            ("retry.multiplier", self.multiplier),
            ("retry.jitter", self.jitter),
        ):
            raw = cast(object, value)
            if not isinstance(raw, (int, float)) or isinstance(raw, bool):
                raise WorkConfigurationError(f"{label}: must be a number")
        if self.base_seconds <= 0:
            raise WorkConfigurationError("retry.base_seconds: must be > 0")
        if self.multiplier < 1:
            raise WorkConfigurationError("retry.multiplier: must be >= 1")
        if not 0 <= self.jitter < 1:
            raise WorkConfigurationError("retry.jitter: must be in [0, 1)")

    def delay_seconds(self, attempt: int, *, sample: float | None = None) -> float:
        """Return the delay before the given (1-based) retry attempt."""

        raw_attempt = cast(object, attempt)
        if (
            not isinstance(raw_attempt, int)
            or isinstance(raw_attempt, bool)
            or raw_attempt < 1
        ):
            raise WorkConfigurationError("retry attempt: must be an int >= 1")
        base = self.base_seconds * (self.multiplier ** (attempt - 1))
        if sample is not None and not 0 <= sample < 1:
            raise WorkConfigurationError("jitter sample: must be in [0, 1)")
        if self.jitter == 0:
            return base
        fraction = random.random() if sample is None else sample
        return base * (1 + self.jitter * (fraction * 2 - 1))


@dataclass(frozen=True, slots=True)
class LeasePolicy:
    """Lease duration and heartbeat cadence."""

    seconds: float = 60.0
    heartbeat_seconds: float = 20.0

    def __post_init__(self) -> None:
        for label, value in (
            ("lease.seconds", self.seconds),
            ("lease.heartbeat_seconds", self.heartbeat_seconds),
        ):
            raw = cast(object, value)
            if not isinstance(raw, (int, float)) or isinstance(raw, bool):
                raise WorkConfigurationError(f"{label}: must be a number")
            if value <= 0:
                raise WorkConfigurationError(f"{label}: must be > 0")
        if self.heartbeat_seconds >= self.seconds:
            raise WorkConfigurationError(
                "lease.heartbeat_seconds: must be less than lease.seconds"
            )

    def until(self, now: datetime) -> datetime:
        if now.tzinfo is None or now.utcoffset() is None:
            raise WorkConfigurationError("lease now: must be timezone-aware")
        return now + timedelta(seconds=self.seconds)


@dataclass(frozen=True, slots=True)
class ConcurrencyPolicy:
    """Bounded local execution and polling cadence."""

    max_concurrency: int = 2
    claim_batch: int = 1
    poll_interval_seconds: float = 1.0

    def __post_init__(self) -> None:
        for label, value in (
            ("concurrency.max_concurrency", self.max_concurrency),
            ("concurrency.claim_batch", self.claim_batch),
        ):
            raw = cast(object, value)
            if not isinstance(raw, int) or isinstance(raw, bool):
                raise WorkConfigurationError(f"{label}: must be an int")
            if value < 1:
                raise WorkConfigurationError(f"{label}: must be >= 1")
        interval = cast(object, self.poll_interval_seconds)
        if not isinstance(interval, (int, float)) or isinstance(interval, bool):
            raise WorkConfigurationError(
                "concurrency.poll_interval_seconds: must be a number"
            )
        if self.poll_interval_seconds <= 0:
            raise WorkConfigurationError(
                "concurrency.poll_interval_seconds: must be > 0"
            )
