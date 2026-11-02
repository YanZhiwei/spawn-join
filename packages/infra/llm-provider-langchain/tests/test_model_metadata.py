"""Tests for model.yaml v2 and optional metadata snapshots."""

import json
from pathlib import Path
from typing import cast

import pytest

from spawn_join_llm_provider import ConfigurationError
from spawn_join_llm_provider_langchain import ModelCatalog, load_model_catalog


def _write(tmp_path: Path, text: str, name: str = "model.yaml") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def _model_v2() -> str:
    return """\
schema_version: 2
default: fast
models:
  fast:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: gpt-5
    api_key_env: FAST_API_KEY
    metadata_ref: openai/gpt-5
    metadata_source:
      models.dev:
        provider: openai
        model: gpt-5
  fast-backup:
    protocol: chat_completions
    endpoint: https://backup.example.com/v1
    model: gpt-5
    api_key_env: BACKUP_API_KEY
    metadata_ref: openai/gpt-5
    metadata_source:
      models.dev:
        provider: backup
        model: gpt-5
"""


def _snapshot() -> dict[str, object]:
    return {
        "schema_version": 1,
        "sources": {
            "models.dev": {
                "url": "https://models.dev/catalog.json",
                "revision": "sha256:" + "b" * 64,
                "fetched_at": "2026-11-02T10:00:00Z",
                "license": "MIT",
            }
        },
        "models": {
            "openai/gpt-5": {
                "name": "GPT-5",
                "type": "chat",
                "modalities": {"input": ["text"], "output": ["text"]},
                "limits": {"context": 400000, "output": 128000},
            }
        },
        "channels": {
            "fast": {
                "base_model": "openai/gpt-5",
                "source": {
                    "id": "models.dev",
                    "provider": "openai",
                    "model": "gpt-5",
                },
                "pricing": {
                    "currency": "USD",
                    "rates": [
                        {
                            "modality": "text",
                            "direction": "input",
                            "unit": "per_million_tokens",
                            "amount": 1.25,
                        }
                    ],
                },
            },
            "fast-backup": {
                "base_model": "openai/gpt-5",
                "source": {
                    "id": "models.dev",
                    "provider": "backup",
                    "model": "gpt-5",
                },
                "pricing": {
                    "currency": "USD",
                    "rates": [
                        {
                            "modality": "text",
                            "direction": "input",
                            "unit": "per_million_tokens",
                            "amount": 1.8,
                        }
                    ],
                },
            },
        },
    }


def _write_snapshot(tmp_path: Path) -> Path:
    path = tmp_path / "model-metadata.json"
    path.write_text(json.dumps(_snapshot()), encoding="utf-8")
    return path


def test_v1_without_metadata_file_preserves_behavior(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """\
schema_version: 1
models:
  fast:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: gpt-test
    api_key_env: FAST_API_KEY
""",
    )

    catalog = load_model_catalog(path, env_file=None)
    summary = catalog.models[0]

    assert summary.metadata_ref is None
    assert summary.metadata is None
    assert summary.metadata_source == {}


def test_v2_exposes_references_without_snapshot(tmp_path: Path) -> None:
    path = _write(tmp_path, _model_v2())

    catalog = load_model_catalog(path, env_file=None)
    fast = catalog.models[0]

    assert fast.metadata_ref == "openai/gpt-5"
    assert fast.metadata is None
    assert fast.metadata_source["models.dev"].provider == "openai"


def test_snapshot_resolves_shared_and_channel_metadata(tmp_path: Path) -> None:
    path = _write(tmp_path, _model_v2())
    snapshot = _write_snapshot(tmp_path)

    catalog = ModelCatalog.from_file(path, env_file=None, metadata_file=snapshot)
    fast, backup = catalog.models

    assert fast.metadata is not None
    assert fast.metadata.name == "GPT-5"
    assert fast.metadata.pricing is not None
    assert fast.metadata.pricing.rates[0].amount == 1.25
    assert backup.metadata is not None
    assert backup.metadata.pricing is not None
    assert backup.metadata.pricing.rates[0].amount == 1.8


def test_inline_metadata_wins_over_snapshot(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        _model_v2().replace(
            "    metadata_source:\n"
            "      models.dev:\n"
            "        provider: openai\n"
            "        model: gpt-5\n",
            "    metadata_source:\n"
            "      models.dev:\n"
            "        provider: openai\n"
            "        model: gpt-5\n"
            "    metadata:\n"
            "      pricing:\n"
            "        currency: USD\n"
            "        rates:\n"
            "          - modality: text\n"
            "            direction: input\n"
            "            unit: per_million_tokens\n"
            "            amount: 0.5\n",
        ),
    )
    snapshot = _write_snapshot(tmp_path)

    catalog = ModelCatalog.from_file(path, env_file=None, metadata_file=snapshot)
    fast = catalog.models[0]

    assert fast.metadata is not None
    assert fast.metadata.pricing is not None
    assert fast.metadata.pricing.rates[0].amount == 0.5


def test_channel_base_model_mismatch_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, _model_v2())
    snapshot_data = _snapshot()
    channels = cast("dict[str, object]", snapshot_data["channels"])
    channel = cast("dict[str, object]", channels["fast"])
    channel["base_model"] = "openai/other"
    models = cast("dict[str, object]", snapshot_data["models"])
    models["openai/other"] = dict(cast("dict[str, object]", models["openai/gpt-5"]))
    snapshot = tmp_path / "model-metadata.json"
    snapshot.write_text(json.dumps(snapshot_data), encoding="utf-8")

    catalog = ModelCatalog.from_file(path, env_file=None, metadata_file=snapshot)
    with pytest.raises(ConfigurationError, match="does not match"):
        _ = catalog.models


def test_missing_metadata_file_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, _model_v2())

    with pytest.raises(ConfigurationError, match="cannot be read"):
        ModelCatalog.from_file(
            path,
            env_file=None,
            metadata_file=tmp_path / "missing.json",
        )


def test_malformed_snapshot_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, _model_v2())
    snapshot = tmp_path / "model-metadata.json"
    snapshot.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="not valid JSON"):
        ModelCatalog.from_file(path, env_file=None, metadata_file=snapshot)


def test_v1_rejects_v2_fields(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        _model_v2().replace("schema_version: 2", "schema_version: 1", 1),
    )

    with pytest.raises(ConfigurationError, match="unknown field"):
        load_model_catalog(path, env_file=None)


def test_metadata_source_requires_metadata_ref(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        """\
schema_version: 2
models:
  fast:
    protocol: chat_completions
    endpoint: https://api.example.com/v1
    model: gpt-test
    api_key_env: FAST_API_KEY
    metadata_source:
      models.dev:
        provider: openai
        model: gpt-test
""",
    )

    with pytest.raises(ConfigurationError, match="metadata_ref is required"):
        load_model_catalog(path, env_file=None)
