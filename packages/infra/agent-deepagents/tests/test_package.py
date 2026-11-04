"""Package metadata and offline test-helper smoke tests."""

from __future__ import annotations

from importlib.metadata import version
from importlib.resources import files

import spawn_join_agent_deepagents as package
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage


def test_package_metadata() -> None:
    assert version("spawn-join-agent-deepagents") == "0.1.0"
    assert package.__doc__ is not None


def test_py_typed_is_packaged() -> None:
    typed = files("spawn_join_agent_deepagents").joinpath("py.typed")
    assert typed.is_file()


def test_fake_chat_model_is_deterministic(fake_chat_model: BaseChatModel) -> None:
    first = fake_chat_model.invoke([HumanMessage(content="hello")])
    second = fake_chat_model.invoke([HumanMessage(content="hello")])
    assert first.content == "first"
    assert second.content == "second"
