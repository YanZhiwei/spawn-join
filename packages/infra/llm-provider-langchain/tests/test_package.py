"""Check the existing adapter namespaces and framework ownership."""

import re
from importlib import import_module, metadata

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "spawn_join_llm_provider_langchain",
        "spawn_join_llm_provider_langchain.providers",
        "spawn_join_llm_provider_langchain.providers.azure_openai",
        "spawn_join_llm_provider_langchain.providers.deepseek",
    ],
)
def test_existing_modules_are_importable(module_name: str) -> None:
    assert import_module(module_name).__file__ is not None


def test_distribution_identity() -> None:
    assert (
        metadata.metadata("spawn-join-llm-provider-langchain")["Name"]
        == "spawn-join-llm-provider-langchain"
    )


def test_framework_dependency_belongs_to_adapter() -> None:
    requirements = metadata.requires("spawn-join-llm-provider-langchain") or []
    dependency_names = {
        re.split(r"[<>=!~;\[\s]", requirement, maxsplit=1)[0]
        for requirement in requirements
    }
    assert dependency_names == {
        "spawn-join-llm-provider",
        "langchain-core",
        "langchain-anthropic",
        "langchain-openai",
    }
