"""Shared LangChain-backed provider flow and error mapping."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, cast
from uuid import uuid4

from langchain_core import exceptions as lc_exceptions
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration
from langchain_core.prompt_values import ChatPromptValue

from spawn_join_llm_provider import (
    AuthenticationError,
    ChatRequest,
    ChatResponse,
    ContextOverflowError,
    FinishReason,
    InvalidRequestError,
    JsonValue,
    LLMError,
    MalformedResponseError,
    Message,
    ModelCapabilities,
    ModelNotFoundError,
    PermissionDeniedError,
    ProtocolKind,
    ProviderAPIError,
    ProviderConnectionError,
    ProviderTimeoutError,
    RateLimitError,
    ReasoningBlock,
    ReasoningDelta,
    Role,
    StreamCompleted,
    StreamEvent,
    TextBlock,
    TextDelta,
    ToolCallBlock,
    ToolCallDelta,
    Usage,
)

from .config import ProviderConfig
from .mapping import (
    capabilities_from_profile,
    finish_reason_from_message,
    finish_reason_from_value,
    from_langchain_response,
    from_langchain_usage,
    provider_finish_reason_from_message,
    response_id_from_message,
    stream_events_from_chunk,
    to_langchain_messages,
)
from .validation import validate_request

logger = logging.getLogger("spawn_join.llm")


class BaseLangChainProvider(ABC):
    """Template implementation shared by the three protocol providers."""

    def __init__(self, model: BaseChatModel, config: ProviderConfig) -> None:
        self._model = model
        self._config = config

    @property
    def protocol(self) -> ProtocolKind:
        return self._config.protocol

    @property
    def model(self) -> str:
        return self._config.model

    @property
    def capabilities(self) -> ModelCapabilities:
        if self._config.capabilities is not None:
            return self._config.capabilities
        return capabilities_from_profile(self._model.profile)

    async def complete(self, request: ChatRequest) -> ChatResponse:
        """Execute one non-streaming request."""

        request_id = request.request_id or uuid4().hex
        started = time.perf_counter()
        self._log_start(request_id, "complete")
        try:
            self._validate(request)
            result = await self._model.agenerate_prompt(
                [
                    ChatPromptValue(
                        messages=to_langchain_messages(
                            request.messages,
                            protocol=self.protocol,
                        )
                    )
                ],
                **_as_kwargs(self._request_kwargs(request)),
            )
            if not result.generations or not result.generations[0]:
                raise MalformedResponseError("Provider returned no generations")
            generation = result.generations[0][0]
            if not isinstance(generation, ChatGeneration):
                raise MalformedResponseError("Provider returned a non-chat generation")
            message = generation.message
            if not isinstance(message, AIMessage):
                raise MalformedResponseError(
                    "Provider did not return an assistant message"
                )
            generation_info = generation.generation_info or {}
            llm_output = result.llm_output or {}
            provider_finish_reason = self._provider_finish_reason(
                message,
                generation_info,
                llm_output,
            )
            response = from_langchain_response(
                message,
                protocol=self.protocol,
                provider_finish_reason=provider_finish_reason,
                finish_reason=self._finish_reason(
                    message,
                    provider_finish_reason,
                ),
                response_id=self._response_id(
                    message,
                    generation_info,
                    llm_output,
                ),
            )
            self._log_end(
                request_id,
                "complete",
                started,
                usage=response.usage,
            )
            return response
        except asyncio.CancelledError:
            self._log_cancel(request_id, "complete", started)
            raise
        except LLMError as exc:
            self._log_error(request_id, "complete", started, exc)
            raise
        except lc_exceptions.LangChainException as exc:
            mapped = _map_langchain_exception(
                exc,
                protocol=self.protocol,
                model=self.model,
            )
            self._log_error(request_id, "complete", started, mapped)
            raise mapped from exc
        except TypeError as exc:
            mapped = MalformedResponseError(
                "Provider returned an invalid response",
                protocol=self.protocol,
                model=self.model,
            )
            self._log_error(request_id, "complete", started, mapped)
            raise mapped from exc
        except ValueError as exc:
            mapped = InvalidRequestError(
                "Provider rejected the request",
                protocol=self.protocol,
                model=self.model,
            )
            self._log_error(request_id, "complete", started, mapped)
            raise mapped from exc
        except Exception as exc:
            self._log_unexpected(request_id, "complete", started, exc)
            raise

    async def stream(  # noqa: C901 - linear stream/error state machine
        self,
        request: ChatRequest,
    ) -> AsyncIterator[StreamEvent]:
        """Execute one streaming request."""

        request_id = request.request_id or uuid4().hex
        started = time.perf_counter()
        self._log_start(request_id, "stream")
        try:
            self._validate(request)
            last_usage = None
            last_finish = FinishReason.UNKNOWN
            last_provider_finish: str | None = None
            last_response_id: str | None = None
            text_parts: list[str] = []
            reasoning_blocks: list[ReasoningBlock] = []
            tool_parts: dict[int, dict[str, str | None]] = {}
            async for chunk in self._model.astream(
                to_langchain_messages(
                    request.messages,
                    protocol=self.protocol,
                ),
                **_as_kwargs(self._request_kwargs(request)),
            ):
                usage = from_langchain_usage(chunk.usage_metadata)
                if usage is not None:
                    last_usage = usage
                finish = finish_reason_from_message(chunk)
                if finish is not FinishReason.UNKNOWN:
                    last_finish = finish
                provider_finish = provider_finish_reason_from_message(chunk)
                if provider_finish is not None:
                    last_provider_finish = provider_finish
                chunk_response_id = response_id_from_message(chunk)
                if chunk_response_id is not None:
                    last_response_id = chunk_response_id
                for event in stream_events_from_chunk(chunk):
                    if isinstance(event, TextDelta):
                        text_parts.append(event.text)
                    elif isinstance(event, ReasoningDelta):
                        reasoning_blocks.append(
                            ReasoningBlock(
                                text=event.text,
                                opaque_state=event.opaque_state,
                            )
                        )
                    elif isinstance(event, ToolCallDelta):
                        key = (
                            event.index if event.index is not None else len(tool_parts)
                        )
                        part = tool_parts.setdefault(
                            key,
                            {"id": None, "name": None, "arguments": ""},
                        )
                        if event.id is not None:
                            part["id"] = event.id
                        if event.name is not None:
                            part["name"] = event.name
                        part["arguments"] = (
                            part["arguments"] or ""
                        ) + event.arguments_delta
                    yield event
            message = _assemble_stream_message(
                text_parts,
                reasoning_blocks,
                tool_parts,
            )
            self._log_end(
                request_id,
                "stream",
                started,
                usage=last_usage,
            )
            yield StreamCompleted(
                finish_reason=last_finish,
                provider_finish_reason=last_provider_finish,
                usage=last_usage,
                response_id=last_response_id,
                message=message,
            )
        except asyncio.CancelledError:
            self._log_cancel(request_id, "stream", started)
            raise
        except LLMError as exc:
            self._log_error(request_id, "stream", started, exc)
            raise
        except lc_exceptions.LangChainException as exc:
            mapped = _map_langchain_exception(
                exc,
                protocol=self.protocol,
                model=self.model,
            )
            self._log_error(request_id, "stream", started, mapped)
            raise mapped from exc
        except TypeError as exc:
            mapped = MalformedResponseError(
                "Provider returned an invalid stream response",
                protocol=self.protocol,
                model=self.model,
            )
            self._log_error(request_id, "stream", started, mapped)
            raise mapped from exc
        except ValueError as exc:
            mapped = InvalidRequestError(
                "Provider rejected the request",
                protocol=self.protocol,
                model=self.model,
            )
            self._log_error(request_id, "stream", started, mapped)
            raise mapped from exc
        except Exception as exc:
            self._log_unexpected(request_id, "stream", started, exc)
            raise

    def _validate(self, request: ChatRequest) -> None:
        validate_request(
            request,
            protocol=self.protocol,
            model=self.model,
            capabilities=self.capabilities,
        )

    @abstractmethod
    def _request_kwargs(self, request: ChatRequest) -> dict[str, object]:
        """Return protocol-specific invocation kwargs."""

    def _provider_finish_reason(
        self,
        message: AIMessage,
        generation_info: dict[str, Any],
        llm_output: dict[str, Any],
    ) -> str | None:
        del generation_info, llm_output
        return provider_finish_reason_from_message(message)

    def _finish_reason(
        self,
        message: AIMessage,
        provider_finish_reason: str | None,
    ) -> FinishReason:
        del message
        return finish_reason_from_value(provider_finish_reason)

    def _response_id(
        self,
        message: AIMessage,
        generation_info: dict[str, Any],
        llm_output: dict[str, Any],
    ) -> str | None:
        del generation_info, llm_output
        return response_id_from_message(message)

    def _log_start(self, request_id: str, operation: str) -> None:
        logger.info(
            "llm.request.start",
            extra={
                "llm_request_id": request_id,
                "llm_protocol": self.protocol.value,
                "llm_model": self.model,
                "llm_operation": operation,
            },
        )

    def _log_end(
        self,
        request_id: str,
        operation: str,
        started: float,
        *,
        usage: Usage | None,
    ) -> None:
        extra: dict[str, object] = {
            "llm_request_id": request_id,
            "llm_protocol": self.protocol.value,
            "llm_model": self.model,
            "llm_operation": operation,
            "llm_duration_ms": _elapsed_ms(started),
            "llm_status": "ok",
        }
        if usage is not None:
            extra["llm_input_tokens"] = usage.input_tokens
            extra["llm_output_tokens"] = usage.output_tokens
            extra["llm_total_tokens"] = usage.total_tokens
        logger.info("llm.request.end", extra=extra)

    def _log_error(
        self,
        request_id: str,
        operation: str,
        started: float,
        error: LLMError,
    ) -> None:
        logger.warning(
            "llm.request.error",
            extra={
                "llm_request_id": request_id,
                "llm_protocol": self.protocol.value,
                "llm_model": self.model,
                "llm_operation": operation,
                "llm_duration_ms": _elapsed_ms(started),
                "llm_status": "error",
                "llm_error_type": type(error).__name__,
            },
        )

    def _log_cancel(
        self,
        request_id: str,
        operation: str,
        started: float,
    ) -> None:
        logger.info(
            "llm.request.cancelled",
            extra={
                "llm_request_id": request_id,
                "llm_protocol": self.protocol.value,
                "llm_model": self.model,
                "llm_operation": operation,
                "llm_duration_ms": _elapsed_ms(started),
                "llm_status": "cancelled",
            },
        )

    def _log_unexpected(
        self,
        request_id: str,
        operation: str,
        started: float,
        error: Exception,
    ) -> None:
        logger.error(
            "llm.request.unexpected",
            extra={
                "llm_request_id": request_id,
                "llm_protocol": self.protocol.value,
                "llm_model": self.model,
                "llm_operation": operation,
                "llm_duration_ms": _elapsed_ms(started),
                "llm_status": "error",
                "llm_error_type": type(error).__name__,
            },
        )


def _assemble_stream_message(
    text_parts: list[str],
    reasoning_blocks: list[ReasoningBlock],
    tool_parts: dict[int, dict[str, str | None]],
) -> Message:
    blocks: list[TextBlock | ReasoningBlock | ToolCallBlock] = []
    if text_parts:
        blocks.append(TextBlock("".join(text_parts)))
    blocks.extend(reasoning_blocks)
    for part in tool_parts.values():
        tool_id = part.get("id")
        name = part.get("name")
        if not isinstance(tool_id, str) or not isinstance(name, str):
            continue
        raw_arguments = part.get("arguments") or ""
        arguments: dict[str, JsonValue] = {}
        if raw_arguments:
            try:
                parsed = json.loads(raw_arguments)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict):
                arguments = cast(dict[str, JsonValue], parsed)
        blocks.append(
            ToolCallBlock(
                id=tool_id,
                name=name,
                arguments=arguments,
            )
        )
    return Message(role=Role.ASSISTANT, content=tuple(blocks))


def _as_kwargs(kwargs: dict[str, object]) -> dict[str, Any]:
    return cast(dict[str, Any], kwargs)


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)


def _map_langchain_exception(  # noqa: C901 - ordered exception taxonomy
    exc: lc_exceptions.LangChainException,
    *,
    protocol: ProtocolKind,
    model: str,
) -> LLMError:
    if isinstance(exc, lc_exceptions.ContextOverflowError):
        return ContextOverflowError(
            "Request exceeds the model context window",
            protocol=protocol,
            model=model,
        )
    if isinstance(exc, lc_exceptions.ModelAuthenticationError):
        return AuthenticationError(
            "Provider authentication failed",
            protocol=protocol,
            model=model,
        )
    if isinstance(exc, lc_exceptions.ModelPermissionDeniedError):
        return PermissionDeniedError(
            "Provider permission denied",
            protocol=protocol,
            model=model,
        )
    if isinstance(exc, lc_exceptions.ModelRateLimitError):
        return RateLimitError(
            "Provider rate limit exceeded",
            protocol=protocol,
            model=model,
        )
    if isinstance(exc, lc_exceptions.ModelTimeoutError):
        return ProviderTimeoutError(
            "Provider request timed out",
            protocol=protocol,
            model=model,
        )
    if isinstance(exc, lc_exceptions.ModelConnectionError):
        return ProviderConnectionError(
            "Provider connection failed",
            protocol=protocol,
            model=model,
        )
    if isinstance(exc, lc_exceptions.ModelNotFoundError):
        return ModelNotFoundError(
            "Requested model was not found",
            protocol=protocol,
            model=model,
        )
    if isinstance(exc, lc_exceptions.ModelInvalidRequestError):
        return InvalidRequestError(
            "Provider rejected the request",
            protocol=protocol,
            model=model,
        )
    if isinstance(exc, lc_exceptions.OutputParserException):
        return MalformedResponseError(
            "Provider response could not be parsed",
            protocol=protocol,
            model=model,
        )
    if isinstance(exc, lc_exceptions.ModelAPIError):
        return ProviderAPIError(
            "Provider returned an API error",
            protocol=protocol,
            model=model,
        )
    return LLMError(
        "Provider call failed",
        protocol=protocol,
        model=model,
    )
