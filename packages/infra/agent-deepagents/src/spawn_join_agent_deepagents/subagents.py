"""Declarative and compiled subagent contracts.

The package validates names, required fields, and experimental fork opt-in
before converting definitions to the native DeepAgents forms. Compiled
runnables keep their own graph, model, and internal middleware.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from deepagents.middleware.filesystem import FilesystemPermission
from langchain.agents.middleware import InterruptOnConfig
from langchain.agents.structured_output import ResponseFormat
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

from .errors import SubagentConfigurationError
from .middleware import validate_middleware_scope
from .models import ModelPurpose

if TYPE_CHECKING:
    from langchain.agents.middleware.types import AgentMiddleware

ToolLike = BaseTool | Callable[..., Any] | dict[str, Any]
ResponseFormatLike = ResponseFormat[Any] | type[Any] | dict[str, Any]


class SubAgentKind(StrEnum):
    """Whether a subagent is declarative or host-compiled."""

    DECLARATIVE = "declarative"
    COMPILED = "compiled"


class SubAgentMode(StrEnum):
    """Context mode for a subagent; fork is experimental upstream behavior."""

    ISOLATED = "isolated"
    FORK = "fork"


@dataclass(frozen=True, slots=True)
class SubAgentDefinition:
    """A product-level declarative subagent definition."""

    name: str
    description: str
    system_prompt: str | None = None
    tools: Sequence[ToolLike] | None = None
    model_purpose: ModelPurpose = ModelPurpose.WORKER
    model: BaseChatModel | None = None
    middleware: Sequence[AgentMiddleware[Any, Any, Any]] = ()
    interrupt_on: Mapping[str, bool | InterruptOnConfig] | None = None
    response_format: ResponseFormatLike | None = None
    mode: SubAgentMode = SubAgentMode.ISOLATED
    skills: Sequence[str] | None = None
    permissions: Sequence[FilesystemPermission] | None = None

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise SubagentConfigurationError("subagents: name must not be blank")
        if not self.description.strip():
            raise SubagentConfigurationError(
                f"subagents.{self.name}: description must not be blank"
            )
        if self.mode == SubAgentMode.FORK and self.skills is not None:
            raise SubagentConfigurationError(
                f"subagents.{self.name}: skills are forbidden under mode='fork'"
            )
        object.__setattr__(
            self,
            "tools",
            None if self.tools is None else tuple(self.tools),
        )
        object.__setattr__(self, "middleware", tuple(self.middleware))
        validate_middleware_scope(self.middleware, f"subagents.{self.name}")
        if self.interrupt_on is not None:
            object.__setattr__(
                self,
                "interrupt_on",
                MappingProxyType(dict(self.interrupt_on)),
            )
        if self.skills is not None:
            object.__setattr__(self, "skills", tuple(self.skills))
        if self.permissions is not None:
            object.__setattr__(self, "permissions", tuple(self.permissions))


@dataclass(frozen=True, slots=True)
class CompiledSubAgentDefinition:
    """A host-owned runnable exposed as a compiled subagent."""

    name: str
    description: str
    runnable: Runnable[Any, Any]
    mode: SubAgentMode = SubAgentMode.ISOLATED

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise SubagentConfigurationError("subagents: name must not be blank")
        if not self.description.strip():
            raise SubagentConfigurationError(
                f"subagents.{self.name}: description must not be blank"
            )


SubAgentDefinitionLike = SubAgentDefinition | CompiledSubAgentDefinition


def validate_unique_subagent_names(
    definitions: Sequence[SubAgentDefinitionLike],
) -> None:
    """Reject duplicate names across declarative and compiled definitions."""

    seen: set[str] = set()
    for definition in definitions:
        if definition.name in seen:
            raise SubagentConfigurationError(
                f"subagents.{definition.name}: duplicate subagent name"
            )
        seen.add(definition.name)


def validate_experimental_fork(
    definitions: Sequence[SubAgentDefinitionLike],
    *,
    allow_experimental_fork: bool,
) -> None:
    """Require an explicit opt-in before any fork-mode subagent is assembled."""

    if allow_experimental_fork:
        return
    for definition in definitions:
        if definition.mode == SubAgentMode.FORK:
            raise SubagentConfigurationError(
                f"subagents.{definition.name}: mode='fork' requires "
                "allow_experimental_fork=True"
            )
