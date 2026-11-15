"""Model catalog inspection and ModelInfo bridge tests."""

from pathlib import Path

import pytest

from spawn_join_llm_provider import (
    ChatCompletionsOptions,
    ConfigurationError,
    ModelInfo,
    ProtocolKind,
)
from spawn_join_llm_provider_langchain import (
    ModelSummary,
    load_model_catalog,
)


def _catalog(tmp_path: Path):
    path = tmp_path / "model.yaml"
    path.write_text(
        "schema_version: 1\n"
        "default: fast\n"
        "models:\n"
        "  fast:\n"
        "    protocol: chat_completions\n"
        "    endpoint: https://api.example.com/v1\n"
        "    model: gpt-fast\n"
        "    api_key_env: OPENAI_API_KEY\n"
        "    timeout_seconds: 12\n"
        "    options:\n"
        "      temperature: 0.2\n"
        "  deep:\n"
        "    protocol: anthropic_messages\n"
        "    endpoint: https://api.anthropic.com\n"
        "    model: claude-deep\n"
        "    api_key_env: ANTHROPIC_API_KEY\n",
        encoding="utf-8",
    )
    return load_model_catalog(path, env_file=None)


def test_summaries_expose_protocol_and_options(tmp_path: Path) -> None:
    catalog = _catalog(tmp_path)
    fast = catalog.get("fast")

    assert fast.protocol is ProtocolKind.CHAT_COMPLETIONS
    assert fast.endpoint == "https://api.example.com/v1"
    assert fast.timeout_seconds == 12.0
    assert fast.max_retries == 0
    assert fast.options == ChatCompletionsOptions(temperature=0.2)


def test_catalog_lookup_and_read_only_views(tmp_path: Path) -> None:
    catalog = _catalog(tmp_path)

    assert catalog.names == ("fast", "deep")
    assert len(catalog) == 2
    assert "fast" in catalog
    assert "missing" not in catalog
    assert [summary.name for summary in catalog.models] == ["fast", "deep"]


def test_unknown_name_uses_the_existing_error(tmp_path: Path) -> None:
    catalog = _catalog(tmp_path)

    with pytest.raises(ConfigurationError, match="Unknown model"):
        catalog.get("missing")


def test_model_summary_from_model_info() -> None:
    summary = ModelSummary.from_model_info(
        ModelInfo(id="gpt-test", display_name="GPT Test"),
        name="fast",
    )

    assert summary.name == "fast"
    assert summary.model == "gpt-test"
    assert summary.display_name == "GPT Test"
    assert summary.protocol is None
    assert summary.metadata is None


def test_model_summary_from_model_info_falls_back_to_id() -> None:
    summary = ModelSummary.from_model_info(ModelInfo(id="gpt-test"))

    assert summary.name == "gpt-test"
    assert summary.display_name == "gpt-test"
