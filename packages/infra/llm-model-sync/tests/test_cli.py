"""Tests for the model-sync CLI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from spawn_join_llm_model_sync import SourceRegistry
from spawn_join_llm_model_sync._cli import main


def test_sources_json(capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["sources", "--json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["id"] == "models.dev"
    assert payload[0]["license"] == "MIT"


def test_unknown_source_is_a_configuration_error(
    model_file: Path,
    tmp_path: Path,
) -> None:
    code = main(
        [
            "sync",
            "--source",
            "missing",
            "--model-file",
            str(model_file),
            "--cache-dir",
            str(tmp_path / "cache"),
        ]
    )

    assert code == 1


def test_apply_and_check_are_mutually_exclusive(
    model_file: Path,
    tmp_path: Path,
) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(
            [
                "sync",
                "--source",
                "models.dev",
                "--model-file",
                str(model_file),
                "--cache-dir",
                str(tmp_path / "cache"),
                "--apply",
                "--check",
            ]
        )

    assert excinfo.value.code == 1


def test_sync_command_with_fake_source(
    fake_source: Any,
    model_file: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    registry = SourceRegistry([fake_source])
    monkeypatch.setattr(
        SourceRegistry,
        "with_builtins",
        lambda: registry,
    )
    output = tmp_path / "model-metadata.json"

    code = main(
        [
            "sync",
            "--source",
            "models.dev",
            "--model-file",
            str(model_file),
            "--output",
            str(output),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--apply",
            "--json",
        ]
    )

    assert code == 0
    assert output.exists()
    payload = json.loads(capsys.readouterr().out)
    assert payload["ignored_upstream_model_ids"] == []
