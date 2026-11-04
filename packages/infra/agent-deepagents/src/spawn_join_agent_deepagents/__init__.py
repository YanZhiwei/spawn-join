"""DeepAgents product assembly, model binding, delegation, and diagnostics."""

from .diagnostics import (
    AssemblyReport,
    DelegationReport,
    DiagnosticEvent,
    DiagnosticEventType,
    DiagnosticsConfig,
    ResourceReport,
    SubagentReport,
)
from .errors import (
    AgentConfigurationError,
    DelegationQueueFullError,
    DelegationTimeoutError,
    MiddlewareConfigurationError,
    ModelBindingError,
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
from .models import ModelBinding, ModelBindings, ModelPurpose
from .recovery import RecoveryContext
from .subagents import (
    CompiledSubAgentDefinition,
    SubAgentDefinition,
    SubAgentKind,
    SubAgentMode,
)
from .supervisor import SupervisorAssembly, SupervisorSpec, build_supervisor

__all__ = [
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
]
