"""SQLite-backed work store (desktop default).

The store is the source of truth. Claims run under ``BEGIN IMMEDIATE`` so two
workers cannot claim the same item, and every write-back is fenced by the lease
token. No migration from older schemas is provided: the product has not shipped.
"""

from __future__ import annotations

import asyncio
import secrets
import sqlite3
from collections.abc import Sequence
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from ..errors import StoreError, WorkConfigurationError, WorkConflictError
from ..models import WorkItem, WorkLease, WorkSpec, WorkState
from ..protocols import Clock

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL);

CREATE TABLE IF NOT EXISTS work_items (
  id               TEXT PRIMARY KEY,
  kind             TEXT NOT NULL,
  payload          BLOB NOT NULL,
  idempotency_key  TEXT NOT NULL UNIQUE,
  state            TEXT NOT NULL,
  queue            TEXT NOT NULL DEFAULT 'default',
  namespace        TEXT NOT NULL DEFAULT 'default',
  priority         INTEGER NOT NULL DEFAULT 0,
  attempts         INTEGER NOT NULL DEFAULT 0,
  max_attempts     INTEGER NOT NULL,
  available_at     TEXT NOT NULL,
  deadline_seconds REAL,
  lease_owner      TEXT,
  lease_token      TEXT,
  lease_until      TEXT,
  last_error       TEXT,
  result           TEXT,
  created_at       TEXT NOT NULL,
  updated_at       TEXT NOT NULL,
  completed_at     TEXT
);

CREATE INDEX IF NOT EXISTS idx_claim
  ON work_items(namespace, queue, state, available_at, priority DESC, created_at);
CREATE INDEX IF NOT EXISTS idx_lease ON work_items(state, lease_until);
"""

_SELECT_COLUMNS = """
  id, kind, payload, idempotency_key, state, queue, namespace, priority,
  attempts, max_attempts, available_at, deadline_seconds,
  lease_owner, lease_token, lease_until, last_error, result,
  created_at, updated_at, completed_at
