"""Check the observability skeleton without requiring an external service."""

import re
from importlib import import_module, metadata


def test_package_is_importable() -> None:
    assert import_module("spawn_join_observability").__file__ is not None


def test_distribution_identity() -> None:
    assert (
        metadata.metadata("spawn-join-observability")["Name"]
        == "spawn-join-observability"
    )


def test_observability_only_depends_on_core() -> None:
    requirements = metadata.requires("spawn-join-observability") or []
    dependency_names = {
        re.split(r"[<>=!~;\[\s]", requirement, maxsplit=1)[0]
        for requirement in requirements
    }
    assert dependency_names == {"spawn-join-core"}
