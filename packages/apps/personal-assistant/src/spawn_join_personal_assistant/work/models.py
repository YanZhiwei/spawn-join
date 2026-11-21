"""个人助理宿主的工作项状态机。

工作项是一个可持久化、可恢复的 agent 工作单元。``WorkStatus`` 与
``transition_allowed`` 是合法迁移的唯一权威；store 在每次写入时强制
执行它们，使非法迁移大声失败，而不是静默改写历史。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class WorkStatus(StrEnum):
    """可持久化工作项的生命周期状态。"""

    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


_ALLOWED_TRANSITIONS: dict[WorkStatus, frozenset[WorkStatus]] = {
    WorkStatus.QUEUED: frozenset({WorkStatus.RUNNING, WorkStatus.CANCELLED}),
    WorkStatus.RUNNING: frozenset(
        {
            # 中断重跑：被硬杀或父级取消的运行回到队列，恢复时恰好再执行一次。
            WorkStatus.QUEUED,
            WorkStatus.WAITING_APPROVAL,
            WorkStatus.COMPLETED,
            WorkStatus.FAILED,
            WorkStatus.CANCELLED,
        }
    ),
    WorkStatus.WAITING_APPROVAL: frozenset(
        {
            WorkStatus.RUNNING,
            WorkStatus.FAILED,
            WorkStatus.CANCELLED,
        }
    ),
    WorkStatus.COMPLETED: frozenset(),
    WorkStatus.FAILED: frozenset(),
    WorkStatus.CANCELLED: frozenset(),
}


def transition_allowed(current: WorkStatus, target: WorkStatus) -> bool:
    """报告状态机是否允许 ``current`` -> ``target``。"""

    return target in _ALLOWED_TRANSITIONS[current]


@dataclass(frozen=True, slots=True)
class WorkItem:
    """一个可持久化的 agent 工作单元及其生命周期字段。

    字段:
        id: store 分配的唯一标识（UUID hex）。
        idempotency_key: 调用方提供的键，跨工作项唯一；重放同一键不会
            创建第二个工作项或副作用。
        goal: 交给 agent 运行的非空自然语言目标。
        status: 当前生命周期状态。
        created_at / updated_at: ISO-8601 UTC 时间戳。
        due_at: 可选的 ISO-8601 UTC 到期时间，到期后工作项才可运行。
        deadline_seconds: 单次尝试的可选总运行预算。
        attempts: 已启动的运行次数；queued->running 时递增。
        result_summary: 可选的人类可读完成摘要。
        failure_category: 可选的稳定失败类别（如 timeout）。
        thread_id: 与本工作项关联的可选 checkpointer thread。
    """

    id: str
    idempotency_key: str
    goal: str
    status: WorkStatus
    created_at: str
    updated_at: str
    due_at: str | None = None
    deadline_seconds: float | None = None
    attempts: int = 0
    result_summary: str | None = None
    failure_category: str | None = None
    thread_id: str | None = None
