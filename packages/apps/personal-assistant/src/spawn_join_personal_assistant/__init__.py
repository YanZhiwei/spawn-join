"""SpawnJoin 个人助理宿主应用的公共 API。

宿主应用组合 SpawnJoin 各 Distribution，在受限工作区下运行可持久化的
工作项：它拥有工作项存储、调度循环、HITL 审批和 CLI。公共面随交付
切片增长；每个导出都是显式且按版本稳定的。
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
from .cli import main
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
    "main",
    "open_host_session",
    "pause_for_approval",
    "resume_approved",
    "resume_rejected",
]
