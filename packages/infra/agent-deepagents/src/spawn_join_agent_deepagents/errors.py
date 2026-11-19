"""Stable, safe error taxonomy for the DeepAgents product package.

Concrete raisers must provide a message that identifies the field, purpose, or
subagent without including credentials, private endpoints, prompts, or raw user
content. The base classes do not append cause text to ``str(exc)``; callers that
need the original failure can inspect ``__cause__``.
"""

from __future__ import annotations

from enum import StrEnum

from langchain_core.exceptions import ContextOverflowError


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


class LLMErrorCode(StrEnum):
    """Stable runtime categories for model-call failures."""

    CONTEXT_OVERFLOW = "context_overflow"
    CONTENT_REJECTED = "content_rejected"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    SPEND_QUOTA_EXHAUSTED = "spend_quota_exhausted"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    INTERNAL_ERROR = "internal_error"


class LLMCallError(Exception):
    """A redacted runtime model error with a stable category.

    ``str(error)`` returns only the safe fallback message. The original provider
    exception stays in ``__cause__`` for host-side diagnosis and never enters the
    public message.
    """

    def __init__(self, code: LLMErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.user_message = message


class ContextOverflowLLMError(LLMCallError, ContextOverflowError):
    """A redacted overflow error that remains catchable as ``ContextOverflowError``.

    The second base keeps DeepAgents' summarization middleware able to catch and
    compress instead of turning overflow into a non-recoverable user error.
    """
