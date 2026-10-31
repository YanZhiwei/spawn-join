"""Stable errors for LLM protocol options and channels."""


class LLMProviderError(Exception):
    """Base class for stable LLM provider and channel errors."""


class ConfigurationError(LLMProviderError):
    """Invalid protocol options, channel configuration or model configuration."""


class ChannelError(LLMProviderError):
    """Base class for channel operation failures."""


class ChannelUnavailableError(ChannelError):
    """A channel could not complete an operation because it was unavailable."""


class UnsupportedChannelOperationError(ChannelError):
    """A channel does not support the requested operation."""


class ChannelResponseError(ChannelError):
    """A channel returned a malformed or unparseable response."""
