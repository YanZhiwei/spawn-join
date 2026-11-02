"""Tests for the sync runner."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from spawn_join_llm_model_sync import (
    MetadataSource,
    SourceConfig,
    SyncContext,
    SyncError,
    run_sync,
)

from spawn_join_llm_provider import ConfigurationError


def _run(
    *,
    source: MetadataSource,
    model_file: Path,
    output: Path,
    cache_dir: Path,
    apply: bool = False,
    check: bool = False,
):
    return run_sync(
        source=source,
        model_file=model_file,
        output=output,
        config=SourceConfig(min_models=1),
        context=SyncContext(cache_dir=cache_dir, timeout_seconds=5),
        apply=apply,
        check=check,
    )


def test_dry_run_does_not_write(
    fake_source: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "model-metadata.json"

    result = _run(
        source=fake_source,
        model_file=model_file,
        output=output,
        cache_dir=tmp_path / "cache",
    )

    assert result.changed is True
    assert result.written is False
    assert result.exit_code == 2
    assert not output.exists()


def test_apply_writes_snapshot_and_keeps_model_file(
    fake_source: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "model-metadata.json"
    before = model_file.read_bytes()

    result = _run(
        source=fake_source,
        model_file=model_file,
        output=output,
        cache_dir=tmp_path / "cache",
        apply=True,
    )

    assert result.written is True
    assert result.exit_code == 0
    assert output.exists()
    assert model_file.read_bytes() == before
    document = json.loads(output.read_text(encoding="utf-8"))
    assert set(document["models"]) == {"openai/gpt-5", "openai/other"}
    assert "fast-backup" in document["channels"]


def test_check_reports_drift_without_writing(
    fake_source: Any,
    fake_source_builder: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "model-metadata.json"
    _run(
        source=fake_source,
        model_file=model_file,
        output=output,
        cache_dir=tmp_path / "cache",
        apply=True,
    )
    existing = output.read_bytes()

    changed_payload = json.loads(fake_source.fetch(SyncContext(cache_dir=tmp_path)))
    changed_payload["providers"]["openai"]["models"]["gpt-5"]["cost"]["input"] = 2.5
    changed_source = fake_source_builder(json.dumps(changed_payload).encode("utf-8"))

    result = _run(
        source=changed_source,
        model_file=model_file,
        output=output,
        cache_dir=tmp_path / "cache",
        check=True,
    )

    assert result.changed is True
    assert result.exit_code == 2
    assert output.read_bytes() == existing


def test_empty_source_is_blocked(
    fake_source_builder: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "model-metadata.json"
    empty = fake_source_builder(b'{"providers": {}, "models": {}}')

    with pytest.raises(SyncError, match="below the safety minimum"):
        _run(
            source=empty,
            model_file=model_file,
            output=output,
            cache_dir=tmp_path / "cache",
            apply=True,
        )
    assert not output.exists()


def test_all_requested_models_missing_is_blocked(
    fake_source_builder: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "model-metadata.json"
    missing = fake_source_builder(
        b'{"providers": {}, "models": {"unrelated/x": {"name": "X"}}}'
    )

    with pytest.raises(SyncError, match="none of the referenced models"):
        _run(
            source=missing,
            model_file=model_file,
            output=output,
            cache_dir=tmp_path / "cache",
            apply=True,
        )


def test_single_missing_model_is_preserved(
    fake_source: Any,
    fake_source_builder: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "model-metadata.json"
    _run(
        source=fake_source,
        model_file=model_file,
        output=output,
        cache_dir=tmp_path / "cache",
        apply=True,
    )
    payload = json.loads(fake_source.fetch(SyncContext(cache_dir=tmp_path)))
    del payload["models"]["openai/other"]
    del payload["providers"]["openai"]["models"]["other"]
    partial_source = fake_source_builder(json.dumps(payload).encode("utf-8"))

    result = _run(
        source=partial_source,
        model_file=model_file,
        output=output,
        cache_dir=tmp_path / "cache",
        apply=True,
    )

    document = json.loads(output.read_text(encoding="utf-8"))
    assert "openai/other" in document["models"]
    assert any(
        "preserved the previous snapshot entry" in item for item in result.warnings
    )


def test_apply_and_check_are_mutually_exclusive(
    fake_source: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    with pytest.raises(ConfigurationError, match="mutually exclusive"):
        _run(
            source=fake_source,
            model_file=model_file,
            output=tmp_path / "model-metadata.json",
            cache_dir=tmp_path / "cache",
            apply=True,
            check=True,
        )
