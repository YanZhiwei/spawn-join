"""桥接原生中断与工作存储的 HITL 审批记账。

审批簿在宿主数据目录中拥有自己的 SQLite 表：每个暂停的工作项一行，
记录请求的动作、用户决定与时间戳。恢复命令按原生 ``resume_batched``
契约构造——与已记录动作严格按顺序一一对应。这里没有任何自行批准的
逻辑；人类决定始终来自宿主。
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
    """以可排序的 ISO-8601 字符串返回当前 UTC 时间。"""

    return datetime.now(UTC).isoformat()


def _require_path(value: object) -> None:
    """拒绝非 Path 输入，抛出稳定、可断言的错误。"""

    if not isinstance(value, Path):
        raise HostApprovalError("db_path: must be a pathlib.Path")


def interrupt_actions(interrupt: PendingInterrupt) -> tuple[dict[str, Any], ...]:
    """以映射元组返回一个原生中断的 ``action_requests``。"""

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
    """一条已持久化的审批请求及其人类决定。

    字段:
        id: 审批簿分配的唯一标识（UUID hex）。
        work_item_id / thread_id: 被暂停的工作项及其 thread。
        interrupt_id: 存在时的原生中断 id。
        actions: 按顺序请求的动作；决定必须与之对齐。
        decision: 用户批准或拒绝前保持 ``pending``。
        created_at / decided_at: ISO-8601 UTC 时间戳。
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
    """在存储边界把无类型的 sqlite3 行收窄为 ApprovalRecord。"""

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
    """基于单个 sqlite3 连接的可持久化审批请求存储。"""

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
        """关闭底层连接；可重复调用。"""

        self._connection.close()

    def save_request(
        self,
        *,
        work_item_id: str,
        thread_id: str,
        interrupt: PendingInterrupt,
    ) -> ApprovalRecord:
        """持久化一条从原生中断提取的审批请求。"""

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
        """返回给定 id 的审批记录，不存在则返回 None。"""

        return self._select_one("id = ?", (record_id,))

    def pending(self) -> list[ApprovalRecord]:
        """按创建顺序返回 pending 状态的审批记录。"""

        return self._select_all("decision = 'pending'")

    def record_decision(
        self,
        record_id: str,
        decision: Literal["approved", "rejected"],
    ) -> ApprovalRecord:
        """持久化人类决定；已决定的记录不可变。"""

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
    """持久化请求并把工作项迁移到 waiting_approval。"""

    record = book.save_request(
        work_item_id=work_item_id,
        thread_id=thread_id,
        interrupt=interrupt,
    )
    store.mark(work_item_id, WorkStatus.WAITING_APPROVAL, thread_id=thread_id)
    return record


def resume_approved(record: ApprovalRecord) -> Command[Any]:
    """构造与已记录动作逐一对应的批准恢复命令。"""

    return resume_batched([approve_decision() for _ in record.actions])


def resume_rejected(
    record: ApprovalRecord,
    message: str | None = None,
) -> Command[Any]:
    """构造与已记录动作逐一对应的拒绝恢复命令。"""

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
    """记录决定、迁移工作项并构造恢复命令。

    批准把工作项送回 ``running`` 继续执行；拒绝在不执行被拒动作的前提
    下落盘持久的 ``failed(rejected)`` 结果。
    """

    decision: Literal["approved", "rejected"] = "approved" if approve else "rejected"
    record = book.record_decision(record_id, decision)
    if approve:
        store.mark(work_item_id, WorkStatus.RUNNING)
        return resume_approved(record)
    store.mark(work_item_id, WorkStatus.FAILED, failure_category="rejected")
    return resume_rejected(record, message)
