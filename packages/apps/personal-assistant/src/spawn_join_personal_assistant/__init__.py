"""Public API for the SpawnJoin personal assistant host application.

The host application composes the SpawnJoin distributions to run durable
work items under a confined workspace: it owns the work-item store, the
scheduler loop, HITL approvals, and the CLI. The public surface grows with
the delivery slices; every export is explicit and stable per version.
"""

from __future__ import annotations

from .approvals import (
    ApprovalBook,
    ApprovalRecord,
    apply_decision,
    interrupt_actions,
    pause_for_approval,
    resume_approved,
    resume_rejected,
)
from .config import AppConfig
from .errors import (
    HostApprovalError,
    HostConfigError,
    HostError,
    HostSchedulingError,
    HostStoreError,
    WorkTransitionError,
)
from .host import HostSession, open_host_session
from .scheduler import Scheduler, WorkExecutor
from .work.models import WorkItem, WorkStatus
from .work.store import WorkStore

__all__ = [
    "ApprovalBook",
    "ApprovalRecord",
    "AppConfig",
    "HostApprovalError",
    "HostConfigError",
    "HostError",
    "HostSchedulingError",
    "HostSession",
    "HostStoreError",
    "Scheduler",
    "WorkExecutor",
    "WorkItem",
    "WorkStatus",
    "WorkStore",
    "WorkTransitionError",
    "apply_decision",
    "interrupt_actions",
    "open_host_session",
    "pause_for_approval",
    "resume_approved",
    "resume_rejected",
]
