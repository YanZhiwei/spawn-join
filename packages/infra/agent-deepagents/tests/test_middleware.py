"""Contracts for product middleware scopes."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

import pytest
from langchain.agents.middleware.types import AgentMiddleware
from spawn_join_agent_deepagents.errors import MiddlewareConfigurationError
from spawn_join_agent_deepagents.middleware import (
    DELEGATION_MIDDLEWARE_NAME,
    DIAGNOSTICS_MIDDLEWARE_NAME,
    RESERVED_SUMMARIZATION_MIDDLEWARE_NAME,
    MiddlewareConfiguration,
    MiddlewareScopeReport,
)


class MarkerMiddleware(AgentMiddleware[Any, Any, Any]):
    """A minimal middleware with a stable name for scope tests."""

    def __init__(self, name: str) -> None:
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        return self._name


def test_valid_three_scope_configuration() -> None:
    supervisor = MarkerMiddleware("audit")
    worker = MarkerMiddleware("rate-limit")
    override = MarkerMiddleware("trace")
    configuration = MiddlewareConfiguration(
        supervisor=(supervisor,),
        workers=(worker,),
        worker_overrides={"researcher": (override,)},
    )

    assert configuration.supervisor == (supervisor,)
    assert configuration.workers == (worker,)
    assert configuration.worker_overrides["researcher"] == (override,)
    configuration.validate_for_subagents(
        declarative_names={"researcher"},
        compiled_names={"compiled"},
    )


def test_duplicate_names_within_one_scope_are_rejected() -> None:
    with pytest.raises(MiddlewareConfigurationError, match="duplicate"):
        MiddlewareConfiguration(
            supervisor=(
                MarkerMiddleware("audit"),
                MarkerMiddleware("audit"),
            )
        )


@pytest.mark.parametrize(
    "reserved",
    [
        RESERVED_SUMMARIZATION_MIDDLEWARE_NAME,
        DELEGATION_MIDDLEWARE_NAME,
        DIAGNOSTICS_MIDDLEWARE_NAME,
    ],
)
def test_reserved_names_are_rejected(reserved: str) -> None:
    with pytest.raises(MiddlewareConfigurationError, match="reserved"):
        MiddlewareConfiguration(workers=(MarkerMiddleware(reserved),))


def test_same_name_in_different_scopes_is_allowed() -> None:
    configuration = MiddlewareConfiguration(
        supervisor=(MarkerMiddleware("audit"),),
        workers=(MarkerMiddleware("audit"),),
    )

    assert configuration.supervisor[0].name == "audit"
    assert configuration.workers[0].name == "audit"


def test_unknown_worker_override_is_rejected() -> None:
    configuration = MiddlewareConfiguration(
        worker_overrides={"missing": (MarkerMiddleware("trace"),)}
    )

    with pytest.raises(MiddlewareConfigurationError, match="unknown"):
        configuration.validate_for_subagents(
            declarative_names={"researcher"},
            compiled_names={"compiled"},
        )


def test_compiled_worker_override_is_rejected() -> None:
    configuration = MiddlewareConfiguration(
        worker_overrides={"compiled": (MarkerMiddleware("trace"),)}
    )

    with pytest.raises(MiddlewareConfigurationError, match="compiled"):
        configuration.validate_for_subagents(
            declarative_names={"researcher"},
            compiled_names={"compiled"},
        )


def test_blank_override_name_is_rejected() -> None:
    with pytest.raises(MiddlewareConfigurationError, match="blank"):
        MiddlewareConfiguration(worker_overrides={"  ": (MarkerMiddleware("trace"),)})


def test_duplicate_override_names_are_rejected() -> None:
    with pytest.raises(MiddlewareConfigurationError, match="duplicate"):
        MiddlewareConfiguration(
            worker_overrides={
                "researcher": (
                    MarkerMiddleware("trace"),
                    MarkerMiddleware("trace"),
                )
            }
        )


def test_scope_report_is_immutable_and_tuple_based() -> None:
    report = MiddlewareScopeReport(
        supervisor_names=("audit",),
        worker_names=("rate-limit",),
        per_subagent={"researcher": ("trace",)},
        replaced_defaults=("SummarizationMiddleware",),
        warnings=("async-diagnostics-only",),
    )

    assert report.supervisor_names == ("audit",)
    assert report.per_subagent["researcher"] == ("trace",)
    assert isinstance(report.per_subagent, MappingProxyType)
