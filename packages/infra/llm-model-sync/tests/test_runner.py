"""Tests for the sync runner."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from spawn_join_llm_model_sync import (
    MetadataSource,
    SourceConfig,
    SyncContext,
    SyncError,
    run_sync,
)

from spawn_join_llm_provider import ConfigurationError, Modality
from spawn_join_llm_provider_langchain import ModelCatalog


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


def test_repeated_sync_is_byte_identical(
    fake_source: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "model-metadata.json"
    with patch(
        "spawn_join_llm_model_sync._runner.utc_now",
        return_value=datetime(2026, 11, 2, 10, tzinfo=UTC),
    ):
        first = _run(
            source=fake_source,
            model_file=model_file,
            output=output,
            cache_dir=tmp_path / "cache",
            apply=True,
        )
    before = output.read_bytes()

    with patch(
        "spawn_join_llm_model_sync._runner.utc_now",
        return_value=datetime(2026, 11, 2, 10, 0, 1, tzinfo=UTC),
    ):
        checked = _run(
            source=fake_source,
            model_file=model_file,
            output=output,
            cache_dir=tmp_path / "cache",
            check=True,
        )
        reapplied = _run(
            source=fake_source,
            model_file=model_file,
            output=output,
            cache_dir=tmp_path / "cache",
            apply=True,
        )

    assert first.written is True
    assert checked.changed is False
    assert checked.exit_code == 0
    assert reapplied.changed is False
    assert reapplied.written is False
    assert output.read_bytes() == before


def test_channel_modalities_are_resolved_per_channel(
    fake_source: Any,
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

    catalog = ModelCatalog.from_file(
        model_file,
        env_file=None,
        metadata_file=output,
    )
    summaries = {summary.name: summary for summary in catalog.models}
    fast = summaries["fast"].metadata
    backup = summaries["fast-backup"].metadata
    assert fast is not None
    assert backup is not None
    assert fast.modalities.input == (Modality.TEXT, Modality.IMAGE)
    assert backup.modalities.input == (Modality.TEXT,)


def test_price_only_host_inherits_shared_capabilities(
    fake_source: Any,
    fake_source_builder: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    payload = json.loads(fake_source.fetch(SyncContext(cache_dir=tmp_path)))
    payload["providers"]["backup"]["models"]["gpt-5"] = {
        "canonical_model_id": "openai/gpt-5",
        "cost": {"input": 1.8},
    }
    source = fake_source_builder(json.dumps(payload).encode("utf-8"))
    output = tmp_path / "model-metadata.json"

    _run(
        source=source,
        model_file=model_file,
        output=output,
        cache_dir=tmp_path / "cache",
        apply=True,
    )

    channel = json.loads(output.read_text(encoding="utf-8"))["channels"]["fast-backup"]
    assert "capabilities" not in channel
    catalog = ModelCatalog.from_file(
        model_file,
        env_file=None,
        metadata_file=output,
    )
    summaries = {summary.name: summary for summary in catalog.models}
    backup = summaries["fast-backup"].metadata
    assert backup is not None
    assert backup.capabilities.reasoning is not None
    assert backup.capabilities.reasoning.supported is True
    assert backup.capabilities.tools is True


def test_second_source_preserves_other_source_data(
    fake_source: Any,
    fake_source_builder: Any,
    catalog_payload: bytes,
    model_file: Path,
    tmp_path: Path,
) -> None:
    text = model_file.read_text(encoding="utf-8")
    text = text.replace(
        "      models.dev:\n" "        provider: openai\n" "        model: gpt-5\n",
        "      models.dev:\n"
        "        provider: openai\n"
        "        model: gpt-5\n"
        "      custom:\n"
        "        provider: backup\n"
        "        model: gpt-5\n",
        1,
    )
    model_file.write_text(text, encoding="utf-8")
    output = tmp_path / "model-metadata.json"

    _run(
        source=fake_source,
        model_file=model_file,
        output=output,
        cache_dir=tmp_path / "cache",
        apply=True,
    )
    custom = fake_source_builder(catalog_payload, source_id="custom")
    _run(
        source=custom,
        model_file=model_file,
        output=output,
        cache_dir=tmp_path / "cache",
        apply=True,
    )

    document = json.loads(output.read_text(encoding="utf-8"))
    assert set(document["sources"]) == {"models.dev", "custom"}
    assert document["channels"]["fast"]["source"]["id"] == "custom"
    assert document["channels"]["fast-backup"]["source"]["id"] == "models.dev"
    assert document["channels"]["other"]["source"]["id"] == "models.dev"


def test_missing_host_preserves_previous_channel(
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
    del payload["providers"]["backup"]["models"]["gpt-5"]
    partial = fake_source_builder(json.dumps(payload).encode("utf-8"))

    result = _run(
        source=partial,
        model_file=model_file,
        output=output,
        cache_dir=tmp_path / "cache",
        apply=True,
    )

    document = json.loads(output.read_text(encoding="utf-8"))
    rates = document["channels"]["fast-backup"]["pricing"]["rates"]
    assert any(rate["amount"] == 1.8 for rate in rates)
    assert any("preserved the previous entry" in item for item in result.warnings)


def test_mass_channel_shrink_is_blocked(
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
    before = output.read_bytes()
    payload = json.loads(fake_source.fetch(SyncContext(cache_dir=tmp_path)))
    payload["providers"] = {}
    shrink = fake_source_builder(json.dumps(payload).encode("utf-8"))

    with pytest.raises(SyncError, match="abnormal channel shrink"):
        _run(
            source=shrink,
            model_file=model_file,
            output=output,
            cache_dir=tmp_path / "cache",
            apply=True,
        )
    assert output.read_bytes() == before


def test_post_commit_cache_failure_is_a_warning(
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
    payload["providers"]["openai"]["models"]["gpt-5"]["cost"]["input"] = 999
    changed = fake_source_builder(json.dumps(payload).encode("utf-8"))
    bad_cache = tmp_path / "cache-is-a-file"
    bad_cache.write_text("occupied", encoding="utf-8")

    result = _run(
        source=changed,
        model_file=model_file,
        output=output,
        cache_dir=bad_cache,
        apply=True,
    )

    document = json.loads(output.read_text(encoding="utf-8"))
    rates = document["channels"]["fast"]["pricing"]["rates"]
    assert any(rate["amount"] == 999 for rate in rates)
    assert result.written is True
    assert result.exit_code == 0
    assert any("post-commit" in item for item in result.warnings)


def test_ignored_models_use_upstream_match_count(
    fake_source: Any,
    fake_source_builder: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    payload = json.loads(fake_source.fetch(SyncContext(cache_dir=tmp_path)))
    del payload["models"]["openai/other"]
    del payload["providers"]["openai"]["models"]["other"]
    payload["models"]["unused/example"] = {"name": "Unused"}
    source = fake_source_builder(json.dumps(payload).encode("utf-8"))

    result = _run(
        source=source,
        model_file=model_file,
        output=tmp_path / "model-metadata.json",
        cache_dir=tmp_path / "cache",
    )

    assert result.ignored_models == 1
    assert result.ignored_model_ids == ("unused/example",)


def test_credential_url_is_rejected_before_write(
    fake_source: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "model-metadata.json"

    with pytest.raises(ConfigurationError, match="credential"):
        run_sync(
            source=fake_source,
            model_file=model_file,
            output=output,
            config=SourceConfig(
                min_models=1,
                url="https://example.com/catalog.json?api_key=PR31_SENTINEL",
            ),
            context=SyncContext(cache_dir=tmp_path / "cache"),
            apply=True,
        )

    assert not output.exists()


def test_sparse_host_is_idempotent(
    fake_source: Any,
    fake_source_builder: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    payload = json.loads(fake_source.fetch(SyncContext(cache_dir=tmp_path)))
    payload["providers"]["backup"]["models"]["gpt-5"] = {
        "canonical_model_id": "openai/gpt-5",
        "cost": {"input": 1.8},
        "tool_call": None,
    }
    source = fake_source_builder(json.dumps(payload).encode("utf-8"))
    output = tmp_path / "model-metadata.json"
    with patch(
        "spawn_join_llm_model_sync._runner.utc_now",
        return_value=datetime(2026, 11, 2, 10, tzinfo=UTC),
    ):
        first = _run(
            source=source,
            model_file=model_file,
            output=output,
            cache_dir=tmp_path / "cache",
            apply=True,
        )
    before = output.read_bytes()

    with patch(
        "spawn_join_llm_model_sync._runner.utc_now",
        return_value=datetime(2026, 11, 2, 10, 0, 1, tzinfo=UTC),
    ):
        checked = _run(
            source=source,
            model_file=model_file,
            output=output,
            cache_dir=tmp_path / "cache",
            check=True,
        )
        reapplied = _run(
            source=source,
            model_file=model_file,
            output=output,
            cache_dir=tmp_path / "cache",
            apply=True,
        )

    assert first.written is True
    assert checked.changed is False
    assert checked.exit_code == 0
    assert reapplied.written is False
    assert output.read_bytes() == before


def test_post_commit_state_failure_keeps_report_path(
    fake_source: Any,
    fake_source_builder: Any,
    model_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
    payload["providers"]["openai"]["models"]["gpt-5"]["cost"]["input"] = 777
    changed = fake_source_builder(json.dumps(payload).encode("utf-8"))

    def fail_state(*args: object, **kwargs: object) -> None:
        raise OSError("state unavailable")

    monkeypatch.setattr(
        "spawn_join_llm_model_sync._runner.write_state",
        fail_state,
    )
    result = _run(
        source=changed,
        model_file=model_file,
        output=output,
        cache_dir=tmp_path / "cache",
        apply=True,
    )

    assert result.written is True
    assert result.report_path is not None
    assert result.report_path.exists()
    assert any("post-commit" in item for item in result.warnings)


def test_invalid_utf8_previous_snapshot_is_a_sync_error(
    fake_source: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "model-metadata.json"
    output.write_bytes(b"\xff\xfe\x00")

    with pytest.raises(SyncError, match="not valid UTF-8"):
        _run(
            source=fake_source,
            model_file=model_file,
            output=output,
            cache_dir=tmp_path / "cache",
            apply=True,
        )


def test_temp_file_failure_is_a_sync_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from spawn_join_llm_model_sync._snapshot import write_snapshot_atomic

    def fail_mkstemp(*args: object, **kwargs: object) -> tuple[int, str]:
        raise OSError("no temp")

    monkeypatch.setattr(
        "spawn_join_llm_model_sync._snapshot.tempfile.mkstemp",
        fail_mkstemp,
    )
    with pytest.raises(SyncError, match="cannot create temporary snapshot"):
        write_snapshot_atomic(tmp_path / "snapshot.json", "{}\n")


def test_missing_canonical_id_fallback_mismatch_is_a_warning(
    fake_source: Any,
    fake_source_builder: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    payload = json.loads(fake_source.fetch(SyncContext(cache_dir=tmp_path)))
    del payload["providers"]["backup"]["models"]["gpt-5"]["canonical_model_id"]
    source = fake_source_builder(json.dumps(payload).encode("utf-8"))
    output = tmp_path / "model-metadata.json"

    result = _run(
        source=source,
        model_file=model_file,
        output=output,
        cache_dir=tmp_path / "cache",
        apply=True,
    )

    document = json.loads(output.read_text(encoding="utf-8"))
    assert "fast-backup" not in document["channels"]
    assert any("has no canonical_model_id" in item for item in result.warnings)
    assert any("skipping this channel" in item for item in result.warnings)


def test_duplicate_key_in_previous_snapshot_is_rejected(
    fake_source: Any,
    model_file: Path,
    tmp_path: Path,
) -> None:
    output = tmp_path / "model-metadata.json"
    output.write_text(
        '{"schema_version":1,"schema_version":1,"sources":{},"models":{},"channels":{}}',
        encoding="utf-8",
    )

    with pytest.raises(SyncError, match="duplicate key"):
        _run(
            source=fake_source,
            model_file=model_file,
            output=output,
            cache_dir=tmp_path / "cache",
            apply=True,
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
