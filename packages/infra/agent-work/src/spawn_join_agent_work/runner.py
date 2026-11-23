"""Single-pass and long-running work execution."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from contextlib import suppress
from datetime import datetime, timedelta
from uuid import uuid4

from .errors import LeaseLostError, WorkConfigurationError
from .models import WorkItem, WorkOutcome, WorkResult
from .policies import ConcurrencyPolicy, LeasePolicy, RetryPolicy
from .protocols import Clock, WorkExecutor, WorkStore
from .stores._support import SystemClock, require_aware

_MAX_ERROR_CHARS = 500


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
    ) -> None:
        self._store = store
        self._executor = executor
        self._clock: Clock = clock or SystemClock()
        self._queues = tuple(queues)
        self._namespace = namespace
        self._lease = lease_policy or LeasePolicy()
        self._retry = retry_policy or RetryPolicy()
        self._concurrency = concurrency or ConcurrencyPolicy()
        self._owner = owner or f"runner-{uuid4().hex}"

    @property
    def owner(self) -> str:
        return self._owner

    async def run_once(self, *, limit: int | None = None) -> int:
        """Claim and process one batch; returns the number of processed items."""

        batch = limit if limit is not None else self._concurrency.claim_batch
        if batch < 1:
            raise WorkConfigurationError("limit: must be >= 1")
        processed = 0
        while processed < batch:
            # 逐项领取，避免等待执行的任务在未续租时过期。
            claimed = await self._store.claim(
                owner=self._owner,
                queues=self._queues,
                namespace=self._namespace,
                limit=1,
                lease_seconds=self._lease.seconds,
                now=self._now(),
            )
            if not claimed:
                break
            await self._execute(claimed[0])
            processed += 1
        return processed

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
