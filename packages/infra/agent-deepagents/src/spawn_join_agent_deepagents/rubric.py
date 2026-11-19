"""Optional rubric grading middleware configuration.

The upstream ``RubricMiddleware`` is beta and activates only when an invocation
passes a ``rubric`` value in state. This module validates the grader inputs and
keeps the package's assembly contract explicit.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from .errors import RubricConfigurationError


def _require_chat_model(model: object) -> None:
    if not isinstance(model, BaseChatModel):
        raise RubricConfigurationError("rubric.model: must be a BaseChatModel instance")


def _require_positive_iterations(value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise RubricConfigurationError(
            "rubric.max_iterations: must be a positive integer"
        )


@dataclass(frozen=True, slots=True)
class RubricConfiguration:
    """A host-provided grader model and its optional tools/prompt."""

    model: BaseChatModel
    system_prompt: str | None = None
    tools: Sequence[BaseTool] = ()
    max_iterations: int = 3
    on_evaluation: Callable[[Any], None] | None = None

    def __post_init__(self) -> None:
        _require_chat_model(self.model)
        _require_positive_iterations(self.max_iterations)
        if self.on_evaluation is not None and not callable(self.on_evaluation):
            raise RubricConfigurationError(
                "rubric.on_evaluation: must be callable or None"
            )
        object.__setattr__(self, "tools", tuple(self.tools))

    @property
    def model_source(self) -> str:
        return f"injected:{type(self.model).__name__}"

    @property
    def tool_count(self) -> int:
        return len(self.tools)
