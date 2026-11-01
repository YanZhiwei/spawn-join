"""Tests for model file parsing and catalog resolution."""

import re
from pathlib import Path

import pytest

from spawn_join_llm_provider import ConfigurationError
from spawn_join_llm_provider_langchain.model_file import (
    _load_yaml_document,  # pyright: ignore[reportPrivateUsage]
)

FIXTURES = Path(__file__).parent / "fixtures"


def _write(tmp_path: Path, text: str, name: str = "model.yaml") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_load_yaml_document_accepts_utf8_bom(tmp_path: Path) -> None:
    path = _write(tmp_path, "\ufeffschema_version: 1\n")

    assert _load_yaml_document(path) == {"schema_version": 1}


def test_load_yaml_document_rejects_duplicate_keys() -> None:
    path = FIXTURES / "model-invalid-duplicate.yaml"

    with pytest.raises(ConfigurationError) as excinfo:
        _load_yaml_document(path)

    message = str(excinfo.value)
    assert "duplicate key" in message
    assert "line 9" in message
    assert "column 3" in message
    assert "fast" not in message


def test_nested_duplicate_key_is_rejected(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "schema_version: 1\n"
        "models:\n"
        "  fast:\n"
        "    options:\n"
        "      temperature: 0.2\n"
        "      temperature: 0.3\n",
    )

    with pytest.raises(ConfigurationError) as excinfo:
        _load_yaml_document(path)

    message = str(excinfo.value)
    assert "duplicate key" in message
    assert "line 6" in message
    assert "temperature" not in message


def test_duplicate_key_inside_sequence_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, "items:\n  - name: a\n    name: b\n")

    with pytest.raises(ConfigurationError) as excinfo:
        _load_yaml_document(path)

    message = str(excinfo.value)
    assert "duplicate key" in message
    assert "line 3" in message
    assert "name" not in message


def test_recursive_alias_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, "value: &a [*a]\n")

    with pytest.raises(ConfigurationError, match="recursive alias"):
        _load_yaml_document(path)


def test_non_utf8_file_reports_path(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_bytes(b"\xff\xfe\x00")

    with pytest.raises(ConfigurationError) as excinfo:
        _load_yaml_document(path)

    message = str(excinfo.value)
    assert "not valid UTF-8" in message
    assert str(path) in message


def test_yaml_syntax_error_does_not_echo_content(tmp_path: Path) -> None:
    path = _write(tmp_path, "schema_version: 1\nmodels: [sk-sentinel\n")

    with pytest.raises(ConfigurationError) as excinfo:
        _load_yaml_document(path)

    message = str(excinfo.value)
    assert "not valid YAML" in message
    assert re.search(r"at line \d+, column \d+", message) is not None
    assert "sk-sentinel" not in message


def test_missing_file_reports_path(tmp_path: Path) -> None:
    path = tmp_path / "missing.yaml"

    with pytest.raises(ConfigurationError) as excinfo:
        _load_yaml_document(path)

    assert str(path) in str(excinfo.value)


def test_non_mapping_document_is_returned_for_schema_validation(
    tmp_path: Path,
) -> None:
    document = _load_yaml_document(_write(tmp_path, "- one\n- two\n"))

    assert document == ["one", "two"]


def test_null_document_is_returned_for_schema_validation(tmp_path: Path) -> None:
    document = _load_yaml_document(_write(tmp_path, "null\n"))

    assert document is None
