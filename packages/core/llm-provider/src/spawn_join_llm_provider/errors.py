"""Stable LLM-domain errors independent of any framework or SDK."""

from .options import ProtocolKind


class LLMError(Exception):
    """Base class for all SpawnJoin LLM-domain errors."""

    def __init__(
        self,
        message: str,
        *,
        protocol: ProtocolKind | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__(message)
        self.protocol = protocol
        self.model = model


class ConfigurationError(LLMError):
    """Invalid provider or channel configuration."""


class InvalidRequestError(LLMError):
    """A request field or cross-field combination is invalid."""


class UnsupportedParameterError(InvalidRequestError):
    """A protocol or model does not support a requested parameter."""

    def __init__(
        self,
        parameter: str,
        *,
        protocol: ProtocolKind,
        model: str,
    ) -> None:
        self.parameter = parameter
        super().__init__(
            f"Parameter {parameter!r} is not supported by "
            f"{protocol.value} for model {model!r}",
            protocol=protocol,
            model=model,
        )


class AuthenticationError(LLMError):
    """The provider rejected the supplied credentials."""


class PermissionDeniedError(LLMError):
    """The credentials are valid but lack permission for the operation."""


class RateLimitError(LLMError):
    """The provider rejected the request because of rate limiting."""


class ProviderTimeoutError(LLMError):
    """The provider did not respond within the configured timeout."""


class ProviderConnectionError(LLMError):
    """The provider endpoint could not be reached."""


class ModelNotFoundError(LLMError):
    """The requested model does not exist for the configured channel."""


class ContextOverflowError(LLMError):
    """The request exceeds the model context window."""


class MalformedResponseError(LLMError):
    """The provider response could not be parsed into the domain contract."""


class ProviderAPIError(LLMError):
    """The provider returned an error that has no more specific mapping."""


class ChannelUnavailableError(LLMError):
    """A channel cannot serve requests in its current state."""


class UnsupportedChannelOperationError(LLMError):
    """A channel does not implement the requested optional operation."""

    def __init__(self, operation: str) -> None:
        self.operation = operation
        super().__init__(f"Channel operation {operation!r} is not supported")
