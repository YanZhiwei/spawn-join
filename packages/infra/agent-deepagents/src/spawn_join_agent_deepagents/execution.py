"""Explicit, reusable, async-first delegation control.

The controller owns a bounded FIFO waiter queue and a fixed number of active
slots. It never uses process-global state. Deadline expiry is enforced with
normal asyncio cancellation; sync execution is rejected because Python cannot
safely preempt a running synchronous callable.
"""

from __future__ import annotations

import asyncio
from collections import deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from langchain.agents.middleware.types import AgentMiddleware
from langchain.tools.tool_node import ToolCallRequest
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from .diagnostics import (
    DiagnosticEmitter,
    DiagnosticEventType,
    RequestContext,
    request_context,
)
from .errors import (
    AgentConfigurationError,
    DelegationQueueFullError,
    DelegationTimeoutError,
    UnsupportedSyncDelegationError,
)
from .middleware import DELEGATION_MIDDLEWARE_NAME

T = TypeVar("T")
ToolResult = ToolMessage | Command[Any]
TransitionCallback = Callable[[], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class DelegationPolicy:
    """Bound the active and waiting delegated work and its total deadline."""

    max_concurrency: int
    max_queue: int
    deadline_seconds: float | None = None

    def __post_init__(self) -> None:
        if self.max_concurrency < 1:
            raise AgentConfigurationError(
                "delegation.max_concurrency: must be at least 1"
            )
        if self.max_queue < 0:
            raise AgentConfigurationError("delegation.max_queue: must be at least 0")
        if self.deadline_seconds is not None and self.deadline_seconds <= 0:
            raise AgentConfigurationError(
                "delegation.deadline_seconds: must be greater than 0"
            )


@dataclass(frozen=True, slots=True)
class DelegationConfiguration:
    """A policy plus an optional host-reused controller."""

    policy: DelegationPolicy
    controller: DelegationController | None = None

    def __post_init__(self) -> None:
        if self.controller is not None and self.controller.policy != self.policy:
            raise AgentConfigurationError(
                "delegation: controller policy does not match configuration"
            )


class DelegationController:
    """A reusable async controller bound to one event loop."""

    def __init__(self, policy: DelegationPolicy) -> None:
        self._policy = policy
        self._available = policy.max_concurrency
        self._waiters: deque[asyncio.Future[None]] = deque()
        self._lock: asyncio.Lock | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    @property
    def policy(self) -> DelegationPolicy:
        return self._policy

    @property
    def active_count(self) -> int:
        return self._policy.max_concurrency - self._available

    @property
    def waiting_count(self) -> int:
        return len(self._waiters)

    async def run(
        self,
        operation: Callable[[], Awaitable[T]],
        *,
        subagent_name: str,
        on_queued: TransitionCallback | None = None,
        on_started: TransitionCallback | None = None,
    ) -> T:
        """Run one operation under the configured concurrency/queue/deadline."""

        self._bind_loop()
        started_at = asyncio.get_running_loop().time()
        acquired = False
        try:
            await self._acquire(started_at, subagent_name, on_queued)
            acquired = True
            if on_started is not None:
                await on_started()
            remaining = self._remaining(started_at, subagent_name)
            if remaining is None:
                return await operation()
            try:
                async with asyncio.timeout(remaining):
                    return await operation()
            except TimeoutError as exc:
                if self._deadline_expired(started_at):
                    raise DelegationTimeoutError(
                        f"delegation.{subagent_name}: deadline exceeded"
                    ) from exc
                raise
        finally:
            if acquired:
                await self._release()

    def _bind_loop(self) -> None:
        loop = asyncio.get_running_loop()
        if self._loop is None:
            self._loop = loop
            return
        if self._loop is not loop:
            raise RuntimeError(
                "DelegationController is bound to one event loop; "
                "create a new controller for another loop"
            )

    async def _get_lock(self) -> asyncio.Lock:
        self._bind_loop()
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _acquire(
        self,
        started_at: float,
        subagent_name: str,
        on_queued: TransitionCallback | None,
    ) -> None:
        self._remaining(started_at, subagent_name)
        lock = await self._get_lock()
        async with lock:
            if self._available > 0:
                self._available -= 1
                return
            if len(self._waiters) >= self._policy.max_queue:
                raise DelegationQueueFullError(
                    f"delegation.{subagent_name}: queue is full "
                    f"(max_concurrency={self._policy.max_concurrency}, "
                    f"max_queue={self._policy.max_queue})"
                )
            future = asyncio.get_running_loop().create_future()
            self._waiters.append(future)

        await self._notify_queued(on_queued, future)
        try:
            remaining = self._remaining(started_at, subagent_name)
        except BaseException:
            await self._remove_waiter_or_release(future)
            raise
        try:
            if remaining is None:
                await future
            else:
                async with asyncio.timeout(remaining):
                    await future
        except TimeoutError as exc:
            await self._remove_waiter_or_release(future)
            raise DelegationTimeoutError(
                f"delegation.{subagent_name}: deadline exceeded while queued"
            ) from exc
        except asyncio.CancelledError:
            await self._remove_waiter_or_release(future)
            raise

    async def _notify_queued(
        self,
        on_queued: TransitionCallback | None,
        future: asyncio.Future[None],
    ) -> None:
        if on_queued is None:
            return
        try:
            await on_queued()
        except BaseException:
            await self._remove_waiter_or_release(future)
            raise

    async def _remove_waiter_or_release(
        self,
        future: asyncio.Future[None],
    ) -> None:
        lock = await self._get_lock()
        async with lock:
            if future in self._waiters:
                self._waiters.remove(future)
                return
            if future.done() and not future.cancelled():
                self._release_locked()

    async def _release(self) -> None:
        lock = await self._get_lock()
        async with lock:
            self._release_locked()

    def _release_locked(self) -> None:
        while self._waiters:
            future = self._waiters.popleft()
            if not future.done():
                future.set_result(None)
                return
        self._available += 1

    def _remaining(
        self,
        started_at: float,
        subagent_name: str,
    ) -> float | None:
        deadline = self._policy.deadline_seconds
        if deadline is None:
            return None
        remaining = deadline - (asyncio.get_running_loop().time() - started_at)
        if remaining <= 0:
            raise DelegationTimeoutError(
                f"delegation.{subagent_name}: deadline exceeded"
            )
        return remaining

    def _deadline_expired(self, started_at: float) -> bool:
        deadline = self._policy.deadline_seconds
        if deadline is None:
            return False
        return deadline - (asyncio.get_running_loop().time() - started_at) <= 0


class DelegationPolicyMiddleware(AgentMiddleware[Any, Any, Any]):
    """Intercept only the native ``task`` tool and apply the controller."""

    def __init__(
        self,
        controller: DelegationController,
        emitter: DiagnosticEmitter | None = None,
    ) -> None:
        super().__init__()
        self._controller = controller
        self._emitter = emitter

    @property
    def name(self) -> str:
        return DELEGATION_MIDDLEWARE_NAME

    @property
    def controller(self) -> DelegationController:
        return self._controller

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolResult],
    ) -> ToolResult:
        if request.tool_call["name"] != "task":
            return handler(request)
        raise UnsupportedSyncDelegationError(
            "delegation: governed delegation requires ainvoke/astream"
        )

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolResult]],
    ) -> ToolResult:
        if request.tool_call["name"] != "task":
            return await handler(request)
        context = request_context(request)

        async def operation() -> ToolResult:
            return await handler(request)

        return await self._run_governed(operation, context)

    async def _run_governed(
        self,
        operation: Callable[[], Awaitable[ToolResult]],
        context: RequestContext,
    ) -> ToolResult:
        try:
            return await self._controller.run(
                operation,
                subagent_name=context.subagent_name,
                on_queued=lambda: self._emit(
                    DiagnosticEventType.DELEGATION_QUEUED,
                    context,
                ),
                on_started=lambda: self._emit(
                    DiagnosticEventType.DELEGATION_STARTED,
                    context,
                ),
            )
        except DelegationQueueFullError:
            await self._emit(
                DiagnosticEventType.DELEGATION_REJECTED,
                context,
                outcome="rejected",
                error_category="delegation_queue_full",
            )
            raise
        except DelegationTimeoutError:
            await self._emit(
                DiagnosticEventType.DELEGATION_TIMED_OUT,
                context,
                outcome="timed_out",
                error_category="delegation_timeout",
            )
            raise

    async def _emit(
        self,
        event_type: DiagnosticEventType,
        context: RequestContext,
        *,
        outcome: str | None = None,
        error_category: str | None = None,
    ) -> None:
        if self._emitter is None:
            return
        await self._emitter.aemit(
            event_type,
            context=context,
            outcome=outcome,
            error_category=error_category,
        )
