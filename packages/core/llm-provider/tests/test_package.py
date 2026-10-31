"""Check framework-independent package imports and dependencies."""

import re
from importlib import import_module, metadata
from importlib.resources import files


def test_package_is_importable() -> None:
    module = import_module("spawn_join_llm_provider")
    assert module.__file__ is not None


def test_distribution_identity() -> None:
    assert (
        metadata.metadata("spawn-join-llm-provider")["Name"]
        == "spawn-join-llm-provider"
    )


def test_py_typed_marker_is_packaged() -> None:
    assert (files("spawn_join_llm_provider") / "py.typed").is_file()


def test_protocol_only_depends_on_core() -> None:
    requirements = metadata.requires("spawn-join-llm-provider") or []
    dependency_names = {
        re.split(r"[<>=!~;\[\s]", requirement, maxsplit=1)[0]
        for requirement in requirements
    }
    assert dependency_names == {"spawn-join-core"}
