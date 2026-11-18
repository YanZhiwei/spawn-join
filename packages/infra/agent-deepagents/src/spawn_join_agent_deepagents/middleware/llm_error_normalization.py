"""Normalize failures at the LangChain model-call boundary."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from langchain.agents.middleware.types import AgentMiddleware
from langgraph.errors import GraphBubbleUp

from .._llm_error_policy import normalize_llm_error
from ..errors import AgentConfigurationError
from .scopes import LLM_ERROR_MIDDLEWARE_NAME


class LLMErrorNormalizationMiddleware(AgentMiddleware[Any, Any, Any]):
    """Normalize model-call failures into stable, redacted errors.

    Only model-call failures are caught. Configuration errors, LangGraph control
    flow (``GraphBubbleUp``), and cancellation propagate unchanged. The middleware
    adds no logging and never copies provider text into the public message; the
    original exception stays in ``__cause__``.

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
        except (AgentConfigurationError, GraphBubbleUp):
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
        except (AgentConfigurationError, GraphBubbleUp):
            raise
        except Exception as exc:
            raise normalize_llm_error(exc) from exc
