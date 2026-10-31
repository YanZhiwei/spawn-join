"""LangChain-first model factory for SpawnJoin LLM channels."""

from .config import ChatModelConfig
from .factory import create_chat_model

__all__ = ["ChatModelConfig", "create_chat_model"]
