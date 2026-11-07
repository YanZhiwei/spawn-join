"""Package-level import and public surface tests."""

from __future__ import annotations

import re
from importlib import metadata

import spawn_join_llm_model_sync as package

EXPECTED_EXPORTS = [
    "MetadataSource",
    "ModelHostMetadata",
    "ModelsDevSource",
    "SourceCatalog",
    "SourceConfig",
    "SourceFetchError",
    "SourceHostRef",
    "SourceInfo",
    "SourceRegistry",
    "SourceRequest",
    "SyncContext",
    "SyncError",
    "SyncResult",
    "builtin_sources",
    "default_cache_dir",
    "run_sync",
]


def test_exact_public_exports() -> None:
    assert package.__all__ == EXPECTED_EXPORTS


def test_import_does_not_fetch_network() -> None:
    assert "spawn_join_llm_model_sync" in package.__name__


def test_runtime_dependencies_include_common_not_langchain() -> None:
    requirements = metadata.requires("spawn-join-llm-model-sync") or []
    dependency_names = {
        re.split(r"[<>=!~;\[\s]", requirement, maxsplit=1)[0]
        for requirement in requirements
    }
    assert dependency_names == {
        "spawn-join-llm-provider",
        "spawn-join-common",
        "platformdirs",
        "PyYAML",
    }
