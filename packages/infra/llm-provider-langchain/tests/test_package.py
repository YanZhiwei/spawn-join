"""Check the LangChain adapter package identity and dependency boundary."""

import re
from importlib import import_module, metadata


def test_package_is_importable() -> None:
    module = import_module("spawn_join_llm_provider_langchain")
    assert module.__file__ is not None


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
        "langchain-openai",
        "langchain-anthropic",
        "pydantic",
    }
