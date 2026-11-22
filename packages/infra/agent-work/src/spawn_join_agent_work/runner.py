"""Single-pass and long-running work execution."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from contextlib import suppress
from datetime import datetime, timedelta
from uuid import uuid4

from .errors import LeaseLostError, WorkConfigurationError
from .models import WorkItem, WorkOutcome, WorkResult
from .policies import ConcurrencyPolicy, LeasePolicy, RetryPolicy
from .protocols import Clock, Notifier, WorkExecutor, WorkStore
from .stores._support import SystemClock, require_aware

_LOGGER = logging.getLogger(__name__)
_MAX_ERROR_CHARS = 500
_SHUTDOWN_TIMEOUT_SECONDS = 5.0
_DEFAULT_RETENTION_SECONDS = 30 * 24 * 60 * 60
_DEFAULT_PRUNE_INTERVAL_SECONDS = 60 * 60


def _require_positive_number(label: str, value: object) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise WorkConfigurationError(f"{label}: must be a number")
    if value <= 0:
        raise WorkConfigurationError(f"{label}: must be > 0")


class WorkRunner:
    """Claim work items, run them through a host executor, and finalize.

    Durable retries stop at ``min(WorkSpec.max_attempts, RetryPolicy.max_attempts)``:
    the spec bounds the item's lifetime, the policy bounds this runner's retries.
    """

    def __init__(
        self,
        store: WorkStore,
        executor: WorkExecutor,
        *,
        clock: Clock | None = None,
        queues: Sequence[str] = ("default",),
        namespace: str = "default",
        lease_policy: LeasePolicy | None = None,
        retry_policy: RetryPolicy | None = None,
        concurrency: ConcurrencyPolicy | None = None,
        owner: str | None = None,
        notifier: Notifier | None = None,
        retention_seconds: float = _DEFAULT_RETENTION_SECONDS,
        prune_interval_seconds: float = _DEFAULT_PRUNE_INTERVAL_SECONDS,
    ) -> None:
        _require_positive_number("retention_seconds", retention_seconds)
        _require_positive_number("prune_interval_seconds", prune_interval_seconds)
        self._store = store
        self._executor = executor
        self._clock: Clock = clock or SystemClock()
        self._queues = tuple(queues)
        self._namespace = namespace
        self._lease = lease_policy or LeasePolicy()
        self._retry = retry_policy or RetryPolicy()
        self._concurrency = concurrency or ConcurrencyPolicy()
        self._owner = owner or f"runner-{uuid4().hex}"
        self._notifier = notifier
        self._retention_seconds = retention_seconds
        self._prune_interval_seconds = prune_interval_seconds
        self._stop = asyncio.Event()
        self._wake = asyncio.Event()
        self._stopped = False
        self._inflight: dict[asyncio.Task[None], WorkItem] = {}
        self._serve_task: asyncio.Task[None] | None = None

    @property
    def owner(self) -> str:
        return self._owner

    async def run_once(self, *, limit: int | None = None) -> int:
        """Claim and process one batch; returns the number of processed items."""

        now = self._now()
        batch = limit if limit is not None else self._concurrency.claim_batch
        claimed = await self._store.claim(
            owner=self._owner,
            queues=self._queues,
            namespace=self._namespace,
            limit=batch,
            lease_seconds=self._lease.seconds,
            now=now,
        )
        for item in claimed:
            await self._execute(item)
        return len(claimed)

    async def serve(self, stop: asyncio.Event | None = None) -> None:
        """Run the claim/execute loop until stopped; cleans up on exit."""

        if stop is not None:
            self._stop = stop
        elif self._stopped:
            return
        else:
            self._stop = asyncio.Event()
        self._wake = asyncio.Event()
        self._serve_task = asyncio.current_task()
        wakeups: asyncio.Task[None] | None = None
        if self._notifier is not None:
            wakeups = asyncio.create_task(self._consume_wakeups())
        last_prune = self._now()
        try:
            while not self._stop.is_set():
                await self._fill_slots()
                last_prune = await self._prune_if_due(last_prune)
                if self._stop.is_set():
                    break
                await self._wait_for_wake()
        finally:
            if wakeups is not None:
                wakeups.cancel()
                with suppress(asyncio.CancelledError):
                    await wakeups
            await self._cancel_inflight()
            if self._notifier is not None:
                await self._notifier.aclose()
            self._serve_task = None

    async def astop(self) -> None:
        """Stop serving and release in-flight leases; safe to call twice."""

        self._stopped = True
        self._stop.set()
        self._wake.set()
        task = self._serve_task
        if task is None or task is asyncio.current_task():
            return
        try:
            await asyncio.wait_for(asyncio.shield(task), timeout=10)
        except TimeoutError:
            _LOGGER.warning("work runner shutdown exceeded 10s")

    async def _fill_slots(self) -> None:
        remaining = self._concurrency.max_concurrency - len(self._inflight)
        while remaining > 0:
            batch = min(self._concurrency.claim_batch, remaining)
            claimed = await self._store.claim(
                owner=self._owner,
                queues=self._queues,
                namespace=self._namespace,
                limit=batch,
                lease_seconds=self._lease.seconds,
                now=self._now(),
            )
            if not claimed:
                return
            for item in claimed:
                task = asyncio.create_task(self._execute(item))
                self._inflight[task] = item
                task.add_done_callback(self._task_done)
            remaining -= len(claimed)
            if len(claimed) < batch:
                return

    def _task_done(self, task: asyncio.Task[None]) -> None:
        self._inflight.pop(task, None)
        if task.cancelled():
            return
        error = task.exception()
        if error is not None and not isinstance(error, LeaseLostError):
            _LOGGER.error("work execution task failed", exc_info=error)

    async def _cancel_inflight(self) -> None:
        pending = list(self._inflight.items())
        if not pending:
            return
        for task, _ in pending:
            task.cancel()
        tasks = [task for task, _ in pending]
        _, still_running = await asyncio.wait(tasks, timeout=_SHUTDOWN_TIMEOUT_SECONDS)
        if still_running:
            _LOGGER.warning(
                "%d work task(s) ignored cancellation; their leases will expire",
                len(still_running),
            )
        now = self._now()
        for task, item in pending:
            if task in still_running or item.lease is None:
                continue
            with suppress(Exception):
                await self._store.fail(
                    work_id=item.id,
                    token=item.lease.token,
                    error="runner stopped",
                    retry_at=now,
                    terminal=False,
                )
        self._inflight.clear()

    async def _wait_for_wake(self) -> None:
        try:
            await asyncio.wait_for(
                self._wake.wait(),
                timeout=self._concurrency.poll_interval_seconds,
            )
        except TimeoutError:
            return
        self._wake.clear()

    async def _prune_if_due(self, last_prune: datetime) -> datetime:
        now = self._now()
        if (now - last_prune).total_seconds() < self._prune_interval_seconds:
            return last_prune
        await self._store.prune(before=now - timedelta(seconds=self._retention_seconds))
        return now

    async def _consume_wakeups(self) -> None:
        if self._notifier is None:
            return
        try:
            async for _event in self._notifier.subscribe(self._queues):
                self._wake.set()
        except Exception:  # notification is best-effort; polling still drains
            return

    async def _execute(self, item: WorkItem) -> None:
        lease = item.lease
        if lease is None:
            raise LeaseLostError(f"{item.id}: claimed item has no lease")
        lease_lost = asyncio.Event()
        loss_reason: list[str] = []
        heartbeat = asyncio.create_task(
            self._heartbeat(item.id, lease.token, lease_lost, loss_reason)
        )
        result: WorkResult | None = None
        error: str | None = None
        deadline = item.spec.deadline_seconds
        try:
            if deadline is None:
                result = await self._executor(item)
            else:
                try:
                    result = await asyncio.wait_for(
                        self._executor(item), timeout=deadline
                    )
                except TimeoutError:
                    error = f"TimeoutError: deadline exceeded after {deadline}s"
        except Exception as exc:  # host failures become a stable terminal failure
            error = self._describe_error(exc)
        finally:
            heartbeat.cancel()
            with suppress(asyncio.CancelledError):
                await heartbeat
        if lease_lost.is_set():
            reason = loss_reason[0] if loss_reason else "renewal rejected"
            raise LeaseLostError(f"{item.id}: lease renewal failed ({reason})")
        if error is not None:
            await self._finalize_failure(item, error)
            return
        if result is None:
            raise WorkConfigurationError(f"{item.id}: executor returned no result")
        await self._finalize(item, result)

    async def _heartbeat(
        self,
        work_id: str,
        token: str,
        lease_lost: asyncio.Event,
        loss_reason: list[str],
    ) -> None:
        while True:
            await asyncio.sleep(self._lease.heartbeat_seconds)
            try:
                until = self._now() + timedelta(seconds=self._lease.seconds)
                renewed = await self._store.heartbeat(
                    work_id=work_id, token=token, lease_until=until
                )
            except Exception as exc:  # a failed renewal means the lease is gone
                loss_reason.append(self._describe_error(exc))
                renewed = False
            if not renewed:
                lease_lost.set()
                return

    @staticmethod
    def _describe_error(exc: Exception) -> str:
        return f"{type(exc).__name__}: {exc}"[:_MAX_ERROR_CHARS]

    async def _finalize(self, item: WorkItem, result: WorkResult) -> None:
        lease = item.lease
        if lease is None:
            raise LeaseLostError(f"{item.id}: claimed item has no lease")

        if result.outcome is WorkOutcome.SUCCESS:
            applied = await self._store.complete(
                work_id=item.id, token=lease.token, summary=result.summary
            )
        elif result.outcome is WorkOutcome.RETRY:
            if item.attempts >= self._retry.max_attempts:
                applied = await self._store.fail(
                    work_id=item.id,
                    token=lease.token,
                    error=result.error or "retry requested",
                    retry_at=None,
                    terminal=True,
                )
            else:
                retry_at = self._now() + timedelta(
                    seconds=self._retry.delay_seconds(item.attempts)
                )
                applied = await self._store.fail(
                    work_id=item.id,
                    token=lease.token,
                    error=result.error or "retry requested",
                    retry_at=retry_at,
                    terminal=False,
                )
        elif result.outcome is WorkOutcome.FAIL:
            applied = await self._store.fail(
                work_id=item.id,
                token=lease.token,
                error=result.error or "failed",
                retry_at=None,
                terminal=True,
            )
        elif result.outcome is WorkOutcome.DEFER:
            if result.wait_until is None:
                raise WorkConfigurationError("wait_until: required for defer")
            applied = await self._store.defer(
                work_id=item.id, token=lease.token, until=result.wait_until
            )
        else:
            raise WorkConfigurationError(f"unknown outcome: {result.outcome!r}")

        if not applied:
            raise LeaseLostError(f"{item.id}: lease is no longer held")

    async def _finalize_failure(self, item: WorkItem, error: str) -> None:
        lease = item.lease
        if lease is None:
            raise LeaseLostError(f"{item.id}: claimed item has no lease")
        applied = await self._store.fail(
            work_id=item.id,
            token=lease.token,
            error=error,
            retry_at=None,
            terminal=True,
        )
        if not applied:
            raise LeaseLostError(f"{item.id}: lease is no longer held")

    def _now(self) -> datetime:
        now = self._clock.now()
        require_aware("clock.now()", now)
        return now
