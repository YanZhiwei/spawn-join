"""Public error-surface contract tests."""

from __future__ import annotations

from importlib.metadata import requires

import pytest
import spawn_join_agent_deepagents as package
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


_S3_PUBLIC_NAMES = {
    "AgentConfigurationError",
    "AssemblyReport",
    "CompiledSubAgentDefinition",
    "DelegationConfiguration",
    "DelegationController",
    "DelegationPolicy",
    "DelegationQueueFullError",
    "DelegationReport",
    "DelegationTimeoutError",
    "DiagnosticEvent",
    "DiagnosticEventType",
    "DiagnosticsConfig",
    "MiddlewareConfiguration",
    "MiddlewareConfigurationError",
    "MiddlewareScopeReport",
    "ModelBinding",
    "ModelBindingError",
    "ModelBindings",
    "ModelPurpose",
    "RecoveryConfigurationError",
    "RecoveryContext",
    "ResourceReport",
    "SubAgentDefinition",
    "SubAgentKind",
    "SubAgentMode",
    "SubagentConfigurationError",
    "SubagentReport",
    "SupervisorAssembly",
    "SupervisorSpec",
    "UnsupportedSyncDelegationError",
    "build_supervisor",
}


def test_public_all_matches_implemented_surface() -> None:
    assert set(package.__all__) == _S3_PUBLIC_NAMES


def test_internal_modules_are_not_exported() -> None:
    for name in ("models", "subagents", "middleware", "diagnostics", "supervisor"):
        assert name not in package.__all__


def test_direct_dependencies_are_declared_and_bounded() -> None:
    requirements = "\n".join(requires("spawn-join-agent-deepagents") or [])
    lowered = requirements.lower()

    assert "deepagents" in lowered
    assert "langchain-core" in lowered
    assert "spawn-join-llm-provider-langchain" in lowered
    assert "spawn-join-llm-model-sync" not in lowered
    assert "spawn-join-observability" not in lowered
