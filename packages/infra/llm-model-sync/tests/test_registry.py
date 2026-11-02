"""Tests for the source registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from spawn_join_llm_model_sync import (
    SourceConfig,
    SourceInfo,
    SourceRegistry,
    SyncContext,
)

from spawn_join_llm_provider import ConfigurationError


def test_builtins_include_models_dev() -> None:
    registry = SourceRegistry.with_builtins()

    assert [info.id for info in registry.list()] == ["models.dev"]


def test_register_get_and_list(fake_source_factory: Any) -> None:
    source = fake_source_factory(source_id="fake")
    registry = SourceRegistry()

    registry.register(source)

    assert registry.get("fake") is source
    assert [info.id for info in registry.list()] == ["fake"]


def test_duplicate_registration_requires_replace(fake_source_factory: Any) -> None:
    source = fake_source_factory(source_id="fake")
    registry = SourceRegistry([source])

    with pytest.raises(ConfigurationError, match="already registered"):
        registry.register(source)

    replacement = fake_source_factory(source_id="fake")
    registry.register(replacement, replace=True)
    assert registry.get("fake") is replacement


def test_unknown_source_raises() -> None:
    registry = SourceRegistry()

    with pytest.raises(ConfigurationError, match="unknown source"):
        registry.get("missing")


def test_invalid_source_id_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="source id"):
        SourceInfo(
            id="Bad ID",
            display_name="Bad",
            homepage="https://example.com",
            license="MIT",
            default_url="https://example.com",
        )


def test_registry_sync_delegates(
    fake_source: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    registry = SourceRegistry([fake_source])
    output = tmp_path / "model-metadata.json"

    result = registry.sync(
        source_id="models.dev",
        model_file=model_file,
        output=output,
        config=SourceConfig(min_models=1),
        context=SyncContext(cache_dir=tmp_path / "cache", timeout_seconds=5),
        apply=True,
    )

    assert result.exit_code == 0
    assert output.exists()
