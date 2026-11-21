"""HITL approval bookkeeping bridging native interrupts and the work store.

The approval book owns its own SQLite table in the host data directory: one
row per paused work item with the requested actions, the user decision, and
timestamps. Resume commands are built from the native ``resume_batched``
contract with exactly one decision per recorded action, in order. Nothing
here approves by itself; the human decision always arrives from the host.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

from langgraph.types import Command
from spawn_join_agent_deepagents import (
    PendingInterrupt,
    approve_decision,
    reject_decision,
    resume_batched,
)

from .errors import HostApprovalError
from .work.models import WorkStatus
from .work.store import WorkStore

Decision = Literal["pending", "approved", "rejected"]

_COLUMNS = (
    "id, work_item_id, thread_id, interrupt_id, actions_json, "
    "decision, created_at, decided_at"
)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS approval_records (
    id TEXT PRIMARY KEY,
    work_item_id TEXT NOT NULL,
    thread_id TEXT NOT NULL,
    interrupt_id TEXT,
    actions_json TEXT NOT NULL,
    decision TEXT NOT NULL,
    created_at TEXT NOT NULL,
    decided_at TEXT
)
"""


def _utc_now_iso() -> str:
    """Return the current UTC time as a sortable ISO-8601 string."""

    return datetime.now(UTC).isoformat()


def _require_path(value: object) -> None:
    """Reject non-Path input with a stable, assertable error."""

    if not isinstance(value, Path):
        raise HostApprovalError("db_path: must be a pathlib.Path")


def interrupt_actions(interrupt: PendingInterrupt) -> tuple[dict[str, Any], ...]:
    """Return the ``action_requests`` of one native interrupt as mappings."""

    value: object = interrupt.value
    if isinstance(value, Mapping):
        requests: object = cast(Mapping[str, object], value).get("action_requests")
        if isinstance(requests, Sequence) and not isinstance(requests, (str, bytes)):
            actions: list[dict[str, Any]] = []
            for request in cast(Sequence[object], requests):
                if not isinstance(request, Mapping):
                    raise HostApprovalError("approval request: malformed action entry")
                actions.append(dict(cast(Mapping[str, object], request)))
            return tuple(actions)
    raise HostApprovalError("approval request: interrupt value has no action_requests")


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    """One persisted approval request and its human decision.

    Attributes:
        id: Book-assigned unique identifier (UUID hex).
        work_item_id / thread_id: The paused work item and its thread.
        interrupt_id: The native interrupt id when present.
        actions: The requested actions, in order; decisions must align.
        decision: ``pending`` until the user approves or rejects.
        created_at / decided_at: ISO-8601 UTC timestamps.
    """

    id: str
    work_item_id: str
    thread_id: str
    interrupt_id: str | None
    actions: tuple[dict[str, Any], ...]
    decision: Decision
    created_at: str
    decided_at: str | None


def _record_from_row(row: sqlite3.Row) -> ApprovalRecord:
    """Narrow an untyped sqlite3 row into an ApprovalRecord at the boundary."""

    decided_at = row["decided_at"]
    actions = json.loads(str(row["actions_json"]))
    interrupt_id = row["interrupt_id"]
    decision = cast(Decision, str(row["decision"]))
    return ApprovalRecord(
        id=str(row["id"]),
        work_item_id=str(row["work_item_id"]),
        thread_id=str(row["thread_id"]),
        interrupt_id=str(interrupt_id) if interrupt_id is not None else None,
        actions=tuple(dict(action) for action in actions),
        decision=decision,
        created_at=str(row["created_at"]),
        decided_at=str(decided_at) if decided_at is not None else None,
    )


