"""Offline tests for host assembly wiring, resources, and smoke execution."""

from __future__ import annotations

import asyncio

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from spawn_join_agent_deepagents import ModelBindings
from spawn_join_personal_assistant import AppConfig, HostSession
from spawn_join_personal_assistant.host import (
    open_host_session,
    strict_msgpack_serializer,
    workspace_permissions,
)


async def _open_session(
    config: AppConfig,
    models: ModelBindings,
    *,
    interrupt_on: dict[str, bool] | None = None,
) -> HostSession:
    return await open_host_session(config, models=models, interrupt_on=interrupt_on)


def test_open_host_session_wires_confinement(
    host_config: AppConfig, host_models: ModelBindings
) -> None:
    async def scenario() -> None:
        session = await _open_session(host_config, host_models)
        await session.aclose()

        assert session.backend.cwd == host_config.workspace_root
        permissions = session.spec.permissions
        assert permissions is not None
        assert tuple(permissions) == workspace_permissions()
        assert session.spec.tools == ()
        assert session.spec.checkpointer is session.checkpointer
        assert session.spec.backend is session.backend

    asyncio.run(scenario())


def test_open_host_session_reports_filesystem_backend(
    host_config: AppConfig, host_models: ModelBindings
) -> None:
    async def scenario() -> None:
        session = await _open_session(host_config, host_models)
        await session.aclose()

        report = session.assembly.report
        assert report.resources.backend_kind == "filesystem"
        assert report.resources.permissions.allow == 1
        assert report.resources.permissions.deny == 0
        assert report.resources.permissions.interrupt == 0

    asyncio.run(scenario())


def test_checkpointer_uses_strict_serializer(
    host_config: AppConfig, host_models: ModelBindings
) -> None:
    async def scenario() -> None:
        session = await _open_session(host_config, host_models)
        await session.aclose()

        serde = session.checkpointer.serde
        assert isinstance(serde, JsonPlusSerializer)
        assert serde.pickle_fallback is False
        strict = strict_msgpack_serializer()
        sample = {"kind": "host", "count": 2}
        assert serde.dumps_typed(sample) == strict.dumps_typed(sample)
        assert strict.loads_typed(strict.dumps_typed(sample)) == sample

    asyncio.run(scenario())


def test_directories_created_on_demand(
    host_config: AppConfig, host_models: ModelBindings
) -> None:
    async def scenario() -> None:
        assert not host_config.workspace_root.exists()
        assert not host_config.data_dir.exists()

        session = await _open_session(host_config, host_models)
        await session.aclose()

        assert host_config.workspace_root.is_dir()
        assert host_config.data_dir.is_dir()

    asyncio.run(scenario())


def test_interrupt_on_mapping_is_passed_through(
    host_config: AppConfig, host_models: ModelBindings
) -> None:
    async def scenario() -> None:
        session = await _open_session(
            host_config, host_models, interrupt_on={"write_file": True}
        )
        await session.aclose()

        assert session.spec.interrupt_on == {"write_file": True}

    asyncio.run(scenario())


def test_offline_assembly_smoke_with_thread_state(
    host_config: AppConfig, host_models: ModelBindings, fake_response: str
) -> None:
    async def scenario() -> None:
        session = await _open_session(host_config, host_models)
        try:
            graph_config = {"configurable": {"thread_id": "smoke-thread-1"}}
            first = await session.assembly.graph.ainvoke(
                {"messages": [HumanMessage(content="记住：偏好深色模式")]},
                graph_config,
            )
            second = await session.assembly.graph.ainvoke(
                {"messages": [HumanMessage(content="我上一条说了什么？")]},
                graph_config,
            )

            assert str(first["messages"][-1].content) == fake_response
            messages = second["messages"]
            assert str(messages[-1].content) == fake_response
            assert len(messages) >= 2
        finally:
            await session.aclose()

    asyncio.run(scenario())


def test_aclose_is_repeatable(
    host_config: AppConfig, host_models: ModelBindings
) -> None:
    async def scenario() -> None:
        session = await _open_session(host_config, host_models)

        await session.aclose()
        await session.aclose()

    asyncio.run(scenario())
