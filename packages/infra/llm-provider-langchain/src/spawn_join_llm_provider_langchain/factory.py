"""Create configured LangChain chat models from explicit protocol configuration."""

from typing import cast

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    AnthropicThinking,
    AnthropicThinkingAdaptive,
    AnthropicThinkingBudget,
    ChatCompletionsOptions,
    ConfigurationError,
    ProtocolKind,
    ProtocolOptions,
    ResponsesOptions,
)

from .config import ChatModelConfig, validate_request


def _chat_completions_model(
    config: ChatModelConfig,
    api_key: SecretStr,
    options: ChatCompletionsOptions | None,
) -> ChatOpenAI:
    return ChatOpenAI(
        model=config.model,
        api_key=api_key,
        base_url=config.endpoint,
        timeout=config.timeout_seconds,
        max_retries=config.max_retries,
        use_responses_api=False,
        temperature=options.temperature if options is not None else None,
        max_completion_tokens=(
            options.max_output_tokens if options is not None else None
        ),
        top_p=options.top_p if options is not None else None,
        stop_sequences=(
            list(options.stop) if options is not None and options.stop else None
        ),
        seed=options.seed if options is not None else None,
    )


def _responses_model(
    config: ChatModelConfig,
    api_key: SecretStr,
    options: ResponsesOptions | None,
) -> ChatOpenAI:
    return ChatOpenAI(
        model=config.model,
        api_key=api_key,
        base_url=config.endpoint,
        timeout=config.timeout_seconds,
        max_retries=config.max_retries,
        use_responses_api=True,
        temperature=options.temperature if options is not None else None,
        max_completion_tokens=(
            options.max_output_tokens if options is not None else None
        ),
        top_p=options.top_p if options is not None else None,
        store=options.store if options is not None else None,
        reasoning_effort=(options.reasoning_effort if options is not None else None),
        truncation=options.truncation if options is not None else None,
    )


def _is_adaptive_thinking(value: object) -> bool:
    return isinstance(value, AnthropicThinkingAdaptive)


def _thinking_payload(
    thinking: AnthropicThinking | None,
) -> dict[str, str | int] | None:
    if thinking is None:
        return None
    if isinstance(thinking, AnthropicThinkingBudget):
        return {"type": "enabled", "budget_tokens": thinking.budget_tokens}
    if _is_adaptive_thinking(thinking):
        return {"type": "adaptive"}
    raise ConfigurationError("Unsupported Anthropic thinking configuration")


def _anthropic_model(
    config: ChatModelConfig,
    api_key: SecretStr,
    options: AnthropicMessagesOptions | None,
) -> ChatAnthropic:
    return ChatAnthropic(
        model_name=config.model,
        api_key=api_key,
        base_url=config.endpoint,
        timeout=config.timeout_seconds,
        max_retries=config.max_retries,
        temperature=options.temperature if options is not None else None,
        max_tokens_to_sample=(
            options.max_output_tokens if options is not None else None
        ),
        top_p=options.top_p if options is not None else None,
        top_k=options.top_k if options is not None else None,
        stop=(
            list(options.stop_sequences)
            if options is not None and options.stop_sequences
            else None
        ),
        thinking=(_thinking_payload(options.thinking) if options is not None else None),
    )


def create_chat_model(
    config: ChatModelConfig,
    *,
    api_key: str,
    options: ProtocolOptions | None = None,
) -> BaseChatModel:
    """Create a LangChain chat model for the configured protocol."""
    validate_request(config, api_key=api_key, options=options)
    secret = SecretStr(api_key)

    match config.protocol:
        case ProtocolKind.CHAT_COMPLETIONS:
            return _chat_completions_model(
                config,
                secret,
                cast(ChatCompletionsOptions | None, options),
            )
        case ProtocolKind.RESPONSES:
            return _responses_model(
                config,
                secret,
                cast(ResponsesOptions | None, options),
            )
        case ProtocolKind.ANTHROPIC_MESSAGES:
            return _anthropic_model(
                config,
                secret,
                cast(AnthropicMessagesOptions | None, options),
            )
        case _:
            raise ConfigurationError(f"Unsupported protocol: {config.protocol}")
