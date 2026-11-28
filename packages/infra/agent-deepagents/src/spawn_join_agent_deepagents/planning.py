"""Opt-in native planning middleware configuration."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import MiddlewareConfigurationError


def _validate_optional_text(field: str, value: object) -> None:
    """Reject non-string and whitespace-only planning overrides."""

    if value is None:
        return
    if not isinstance(value, str) or not value.strip():
        raise MiddlewareConfigurationError(
            f"planning.{field}: expected a non-blank string or None"
        )


@dataclass(frozen=True, slots=True)
class PlanningConfiguration:
    """Opt-in native planning middleware for the supervisor.

    ``None`` keeps the corresponding LangChain ``TodoListMiddleware`` default.
    The configuration holds no middleware instance and creates no external
    resources; ``build_supervisor`` constructs a fresh middleware per build.
    """

    system_prompt: str | None = None
    tool_description: str | None = None

    def __post_init__(self) -> None:
        _validate_optional_text("system_prompt", self.system_prompt)
        _validate_optional_text("tool_description", self.tool_description)
