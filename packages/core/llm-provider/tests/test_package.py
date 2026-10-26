"""Check framework-independent LLM package imports and dependencies."""

import re
from importlib import import_module, metadata

import pytest


@pytest.mark.parametrize(
    "module_name",
    ["spawn_join_llm_provider", "spawn_join_llm_provider.abstractions"],
)
def test_existing_modules_are_importable(module_name: str) -> None:
    assert import_module(module_name).__file__ is not None


def test_distribution_identity() -> None:
    assert (
        metadata.metadata("spawn-join-llm-provider")["Name"]
        == "spawn-join-llm-provider"
    )


def test_protocol_only_depends_on_core() -> None:
    requirements = metadata.requires("spawn-join-llm-provider") or []
    dependency_names = {
        re.split(r"[<>=!~;\[\s]", requirement, maxsplit=1)[0]
        for requirement in requirements
    }
    assert dependency_names == {"spawn-join-core"}
