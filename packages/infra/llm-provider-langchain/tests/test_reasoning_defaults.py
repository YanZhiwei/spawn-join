"""Offline request contracts for file-configured reasoning effort."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from anthropic.types import Message, TextBlock, Usage
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from spawn_join_llm_provider_langchain import load_model_catalog

_ENVIRON = {"OPENAI_API_KEY": "sk-test"}


def _write(
    tmp_path: Path,
    protocol: str,
    effort: str,
    *,
    schema_version: int = 1,
) -> Path:
    path = tmp_path / "model.yaml"
    path.write_text(
        f"schema_version: {schema_version}\n"
        "models:\n"
        "  fast:\n"
        f"    protocol: {protocol}\n"
        "    endpoint: https://api.example.com/v1\n"
        "    model: gpt-test\n"
        "    api_key_env: OPENAI_API_KEY\n"
        "    options:\n"
        f"      reasoning_effort: {effort}\n",
        encoding="utf-8",
    )
    return path


def _model(
    tmp_path: Path,
    protocol: str,
    effort: str = "low",
    *,
    schema_version: int = 1,
) -> ChatOpenAI:
    catalog = load_model_catalog(
        _write(tmp_path, protocol, effort, schema_version=schema_version)
    )
    model = catalog.create_chat_model(environ=_ENVIRON)
    assert isinstance(model, ChatOpenAI)
    return model


def _anthropic_model(
    tmp_path: Path,
    effort: str,
    *,
    schema_version: int = 1,
) -> ChatAnthropic:
    catalog = load_model_catalog(
        _write(tmp_path, "anthropic_messages", effort, schema_version=schema_version)
    )
    model = catalog.create_chat_model(environ=_ENVIRON)
    assert isinstance(model, ChatAnthropic)
    return model


def _payload(model: ChatOpenAI | ChatAnthropic, **kwargs: Any) -> dict[str, Any]:
    payload = cast(
        dict[str, Any],
        model._get_request_payload(  # pyright: ignore[reportPrivateUsage, reportUnknownMemberType]
            [HumanMessage(content="hi")],
            **kwargs,
        ),
    )
    return payload


def _completion() -> ChatCompletion:
    return ChatCompletion(
        id="chatcmpl-test",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(content="ok", role="assistant"),
            )
        ],
        created=0,
        model="gpt-test",
        object="chat.completion",
    )


def _raw_response() -> MagicMock:
    response = MagicMock()
    response.headers = {}
    response.parse.return_value = _completion()
    return response


def _capture(**_kwargs: object) -> MagicMock:
    return _raw_response()


class _NativeAnthropicResponse:
    """Offline response compatible with both `_create` return contracts."""

    def __init__(self, message: Message) -> None:
        self.headers: dict[str, str] = {}
        self._message = message

    def parse(self) -> Message:
        return self._message

    def __getattr__(self, name: str) -> object:
        return getattr(self._message, name)


def _anthropic_response() -> _NativeAnthropicResponse:
    return _NativeAnthropicResponse(
        Message(
            id="msg_test",
            content=[TextBlock(type="text", text="ok")],
            model="claude-test",
            role="assistant",
            stop_reason="end_turn",
            stop_sequence=None,
            type="message",
            usage=Usage(input_tokens=1, output_tokens=1),
        )
    )


@pytest.mark.parametrize("schema_version", [1, 2])
@pytest.mark.parametrize("effort", ["low", "medium", "high"])
def test_chat_completions_default_reaches_native_payload(
    tmp_path: Path,
    schema_version: int,
    effort: str,
) -> None:
    model = _model(tmp_path, "chat_completions", effort, schema_version=schema_version)

    payload = _payload(model)

    assert payload["reasoning_effort"] == effort
    assert "reasoning" not in payload


def test_chat_completions_override_restores_default(tmp_path: Path) -> None:
    model = _model(tmp_path, "chat_completions")

    assert _payload(model, reasoning_effort="high")["reasoning_effort"] == "high"
    assert _payload(model)["reasoning_effort"] == "low"


@pytest.mark.parametrize("schema_version", [1, 2])
@pytest.mark.parametrize("effort", ["low", "medium", "high"])
def test_responses_default_uses_nested_reasoning(
    tmp_path: Path,
    schema_version: int,
    effort: str,
) -> None:
    model = _model(tmp_path, "responses", effort, schema_version=schema_version)

    payload = _payload(model)

    assert payload["reasoning"] == {"effort": effort}
    assert "reasoning_effort" not in payload


def test_responses_override_restores_default(tmp_path: Path) -> None:
    model = _model(tmp_path, "responses")

    assert _payload(model, reasoning_effort="high")["reasoning"] == {"effort": "high"}
    assert _payload(model)["reasoning"] == {"effort": "low"}


@pytest.mark.parametrize("schema_version", [1, 2])
@pytest.mark.parametrize("effort", ["low", "medium", "high"])
def test_anthropic_default_reaches_output_config(
    tmp_path: Path,
    schema_version: int,
    effort: str,
) -> None:
    model = _anthropic_model(tmp_path, effort, schema_version=schema_version)

    payload = _payload(model)

    assert payload["output_config"] == {"effort": effort}
    assert "reasoning_effort" not in payload


def test_anthropic_override_restores_default(tmp_path: Path) -> None:
    model = _anthropic_model(tmp_path, "low")

    assert _payload(model, reasoning_effort="high")["output_config"] == {
        "effort": "high"
    }
    assert _payload(model)["output_config"] == {"effort": "low"}


@pytest.mark.parametrize("asynchronous", [False, True])
def test_anthropic_sync_and_async_override_reach_sdk_and_restore(
    tmp_path: Path,
    asynchronous: bool,
) -> None:
    model = _anthropic_model(tmp_path, "low")
    response = _anthropic_response()
    request = (
        AsyncMock(return_value=response)
        if asynchronous
        else MagicMock(return_value=response)
    )
    method = "_acreate" if asynchronous else "_create"

    with patch.object(model, method, request):
        if asynchronous:
            asyncio.run(
                model.ainvoke([HumanMessage(content="hi")], reasoning_effort="high")
            )
            assert request.call_args.args[0]["output_config"] == {"effort": "high"}
            asyncio.run(model.ainvoke([HumanMessage(content="hi")]))
            assert request.call_args.args[0]["output_config"] == {"effort": "low"}
        else:
            model.invoke([HumanMessage(content="hi")], reasoning_effort="high")
            assert request.call_args.args[0]["output_config"] == {"effort": "high"}
            model.invoke([HumanMessage(content="hi")])
            assert request.call_args.args[0]["output_config"] == {"effort": "low"}


def test_anthropic_omitted_options_omit_reasoning_effort(tmp_path: Path) -> None:
    path = tmp_path / "model.yaml"
    path.write_text(
        "schema_version: 1\n"
        "models:\n"
        "  fast:\n"
        "    protocol: anthropic_messages\n"
        "    endpoint: https://api.example.com/v1\n"
        "    model: claude-test\n"
        "    api_key_env: OPENAI_API_KEY\n",
        encoding="utf-8",
    )
    model = load_model_catalog(path).create_chat_model(environ=_ENVIRON)
    assert isinstance(model, ChatAnthropic)

    payload = _payload(model)

    assert "output_config" not in payload
    assert "reasoning_effort" not in payload


@pytest.mark.parametrize(
    "thinking_block,expected",
    [
        ("        mode: adaptive\n", {"type": "adaptive"}),
        (
            "        mode: budget\n        budget_tokens: 2048\n",
            {"type": "enabled", "budget_tokens": 2048},
        ),
    ],
)
def test_anthropic_effort_and_thinking_are_independent(
    tmp_path: Path,
    thinking_block: str,
    expected: dict[str, object],
) -> None:
    path = tmp_path / "model.yaml"
    path.write_text(
        "schema_version: 1\n"
        "models:\n"
        "  fast:\n"
        "    protocol: anthropic_messages\n"
        "    endpoint: https://api.example.com/v1\n"
        "    model: claude-test\n"
        "    api_key_env: OPENAI_API_KEY\n"
        "    options:\n"
        "      max_output_tokens: 4096\n"
        "      reasoning_effort: low\n"
        "      thinking:\n"
        f"{thinking_block}",
        encoding="utf-8",
    )
    model = load_model_catalog(path).create_chat_model(environ=_ENVIRON)
    assert isinstance(model, ChatAnthropic)

    payload = _payload(model)

    assert payload["thinking"] == expected
    assert payload["output_config"] == {"effort": "low"}

    overridden = _payload(model, reasoning_effort="high")

    assert overridden["thinking"] == expected
    assert overridden["output_config"] == {"effort": "high"}


def test_anthropic_disabled_reaches_payload_with_effort(tmp_path: Path) -> None:
    path = tmp_path / "model.yaml"
    path.write_text(
        "schema_version: 1\n"
        "models:\n"
        "  fast:\n"
        "    protocol: anthropic_messages\n"
        "    endpoint: https://api.example.com/v1\n"
        "    model: claude-test\n"
        "    api_key_env: OPENAI_API_KEY\n"
        "    options:\n"
        "      reasoning_effort: low\n"
        "      thinking:\n"
        "        mode: disabled\n",
        encoding="utf-8",
    )
    model = load_model_catalog(path).create_chat_model(environ=_ENVIRON)
    assert isinstance(model, ChatAnthropic)

    payload = _payload(model)

    assert payload["thinking"] == {"type": "disabled"}
    assert payload["output_config"] == {"effort": "low"}

    overridden = _payload(model, reasoning_effort="high")

    assert overridden["thinking"] == {"type": "disabled"}
    assert overridden["output_config"] == {"effort": "high"}


def _thinking_model(tmp_path: Path, thinking_block: str) -> ChatAnthropic:
    path = tmp_path / "model.yaml"
    path.write_text(
        "schema_version: 1\n"
        "models:\n"
        "  fast:\n"
        "    protocol: anthropic_messages\n"
        "    endpoint: https://api.example.com/v1\n"
        "    model: claude-test\n"
        "    api_key_env: OPENAI_API_KEY\n"
        "    options:\n"
        "      thinking:\n"
        f"{thinking_block}",
        encoding="utf-8",
    )
    model = load_model_catalog(path).create_chat_model(environ=_ENVIRON)
    assert isinstance(model, ChatAnthropic)
    return model


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("effort", ["low", "medium", "high"])
def test_anthropic_disabled_sync_async_three_levels(
    tmp_path: Path,
    asynchronous: bool,
    effort: str,
) -> None:
    model = _thinking_model(tmp_path, "        mode: disabled\n")
    response = _anthropic_response()
    request = (
        AsyncMock(return_value=response)
        if asynchronous
        else MagicMock(return_value=response)
    )
    method = "_acreate" if asynchronous else "_create"

    with patch.object(model, method, request):
        if asynchronous:
            asyncio.run(
                model.ainvoke([HumanMessage(content="hi")], reasoning_effort=effort)
            )
        else:
            model.invoke([HumanMessage(content="hi")], reasoning_effort=effort)

    payload = request.call_args.args[0]
    assert payload["thinking"] == {"type": "disabled"}
    assert payload["output_config"] == {"effort": effort}


def test_instance_disabled_wins_over_call_adaptive(tmp_path: Path) -> None:
    model = _thinking_model(tmp_path, "        mode: disabled\n")

    payload = _payload(model, thinking={"type": "adaptive"})

    assert payload["thinking"] == {"type": "disabled"}


def test_instance_adaptive_wins_over_call_disabled(tmp_path: Path) -> None:
    model = _thinking_model(tmp_path, "        mode: adaptive\n")

    payload = _payload(model, thinking={"type": "disabled"})

    assert payload["thinking"] == {"type": "adaptive"}


def test_unset_instance_accepts_call_disabled(tmp_path: Path) -> None:
    model = _anthropic_model(tmp_path, "low")

    payload = _payload(model, thinking={"type": "disabled"})

    assert payload["thinking"] == {"type": "disabled"}


@pytest.mark.parametrize("options_block", ["", "    options: {}\n"])
def test_omitted_options_omit_reasoning_effort(
    tmp_path: Path,
    options_block: str,
) -> None:
    path = tmp_path / "model.yaml"
    path.write_text(
        "schema_version: 1\n"
        "models:\n"
        "  fast:\n"
        "    protocol: chat_completions\n"
        "    endpoint: https://api.example.com/v1\n"
        "    model: gpt-test\n"
        "    api_key_env: OPENAI_API_KEY\n"
        f"{options_block}",
        encoding="utf-8",
    )
    catalog = load_model_catalog(path)
    model = catalog.create_chat_model(environ=_ENVIRON)
    assert isinstance(model, ChatOpenAI)

    assert "reasoning_effort" not in _payload(model)


@pytest.mark.parametrize("asynchronous", [False, True])
def test_sync_and_async_override_reach_sdk_and_restore(
    tmp_path: Path,
    asynchronous: bool,
) -> None:
    model = _model(tmp_path, "chat_completions")
    sync_create = MagicMock(side_effect=_capture)
    async_create = AsyncMock(side_effect=_capture)

    with (
        patch.object(model.client, "create", sync_create),
        patch.object(model.async_client, "create", async_create),
    ):
        if asynchronous:
            asyncio.run(
                model.ainvoke([HumanMessage(content="hi")], reasoning_effort="high")
            )
            assert async_create.call_args.kwargs["reasoning_effort"] == "high"
            asyncio.run(model.ainvoke([HumanMessage(content="hi")]))
            assert async_create.call_args.kwargs["reasoning_effort"] == "low"
        else:
            model.invoke([HumanMessage(content="hi")], reasoning_effort="high")
            assert sync_create.call_args.kwargs["reasoning_effort"] == "high"
            model.invoke([HumanMessage(content="hi")])
            assert sync_create.call_args.kwargs["reasoning_effort"] == "low"
