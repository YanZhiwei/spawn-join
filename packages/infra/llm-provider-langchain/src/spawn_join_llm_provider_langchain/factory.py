"""Create configured providers from explicit protocol configuration."""

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from spawn_join_llm_provider import ConfigurationError, LLMProvider

from .config import (
    AnthropicMessagesConfig,
    ChatCompletionsConfig,
    ProviderConfigType,
    ResponsesConfig,
)
from .credentials import resolve_credential
from .protocols import (
    AnthropicMessagesProvider,
    ChatCompletionsProvider,
    ResponsesProvider,
)


def create_provider(config: ProviderConfigType) -> LLMProvider:
    """Create exactly the provider selected by the configuration type."""

    secret = resolve_credential(config.credential_ref)

    if isinstance(config, ChatCompletionsConfig):
        model = ChatOpenAI(
            model=config.model,
            api_key=SecretStr(secret),
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            max_retries=0,
            use_responses_api=False,
        )
        return ChatCompletionsProvider(model, config)

    if isinstance(config, ResponsesConfig):
        model = ChatOpenAI(
            model=config.model,
            api_key=SecretStr(secret),
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            max_retries=0,
            use_responses_api=True,
        )
        return ResponsesProvider(model, config)

    if not isinstance(
        config, AnthropicMessagesConfig
    ):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise ConfigurationError("Unsupported provider configuration")

    model = ChatAnthropic(
        model_name=config.model,
        api_key=SecretStr(secret),
        base_url=config.base_url,
        timeout=config.timeout_seconds,
        max_retries=0,
        stop=None,
    )
    return AnthropicMessagesProvider(model, config)
