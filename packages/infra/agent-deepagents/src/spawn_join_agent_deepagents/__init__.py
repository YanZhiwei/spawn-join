"""DeepAgents product assembly, model binding, delegation, and diagnostics."""

from .context_sources import MemoryConfiguration, SkillsConfiguration
from .diagnostics import (
    AssemblyReport,
    AsyncDiagnosticCallback,
    ContextReport,
    DelegationReport,
    DiagnosticCallback,
    DiagnosticEvent,
    DiagnosticEventType,
    DiagnosticsConfig,
    ProfileReport,
    ResourceReport,
    SubagentReport,
)
from .errors import (
    AgentConfigurationError,
    ContextConfigurationError,
    DelegationQueueFullError,
    DelegationTimeoutError,
    MiddlewareConfigurationError,
    ModelBindingError,
    ProfileConfigurationError,
    RecoveryConfigurationError,
    SubagentConfigurationError,
    UnsupportedSyncDelegationError,
)
from .execution import (
    DelegationConfiguration,
    DelegationController,
    DelegationPolicy,
)
from .middleware import MiddlewareConfiguration, MiddlewareScopeReport
from .models import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    ResolvedModelBindings,
)
from .profiles import (
    HarnessProfileBinding,
    ProfilesConfiguration,
    ProviderProfileBinding,
)
from .recovery import RecoveryContext
from .subagents import (
    AsyncSubAgentDefinition,
    CompiledSubAgentDefinition,
    SubAgentDefinition,
    SubAgentKind,
    SubAgentMode,
)
from .supervisor import SupervisorAssembly, SupervisorSpec, build_supervisor

__all__ = [
    "AgentConfigurationError",
    "AssemblyReport",
    "AsyncDiagnosticCallback",
    "AsyncSubAgentDefinition",
    "CompiledSubAgentDefinition",
    "ContextConfigurationError",
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
    "MemoryConfiguration",
    "MiddlewareConfiguration",
    "MiddlewareConfigurationError",
    "MiddlewareScopeReport",
    "ModelBinding",
    "ModelBindingError",
    "ModelBindings",
    "ModelPurpose",
    "ProfileConfigurationError",
    "ProfileReport",
    "ProfilesConfiguration",
    "ProviderProfileBinding",
    "RecoveryConfigurationError",
    "RecoveryContext",
    "ResolvedModelBindings",
    "ResourceReport",
    "SkillsConfiguration",
    "SubAgentDefinition",
    "SubAgentKind",
    "SubAgentMode",
    "SubagentConfigurationError",
    "SubagentReport",
    "SupervisorAssembly",
    "SupervisorSpec",
    "UnsupportedSyncDelegationError",
    "build_supervisor",
]
