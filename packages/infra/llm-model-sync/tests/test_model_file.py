"""Tests for the metadata-only model.yaml reader."""

from __future__ import annotations

from pathlib import Path

import pytest
from spawn_join_llm_model_sync._model_file import load_model_metadata_entries

from spawn_join_llm_provider import ConfigurationError
from spawn_join_llm_provider_langchain import ModelCatalog


def test_metadata_projection_matches_runtime_catalog(model_file: Path) -> None:
    entries = load_model_metadata_entries(model_file)
    runtime = ModelCatalog.from_file(model_file, env_file=None)

    assert [entry.name for entry in entries] == [item.name for item in runtime.models]
    assert [entry.metadata_ref for entry in entries] == [
        item.metadata_ref for item in runtime.models
    ]
    assert [dict(entry.metadata_source) for entry in entries] == [
        dict(item.metadata_source) for item in runtime.models
    ]


def test_v1_entry_has_no_metadata_projection(tmp_path: Path) -> None:
    path = tmp_path / "model.yaml"
    path.write_text(
        """\
schema_version: 1
models:
  fast:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: gpt-5
    api_key_env: FAST_API_KEY
""",
        encoding="utf-8",
    )

    entry = load_model_metadata_entries(path)[0]

    assert entry.metadata_ref is None
    assert entry.metadata_source == {}
    assert entry.metadata is None


def test_metadata_source_requires_metadata_ref(tmp_path: Path) -> None:
    path = tmp_path / "model.yaml"
    path.write_text(
        """\
schema_version: 2
models:
  fast:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: gpt-5
    api_key_env: FAST_API_KEY
    metadata_source:
      models.dev:
        provider: openai
        model: gpt-5
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="metadata_ref is required"):
        load_model_metadata_entries(path)
