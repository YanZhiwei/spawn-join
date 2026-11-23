"""工作项存储的离线测试：状态机、幂等、恢复。"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

import pytest
from spawn_join_personal_assistant import (
    HostStoreError,
    WorkItem,
    WorkStatus,
    WorkStore,
    WorkTransitionError,
)


def test_accept_persists_queued_item(tmp_path: Path) -> None:
    with WorkStore(tmp_path / "work.db") as store:
        item = store.accept(
            "整理发票并汇总",
            idempotency_key="invoice-001",
            due_at="2026-11-22T09:00:00+00:00",
            deadline_seconds=120.0,
        )

        assert item.status is WorkStatus.QUEUED
        assert item.attempts == 0
        assert item.due_at == "2026-11-22T09:00:00+00:00"
        assert item.deadline_seconds == 120.0
        assert store.get(item.id) == item
        assert store.get_by_idempotency_key("invoice-001") == item


def test_accept_rejects_replayed_idempotency_key(tmp_path: Path) -> None:
    with WorkStore(tmp_path / "work.db") as store:
        first = store.accept("任务A", idempotency_key="key-1")

        with pytest.raises(HostStoreError, match="idempotency_key"):
            store.accept("任务B", idempotency_key="key-1")

        assert store.get(first.id) == first
        assert store.count_by_status(WorkStatus.QUEUED) == 1


def test_accept_rejects_empty_goal_and_key(tmp_path: Path) -> None:
    with WorkStore(tmp_path / "work.db") as store:
        with pytest.raises(HostStoreError, match="goal"):
            store.accept("   ", idempotency_key="key-1")
        with pytest.raises(HostStoreError, match="idempotency_key"):
            store.accept("任务A", idempotency_key="")


def test_legal_transitions_update_state(tmp_path: Path) -> None:
    with WorkStore(tmp_path / "work.db") as store:
        item = store.accept("任务A", idempotency_key="key-1")

        running = store.mark(item.id, WorkStatus.RUNNING, increment_attempt=True)
        assert running.status is WorkStatus.RUNNING
        assert running.attempts == 1

        waiting = store.mark(
            running.id, WorkStatus.WAITING_APPROVAL, thread_id="thread-1"
        )
        assert waiting.status is WorkStatus.WAITING_APPROVAL
        assert waiting.thread_id == "thread-1"

        resumed = store.mark(waiting.id, WorkStatus.RUNNING)
        assert resumed.status is WorkStatus.RUNNING
        assert resumed.attempts == 1

        done = store.mark(
            resumed.id,
            WorkStatus.COMPLETED,
            result_summary="汇总完成：12 张发票",
        )
        assert done.status is WorkStatus.COMPLETED
        assert done.result_summary == "汇总完成：12 张发票"
        assert done.updated_at >= item.updated_at
        assert store.get(item.id) == done


def test_illegal_transition_rejected_without_side_effect(tmp_path: Path) -> None:
    with WorkStore(tmp_path / "work.db") as store:
        item = store.accept("任务A", idempotency_key="key-1")

        with pytest.raises(WorkTransitionError, match="illegal transition"):
            store.mark(item.id, WorkStatus.COMPLETED)

        assert store.get(item.id) == item


def test_terminal_states_reject_every_transition(tmp_path: Path) -> None:
    with WorkStore(tmp_path / "work.db") as store:
        failed = store.accept("任务F", idempotency_key="key-f")
        store.mark(failed.id, WorkStatus.RUNNING)
        failed = store.mark(failed.id, WorkStatus.FAILED, failure_category="deadline")

        for target in (
            WorkStatus.QUEUED,
            WorkStatus.RUNNING,
            WorkStatus.WAITING_APPROVAL,
            WorkStatus.COMPLETED,
            WorkStatus.CANCELLED,
        ):
            with pytest.raises(WorkTransitionError):
                store.mark(failed.id, target)
        assert store.get(failed.id) == failed


def test_pending_recovery_returns_only_unfinished(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # 固定时间戳和反向 ID，覆盖恢复扫描的排序并列边界。
    monkeypatch.setattr(
        "spawn_join_personal_assistant.work.store._utc_now_iso",
        lambda: "2026-11-24T00:00:00+00:00",
    )
    identifiers = iter((UUID(int=2), UUID(int=1), UUID(int=3)))
    monkeypatch.setattr(
        "spawn_join_personal_assistant.work.store.uuid.uuid4",
        lambda: next(identifiers),
    )
    with WorkStore(tmp_path / "work.db") as store:
        queued = store.accept("排队任务", idempotency_key="key-q")
        running = store.accept("运行任务", idempotency_key="key-r")
        store.mark(running.id, WorkStatus.RUNNING)
        done = store.accept("完成任务", idempotency_key="key-d")
        store.mark(done.id, WorkStatus.RUNNING)
        store.mark(done.id, WorkStatus.COMPLETED)

        recovered = store.pending_recovery()

        assert queued.created_at == running.created_at
        assert [item.id for item in recovered] == [running.id, queued.id]


def test_store_survives_restart_with_schema_idempotent(tmp_path: Path) -> None:
    db_path = tmp_path / "work.db"
    with WorkStore(db_path) as store:
        store.accept("任务A", idempotency_key="key-1")
        store.accept("任务B", idempotency_key="key-2")

    with WorkStore(db_path) as store:
        items = store.pending_recovery()

        assert len(items) == 2
        assert store.get_by_idempotency_key("key-1") is not None
        # Schema 建立是幂等的；第二次打开没有产生重复行。
        assert store.count_by_status(WorkStatus.QUEUED) == 2


def test_corrupt_database_fails_with_stable_error(tmp_path: Path) -> None:
    db_path = tmp_path / "work.db"
    db_path.write_bytes(b"this is not a sqlite database")

    with pytest.raises(HostStoreError, match="cannot open or initialize"):
        WorkStore(db_path)


def test_non_path_db_path_rejected(tmp_path: Path) -> None:
    with pytest.raises(HostStoreError, match="db_path"):
        WorkStore(str(tmp_path / "work.db"))  # type: ignore[arg-type]


def test_mark_unknown_item_reports_not_found(tmp_path: Path) -> None:
    with WorkStore(tmp_path / "work.db") as store:
        with pytest.raises(HostStoreError, match="not found"):
            store.mark("missing-id", WorkStatus.RUNNING)


def test_requeue_edge_supports_interrupted_rerun(tmp_path: Path) -> None:
    with WorkStore(tmp_path / "work.db") as store:
        item = store.accept("中断任务", idempotency_key="key-x")
        store.mark(item.id, WorkStatus.RUNNING, increment_attempt=True)

        requeued = store.mark(item.id, WorkStatus.QUEUED)

        assert requeued.status is WorkStatus.QUEUED
        assert requeued.attempts == 1

        rerun = store.mark(requeued.id, WorkStatus.RUNNING, increment_attempt=True)
        done = store.mark(rerun.id, WorkStatus.COMPLETED, result_summary="重跑完成")

        assert rerun.attempts == 2
        assert done.status is WorkStatus.COMPLETED


def test_work_item_fields_default(tmp_path: Path) -> None:
    item = WorkItem(
        id="id-1",
        idempotency_key="key-1",
        goal="目标",
        status=WorkStatus.QUEUED,
        created_at="2026-11-21T08:00:00+00:00",
        updated_at="2026-11-21T08:00:00+00:00",
    )

    assert item.due_at is None
    assert item.deadline_seconds is None
    assert item.attempts == 0
    assert item.result_summary is None
    assert item.failure_category is None
    assert item.thread_id is None
