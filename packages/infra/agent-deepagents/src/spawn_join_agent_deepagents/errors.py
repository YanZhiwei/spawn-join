"""Stable, safe error taxonomy for the DeepAgents product package.

Concrete raisers must provide a message that identifies the field, purpose, or
subagent without including credentials, private endpoints, prompts, or raw user
content. The base classes do not append cause text to ``str(exc)``; callers that
need the original failure can inspect ``__cause__``.
"""

from __future__ import annotations


class AgentConfigurationError(Exception):
    """Base class for package configuration errors raised before execution."""


class ModelBindingError(AgentConfigurationError):
    """A model purpose is missing, cyclic, unknown, or incompatible."""


class SubagentConfigurationError(AgentConfigurationError):
    """A subagent definition is duplicate, blank, or otherwise invalid."""


class MiddlewareConfigurationError(AgentConfigurationError):
    """A middleware scope or reserved name is invalid."""


class DelegationQueueFullError(AgentConfigurationError):
    """The bounded delegation queue has no capacity for another caller."""


class DelegationTimeoutError(AgentConfigurationError):
    """A delegated operation exceeded its configured deadline."""


class UnsupportedSyncDelegationError(AgentConfigurationError):
    """A governed delegation policy was used with synchronous execution."""


class RecoveryConfigurationError(AgentConfigurationError):
    """A checkpoint, interrupt, or thread identity requirement is missing."""


class ContextConfigurationError(AgentConfigurationError):
    """A memory or skills source list is empty, blank, or duplicated."""


class ProfileConfigurationError(AgentConfigurationError):
    """A harness or provider profile registration is invalid or failed."""


class RubricConfigurationError(AgentConfigurationError):
    """A rubric grader configuration is invalid or used without its beta gate."""
