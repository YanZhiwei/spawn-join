"""Supervisor assembly for the personal assistant host.

The host owns every resource: the confined workspace backend, the explicit
permission policy, the strict-msgpack SQLite checkpointer, and the model
bindings. ``build_supervisor`` from ``spawn-join-agent-deepagents`` stays
the only assembly authority (ADR-0010); this module validates host inputs,
wires the native ``SupervisorSpec``, and returns a session the caller must
close. Credentials never pass through here: models arrive as already
constructed ``BaseChatModel`` instances or a caller-owned catalog binding
(ADR-0008 environment boundary).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import aiosqlite
from deepagents.backends import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemPermission
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from spawn_join_agent_deepagents import (
    ModelBindings,
    SupervisorAssembly,
    SupervisorSpec,
    build_supervisor,
)

from .config import AppConfig
from .errors import HostConfigError


def workspace_permissions() -> tuple[FilesystemPermission, ...]:
    """Express the confined-workspace policy as explicit permission rules.

    Reads and writes are allowed throughout the workspace. Escapes are
    blocked by the backend itself: it is constructed with virtual path
    guardrails that reject traversal (``..``), ``~``, and absolute paths
    outside the workspace root.
    """

    return (
        FilesystemPermission(operations=["read", "write"], paths=["/**"], mode="allow"),
    )


def strict_msgpack_serializer() -> JsonPlusSerializer:
    """Return the strict checkpointer serializer.

    ``allowed_msgpack_modules=None`` restricts deserialization to the
    framework's safe msgpack type whitelist — the same behavior the
    documented ``LANGGRAPH_STRICT_MSGPACK`` switch enables — without
    mutating process-global environment state. Pickle fallback stays
    disabled.
    """

    return JsonPlusSerializer(allowed_msgpack_modules=None, pickle_fallback=False)


@dataclass(frozen=True, slots=True)
class HostSession:
    """The assembled supervisor plus the resources this host owns.

    Closing is the caller's responsibility (``aclose`` is idempotent); the
    native graph itself owns no host resources (ADR-0010 resource
    ownership).
    """

    spec: SupervisorSpec
    assembly: SupervisorAssembly
    backend: FilesystemBackend
    checkpointer: AsyncSqliteSaver
    connection: aiosqlite.Connection

    async def aclose(self) -> None:
        """Close the host-owned checkpointer connection; safe to repeat."""

        await self.connection.close()


async def open_host_session(
    config: AppConfig,
    *,
    models: ModelBindings,
    interrupt_on: Mapping[str, bool] | None = None,
    name: str = "personal-assistant",
) -> HostSession:
    """Assemble the native supervisor graph with host-owned resources.

    The workspace and data directories are created on demand; the backend
    confines agent file effects to the workspace root; the checkpointer
    persists thread state under the data directory with a strict
    deserialization whitelist; and no shell execution tools are exposed by
    default.
    """

    try:
        config.workspace_root.mkdir(parents=True, exist_ok=True)
        config.data_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise HostConfigError(f"host: cannot prepare directories: {exc}") from exc
    backend = FilesystemBackend(root_dir=config.workspace_root, virtual_mode=True)
    connection = await aiosqlite.connect(config.data_dir / "threads.db")
    checkpointer = AsyncSqliteSaver(connection, serde=strict_msgpack_serializer())
    spec = SupervisorSpec(
        models=models,
        backend=backend,
        permissions=workspace_permissions(),
        interrupt_on=interrupt_on,
        checkpointer=checkpointer,
        tools=(),
        name=name,
    )
    assembly = build_supervisor(spec)
    return HostSession(
        spec=spec,
        assembly=assembly,
        backend=backend,
        checkpointer=checkpointer,
        connection=connection,
    )
