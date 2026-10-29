"""Tri-state model capability declarations."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ModelCapabilities:
    """Known model capabilities; ``None`` means the capability is unknown."""

    context_window: int | None = None
    max_output_tokens: int | None = None
    supports_tools: bool | None = None
    supports_tool_choice: bool | None = None
    supports_tool_call_streaming: bool | None = None
    supports_parallel_tool_calls: bool | None = None
    supports_structured_output: bool | None = None
    supports_reasoning: bool | None = None
    reasoning_efforts: frozenset[str] | None = None
    supports_temperature: bool | None = None
    supports_server_state: bool | None = None
    supports_prompt_cache: bool | None = None
