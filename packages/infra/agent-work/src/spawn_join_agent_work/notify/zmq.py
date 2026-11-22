"""ZeroMQ PUB/SUB wake-up adapter (loopback by default).

Messages are best-effort wake-ups and carry only ``work_id``/``queue``; the
store always remains the source of truth.

On Windows, ``zmq.asyncio`` needs a selector event loop; hosts using the
default Proactor loop must set ``WindowsSelectorEventLoopPolicy`` or run the
notifier under ``asyncio.Runner(loop_factory=asyncio.SelectorEventLoop)``.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Sequence
from datetime import UTC, datetime
from typing import cast

import zmq
import zmq.asyncio

from ..errors import NotifierError
from ..models import WorkEvent

DEFAULT_ENDPOINT = "tcp://127.0.0.1:5559"
_LOOP_HINT = (
    "zmq.asyncio requires a selector event loop; on Windows set "
    "WindowsSelectorEventLoopPolicy or use asyncio.SelectorEventLoop"
)


def _failure(label: str, exc: Exception) -> str:
    if isinstance(exc, RuntimeError):
        return f"{label}: {_LOOP_HINT}"
    return label


def _close_socket(socket: zmq.asyncio.Socket) -> None:
    try:
        socket.close(linger=0)
        return
    except Exception:
        # On a Proactor loop asyncio close can fail before the libzmq socket
        # closes; close the sync socket directly so context teardown cannot hang.
        pass
    inner = getattr(socket, "_socket", None)
    if inner is not None:
        try:
            inner.close(linger=0)
        except Exception:
            pass


class ZmqNotifier:
    """Best-effort wake-up transport over a PUB/SUB socket pair."""

    def __init__(
        self,
        endpoint: str = DEFAULT_ENDPOINT,
        *,
        context: zmq.asyncio.Context | None = None,
    ) -> None:
        self._configured_endpoint = endpoint
        self._actual_endpoint: str | None = None
        self._context = context
        self._owns_context = context is None
        self._publisher: zmq.asyncio.Socket | None = None
        self._subscriber: zmq.asyncio.Socket | None = None
        self._closed = False

    @property
    def endpoint(self) -> str:
        return self._actual_endpoint or self._configured_endpoint

    async def publish(self, event: WorkEvent) -> None:
        if self._closed:
            raise NotifierError("notifier is closed")
        socket = self._ensure_publisher()
        payload = json.dumps({"work_id": event.work_id, "queue": event.queue}).encode(
            "utf-8"
        )
        try:
            await socket.send(payload)
        except (zmq.ZMQError, RuntimeError) as exc:
            raise NotifierError(_failure("failed to publish wake-up", exc)) from exc

    async def subscribe(self, queues: Sequence[str]) -> AsyncIterator[WorkEvent]:
        if self._closed:
            raise NotifierError("notifier is closed")
        allowed = {queue for queue in queues if queue}
        if not allowed:
            return
        socket = self._ensure_subscriber()
        while not self._closed:
            try:
                raw = await socket.recv()
            except asyncio.CancelledError:
                if self._closed:
                    return
                raise
            except (zmq.ZMQError, RuntimeError) as exc:
                if self._closed:
                    return
                raise NotifierError(_failure("failed to receive wake-up", exc)) from exc
            event = self._decode(raw)
            if event is None:
                continue
            if event.queue not in allowed:
                continue
            yield event

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        publisher, subscriber = self._publisher, self._subscriber
        self._publisher = None
        self._subscriber = None
        for socket in (publisher, subscriber):
            if socket is not None:
                _close_socket(socket)
        if self._owns_context and self._context is not None:
            try:
                self._context.destroy(linger=0)
            except Exception:  # a broken loop host still gets idempotent close
                pass

    def _ensure_context(self) -> zmq.asyncio.Context:
        if self._context is None:
            self._context = zmq.asyncio.Context()
        return self._context

    def _new_socket(self, kind: int) -> zmq.asyncio.Socket:
        try:
            return self._ensure_context().socket(kind)
        except (RuntimeError, zmq.ZMQError) as exc:
            raise NotifierError(
                _failure("failed to create wake-up socket", exc)
            ) from exc

    def _ensure_publisher(self) -> zmq.asyncio.Socket:
        if self._publisher is not None:
            return self._publisher
        socket = self._new_socket(zmq.PUB)
        socket.setsockopt(zmq.LINGER, 0)
        try:
            if self._configured_endpoint.endswith(":0"):
                base = self._configured_endpoint.rsplit(":", 1)[0]
                port = socket.bind_to_random_port(base)
                self._actual_endpoint = f"{base}:{port}"
            else:
                socket.bind(self._configured_endpoint)
                self._actual_endpoint = self._configured_endpoint
        except (zmq.ZMQError, RuntimeError) as exc:
            socket.close(linger=0)
            raise NotifierError(
                _failure("failed to bind wake-up endpoint", exc)
            ) from exc
        self._publisher = socket
        return socket

    def _ensure_subscriber(self) -> zmq.asyncio.Socket:
        if self._subscriber is not None:
            return self._subscriber
        socket = self._new_socket(zmq.SUB)
        socket.setsockopt(zmq.LINGER, 0)
        socket.setsockopt(zmq.SUBSCRIBE, b"")
        try:
            socket.connect(self.endpoint)
        except (zmq.ZMQError, RuntimeError) as exc:
            socket.close(linger=0)
            raise NotifierError(
                _failure("failed to connect wake-up endpoint", exc)
            ) from exc
        self._subscriber = socket
        return socket

    @staticmethod
    def _decode(raw: bytes) -> WorkEvent | None:
        try:
            payload = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        data = cast(dict[str, object], payload)
        work_id = data.get("work_id")
        queue = data.get("queue")
        if not isinstance(work_id, str) or not isinstance(queue, str):
            return None
        if not work_id or not queue:
            return None
        return WorkEvent(
            work_id=work_id,
            queue=queue,
            namespace="default",
            type="wakeup",
            occurred_at=datetime.now(UTC),
        )