"""


def _to_text(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _to_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _require_aware(label: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise WorkConfigurationError(f"{label}: must be timezone-aware")


def _require_positive_seconds(label: str, value: float) -> None:
    if value <= 0:
        raise WorkConfigurationError(f"{label}: must be > 0")


class _SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class SqliteWorkStore:
    """Durable work storage backed by a local SQLite database."""

    def __init__(
        self,
        database: str | Path,
        *,
        clock: Clock | None = None,
        busy_timeout_ms: int = 5000,
    ) -> None:
        if busy_timeout_ms <= 0:
            raise WorkConfigurationError("busy_timeout_ms: must be > 0")
        self._database = str(database)
        self._busy_timeout_ms = busy_timeout_ms
        self._clock: Clock = clock or _SystemClock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database, timeout=self._busy_timeout_ms / 1000
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(f"PRAGMA busy_timeout = {self._busy_timeout_ms}")
        return connection

    def _initialize(self) -> None:
        try:
            with closing(self._connect()) as connection:
                connection.execute("PRAGMA journal_mode = WAL")
                connection.executescript(_SCHEMA)
                row = connection.execute(
                    "SELECT version FROM schema_version LIMIT 1"
                ).fetchone()
                if row is None:
                    connection.execute(
                        "INSERT INTO schema_version(version) VALUES (?)",
                        (SCHEMA_VERSION,),
                    )
                elif int(row["version"]) != SCHEMA_VERSION:
                    raise StoreError(
                        "unsupported schema version: "
                        f"{row['version']} (expected {SCHEMA_VERSION})"
                    )
                connection.commit()
        except sqlite3.Error as exc:
            raise StoreError("failed to initialize SQLite work store") from exc

    def _now(self) -> datetime:
        now = self._clock.now()
        _require_aware("clock.now()", now)
        return now

    async def enqueue(self, spec: WorkSpec) -> WorkItem:
        return await asyncio.to_thread(self._enqueue, spec)

    def _enqueue(self, spec: WorkSpec) -> WorkItem:
        now = self._now()
        work_id = uuid4().hex
        try:
            with closing(self._connect()) as connection:
                connection.execute(
                    """
                    INSERT INTO work_items(
                      id, kind, payload, idempotency_key, state, queue, namespace,
                      priority, attempts, max_attempts, available_at,
                      deadline_seconds, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
                    """,
                    (
                        work_id,
                        spec.kind,
                        spec.payload,
                        spec.idempotency_key,
                        WorkState.QUEUED.value,
                        spec.queue,
                        spec.namespace,
                        spec.priority,
                        spec.max_attempts,
                        _to_text(spec.available_at or now),
                        spec.deadline_seconds,
                        _to_text(now),
                        _to_text(now),
                    ),
                )
                row = connection.execute(
                    f"SELECT {_SELECT_COLUMNS} FROM work_items WHERE id = ?",
                    (work_id,),
                ).fetchone()
                connection.commit()
        except sqlite3.IntegrityError as exc:
            if "idempotency_key" in str(exc):
                raise WorkConflictError(
                    f"idempotency key already exists: {spec.idempotency_key}"
                ) from exc
            raise StoreError("failed to enqueue work item") from exc
        except sqlite3.Error as exc:
            raise StoreError("failed to enqueue work item") from exc
        if row is None:
            raise StoreError("enqueued work item could not be read back")
        return self._row_to_item(row)

    async def claim(
        self,
        *,
        owner: str,
        queues: Sequence[str],
        namespace: str,
        limit: int,
        lease_seconds: float,
        now: datetime,
    ) -> list[WorkItem]:
        if not owner.strip():
            raise WorkConfigurationError("owner: must be non-empty")
        if not namespace.strip():
            raise WorkConfigurationError("namespace: must be non-empty")
        if limit < 1:
            raise WorkConfigurationError("limit: must be >= 1")
        _require_positive_seconds("lease_seconds", lease_seconds)
        _require_aware("now", now)
        selected_queues = tuple(queue for queue in queues if queue)
        if not selected_queues:
            return []
        return await asyncio.to_thread(
            self._claim,
            owner,
            selected_queues,
            namespace,
            limit,
            lease_seconds,
            now,
        )

    def _claim(
        self,
        owner: str,
        queues: tuple[str, ...],
        namespace: str,
        limit: int,
        lease_seconds: float,
        now: datetime,
    ) -> list[WorkItem]:
        lease_until = now + timedelta(seconds=lease_seconds)
        placeholders = ",".join("?" for _ in queues)
        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                self._expire_leases(connection, now)
                rows = connection.execute(
                    f"""
                    SELECT id FROM work_items
                     WHERE state = ?
                       AND queue IN ({placeholders})
                       AND namespace = ?
                       AND available_at <= ?
                     ORDER BY priority DESC, created_at ASC, id ASC
                     LIMIT ?
                    """,
                    (
                        WorkState.QUEUED.value,
                        *queues,
                        namespace,
                        _to_text(now),
                        limit,
                    ),
                ).fetchall()
                ids = [row["id"] for row in rows]
                if not ids:
                    return []
                token = secrets.token_hex(16)
                for work_id in ids:
                    connection.execute(
                        """
                        UPDATE work_items
                           SET state = ?, lease_owner = ?, lease_token = ?,
                               lease_until = ?, attempts = attempts + 1,
                               updated_at = ?
                         WHERE id = ? AND state = ?
                        """,
                        (
                            WorkState.RUNNING.value,
                            owner,
                            token,
                            _to_text(lease_until),
                            _to_text(now),
                            work_id,
                            WorkState.QUEUED.value,
                        ),
                    )
                claimed = connection.execute(
                    f"""
                    SELECT {_SELECT_COLUMNS} FROM work_items
                     WHERE id IN ({",".join("?" for _ in ids)})
                     ORDER BY priority DESC, created_at ASC, id ASC
                    """,
                    tuple(ids),
                ).fetchall()
                connection.commit()
        except sqlite3.Error as exc:
            raise StoreError("failed to claim work items") from exc
        return [self._row_to_item(row) for row in claimed]

    def _expire_leases(self, connection: sqlite3.Connection, now: datetime) -> None:
        moment = _to_text(now)
        connection.execute(
            """
            UPDATE work_items
               SET state = ?, last_error = COALESCE(last_error, 'lease expired'),
                   lease_owner = NULL, lease_token = NULL, lease_until = NULL,
                   completed_at = ?, updated_at = ?
             WHERE state = ? AND lease_until IS NOT NULL AND lease_until <= ?
               AND attempts >= max_attempts
            """,
            (
                WorkState.DEAD.value,
                moment,
                moment,
                WorkState.RUNNING.value,
                moment,
            ),
        )
        connection.execute(
            """
            UPDATE work_items
               SET state = ?, available_at = ?,
                   lease_owner = NULL, lease_token = NULL, lease_until = NULL,
                   updated_at = ?
             WHERE state = ? AND lease_until IS NOT NULL AND lease_until <= ?
            """,
            (
                WorkState.QUEUED.value,
                moment,
                moment,
                WorkState.RUNNING.value,
                moment,
            ),
        )

    async def get(self, work_id: str) -> WorkItem | None:
        return await asyncio.to_thread(self._get, work_id)

    def _get(self, work_id: str) -> WorkItem | None:
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    f"SELECT {_SELECT_COLUMNS} FROM work_items WHERE id = ?",
                    (work_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise StoreError("failed to read work item") from exc
        return None if row is None else self._row_to_item(row)

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> WorkItem:
        lease: WorkLease | None = None
        if row["lease_owner"] is not None:
            until = _to_datetime(row["lease_until"])
            if until is None:
                raise StoreError("stored lease is missing its expiry")
            lease = WorkLease(
                owner=row["lease_owner"],
                token=row["lease_token"],
                until=until,
            )
        created_at = _to_datetime(row["created_at"])
        updated_at = _to_datetime(row["updated_at"])
        if created_at is None or updated_at is None:
            raise StoreError("stored work item is missing timestamps")
        return WorkItem(
            id=row["id"],
            spec=WorkSpec(
                kind=row["kind"],
                payload=row["payload"],
                idempotency_key=row["idempotency_key"],
                queue=row["queue"],
                namespace=row["namespace"],
                priority=row["priority"],
                available_at=_to_datetime(row["available_at"]),
                deadline_seconds=row["deadline_seconds"],
                max_attempts=row["max_attempts"],
            ),
            state=WorkState(row["state"]),
            attempts=row["attempts"],
            lease=lease,
            last_error=row["last_error"],
            created_at=created_at,
            updated_at=updated_at,
            result=row["result"],
            completed_at=_to_datetime(row["completed_at"]),
        )
