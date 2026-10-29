"""Contract tests for messages, requests, responses, and stream events."""

from spawn_join_llm_provider import (
    ChatRequest,
    ChatResponse,
    FinishReason,
    Message,
    OpaqueBlock,
    ReasoningBlock,
    ReasoningDelta,
    Role,
    StreamCompleted,
    TextBlock,
    TextDelta,
    ToolCallBlock,
    ToolCallDelta,
    ToolResultBlock,
    Usage,
)


def test_reasoning_blocks_do_not_share_opaque_state() -> None:
    first = ReasoningBlock(text="one")
    second = ReasoningBlock(text="two")

    assert first.opaque_state == {}
    assert second.opaque_state == {}
    assert first.opaque_state is not second.opaque_state


def test_chat_request_defaults() -> None:
    request = ChatRequest(
        messages=(Message(role=Role.USER, content=(TextBlock("hello"),)),)
    )

    assert request.tools == ()
    assert request.tool_choice == "auto"
    assert request.options is None
    assert request.request_id is None


def test_chat_response_and_usage() -> None:
    usage = Usage(
        input_tokens=10,
        output_tokens=4,
        total_tokens=14,
        reasoning_tokens=2,
        cache_read_tokens=3,
        cache_creation_tokens=None,
    )
    response = ChatResponse(
        message=Message(
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
                TextBlock("done"),
            ),
        ),
        usage=usage,
        finish_reason=FinishReason.TOOL_CALLS,
        provider_finish_reason="tool_calls",
        response_id="msg-1",
    )

    assert response.usage == usage
    assert response.message.role == Role.ASSISTANT
    assert isinstance(response.message.content[0], ReasoningBlock)
    assert response.finish_reason == FinishReason.TOOL_CALLS


def test_chat_response_allows_missing_usage() -> None:
    response = ChatResponse(
        message=Message(
            role=Role.ASSISTANT,
            content=(TextBlock("hello"),),
        ),
        usage=None,
        finish_reason=FinishReason.STOP,
    )

    assert response.usage is None


def test_tool_result_and_opaque_blocks() -> None:
    tool_result = ToolResultBlock(tool_call_id="call-1", content="ok")
    opaque = OpaqueBlock(provider_type="citation", payload={"url": "x"})

    assert tool_result.type == "tool_result"
    assert opaque.type == "opaque"


def test_stream_events_are_discriminated_by_type() -> None:
    events = [
        TextDelta("a"),
        ReasoningDelta("b"),
        ToolCallDelta(
            index=0,
            id="call-1",
            name="lookup",
            arguments_delta='{"q":',
        ),
        StreamCompleted(finish_reason=FinishReason.STOP),
    ]

    assert [type(event).__name__ for event in events] == [
        "TextDelta",
        "ReasoningDelta",
        "ToolCallDelta",
        "StreamCompleted",
    ]
