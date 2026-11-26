"""Public error-surface contract tests."""

from __future__ import annotations

from importlib.metadata import metadata, requires

import pytest
import spawn_join_agent_deepagents as package
import spawn_join_agent_deepagents.llm_errors as llm_errors
import spawn_join_agent_deepagents.middleware as middleware
from spawn_join_agent_deepagents import (
    AgentConfigurationError,
    ContextConfigurationError,
    DelegationQueueFullError,
    DelegationTimeoutError,
    MiddlewareConfigurationError,
    ModelBindingError,
    ProfileConfigurationError,
    RecoveryConfigurationError,
    RubricConfigurationError,
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
    ContextConfigurationError,
    ProfileConfigurationError,
    RubricConfigurationError,
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


_CURRENT_PUBLIC_NAMES = {
    "AgentConfigurationError",
    "AssemblyReport",
    "AsyncDiagnosticCallback",
    "AsyncSubAgentDefinition",
    "CompiledSubAgentDefinition",
    "ContextConfigurationError",
    "ContextOverflowLLMError",
    "ContextReport",
    "DelegationConfiguration",
    "DelegationController",
    "DelegationPolicy",
    "DelegationQueueFullError",
    "DelegationReport",
    "DelegationTimeoutError",
    "DiagnosticCallback",
    "DiagnosticEvent",
    "DiagnosticEventType",
    "DiagnosticsConfig",
    "HarnessProfileBinding",
    "LLMCallError",
    "LLMErrorCode",
    "LLMErrorNormalizationMiddleware",
    "MemoryConfiguration",
    "MiddlewareConfiguration",
    "MiddlewareConfigurationError",
    "MiddlewareScopeReport",
    "ModelBinding",
    "ModelBindingError",
    "ModelBindings",
    "ModelPurpose",
    "PendingInterrupt",
    "PermissionReport",
    "ProfileConfigurationError",
    "ProfileReport",
    "ProfilesConfiguration",
    "ProviderProfileBinding",
    "RecoveryConfigurationError",
    "RecoveryContext",
    "ResolvedModelBindings",
    "ResourceReport",
    "RubricConfiguration",
    "RubricConfigurationError",
    "RubricReport",
    "SkillsConfiguration",
    "SubAgentDefinition",
    "SubAgentKind",
    "SubAgentMode",
    "SubagentConfigurationError",
    "SubagentReport",
    "SupervisorAssembly",
    "SupervisorSpec",
    "UnsupportedSyncDelegationError",
    "approve_decision",
    "build_supervisor",
    "classify_llm_error",
    "edit_decision",
    "normalize_llm_error",
    "pending_interrupts",
    "reject_decision",
    "respond_decision",
    "resume_batched",
    "resume_per_call",
    "resume_with",
}


def test_public_all_matches_implemented_surface() -> None:
    assert set(package.__all__) == _CURRENT_PUBLIC_NAMES
    for name in package.__all__:
        assert hasattr(package, name), name


def test_internal_modules_are_not_exported() -> None:
    for name in (
        "models",
        "subagents",
        "middleware",
        "diagnostics",
        "supervisor",
        "backends",
        "rubric",
        "interrupts",
    ):
        assert name not in package.__all__


def test_legacy_import_entries_resolve_to_canonical_objects() -> None:
    assert llm_errors.LLMErrorNormalizationMiddleware is (
        package.LLMErrorNormalizationMiddleware
    )
    assert llm_errors.classify_llm_error is package.classify_llm_error
    assert llm_errors.normalize_llm_error is package.normalize_llm_error
    assert middleware.MiddlewareConfiguration is package.MiddlewareConfiguration
    assert middleware.MiddlewareScopeReport is package.MiddlewareScopeReport
    assert middleware.LLM_ERROR_MIDDLEWARE_NAME == "spawn_join_llm_error_normalization"


def test_direct_dependencies_are_declared_and_bounded() -> None:
    requirements = "\n".join(requires("spawn-join-agent-deepagents") or [])
    lowered = requirements.lower()

    assert "deepagents" in lowered
    assert "langchain-core" in lowered
    assert "langgraph" in lowered
    assert "spawn-join-llm-provider-langchain" in lowered
    assert "spawn-join-llm-model-sync" not in lowered
    assert "spawn-join-observability" not in lowered


def test_mcp_dependencies_are_optional_and_bounded() -> None:
    distribution = metadata("spawn-join-agent-deepagents")
    assert "mcp" in distribution.get_all("Provides-Extra", [])
    requirements = requires("spawn-join-agent-deepagents") or []
    optional = [item for item in requirements if 'extra == "mcp"' in item]
    assert any(item.startswith("langchain[mcp]") for item in optional)
    assert any(item.startswith("fastmcp<5.0,>=4.0.11") for item in optional)
    assert any(item.startswith("spawn-join-common<0.2.0,>=0.0.1.dev0") for item in optional)
    assert not any(
        item.startswith(("fastmcp", "mcp")) and ";" not in item for item in requirements
    )


def test_mcp_namespace_exports_the_complete_optional_surface() -> None:
    import spawn_join_agent_deepagents.mcp as mcp

    assert set(mcp.__all__) == {
        "McpCleanupError",
        "McpConfigurationError",
        "McpLoadError",
        "McpLoadReport",
        "McpServerReport",
        "McpTools",
        "open_mcp_tools",
    }
    assert callable(mcp.open_mcp_tools)
    assert not set(mcp.__all__).intersection(package.__all__)
