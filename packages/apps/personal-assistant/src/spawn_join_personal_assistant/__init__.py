"""Public API for the SpawnJoin personal assistant host application.

The host application composes the SpawnJoin distributions to run durable
work items under a confined workspace: it owns the work-item store, the
scheduler loop, HITL approvals, and the CLI. The public surface grows with
the delivery slices; every export is explicit and stable per version.
"""

from __future__ import annotations

from .config import AppConfig
from .errors import (
    HostApprovalError,
    HostConfigError,
    HostError,
    HostSchedulingError,
    HostStoreError,
)

__all__ = [
    "AppConfig",
    "HostApprovalError",
    "HostConfigError",
    "HostError",
    "HostSchedulingError",
    "HostStoreError",
]
