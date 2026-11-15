"""Offline end-to-end loop from channel config to native model."""

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from spawn_join_llm_provider import (
    ChannelConfig,
    ModelInfo,
    ProtocolKind,
)
from spawn_join_llm_provider_langchain import (
    ChatModelConfig,
    ModelSummary,
    create_chat_model,
)


def test_offline_channel_to_model_loop() -> None:
    channel = ChannelConfig(
        name="primary",
        protocol=ProtocolKind.CHAT_COMPLETIONS,
        endpoint="https://api.example.com/v1",
        credential_ref="OPENAI_API_KEY",
        timeout_seconds=12.0,
    )
    discovered = ModelInfo(id="gpt-test", display_name="GPT Test")

    summary = ModelSummary.from_model_info(discovered, name="fast")
    config = ChatModelConfig.from_channel(channel, model=summary.model)
    model = create_chat_model(config, api_key="sk-test-secret")

    assert summary.name == "fast"
    assert config.protocol is ProtocolKind.CHAT_COMPLETIONS
    assert config.endpoint == "https://api.example.com/v1"
    assert isinstance(model, ChatOpenAI)
    assert isinstance(model, BaseChatModel)
    assert model.model_name == "gpt-test"
    assert "sk-test-secret" not in repr(model)
