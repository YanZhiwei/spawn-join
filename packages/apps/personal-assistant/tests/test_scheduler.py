"""due 调度器的离线测试：拾取、约束、取消、恢复。"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from spawn_join_personal_assistant import (
    HostSchedulingError,
    Scheduler,
    WorkItem,
    WorkStatus,
    WorkStore,
)


def _open_store(tmp_path: Path) -> WorkStore:
    return WorkStore(tmp_path / "work.db")


def test_due_items_execute_and_bound_concurrency(tmp_path: Path) -> None:
    async def scenario() -> None:
        with _open_store(tmp_path) as store:
            for index in range(4):
                store.accept(f"任务{index}", idempotency_key=f"key-{index}")

            active = 0
            peak = 0

            async def execute(item: WorkItem) -> None:
                nonlocal active, peak
                active += 1
                peak = max(peak, active)
                await asyncio.sleep(0.02)
                store.mark(item.id, WorkStatus.COMPLETED)
                active -= 1

            scheduler = Scheduler(store, max_concurrency=2)
            outcomes = await scheduler.run_due(execute)

            assert len(outcomes) == 4
            assert peak <= 2
            assert all(o.status is WorkStatus.COMPLETED for o in outcomes)
            assert store.count_by_status(WorkStatus.COMPLETED) == 4

    asyncio.run(scenario())


def test_future_due_items_are_skipped(tmp_path: Path) -> None:
    async def scenario() -> None:
        with _open_store(tmp_path) as store:
            due = store.accept("到期任务", idempotency_key="key-due")
            later = store.accept(
                "未来任务",
                idempotency_key="key-later",
                due_at="2099-01-01T00:00:00+00:00",
            )

            async def execute(item: WorkItem) -> None:
                store.mark(item.id, WorkStatus.COMPLETED)

            scheduler = Scheduler(store, max_concurrency=1)
            outcomes = await scheduler.run_due(execute)

            assert [o.id for o in outcomes] == [due.id]
            assert store.get(later.id) == later

    asyncio.run(scenario())


def test_executor_return_with_persisted_outcome_is_kept(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        with _open_store(tmp_path) as store:
            item = store.accept("任务A", idempotency_key="key-1")

            async def execute(item: WorkItem) -> None:
                store.mark(item.id, WorkStatus.COMPLETED, result_summary="ok")

            scheduler = Scheduler(store, max_concurrency=1)
            outcomes = await scheduler.run_due(execute)

            assert len(outcomes) == 1
            assert outcomes[0].status is WorkStatus.COMPLETED
            assert outcomes[0].attempts == 1
            assert store.get(item.id) == outcomes[0]

    asyncio.run(scenario())


def test_executor_incomplete_marks_failed(tmp_path: Path) -> None:
    async def scenario() -> None:
        with _open_store(tmp_path) as store:
            store.accept("任务A", idempotency_key="key-1")

            async def execute(item: WorkItem) -> None:
                del item  # returns without persisting any outcome

            scheduler = Scheduler(store, max_concurrency=1)
            outcomes = await scheduler.run_due(execute)

            assert outcomes[0].status is WorkStatus.FAILED
            assert outcomes[0].failure_category == "executor_incomplete"

    asyncio.run(scenario())


def test_executor_exception_marks_failed_with_category(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        with _open_store(tmp_path) as store:
            store.accept("任务A", idempotency_key="key-1")
            store.accept("任务B", idempotency_key="key-2")

            async def execute(item: WorkItem) -> None:
                if item.idempotency_key == "key-1":
                    msg = "boom"
                    raise ValueError(msg)
                store.mark(item.id, WorkStatus.COMPLETED)

            scheduler = Scheduler(store, max_concurrency=2)
            outcomes = await scheduler.run_due(execute)

            by_key = {o.idempotency_key: o for o in outcomes}
            assert by_key["key-1"].status is WorkStatus.FAILED
            assert by_key["key-1"].failure_category == "ValueError"
            assert by_key["key-2"].status is WorkStatus.COMPLETED

    asyncio.run(scenario())


def test_deadline_expiry_marks_failed_and_releases_slot(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        with _open_store(tmp_path) as store:
            store.accept("慢任务", idempotency_key="key-slow")
            store.accept("快任务", idempotency_key="key-fast")

            async def execute(item: WorkItem) -> None:
                if item.idempotency_key == "key-slow":
                    await asyncio.sleep(0.5)
                store.mark(item.id, WorkStatus.COMPLETED)

            scheduler = Scheduler(store, max_concurrency=1, deadline_seconds=0.05)
            outcomes = await scheduler.run_due(execute)

            by_key = {o.idempotency_key: o for o in outcomes}
            assert by_key["key-slow"].status is WorkStatus.FAILED
            assert by_key["key-slow"].failure_category == "deadline"
            assert by_key["key-fast"].status is WorkStatus.COMPLETED

    asyncio.run(scenario())


def test_parent_cancellation_requeues_and_propagates(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        with _open_store(tmp_path) as store:
            item = store.accept("阻塞任务", idempotency_key="key-1")

            started = asyncio.Event()

            async def execute(item: WorkItem) -> None:
                started.set()
                await asyncio.Event().wait()

            scheduler = Scheduler(store, max_concurrency=1)
            task = asyncio.create_task(scheduler.run_due(execute))
            await started.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

            recovered = store.get(item.id)
            assert recovered is not None
            assert recovered.status is WorkStatus.QUEUED
            assert recovered.attempts == 1

    asyncio.run(scenario())


def test_recover_interrupted_requeues_running_exactly_once(
    tmp_path: Path,
) -> None:
    async def scenario() -> None:
        with _open_store(tmp_path) as store:
            first = store.accept("中断A", idempotency_key="key-a")
            second = store.accept("中断B", idempotency_key="key-b")
            store.mark(first.id, WorkStatus.RUNNING)
            store.mark(second.id, WorkStatus.RUNNING)
            waiting = store.accept("待审批", idempotency_key="key-w")
            store.mark(waiting.id, WorkStatus.RUNNING)
            waiting_item = store.mark(waiting.id, WorkStatus.WAITING_APPROVAL)

            scheduler = Scheduler(store, max_concurrency=1)
            requeued = await scheduler.recover_interrupted()

            assert {item.id for item in requeued} == {first.id, second.id}
            assert all(o.status is WorkStatus.QUEUED for o in requeued)
            assert await scheduler.recover_interrupted() == []

            executed: list[str] = []

            async def execute(item: WorkItem) -> None:
                executed.append(item.id)
                store.mark(item.id, WorkStatus.COMPLETED)

            outcomes = await scheduler.run_due(execute)

            assert sorted(executed) == sorted([first.id, second.id])
            assert all(o.status is WorkStatus.COMPLETED for o in outcomes)
            assert store.get(waiting.id) == waiting_item

    asyncio.run(scenario())


def test_scheduler_rejects_invalid_bounds(tmp_path: Path) -> None:
    with _open_store(tmp_path) as store:
        with pytest.raises(HostSchedulingError, match="max_concurrency"):
            Scheduler(store, max_concurrency=0)
        with pytest.raises(HostSchedulingError, match="deadline_seconds"):
            Scheduler(store, max_concurrency=1, deadline_seconds=0.0)


def test_waiting_approval_items_are_not_picked(tmp_path: Path) -> None:
    async def scenario() -> None:
        with _open_store(tmp_path) as store:
            waiting = store.accept("待审批", idempotency_key="key-w")
            store.mark(waiting.id, WorkStatus.RUNNING)
            waiting_item = store.mark(waiting.id, WorkStatus.WAITING_APPROVAL)

            async def execute(item: WorkItem) -> None:
                store.mark(item.id, WorkStatus.COMPLETED)

            scheduler = Scheduler(store, max_concurrency=1)
            outcomes = await scheduler.run_due(execute)

            assert outcomes == []
            assert store.get(waiting.id) == waiting_item

    asyncio.run(scenario())
