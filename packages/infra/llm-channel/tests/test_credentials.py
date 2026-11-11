"""Credential resolution tests."""

import pytest
from spawn_join_llm_channel._credentials import resolve_api_key

from spawn_join_llm_provider import ConfigurationError


def test_resolve_api_key_reads_the_supplied_mapping() -> None:
    assert resolve_api_key("KEY", environ={"KEY": "value"}) == "value"


def test_resolve_api_key_reads_process_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SPAWN_JOIN_TEST_KEY", "value")
    assert resolve_api_key("SPAWN_JOIN_TEST_KEY") == "value"


def test_resolve_api_key_rejects_missing_value() -> None:
    with pytest.raises(ConfigurationError, match="is not set"):
        resolve_api_key("MISSING", environ={})


@pytest.mark.parametrize("value", ["", "   ", " value", "value "])
def test_resolve_api_key_rejects_empty_or_padded_value(value: str) -> None:
    with pytest.raises(ConfigurationError, match="API key must be non-empty"):
        resolve_api_key("KEY", environ={"KEY": value})


def test_resolve_api_key_does_not_mutate_the_mapping() -> None:
    environ = {"KEY": "value"}
    resolve_api_key("KEY", environ=environ)
    assert environ == {"KEY": "value"}
