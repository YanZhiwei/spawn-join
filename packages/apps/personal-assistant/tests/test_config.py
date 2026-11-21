"""AppConfig 边界校验的离线测试。"""

from __future__ import annotations

from pathlib import Path

import pytest
from spawn_join_personal_assistant import AppConfig, HostConfigError


def _write_catalog(tmp_path: Path) -> Path:
    catalog = tmp_path / "model.yaml"
    catalog.write_text("schema_version: 1\n", encoding="utf-8")
    return catalog


def test_accepts_valid_configuration(tmp_path: Path) -> None:
    config = AppConfig(
        data_dir=tmp_path / "data",
        workspace_root=tmp_path / "workspace",
        model_catalog_path=_write_catalog(tmp_path),
    )

    assert config.max_concurrency == 2
    assert config.work_deadline_seconds is None


def test_rejects_missing_model_catalog(tmp_path: Path) -> None:
    with pytest.raises(HostConfigError, match="model_catalog_path"):
        AppConfig(
            data_dir=tmp_path / "data",
            workspace_root=tmp_path / "workspace",
            model_catalog_path=tmp_path / "missing.yaml",
        )


def test_rejects_non_path_input(tmp_path: Path) -> None:
    with pytest.raises(HostConfigError, match="data_dir"):
        AppConfig(
            data_dir=str(tmp_path),  # type: ignore[arg-type]
            workspace_root=tmp_path / "workspace",
            model_catalog_path=_write_catalog(tmp_path),
        )


def test_rejects_zero_concurrency(tmp_path: Path) -> None:
    with pytest.raises(HostConfigError, match="max_concurrency"):
        AppConfig(
            data_dir=tmp_path / "data",
            workspace_root=tmp_path / "workspace",
            model_catalog_path=_write_catalog(tmp_path),
            max_concurrency=0,
        )


def test_rejects_boolean_concurrency(tmp_path: Path) -> None:
    with pytest.raises(HostConfigError, match="max_concurrency"):
        AppConfig(
            data_dir=tmp_path / "data",
            workspace_root=tmp_path / "workspace",
            model_catalog_path=_write_catalog(tmp_path),
            max_concurrency=True,  # type: ignore[arg-type]
        )


def test_rejects_non_positive_deadline(tmp_path: Path) -> None:
    with pytest.raises(HostConfigError, match="work_deadline_seconds"):
        AppConfig(
            data_dir=tmp_path / "data",
            workspace_root=tmp_path / "workspace",
            model_catalog_path=_write_catalog(tmp_path),
            work_deadline_seconds=0.0,
        )


def test_rejects_non_numeric_deadline(tmp_path: Path) -> None:
    with pytest.raises(HostConfigError, match="work_deadline_seconds"):
        AppConfig(
            data_dir=tmp_path / "data",
            workspace_root=tmp_path / "workspace",
            model_catalog_path=_write_catalog(tmp_path),
            work_deadline_seconds="120",  # type: ignore[arg-type]
        )
