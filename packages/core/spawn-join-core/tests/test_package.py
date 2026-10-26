"""Check the existing Core distribution and dependency boundary."""

from importlib import import_module, metadata

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "spawn_join_core",
        "spawn_join_core.config",
        "spawn_join_core.exceptions",
        "spawn_join_core.protocols",
        "spawn_join_core.types",
    ],
)
def test_existing_modules_are_importable(module_name: str) -> None:
    assert import_module(module_name).__file__ is not None


def test_distribution_identity() -> None:
    assert metadata.metadata("spawn-join-core")["Name"] == "spawn-join-core"


def test_core_has_no_runtime_dependencies() -> None:
    assert not metadata.requires("spawn-join-core")
