"""Backend classification and permission summaries for assembly reporting."""

from __future__ import annotations

from collections.abc import Sequence

from deepagents.backends import (
    BackendProtocol,
    CompositeBackend,
    ContextHubBackend,
    FilesystemBackend,
    LangSmithSandbox,
    LocalShellBackend,
    StateBackend,
    StoreBackend,
)
from deepagents.middleware.filesystem import FilesystemPermission

from .diagnostics import PermissionReport


def backend_kind(backend: BackendProtocol | None) -> str:
    """Return a stable, non-secret label for a host-provided backend."""

    if backend is None:
        return "default_state"
    if isinstance(backend, LocalShellBackend):
        return "local_shell"
    if isinstance(backend, LangSmithSandbox):
        return "sandbox"
    if isinstance(backend, StateBackend):
        return "state"
    if isinstance(backend, StoreBackend):
        return "store"
    if isinstance(backend, CompositeBackend):
        return "composite"
    if isinstance(backend, FilesystemBackend):
        return "filesystem"
    if isinstance(backend, ContextHubBackend):
        return "context_hub"
    return "custom"


def permission_report(
    permissions: Sequence[FilesystemPermission] | None,
) -> PermissionReport:
    """Count permission rules by effect without exposing paths or rules."""

    allow = deny = interrupt = 0
    for permission in permissions or ():
        if permission.mode == "allow":
            allow += 1
        elif permission.mode == "deny":
            deny += 1
        elif permission.mode == "interrupt":
            interrupt += 1
    return PermissionReport(allow=allow, deny=deny, interrupt=interrupt)
