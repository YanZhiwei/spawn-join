"""Characterize the private schema refactor through both public file loaders."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Literal

import pytest
import yaml
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import StrictInt, ValidationError

from spawn_join_llm_provider import ConfigurationError
from spawn_join_llm_provider_langchain import ModelCatalog, load_model_catalog
from spawn_join_llm_provider_langchain.model_file._validation import (
    FileInput,
    validate_input,
)


@pytest.fixture(params=["function", "classmethod"])
def loader(request: pytest.FixtureRequest) -> Literal["function", "classmethod"]:
    return "function" if request.param == "function" else "classmethod"


def _load(
    tmp_path: Path,
    protocol: str,
    options: object,
    loader: Literal["function", "classmethod"],
    version: int = 1,
    entry_overrides: Mapping[str, object] | None = None,
) -> ModelCatalog:
    entry: dict[str, object] = {
        "protocol": protocol,
        "endpoint": "https://api.example.com/v1",
        "model": "example-model",
        "api_key_env": "EXAMPLE_KEY",
        "options": options,
    }
    if entry_overrides is not None:
        entry.update(entry_overrides)
    document = {
        "schema_version": version,
        "models": {"demo": entry},
    }
    path = tmp_path / "model.yaml"
    path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    if loader == "classmethod":
        return ModelCatalog.from_file(path, env_file=None)
    return load_model_catalog(path, env_file=None)


@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize(
    ("protocol", "options", "message"),
    [
        ("chat_completions", None, "models.demo.options: must be a mapping"),
        (
            "chat_completions",
            {"temperature": None},
            "models.demo.options.temperature: must be a number",
        ),
        (
            "chat_completions",
            {"seed": True},
            "models.demo.options.seed: must be an integer",
        ),
        (
            "responses",
            {"store": 0},
            "models.demo.options.store: must be a boolean",
        ),
        (
            "responses",
            {"reasoning_effort": None},
            "models.demo.options.reasoning_effort: must be a string",
        ),
        (
            "responses",
            {"reasoning_effort": "invalid-secret-sentinel"},
            "models.demo.options: reasoning_effort must be one of: low, medium, high",
        ),
        (
            "chat_completions",
            {"stop": ["ok", ""]},
            "models.demo.options.stop[1]: must be a non-empty string",
        ),
        (
            "chat_completions",
            {"api_key": "secret-sentinel"},
            "models.demo.options: unknown field(s): api_key",
        ),
        (
            "anthropic_messages",
            {"thinking": None},
            "models.demo.options.thinking: must be a mapping",
        ),
        (
            "anthropic_messages",
            {"thinking": {"mode": "adaptive", "budget_tokens": None}},
            "models.demo.options.thinking: budget_tokens is not allowed "
            "for adaptive thinking",
        ),
        (
            "anthropic_messages",
            {"thinking": {"mode": "budget"}},
            "models.demo.options.thinking: budget_tokens is required for budget thinking",
        ),
        (
            "anthropic_messages",
            {"thinking": {"mode": "budget", "budget_tokens": 1023}},
            "models.demo.options.thinking: thinking budget_tokens must be at least 1024",
        ),
    ],
)
def test_file_schema_keeps_strict_errors(
    tmp_path: Path,
    protocol: str,
    options: object,
    message: str,
    version: int,
    loader: Literal["function", "classmethod"],
) -> None:
    with pytest.raises(ConfigurationError) as error:
        _load(tmp_path, protocol, options, loader, version)
    assert str(error.value) == message
    assert "secret-sentinel" not in str(error.value)


@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize(
    "protocol", ["chat_completions", "responses", "anthropic_messages"]
)
def test_file_schema_keeps_empty_options_and_defaults(
    tmp_path: Path,
    protocol: str,
    version: int,
    loader: Literal["function", "classmethod"],
) -> None:
    catalog = _load(tmp_path, protocol, {}, loader, version)
    model = catalog.create_chat_model(environ={"EXAMPLE_KEY": "offline-fake-key"})
    assert catalog.default_name == "demo"
    assert isinstance(model, (ChatOpenAI, ChatAnthropic))
    assert model.max_retries == 0
    assert model.temperature is None


def test_domain_error_keeps_its_cause(
    tmp_path: Path, loader: Literal["function", "classmethod"]
) -> None:
    with pytest.raises(ConfigurationError) as error:
        _load(tmp_path, "chat_completions", {"temperature": 3}, loader)
    assert (
        str(error.value)
        == "models.demo.options: temperature must be between 0.0 and 2.0"
    )
    assert isinstance(error.value.__cause__, ConfigurationError)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        (
            {"protocol": "unsupported", "model": None},
            "models.demo.protocol: unsupported protocol 'unsupported'",
        ),
        (
            {"model": " padded ", "display_name": None},
            "models.demo: Chat model must be non-empty without surrounding whitespace",
        ),
        (
            {"metadata_ref": "invalid", "display_name": None},
            "models.demo.metadata_ref: must use <lab>/<model>",
        ),
    ],
)
def test_file_schema_preserves_validation_order(
    tmp_path: Path,
    overrides: Mapping[str, object],
    message: str,
    loader: Literal["function", "classmethod"],
) -> None:
    with pytest.raises(ConfigurationError) as error:
        _load(tmp_path, "chat_completions", {}, loader, 2, overrides)
    assert str(error.value) == message


class _StrictInput(FileInput):
    count: StrictInt


def test_validation_helper_does_not_render_foreign_error_input() -> None:
    with pytest.raises(ConfigurationError) as error:
        validate_input(_StrictInput, {"count": "secret-sentinel"}, "models.demo")
    assert str(error.value) == "models.demo: invalid configuration"
    assert isinstance(error.value.__cause__, ValidationError)
    assert "secret-sentinel" not in str(error.value)
