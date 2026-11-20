"""Normalize failures at the LangChain model-call boundary."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware
from langgraph.errors import GraphBubbleUp

from .._llm_error_policy import normalize_llm_error
from ..errors import AgentConfigurationError, LLMCallError
from .scopes import LLM_ERROR_MIDDLEWARE_NAME


class LLMErrorNormalizationMiddleware(AgentMiddleware[Any, Any, Any]):
    """Normalize model-call failures into stable, redacted errors.

    Already-normalized errors, configuration errors, LangGraph control flow
    (``GraphBubbleUp``), and cancellation propagate unchanged. For a newly
    normalized error, the original exception stays in ``__cause__`` and the
    public message omits provider details.

    Note: DeepAgents inserts host middleware after its own base stack, so
    summarization middleware errors may bypass this seam.
    """

    @property
    def name(self) -> str:
        return LLM_ERROR_MIDDLEWARE_NAME

    def wrap_model_call(
        self,
        request: Any,
        handler: Callable[[Any], Any],
    ) -> Any:
        try:
            return handler(request)
        except (AgentConfigurationError, GraphBubbleUp, LLMCallError):
            raise
        except Exception as exc:
            raise normalize_llm_error(exc) from exc

    async def awrap_model_call(
        self,
        request: Any,
        handler: Callable[[Any], Awaitable[Any]],
    ) -> Any:
        try:
            return await handler(request)
        except (AgentConfigurationError, GraphBubbleUp, LLMCallError):
            raise
        except Exception as exc:
            raise normalize_llm_error(exc) from exc
