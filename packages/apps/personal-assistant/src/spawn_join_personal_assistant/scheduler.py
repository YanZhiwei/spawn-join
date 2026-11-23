"""面向可持久化工作项的 asyncio due 调度器。

调度器拥有单个有界执行周期内工作项侧的全部行为：拾取到期的排队项、
在并发上限内把它们标记为 running、用可选 deadline 包裹每个执行器
调用、强制执行器落盘其最终状态，并把失败转换为稳定的 ``failed``
状态。执行器异常被记录为 failed 工作项（store 即记录），而不是中断
兄弟项；父级取消把运行中的工作项重新排队并传播。被中断的运行（硬杀）
在恢复时经 ``recover_interrupted`` 恰好重排队一次。
"""

# 兼容层：HITL 审批仍依赖同步状态机；新的目标执行走
# work.runtime.GoalRuntime（spawn-join-agent-work 的 WorkStore/WorkRunner）。

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from .errors import HostSchedulingError
from .work.models import WorkItem, WorkStatus
from .work.store import WorkStore

WorkExecutor = Callable[[WorkItem], Awaitable[None]]
"""执行一个 RUNNING 工作项，并自行持久化其最终 store 状态。"""

_MIN_CONCURRENCY = 1


def _utc_now_iso() -> str:
    """以可排序的 ISO-8601 字符串返回当前 UTC 时间。"""

    return datetime.now(UTC).isoformat()


def _require_positive_int(label: str, value: object) -> None:
    """拒绝非 int、bool 或低于下限的并发输入。"""

    if not isinstance(value, int) or isinstance(value, bool):
        raise HostSchedulingError(f"{label}: must be an int")
    if value < _MIN_CONCURRENCY:
        raise HostSchedulingError(f"{label}: must be at least {_MIN_CONCURRENCY}")


def _require_positive_number_or_none(label: str, value: object) -> None:
    """拒绝非数值（或非正数）的 deadline 输入；None 表示禁用。"""

    if value is None:
        return
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise HostSchedulingError(f"{label}: must be a number or None")
    if value <= 0:
        raise HostSchedulingError(f"{label}: must be greater than 0")


class Scheduler:
    """基于单写者工作存储的有界 due 调度器。"""

    def __init__(
        self,
        store: WorkStore,
        *,
        max_concurrency: int,
        deadline_seconds: float | None = None,
    ) -> None:
        _require_positive_int("max_concurrency", max_concurrency)
        _require_positive_number_or_none("deadline_seconds", deadline_seconds)
        self._store = store
        self._max_concurrency = max_concurrency
        self._deadline_seconds = deadline_seconds

    async def recover_interrupted(self) -> list[WorkItem]:
        """重启后把 RUNNING 工作项重新排队（中断重跑）。

        每个被中断的工作项在这里恰好重新排队一次；随后的 ``run_due``
        会再执行它一次，工作项的幂等键保证任何外部副作用不会重复。
        """

        requeued: list[WorkItem] = []
        for item in self._store.pending_recovery():
            if item.status is WorkStatus.RUNNING:
                requeued.append(self._store.mark(item.id, WorkStatus.QUEUED))
        return requeued

    async def run_due(
        self,
        executor: WorkExecutor,
        *,
        now: str | None = None,
    ) -> list[WorkItem]:
        """对到期的排队工作项运行一个有界周期。

        返回每个被处理工作项已持久化的最终状态。无到期时间或到期时间
        已过的排队项可被拾取；父级取消在重新排队被中断项之后传播。
        """

        current = now if now is not None else _utc_now_iso()
        due = [
            item
            for item in self._store.pending_recovery()
            if item.status is WorkStatus.QUEUED
            and (item.due_at is None or item.due_at <= current)
        ]
        if not due:
            return []
        semaphore = asyncio.Semaphore(self._max_concurrency)
        outcomes = await asyncio.gather(
            *(self._run_one(semaphore, executor, item) for item in due)
        )
        return [outcome for outcome in outcomes if outcome is not None]

    async def _run_one(
        self,
        semaphore: asyncio.Semaphore,
        executor: WorkExecutor,
        item: WorkItem,
    ) -> WorkItem | None:
        async with semaphore:
            running = self._store.mark(
                item.id, WorkStatus.RUNNING, increment_attempt=True
            )
            try:
                if self._deadline_seconds is None:
                    await executor(running)
                else:
                    timeout = asyncio.timeout(self._deadline_seconds)
                    try:
                        async with timeout:
                            await executor(running)
                    except TimeoutError:
                        if not timeout.expired():
                            raise
                        return self._store.mark(
                            running.id,
                            WorkStatus.FAILED,
                            failure_category="deadline",
                        )
            except asyncio.CancelledError:
                self._store.mark(running.id, WorkStatus.QUEUED)
                raise
            except Exception as exc:
                current = self._store.get(running.id)
                if current is not None and current.status is WorkStatus.RUNNING:
                    return self._store.mark(
                        running.id,
                        WorkStatus.FAILED,
                        failure_category=type(exc).__name__,
                    )
                return current
            current = self._store.get(running.id)
            if current is None or current.status is WorkStatus.RUNNING:
                return self._store.mark(
                    running.id,
                    WorkStatus.FAILED,
                    failure_category="executor_incomplete",
                )
            return current
