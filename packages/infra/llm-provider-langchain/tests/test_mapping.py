"""Tests for LangChain/domain mapping without network access."""

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage, ToolMessage
from langchain_core.messages.ai import UsageMetadata

from spawn_join_llm_provider import (
    FinishReason,
    Message,
    OpaqueBlock,
    ReasoningBlock,
    ReasoningDelta,
    Role,
    TextBlock,
    TextDelta,
    ToolCallBlock,
    ToolCallDelta,
    ToolResultBlock,
)
from spawn_join_llm_provider_langchain.mapping import (
    capabilities_from_profile,
    finish_reason_from_value,
    from_langchain_message,
    from_langchain_usage,
    stream_events_from_chunk,
    to_langchain_messages,
)


def test_domain_messages_to_langchain() -> None:
    messages = (
        Message(role=Role.SYSTEM, content=(TextBlock("system"),)),
        Message(role=Role.USER, content=(TextBlock("hello"),)),
        Message(
            role=Role.ASSISTANT,
            content=(
                ReasoningBlock(
                    text="thinking",
                    opaque_state={"signature": "sig"},
                ),
                ToolCallBlock(
                    id="call-1",
                    name="lookup",
                    arguments={"query": "x"},
                ),
            ),
        ),
        Message(
            role=Role.TOOL,
            content=(ToolResultBlock(tool_call_id="call-1", content="result"),),
        ),
    )

    converted = to_langchain_messages(messages)

    assert isinstance(converted[0], HumanMessage) is False
    assert isinstance(converted[1], HumanMessage) is True
    assert isinstance(converted[2], AIMessage) is True
    assert isinstance(converted[3], ToolMessage) is True
    assistant = converted[2]
    assert isinstance(assistant, AIMessage)
    assert assistant.tool_calls[0]["name"] == "lookup"
    assert assistant.content_blocks[0]["type"] == "reasoning"


def test_tool_call_only_assistant_message_roundtrips() -> None:
    domain = Message(
        role=Role.ASSISTANT,
        content=(
            ToolCallBlock(
                id="call-1",
                name="lookup",
                arguments={"query": "x"},
            ),
        ),
    )

    converted = to_langchain_messages((domain,))

    assert isinstance(converted[0], AIMessage)
    assert converted[0].content == []
    assert converted[0].tool_calls[0]["name"] == "lookup"


def test_langchain_message_to_domain() -> None:
    message = AIMessage(
        content=[
            {"type": "text", "text": "answer"},
            {
                "type": "reasoning",
                "reasoning": "why",
                "extras": {"signature": "sig"},
            },
            {
                "type": "non_standard",
                "value": {"provider_type": "citation", "payload": {"id": 1}},
            },
        ],
        tool_calls=[
            {
                "type": "tool_call",
                "id": "call-1",
                "name": "lookup",
                "args": {"query": "x"},
            }
        ],
    )

    converted = from_langchain_message(message)

    assert converted.role == Role.ASSISTANT
    assert isinstance(converted.content[0], TextBlock)
    assert isinstance(converted.content[1], ReasoningBlock)
    assert converted.content[1].opaque_state == {"signature": "sig"}
    assert isinstance(converted.content[2], OpaqueBlock)
    assert isinstance(converted.content[3], ToolCallBlock)
    assert converted.content[3].arguments == {"query": "x"}


def test_usage_mapping_preserves_details() -> None:
    usage: UsageMetadata = {
        "input_tokens": 10,
        "output_tokens": 4,
        "total_tokens": 14,
        "input_token_details": {"cache_read": 3, "cache_creation": 2},
        "output_token_details": {"reasoning": 1},
    }

    converted = from_langchain_usage(usage)

    assert converted is not None
    assert converted.input_tokens == 10
    assert converted.reasoning_tokens == 1
    assert converted.cache_read_tokens == 3
    assert converted.cache_creation_tokens == 2


def test_stream_chunk_mapping() -> None:
    chunk = AIMessageChunk(
        content=[
            {"type": "text", "text": "hello"},
            {"type": "reasoning", "reasoning": "why"},
        ],
        tool_call_chunks=[
            {
                "type": "tool_call_chunk",
                "id": "call-1",
                "name": "lookup",
                "args": '{"q":',
                "index": 0,
            }
        ],
    )

    events = stream_events_from_chunk(chunk)

    assert isinstance(events[0], TextDelta)
    assert isinstance(events[1], ReasoningDelta)
    assert isinstance(events[2], ToolCallDelta)
    assert events[2].arguments_delta == '{"q":'


def test_finish_reason_mapping() -> None:
    assert finish_reason_from_value("end_turn") is FinishReason.STOP
    assert finish_reason_from_value("max_tokens") is FinishReason.LENGTH
    assert finish_reason_from_value("tool_use") is FinishReason.TOOL_CALLS
    assert finish_reason_from_value("unexpected") is FinishReason.UNKNOWN
    assert finish_reason_from_value(None) is FinishReason.UNKNOWN


def test_capabilities_from_profile() -> None:
    capabilities = capabilities_from_profile(
        {
            "max_input_tokens": 1000,
            "max_output_tokens": 200,
            "tool_calling": True,
            "tool_choice": True,
            "tool_call_streaming": True,
            "structured_output": True,
            "reasoning_output": True,
            "reasoning_effort_levels": ["low", "high"],
            "temperature": False,
        }
    )

    assert capabilities.context_window == 1000
    assert capabilities.max_output_tokens == 200
    assert capabilities.supports_tools is True
    assert capabilities.reasoning_efforts == frozenset({"low", "high"})
    assert capabilities.supports_temperature is False
    assert capabilities.supports_parallel_tool_calls is None
