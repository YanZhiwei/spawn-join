"""Policy tests for spawn-join-agent-work."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from spawn_join_agent_work import (
    ConcurrencyPolicy,
    LeasePolicy,
    RetryPolicy,
    WorkConfigurationError,
)


def test_retry_backoff_and_jitter() -> None:
    policy = RetryPolicy(max_attempts=3, base_seconds=2.0, multiplier=2.0)
    assert policy.delay_seconds(1) == 2.0
    assert policy.delay_seconds(2) == 4.0
    assert policy.delay_seconds(3) == 8.0

    jittered = RetryPolicy(base_seconds=10.0, jitter=0.5)
    assert jittered.delay_seconds(1, sample=0.0) == 5.0
    with pytest.raises(WorkConfigurationError):
        jittered.delay_seconds(1, sample=1.0)


def test_retry_validation() -> None:
    with pytest.raises(WorkConfigurationError):
        RetryPolicy(max_attempts=0)
    with pytest.raises(WorkConfigurationError):
        RetryPolicy(base_seconds=0)
    with pytest.raises(WorkConfigurationError):
        RetryPolicy(multiplier=0.5)
    with pytest.raises(WorkConfigurationError):
        RetryPolicy(jitter=1.0)


def test_lease_policy() -> None:
    policy = LeasePolicy(seconds=60, heartbeat_seconds=20)
    now = datetime(2026, 11, 22, tzinfo=UTC)
    assert (policy.until(now) - now).total_seconds() == 60

    with pytest.raises(WorkConfigurationError):
        LeasePolicy(seconds=10, heartbeat_seconds=10)
    with pytest.raises(WorkConfigurationError):
        policy.until(datetime(2026, 11, 22))


def test_concurrency_policy() -> None:
    policy = ConcurrencyPolicy(max_concurrency=2, claim_batch=1)
    assert policy.poll_interval_seconds == 1.0
    with pytest.raises(WorkConfigurationError):
        ConcurrencyPolicy(max_concurrency=0)
    with pytest.raises(WorkConfigurationError):
        ConcurrencyPolicy(poll_interval_seconds=0)
