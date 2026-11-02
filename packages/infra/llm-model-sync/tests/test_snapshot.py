"""Tests for deterministic snapshot construction and writes."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from spawn_join_llm_model_sync import ModelsDevSource
from spawn_join_llm_model_sync._merge import build_source_request, merge_source
from spawn_join_llm_model_sync._snapshot import (
    build_snapshot_mapping,
    serialize_snapshot,
    write_snapshot_atomic,
)

from spawn_join_llm_provider import ModelSource, parse_model_metadata_document
from spawn_join_llm_provider_langchain import ModelCatalog


def _mapping(model_file: Path, payload: bytes) -> dict[str, object]:
    catalog = ModelCatalog.from_file(model_file, env_file=None)
    request = build_source_request(catalog.models, "models.dev")
    source_catalog = ModelsDevSource().translate(payload, request)
    merged = merge_source(
        source_id="models.dev",
        catalog=source_catalog,
        summaries=catalog.models,
    )
    source = ModelSource(
        url="https://models.dev/catalog.json",
        revision="sha256:" + "c" * 64,
        fetched_at=datetime(2026, 11, 2, 10, tzinfo=UTC),
        license="MIT",
    )
    return build_snapshot_mapping(
        models=dict(merged.models),
        channels=dict(merged.channels),
        sources={"models.dev": source},
    )


def test_snapshot_is_deterministic(
    model_file: Path,
    catalog_payload: bytes,
) -> None:
    mapping = _mapping(model_file, catalog_payload)

    first = serialize_snapshot(mapping)
    second = serialize_snapshot(_mapping(model_file, catalog_payload))

    assert first == second
    assert first.endswith("\n")
    document = parse_model_metadata_document(json.loads(first))
    assert set(document.models) == {"openai/gpt-5", "openai/other"}
    assert set(document.channels) == {"fast", "fast-backup", "other"}


def test_atomic_write_replaces_file(
    model_file: Path,
    catalog_payload: bytes,
    tmp_path: Path,
) -> None:
    output = tmp_path / "model-metadata.json"
    text = serialize_snapshot(_mapping(model_file, catalog_payload))

    write_snapshot_atomic(output, text)

    assert output.read_text(encoding="utf-8") == text
