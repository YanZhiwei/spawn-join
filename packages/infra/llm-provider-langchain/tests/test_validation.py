"""Tests for preflight request, option, and capability validation."""

from typing import Any, cast

import pytest

from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    AnthropicThinkingAdaptive,
    AnthropicThinkingBudget,
    ChatCompletionsOptions,
    ChatRequest,
    InvalidRequestError,
    Message,
    ModelCapabilities,
    NamedToolChoice,
    ProtocolKind,
    ResponsesOptions,
    Role,
    TextBlock,
    ToolDefinition,
    ToolResultBlock,
    UnsupportedParameterError,
)
from spawn_join_llm_provider_langchain.validation import validate_request


def _request(**kwargs: Any) -> ChatRequest:
    defaults: dict[str, Any] = {
        "messages": (Message(role=Role.USER, content=(TextBlock("hello"),)),)
    }
    defaults.update(kwargs)
    return ChatRequest(**defaults)


def _validate(
    request: ChatRequest,
    *,
    protocol: ProtocolKind = ProtocolKind.CHAT_COMPLETIONS,
    capabilities: ModelCapabilities | None = None,
) -> None:
    validate_request(
        request,
        protocol=protocol,
        model="test-model",
        capabilities=capabilities or ModelCapabilities(),
    )


def test_valid_common_request() -> None:
    _validate(_request())


@pytest.mark.parametrize(
    "chat_request",
    [
        _request(messages=()),
        _request(max_output_tokens=0),
        _request(temperature=-0.1),
        _request(top_p=1.1),
        _request(request_id=" "),
    ],
)
def test_invalid_common_fields(chat_request: ChatRequest) -> None:
    with pytest.raises(InvalidRequestError):
        _validate(chat_request)


def test_tool_choice_must_reference_known_tool() -> None:
    request = _request(
        tools=(ToolDefinition(name="lookup", description="lookup"),),
        tool_choice=NamedToolChoice(name="missing"),
    )
    with pytest.raises(InvalidRequestError):
        _validate(request)


def test_required_tool_choice_needs_tools() -> None:
    with pytest.raises(InvalidRequestError):
        _validate(_request(tool_choice="required"))


def test_tool_result_must_be_in_tool_role() -> None:
    request = _request(
        messages=(
            Message(
                role=Role.USER,
                content=(ToolResultBlock(tool_call_id="call-1", content="x"),),
            ),
        )
    )
    with pytest.raises(InvalidRequestError):
        _validate(request)


def test_tool_role_requires_tool_result() -> None:
    request = _request(
        messages=(Message(role=Role.TOOL, content=(TextBlock("not a result"),)),)
    )
    with pytest.raises(InvalidRequestError):
        _validate(request)


def test_options_type_must_match_protocol() -> None:
    request = _request(options=ResponsesOptions())
    with pytest.raises(UnsupportedParameterError):
        _validate(request, protocol=ProtocolKind.CHAT_COMPLETIONS)


def test_chat_completions_options_validation() -> None:
    with pytest.raises(InvalidRequestError):
        _validate(_request(options=ChatCompletionsOptions(stop=("",))))
    invalid_effort = ChatCompletionsOptions(reasoning_effort=cast(Any, "invalid"))
    with pytest.raises(InvalidRequestError):
        _validate(_request(options=invalid_effort))


def test_responses_options_validation() -> None:
    with pytest.raises(InvalidRequestError):
        _validate(
            _request(options=ResponsesOptions(previous_response_id=" ")),
            protocol=ProtocolKind.RESPONSES,
        )
    invalid_truncation = ResponsesOptions(truncation=cast(Any, "unknown"))
    with pytest.raises(InvalidRequestError):
        _validate(
            _request(options=invalid_truncation),
            protocol=ProtocolKind.RESPONSES,
        )


def test_anthropic_budget_requires_larger_max_output() -> None:
    with pytest.raises(InvalidRequestError):
        _validate(
            _request(
                max_output_tokens=4096,
                options=AnthropicMessagesOptions(
                    thinking=AnthropicThinkingBudget(budget_tokens=100)
                ),
            ),
            protocol=ProtocolKind.ANTHROPIC_MESSAGES,
        )


def test_anthropic_budget_requires_max_output() -> None:
    with pytest.raises(InvalidRequestError):
        _validate(
            _request(
                options=AnthropicMessagesOptions(
                    thinking=AnthropicThinkingBudget(budget_tokens=2048)
                )
            ),
            protocol=ProtocolKind.ANTHROPIC_MESSAGES,
        )


def test_anthropic_budget_rejects_non_unit_temperature() -> None:
    with pytest.raises(InvalidRequestError):
        _validate(
            _request(
                max_output_tokens=4096,
                temperature=0.5,
                options=AnthropicMessagesOptions(
                    thinking=AnthropicThinkingBudget(budget_tokens=2048)
                ),
            ),
            protocol=ProtocolKind.ANTHROPIC_MESSAGES,
        )


def test_anthropic_thinking_rejects_top_k() -> None:
    with pytest.raises(UnsupportedParameterError):
        _validate(
            _request(
                max_output_tokens=4096,
                options=AnthropicMessagesOptions(
                    thinking=AnthropicThinkingBudget(budget_tokens=2048),
                    top_k=5,
                ),
            ),
            protocol=ProtocolKind.ANTHROPIC_MESSAGES,
        )


def test_anthropic_adaptive_thinking_is_valid() -> None:
    _validate(
        _request(
            options=AnthropicMessagesOptions(
                thinking=AnthropicThinkingAdaptive(display="summarized")
            )
        ),
        protocol=ProtocolKind.ANTHROPIC_MESSAGES,
    )


def test_capability_rejection_precedes_call() -> None:
    capabilities = ModelCapabilities(
        supports_tools=False,
        supports_temperature=False,
        max_output_tokens=10,
        supports_reasoning=False,
    )
    with pytest.raises(UnsupportedParameterError):
        _validate(
            _request(
                tools=(ToolDefinition(name="lookup", description="lookup"),),
                temperature=0.2,
            ),
            capabilities=capabilities,
        )
    with pytest.raises(InvalidRequestError):
        _validate(_request(max_output_tokens=11), capabilities=capabilities)
    with pytest.raises(UnsupportedParameterError):
        _validate(
            _request(options=ChatCompletionsOptions(reasoning_effort="low")),
            capabilities=capabilities,
        )


def test_reasoning_effort_must_be_in_known_set() -> None:
    with pytest.raises(UnsupportedParameterError):
        _validate(
            _request(options=ChatCompletionsOptions(reasoning_effort="high")),
            capabilities=ModelCapabilities(
                supports_reasoning=True,
                reasoning_efforts=frozenset({"low"}),
            ),
        )
