"""Shared fixtures for model-sync tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from spawn_join_llm_model_sync import (
    MetadataSource,
    ModelsDevSource,
    SourceCatalog,
    SourceInfo,
    SourceRequest,
    SyncContext,
)

FIXTURES = Path(__file__).parent / "fixtures"


class FakeSource:
    """A network-free source used by runner and registry tests."""

    def __init__(
        self,
        payload: bytes,
        *,
        source_id: str = "models.dev",
        min_models: int = 1,
    ) -> None:
        self._payload = payload
        self.info = SourceInfo(
            id=source_id,
            display_name="Fake source",
            homepage="https://example.com",
            license="MIT",
            default_url="https://example.com/catalog.json",
            min_models=min_models,
        )

    def fetch(self, context: SyncContext) -> bytes:
        return self._payload

    def translate(
        self,
        payload: bytes,
        request: SourceRequest,
    ) -> SourceCatalog:
        return ModelsDevSource().translate(payload, request)


@pytest.fixture
def catalog_payload() -> bytes:
    return (FIXTURES / "catalog.json").read_bytes()


@pytest.fixture
def model_file(tmp_path: Path) -> Path:
    path = tmp_path / "model.yaml"
    shutil.copyfile(FIXTURES / "model.yaml", path)
    return path


@pytest.fixture
def fake_source(catalog_payload: bytes) -> FakeSource:
    return FakeSource(catalog_payload)


@pytest.fixture
def fake_source_factory(catalog_payload: bytes):
    def build(*, source_id: str = "fake", min_models: int = 1) -> FakeSource:
        return FakeSource(
            catalog_payload,
            source_id=source_id,
            min_models=min_models,
        )

    return build


@pytest.fixture
def fake_source_builder():
    def build(payload: bytes, *, source_id: str = "models.dev") -> FakeSource:
        return FakeSource(payload, source_id=source_id)

    return build


def make_source(payload: bytes, *, source_id: str = "fake") -> MetadataSource:
    return FakeSource(payload, source_id=source_id)
