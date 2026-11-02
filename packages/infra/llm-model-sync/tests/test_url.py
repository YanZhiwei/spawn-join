"""Tests for source URL validation and credential redaction."""

from __future__ import annotations

import pytest
from spawn_join_llm_model_sync import SourceConfig, SourceFetchError
from spawn_join_llm_model_sync._source import UrllibFetcher

from spawn_join_llm_provider import ConfigurationError


def test_source_url_rejects_userinfo() -> None:
    with pytest.raises(ConfigurationError, match="credentials"):
        SourceConfig(url="https://user:secret@example.com/catalog.json")


def test_source_url_rejects_sensitive_query() -> None:
    with pytest.raises(ConfigurationError, match="credential query"):
        SourceConfig(url="https://example.com/catalog.json?api_key=secret")


def test_source_url_allows_non_sensitive_query() -> None:
    config = SourceConfig(url="https://example.com/catalog.json?format=json")

    assert config.url == "https://example.com/catalog.json?format=json"


def test_fetch_error_does_not_expose_embedded_credentials() -> None:
    with pytest.raises(SourceFetchError) as excinfo:
        UrllibFetcher()(
            "https://user:PR31_SENTINEL@example.com/catalog.json",
            timeout=1,
        )

    message = str(excinfo.value)
    assert "PR31_SENTINEL" not in message
    assert "user:" not in message
    assert "invalid source URL" in message
