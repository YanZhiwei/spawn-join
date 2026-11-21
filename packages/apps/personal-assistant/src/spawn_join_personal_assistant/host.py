"""个人助理宿主的 supervisor 装配。

宿主拥有全部资源：受限工作区 backend、显式权限策略、strict-msgpack
SQLite checkpointer 和模型绑定。``spawn-join-agent-deepagents`` 的
``build_supervisor`` 始终是唯一装配权威（ADR-0010）；本模块只校验宿主
输入、接线上游 ``SupervisorSpec``，并返回一个由调用方负责关闭的
session。凭据不经过这里：模型以已构造好的 ``BaseChatModel`` 实例或
调用方自有的目录绑定形式进入（ADR-0008 环境边界）。
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
    """把受限工作区策略表达为显式权限规则。

    工作区内允许读写。越界由 backend 自身阻断：它以虚拟路径守卫构造，
    拒绝穿越（``..``）、``~`` 以及工作区根之外的绝对路径。
    """

    return (
        FilesystemPermission(operations=["read", "write"], paths=["/**"], mode="allow"),
    )


def strict_msgpack_serializer() -> JsonPlusSerializer:
    """返回 strict checkpointer 序列化器。

    ``allowed_msgpack_modules=None`` 把反序列化限制在框架安全的
    msgpack 类型白名单内——与文档化的 ``LANGGRAPH_STRICT_MSGPACK``
    开关等价——且不修改进程级全局环境状态。Pickle 回退保持禁用。
    """

    return JsonPlusSerializer(allowed_msgpack_modules=None, pickle_fallback=False)


@dataclass(frozen=True, slots=True)
class HostSession:
    """装配好的 supervisor 加上本宿主拥有的资源。

    关闭由调用方负责（``aclose`` 幂等）；原生图本身不拥有任何宿主
    资源（ADR-0010 资源所有权）。
    """

    spec: SupervisorSpec
    assembly: SupervisorAssembly
    backend: FilesystemBackend
    checkpointer: AsyncSqliteSaver
    connection: aiosqlite.Connection

    async def aclose(self) -> None:
        """关闭宿主自有的 checkpointer 连接；可重复调用。"""

        await self.connection.close()


async def open_host_session(
    config: AppConfig,
    *,
    models: ModelBindings,
    interrupt_on: Mapping[str, bool] | None = None,
    name: str = "personal-assistant",
) -> HostSession:
    """用宿主自有资源装配原生 supervisor 图。

    工作区与数据目录按需创建；backend 把 agent 文件副作用限制在工作区
    根内；checkpointer 以严格反序列化白名单把 thread 状态持久化到数据
    目录下；默认不暴露任何 shell 执行工具。
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
