"""Product middleware scopes and their validated reporting shape.

DeepAgents owns middleware merging and replacement by ``.name``. This module
only validates product scopes and reserves the names the package itself owns.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware

from .errors import MiddlewareConfigurationError

RESERVED_SUMMARIZATION_MIDDLEWARE_NAME = "SummarizationMiddleware"
DELEGATION_MIDDLEWARE_NAME = "spawn_join_delegation_policy"
DIAGNOSTICS_MIDDLEWARE_NAME = "spawn_join_diagnostics"

RESERVED_MIDDLEWARE_NAMES = frozenset(
    {
        RESERVED_SUMMARIZATION_MIDDLEWARE_NAME,
        DELEGATION_MIDDLEWARE_NAME,
        DIAGNOSTICS_MIDDLEWARE_NAME,
    }
)

_RESERVED_NAMES = RESERVED_MIDDLEWARE_NAMES


def _empty_worker_overrides() -> Mapping[str, Sequence[AgentMiddleware[Any, Any, Any]]]:
    return {}


def validate_middleware_scope(
    middleware: Sequence[AgentMiddleware[Any, Any, Any]],
    label: str,
) -> None:
    """Validate one product middleware list for duplicates and reserved names."""

    _validate_scope(middleware, label)


def _validate_scope(
    middleware: Sequence[AgentMiddleware[Any, Any, Any]],
    label: str,
) -> None:
    names: set[str] = set()
    for item in middleware:
        name = item.name
        if not name:
            raise MiddlewareConfigurationError(
                f"middleware.{label}: middleware name must not be blank"
            )
        if name in _RESERVED_NAMES:
            raise MiddlewareConfigurationError(
                f"middleware.{label}: the name {name!r} is reserved"
            )
        if name in names:
            raise MiddlewareConfigurationError(
                f"middleware.{label}: duplicate middleware name {name!r}"
            )
        names.add(name)


@dataclass(frozen=True, slots=True)
class MiddlewareConfiguration:
    """User middleware grouped by the scope it may affect."""

    supervisor: Sequence[AgentMiddleware[Any, Any, Any]] = ()
    workers: Sequence[AgentMiddleware[Any, Any, Any]] = ()
    worker_overrides: Mapping[str, Sequence[AgentMiddleware[Any, Any, Any]]] = field(
        default_factory=_empty_worker_overrides
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "supervisor", tuple(self.supervisor))
        object.__setattr__(self, "workers", tuple(self.workers))
        overrides = {
            name: tuple(middleware)
            for name, middleware in self.worker_overrides.items()
        }
        for name, middleware in overrides.items():
            if not name.strip():
                raise MiddlewareConfigurationError(
                    "middleware.worker_overrides: subagent name must not be blank"
                )
            _validate_scope(middleware, f"worker_overrides.{name}")
        _validate_scope(self.supervisor, "supervisor")
        _validate_scope(self.workers, "workers")
        object.__setattr__(
            self,
            "worker_overrides",
            MappingProxyType(overrides),
        )

    def validate_for_subagents(
        self,
        *,
        declarative_names: Collection[str],
        compiled_names: Collection[str],
    ) -> None:
        """Reject overrides for unknown or compiled subagents."""

        declarative = set(declarative_names)
        compiled = set(compiled_names)
        unknown = set(self.worker_overrides) - declarative
        if unknown:
            names = ", ".join(sorted(unknown))
            raise MiddlewareConfigurationError(
                "middleware.worker_overrides: unknown declarative subagent(s): " + names
            )
        compiled_overrides = set(self.worker_overrides) & compiled
        if compiled_overrides:
            names = ", ".join(sorted(compiled_overrides))
            raise MiddlewareConfigurationError(
                "middleware.worker_overrides: compiled subagent(s) own their "
                "middleware: " + names
            )


@dataclass(frozen=True, slots=True)
class MiddlewareScopeReport:
    """Safe, immutable summary of the effective middleware names."""

    supervisor_names: tuple[str, ...]
    worker_names: tuple[str, ...]
    per_subagent: Mapping[str, tuple[str, ...]]
    replaced_defaults: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "supervisor_names", tuple(self.supervisor_names))
        object.__setattr__(self, "worker_names", tuple(self.worker_names))
        object.__setattr__(
            self,
            "per_subagent",
            MappingProxyType(
                {
                    name: tuple(middleware)
                    for name, middleware in self.per_subagent.items()
                }
            ),
        )
        object.__setattr__(
            self,
            "replaced_defaults",
            tuple(self.replaced_defaults),
        )
        object.__setattr__(self, "warnings", tuple(self.warnings))