class ApprovalBook:
    """Durable approval-request persistence over one sqlite3 connection."""

    def __init__(self, db_path: Path) -> None:
        _require_path(db_path)
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(db_path)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute(_SCHEMA)
            self._connection.commit()
        except sqlite3.Error as exc:
            raise HostApprovalError(
                f"approval book: cannot open or initialize {db_path}: {exc}"
            ) from exc

    def __enter__(self) -> ApprovalBook:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying connection; safe to call more than once."""

        self._connection.close()

    def save_request(
        self,
        *,
        work_item_id: str,
        thread_id: str,
        interrupt: PendingInterrupt,
    ) -> ApprovalRecord:
        """Persist one approval request extracted from a native interrupt."""

        actions = interrupt_actions(interrupt)
        now = _utc_now_iso()
        record = ApprovalRecord(
            id=uuid.uuid4().hex,
            work_item_id=work_item_id,
            thread_id=thread_id,
            interrupt_id=interrupt.id,
            actions=actions,
            decision="pending",
            created_at=now,
            decided_at=None,
        )
        try:
            with self._connection:
                self._connection.execute(
                    f"INSERT INTO approval_records ({_COLUMNS}) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        record.id,
                        record.work_item_id,
                        record.thread_id,
                        record.interrupt_id,
                        json.dumps(list(record.actions)),
                        record.decision,
                        record.created_at,
                        record.decided_at,
                    ),
                )
        except sqlite3.Error as exc:
            raise HostApprovalError(f"approval book: save failed: {exc}") from exc
        return record

    def get(self, record_id: str) -> ApprovalRecord | None:
        """Return the approval record with the given id, or None."""

        return self._select_one("id = ?", (record_id,))

    def pending(self) -> list[ApprovalRecord]:
        """Return pending approval records in creation order."""

        return self._select_all("decision = 'pending'")

    def record_decision(
        self,
        record_id: str,
        decision: Literal["approved", "rejected"],
    ) -> ApprovalRecord:
        """Persist the human decision; decided records are immutable."""

        current = self.get(record_id)
        if current is None:
            raise HostApprovalError(f"approval record: not found: {record_id}")
        if current.decision != "pending":
            raise HostApprovalError(
                f"approval record {record_id}: already {current.decision}"
            )
        now = _utc_now_iso()
        decided = ApprovalRecord(
            id=current.id,
            work_item_id=current.work_item_id,
            thread_id=current.thread_id,
            interrupt_id=current.interrupt_id,
            actions=current.actions,
            decision=decision,
            created_at=current.created_at,
            decided_at=now,
        )
        try:
            with self._connection:
                self._connection.execute(
                    "UPDATE approval_records SET decision = ?, "
                    "decided_at = ? WHERE id = ?",
                    (decided.decision, decided.decided_at, decided.id),
                )
        except sqlite3.Error as exc:
            raise HostApprovalError(f"approval book: decision failed: {exc}") from exc
        return decided

    def _select_one(
        self, where: str, parameters: tuple[object, ...]
    ) -> ApprovalRecord | None:
        try:
            cursor = self._connection.execute(
                f"SELECT {_COLUMNS} FROM approval_records WHERE {where}",
                parameters,
            )
        except sqlite3.Error as exc:
            raise HostApprovalError(f"approval book: select failed: {exc}") from exc
        row = cursor.fetchone()
        return None if row is None else _record_from_row(row)

    def _select_all(
        self, where: str, parameters: tuple[object, ...] = ()
    ) -> list[ApprovalRecord]:
        try:
            cursor = self._connection.execute(
                f"SELECT {_COLUMNS} FROM approval_records WHERE {where} "
                "ORDER BY created_at, id",
                parameters,
            )
        except sqlite3.Error as exc:
            raise HostApprovalError(f"approval book: select failed: {exc}") from exc
        return [_record_from_row(row) for row in cursor.fetchall()]


def pause_for_approval(
    store: WorkStore,
    book: ApprovalBook,
    *,
    work_item_id: str,
    thread_id: str,
    interrupt: PendingInterrupt,
) -> ApprovalRecord:
    """Persist the request and move the work item to waiting_approval."""

    record = book.save_request(
        work_item_id=work_item_id,
        thread_id=thread_id,
        interrupt=interrupt,
    )
    store.mark(work_item_id, WorkStatus.WAITING_APPROVAL, thread_id=thread_id)
    return record


def resume_approved(record: ApprovalRecord) -> Command[Any]:
    """Build the aligned resume command approving every recorded action."""

    return resume_batched([approve_decision() for _ in record.actions])


def resume_rejected(
    record: ApprovalRecord,
    message: str | None = None,
) -> Command[Any]:
    """Build the aligned resume command rejecting every recorded action."""

    return resume_batched([reject_decision(message) for _ in record.actions])


def apply_decision(
    store: WorkStore,
    book: ApprovalBook,
    *,
    record_id: str,
    work_item_id: str,
    approve: bool,
    message: str | None = None,
) -> Command[Any]:
    """Record the decision, move the work item, and build the resume command.

    Approve returns the work item to ``running`` for the resumed execution;
    reject records the durable ``failed(rejected)`` outcome without executing
    the refused actions.
    """

    decision: Literal["approved", "rejected"] = "approved" if approve else "rejected"
    record = book.record_decision(record_id, decision)
    if approve:
        store.mark(work_item_id, WorkStatus.RUNNING)
        return resume_approved(record)
    store.mark(work_item_id, WorkStatus.FAILED, failure_category="rejected")
    return resume_rejected(record, message)
