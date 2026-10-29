"""Common LLM provider protocol independent of frameworks and SDKs."""

from collections.abc import AsyncIterator
from typing import Protocol

from ..capabilities import ModelCapabilities
from ..models import ChatRequest, ChatResponse, StreamEvent
from ..options import ProtocolKind


class LLMProvider(Protocol):
    """A configured model-inference capability."""

    @property
    def protocol(self) -> ProtocolKind:
        """Return the protocol selected by the channel configuration."""
        ...

    @property
    def model(self) -> str:
        """Return the model identifier selected by the configuration."""
        ...

    @property
    def capabilities(self) -> ModelCapabilities:
        """Return known capabilities, with unknown fields left as ``None``."""
        ...

    async def complete(self, request: ChatRequest) -> ChatResponse:
        """Execute one non-streaming request."""
        ...

    def stream(self, request: ChatRequest) -> AsyncIterator[StreamEvent]:
        """Execute one streaming request."""
        ...
