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


@dataclass(frozen=True, slots=True)
class RubricConfiguration:
    """A host-provided grader model and its optional tools/prompt."""

    model: BaseChatModel
    system_prompt: str | None = None
    tools: Sequence[BaseTool] = ()
    max_iterations: int = 3
    on_evaluation: Callable[[Any], None] | None = None

    def __post_init__(self) -> None:
        if self.max_iterations < 1 or isinstance(self.max_iterations, bool):
            raise RubricConfigurationError(
                "rubric.max_iterations: must be a positive integer"
            )
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
