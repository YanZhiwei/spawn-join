"""带幂等接收的 SQLite 工作项存储。

store 是工作项持久化的唯一写者：单连接、显式事务和幂等键 UNIQUE
约束。它假设每个数据目录一个宿主进程（文档化的限制），不做跨进程
协调。
"""

# 兼容层：审批流与既有 CLI 仍使用此同步 store；新的目标队列使用
# work.runtime.GoalRuntime（spawn-join-agent-work 的 SqliteWorkStore）。

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from ..errors import HostStoreError, WorkTransitionError
from .models import WorkItem, WorkStatus, transition_allowed

_COLUMNS = (
    "id, idempotency_key, goal, status, created_at, updated_at, "
    "due_at, deadline_seconds, attempts, result_summary, "
    "failure_category, thread_id"
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS work_items (
    id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    goal TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    due_at TEXT,
    deadline_seconds REAL,
    attempts INTEGER NOT NULL DEFAULT 0,
    result_summary TEXT,
    failure_category TEXT,
    thread_id TEXT
)
"""

_UNFINISHED_STATUSES = (
    WorkStatus.QUEUED,
    WorkStatus.RUNNING,
    WorkStatus.WAITING_APPROVAL,
)


def _utc_now_iso() -> str:
    """以可排序的 ISO-8601 字符串返回当前 UTC 时间。"""

    return datetime.now(UTC).isoformat()


def _require_path(value: object) -> None:
    """拒绝非 Path 输入，抛出稳定、可断言的错误。"""

    if not isinstance(value, Path):
        raise HostStoreError("db_path: must be a pathlib.Path")


def _require_non_empty_str(label: str, value: object) -> None:
    """拒绝非字符串或空白输入，抛出稳定、可断言的错误。"""

    if not isinstance(value, str) or not value.strip():
        raise HostStoreError(f"{label}: must be a non-empty string")


def _item_from_row(row: sqlite3.Row) -> WorkItem:
    """在存储边界把无类型的 sqlite3 行收窄为 WorkItem。"""

    due_at = row["due_at"]
    deadline = row["deadline_seconds"]
    attempts = row["attempts"]
    result_summary = row["result_summary"]
    failure_category = row["failure_category"]
    thread_id = row["thread_id"]
    return WorkItem(
        id=str(row["id"]),
        idempotency_key=str(row["idempotency_key"]),
        goal=str(row["goal"]),
        status=WorkStatus(str(row["status"])),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        due_at=str(due_at) if due_at is not None else None,
        deadline_seconds=(float(deadline) if deadline is not None else None),
        attempts=int(attempts),
        result_summary=(str(result_summary) if result_summary is not None else None),
        failure_category=(
            str(failure_category) if failure_category is not None else None
        ),
        thread_id=str(thread_id) if thread_id is not None else None,
    )


class WorkStore:
    """基于单个 sqlite3 连接的可持久化工作项存储。"""

    def __init__(self, db_path: Path) -> None:
        _require_path(db_path)
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(db_path)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute(_SCHEMA)
            self._connection.commit()
        except sqlite3.Error as exc:
            raise HostStoreError(
                f"work store: cannot open or initialize {db_path}: {exc}"
            ) from exc

    def __enter__(self) -> WorkStore:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        """关闭底层连接；可重复调用。"""

        self._connection.close()

    def accept(
        self,
        goal: str,
        *,
        idempotency_key: str,
        due_at: str | None = None,
        deadline_seconds: float | None = None,
    ) -> WorkItem:
        """插入一个新的排队工作项；拒绝重放的幂等键。"""

        _require_non_empty_str("goal", goal)
        _require_non_empty_str("idempotency_key", idempotency_key)
        now = _utc_now_iso()
        item = WorkItem(
            id=uuid.uuid4().hex,
            idempotency_key=idempotency_key,
            goal=goal,
            status=WorkStatus.QUEUED,
            created_at=now,
            updated_at=now,
            due_at=due_at,
            deadline_seconds=deadline_seconds,
        )
        try:
            with self._connection:
                self._connection.execute(
                    f"INSERT INTO work_items ({_COLUMNS}) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        item.id,
                        item.idempotency_key,
                        item.goal,
                        item.status.value,
                        item.created_at,
                        item.updated_at,
                        item.due_at,
                        item.deadline_seconds,
                        item.attempts,
                        item.result_summary,
                        item.failure_category,
                        item.thread_id,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            raise HostStoreError(
                f"idempotency_key: already exists: {idempotency_key}"
            ) from exc
        except sqlite3.Error as exc:
            raise HostStoreError(f"work store: accept failed: {exc}") from exc
        return item

    def get(self, item_id: str) -> WorkItem | None:
        """返回给定 id 的工作项，不存在则返回 None。"""

        return self._select_one("id = ?", (item_id,))

    def get_by_idempotency_key(self, key: str) -> WorkItem | None:
        """返回以给定幂等键接收的工作项，不存在则返回 None。"""

        return self._select_one("idempotency_key = ?", (key,))

    def mark(
        self,
        item_id: str,
        target: WorkStatus,
        *,
        result_summary: str | None = None,
        failure_category: str | None = None,
        thread_id: str | None = None,
        increment_attempt: bool = False,
    ) -> WorkItem:
        """应用一次已校验的状态迁移并持久化可选字段。

        传入非 None 的可选字段会更新它；None 保留已存值。非法迁移抛出
        ``WorkTransitionError``，且绝不改变已持久化状态。
        """

        current = self.get(item_id)
        if current is None:
            raise HostStoreError(f"work item: not found: {item_id}")
        if not transition_allowed(current.status, target):
            raise WorkTransitionError(
                f"work item {item_id}: illegal transition "
                f"{current.status.value} -> {target.value}"
            )
        now = _utc_now_iso()
        updated = WorkItem(
            id=current.id,
            idempotency_key=current.idempotency_key,
            goal=current.goal,
            status=target,
            created_at=current.created_at,
            updated_at=now,
            due_at=current.due_at,
            deadline_seconds=current.deadline_seconds,
            attempts=current.attempts + 1 if increment_attempt else current.attempts,
            result_summary=(
                result_summary if result_summary is not None else current.result_summary
            ),
            failure_category=(
                failure_category
                if failure_category is not None
                else current.failure_category
            ),
            thread_id=(thread_id if thread_id is not None else current.thread_id),
        )
        try:
            with self._connection:
                self._connection.execute(
                    "UPDATE work_items SET status = ?, updated_at = ?, "
                    "attempts = ?, result_summary = ?, failure_category = ?, "
                    "thread_id = ? WHERE id = ?",
                    (
                        updated.status.value,
                        updated.updated_at,
                        updated.attempts,
                        updated.result_summary,
                        updated.failure_category,
                        updated.thread_id,
                        updated.id,
                    ),
                )
        except sqlite3.Error as exc:
            raise HostStoreError(f"work store: mark failed: {exc}") from exc
        return updated

    def pending_recovery(self) -> list[WorkItem]:
        """返回未完成项（queued/running/waiting），供重启扫描使用。"""

        placeholders = ", ".join("?" for _ in _UNFINISHED_STATUSES)
        return self._select_all(
            f"status IN ({placeholders})",
            tuple(status.value for status in _UNFINISHED_STATUSES),
        )

    def list_all(self) -> list[WorkItem]:
        """按创建顺序返回全部工作项。"""

        return self._select_all("1 = 1", ())

    def count_by_status(self, status: WorkStatus) -> int:
        """返回当前持有给定状态的工作项数量。"""

        try:
            cursor = self._connection.execute(
                "SELECT COUNT(*) FROM work_items WHERE status = ?",
                (status.value,),
            )
        except sqlite3.Error as exc:
            raise HostStoreError(f"work store: count failed: {exc}") from exc
        row = cursor.fetchone()
        return int(row[0]) if row is not None else 0

    def _select_one(
        self, where: str, parameters: tuple[object, ...]
    ) -> WorkItem | None:
        try:
            cursor = self._connection.execute(
                f"SELECT {_COLUMNS} FROM work_items WHERE {where}",
                parameters,
            )
        except sqlite3.Error as exc:
            raise HostStoreError(f"work store: select failed: {exc}") from exc
        row = cursor.fetchone()
        return None if row is None else _item_from_row(row)

    def _select_all(self, where: str, parameters: tuple[object, ...]) -> list[WorkItem]:
        try:
            cursor = self._connection.execute(
                f"SELECT {_COLUMNS} FROM work_items WHERE {where} "
                "ORDER BY created_at, id",
                parameters,
            )
        except sqlite3.Error as exc:
            raise HostStoreError(f"work store: select failed: {exc}") from exc
        return [_item_from_row(row) for row in cursor.fetchall()]
