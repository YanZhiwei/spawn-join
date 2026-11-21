"""SQLite-backed work-item store with idempotent acceptance.

The store is the single writer for work-item persistence: one connection,
explicit transactions, and a UNIQUE idempotency-key constraint. It assumes
one host process per data directory (a documented limitation); it does not
attempt cross-process coordination.
"""

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
    """Return the current UTC time as a sortable ISO-8601 string."""

    return datetime.now(UTC).isoformat()


def _require_path(value: object) -> None:
    """Reject non-Path input with a stable, assertable error."""

    if not isinstance(value, Path):
        raise HostStoreError("db_path: must be a pathlib.Path")


def _require_non_empty_str(label: str, value: object) -> None:
    """Reject non-string or blank input with a stable, assertable error."""

    if not isinstance(value, str) or not value.strip():
        raise HostStoreError(f"{label}: must be a non-empty string")


def _item_from_row(row: sqlite3.Row) -> WorkItem:
    """Narrow an untyped sqlite3 row into a WorkItem at the storage boundary."""

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
    """Durable work-item persistence over a single sqlite3 connection."""

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
        """Close the underlying connection; safe to call more than once."""

        self._connection.close()

    def accept(
        self,
        goal: str,
        *,
        idempotency_key: str,
        due_at: str | None = None,
        deadline_seconds: float | None = None,
    ) -> WorkItem:
        """Insert a new queued work item; reject replayed idempotency keys."""

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
        """Return the work item with the given id, or None."""

        return self._select_one("id = ?", (item_id,))

    def get_by_idempotency_key(self, key: str) -> WorkItem | None:
        """Return the work item accepted with the given key, or None."""

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
        """Apply one validated state transition and persist optional fields.

        Passing a non-None optional field updates it; None keeps the stored
        value. Illegal transitions raise ``WorkTransitionError`` and never
        change persisted state.
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
        """Return unfinished items (queued/running/waiting) for restart scans."""

        placeholders = ", ".join("?" for _ in _UNFINISHED_STATUSES)
        return self._select_all(
            f"status IN ({placeholders})",
            tuple(status.value for status in _UNFINISHED_STATUSES),
        )

    def count_by_status(self, status: WorkStatus) -> int:
        """Return how many items currently hold the given status."""

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
