"""Package identity tests for spawn-join-agent-work."""

from __future__ import annotations

import importlib.metadata

import spawn_join_agent_work


def test_package_imports() -> None:
    assert spawn_join_agent_work.__name__ == "spawn_join_agent_work"
    assert "WorkSpec" in spawn_join_agent_work.__all__
    assert "RetryPolicy" in spawn_join_agent_work.__all__
    assert importlib.metadata.version("spawn-join-agent-work") == "0.1.0"
