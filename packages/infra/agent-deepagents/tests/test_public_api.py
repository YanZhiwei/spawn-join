"""Public error-surface contract tests."""

from __future__ import annotations

import pytest
from spawn_join_agent_deepagents import (
    AgentConfigurationError,
    DelegationQueueFullError,
    DelegationTimeoutError,
    MiddlewareConfigurationError,
    ModelBindingError,
    RecoveryConfigurationError,
    SubagentConfigurationError,
    UnsupportedSyncDelegationError,
)

_SUBCLASSES = [
    ModelBindingError,
    SubagentConfigurationError,
    MiddlewareConfigurationError,
    DelegationQueueFullError,
    DelegationTimeoutError,
    UnsupportedSyncDelegationError,
    RecoveryConfigurationError,
]


@pytest.mark.parametrize("error_type", _SUBCLASSES)
def test_error_types_inherit_from_the_package_base(
    error_type: type[AgentConfigurationError],
) -> None:
    assert issubclass(error_type, AgentConfigurationError)


def test_error_message_does_not_include_the_cause_text() -> None:
    secret = "sk-live-secret-value"
    with pytest.raises(ModelBindingError) as caught:
        try:
            raise ValueError(secret)
        except ValueError as exc:
            raise ModelBindingError("models.worker: missing binding") from exc

    assert str(caught.value) == "models.worker: missing binding"
    assert secret not in str(caught.value)
    assert isinstance(caught.value.__cause__, ValueError)
