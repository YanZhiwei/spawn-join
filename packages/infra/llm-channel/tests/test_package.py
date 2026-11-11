"""Package import and dependency-boundary tests."""

import importlib
import sys


def test_package_imports() -> None:
    package = importlib.import_module("spawn_join_llm_channel")
    assert package.__name__ == "spawn_join_llm_channel"


def test_import_does_not_load_langchain() -> None:
    assert "langchain_core" not in sys.modules
    assert "langchain" not in sys.modules
