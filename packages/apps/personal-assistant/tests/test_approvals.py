"""HITL 审批的离线测试：暂停、决定、恢复、重启。"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command
from spawn_join_agent_deepagents import (
    ModelBindings,
    PendingInterrupt,
    pending_interrupts,
)
from spawn_join_personal_assistant import (
    AppConfig,
    ApprovalBook,
    HostApprovalError,
    WorkStatus,
    WorkStore,
)
from spawn_join_personal_assistant.approvals import (
    apply_decision,
    interrupt_actions,
    pause_for_approval,
)
from spawn_join_personal_assistant.host import open_host_session


def _catalog(tmp_path: Path) -> Path:
    catalog = tmp_path / "model.yaml"
    catalog.write_text("schema_version: 1\n", encoding="utf-8")
    return catalog


def _app_config(tmp_path: Path) -> AppConfig:
    return AppConfig(
        data_dir=tmp_path / "data",
        workspace_root=tmp_path / "workspace",
        model_catalog_path=_catalog(tmp_path),
    )


def _write_call() -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "write_file",
                "args": {"file_path": "/notes.txt", "content": "note"},
                "id": "call-write-1",
                "type": "tool_call",
            }
        ],
    )


def _models(
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    make_models: Callable[[BaseChatModel], ModelBindings],
) -> ModelBindings:
    model = make_sequence_model([_write_call(), AIMessage(content="all done")])
    return make_models(model)


async def _run_until_interrupt(
    session: Any, thread_id: str
) -> tuple[Any, dict[str, Any]]:
    graph_config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    interrupt_found = None
    async for update in session.assembly.graph.astream(
        {"messages": [HumanMessage(content="写一条笔记")]},
        graph_config,
        stream_mode="updates",
        version="v1",
    ):
        found = pending_interrupts(update)
        if found:
            interrupt_found = found[0]
    return interrupt_found, graph_config


def test_pause_persists_request_and_moves_to_waiting(
    tmp_path: Path,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    make_models: Callable[[BaseChatModel], ModelBindings],
) -> None:
    async def scenario() -> None:
        with (
            WorkStore(tmp_path / "work.db") as store,
            ApprovalBook(tmp_path / "approvals.db") as book,
        ):
            item = store.accept("写笔记", idempotency_key="key-1")
            store.mark(item.id, WorkStatus.RUNNING)

            session = await open_host_session(
                _app_config(tmp_path),
                models=_models(make_sequence_model, make_models),
                interrupt_on={"write_file": True},
            )
            try:
                interrupt, _ = await _run_until_interrupt(session, "t-1")
                assert interrupt is not None
                actions = interrupt_actions(interrupt)
                assert len(actions) == 1
                assert actions[0]["name"] == "write_file"

                record = pause_for_approval(
                    store,
                    book,
                    work_item_id=item.id,
                    thread_id="t-1",
                    interrupt=interrupt,
                )

                assert record.decision == "pending"
                assert book.get(record.id) == record
                paused = store.get(item.id)
                assert paused is not None
                assert paused.status is WorkStatus.WAITING_APPROVAL
                assert paused.thread_id == "t-1"
            finally:
                await session.aclose()

    asyncio.run(scenario())


def test_approve_resumes_and_executes_the_action(
    tmp_path: Path,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    make_models: Callable[[BaseChatModel], ModelBindings],
) -> None:
    async def scenario() -> None:
        with (
            WorkStore(tmp_path / "work.db") as store,
            ApprovalBook(tmp_path / "approvals.db") as book,
        ):
            item = store.accept("写笔记", idempotency_key="key-1")
            store.mark(item.id, WorkStatus.RUNNING)

            session = await open_host_session(
                _app_config(tmp_path),
                models=_models(make_sequence_model, make_models),
                interrupt_on={"write_file": True},
            )
            try:
                interrupt, graph_config = await _run_until_interrupt(session, "t-1")
                assert interrupt is not None
                record = pause_for_approval(
                    store,
                    book,
                    work_item_id=item.id,
                    thread_id="t-1",
                    interrupt=interrupt,
                )

                command = apply_decision(
                    store,
                    book,
                    record_id=record.id,
                    work_item_id=item.id,
                    approve=True,
                )

                assert isinstance(command, Command)
                resumed = cast(Any, command).resume
                assert len(resumed["decisions"]) == len(record.actions)
                running = store.get(item.id)
                assert running is not None
                assert running.status is WorkStatus.RUNNING

                await session.assembly.graph.ainvoke(command, graph_config)

                assert (tmp_path / "workspace" / "notes.txt").is_file()

                store.mark(item.id, WorkStatus.COMPLETED, result_summary="all done")
                final = store.get(item.id)
                assert final is not None
                assert final.status is WorkStatus.COMPLETED
                decided = book.get(record.id)
                assert decided is not None
                assert decided.decision == "approved"
                assert decided.decided_at is not None
            finally:
                await session.aclose()

    asyncio.run(scenario())


def test_reject_fails_item_without_executing_action(
    tmp_path: Path,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    make_models: Callable[[BaseChatModel], ModelBindings],
) -> None:
    async def scenario() -> None:
        with (
            WorkStore(tmp_path / "work.db") as store,
            ApprovalBook(tmp_path / "approvals.db") as book,
        ):
            item = store.accept("写笔记", idempotency_key="key-1")
            store.mark(item.id, WorkStatus.RUNNING)

            session = await open_host_session(
                _app_config(tmp_path),
                models=_models(make_sequence_model, make_models),
                interrupt_on={"write_file": True},
            )
            try:
                interrupt, graph_config = await _run_until_interrupt(session, "t-1")
                assert interrupt is not None
                record = pause_for_approval(
                    store,
                    book,
                    work_item_id=item.id,
                    thread_id="t-1",
                    interrupt=interrupt,
                )

                command = apply_decision(
                    store,
                    book,
                    record_id=record.id,
                    work_item_id=item.id,
                    approve=False,
                    message="not allowed",
                )

                rejected = store.get(item.id)
                assert rejected is not None
                assert rejected.status is WorkStatus.FAILED
                assert rejected.failure_category == "rejected"

                await session.assembly.graph.ainvoke(command, graph_config)

                assert not (tmp_path / "workspace" / "notes.txt").exists()
                decided = book.get(record.id)
                assert decided is not None
                assert decided.decision == "rejected"
            finally:
                await session.aclose()

    asyncio.run(scenario())


def test_decided_records_are_immutable(tmp_path: Path) -> None:
    with (
        WorkStore(tmp_path / "work.db") as store,
        ApprovalBook(tmp_path / "approvals.db") as book,
    ):
        item = store.accept("任务A", idempotency_key="key-1")
        store.mark(item.id, WorkStatus.RUNNING)
        interrupt = PendingInterrupt(
            id="int-1",
            value={
                "action_requests": [{"name": "write_file", "args": {"path": "/x.txt"}}]
            },
        )
        record = pause_for_approval(
            store,
            book,
            work_item_id=item.id,
            thread_id="t-1",
            interrupt=interrupt,
        )

        apply_decision(
            store,
            book,
            record_id=record.id,
            work_item_id=item.id,
            approve=True,
        )

        with pytest.raises(HostApprovalError, match="already approved"):
            apply_decision(
                store,
                book,
                record_id=record.id,
                work_item_id=item.id,
                approve=False,
            )


def test_pending_alignment_survives_restart(tmp_path: Path) -> None:
    with (
        WorkStore(tmp_path / "work.db") as store,
        ApprovalBook(tmp_path / "approvals.db") as book,
    ):
        item = store.accept("任务A", idempotency_key="key-1")
        store.mark(item.id, WorkStatus.RUNNING)
        interrupt = PendingInterrupt(
            id=None,
            value={
                "action_requests": [
                    {"name": "write_file", "args": {"path": "/a.txt"}},
                    {"name": "write_file", "args": {"path": "/b.txt"}},
                ]
            },
        )
        record = pause_for_approval(
            store,
            book,
            work_item_id=item.id,
            thread_id="t-9",
            interrupt=interrupt,
        )

    with (
        WorkStore(tmp_path / "work.db") as store,
        ApprovalBook(tmp_path / "approvals.db") as book,
    ):
        pending_records = book.pending()
        assert [r.id for r in pending_records] == [record.id]
        assert len(pending_records[0].actions) == 2

        unfinished = store.pending_recovery()
        assert [i.id for i in unfinished] == [item.id]
        assert unfinished[0].status is WorkStatus.WAITING_APPROVAL
        assert unfinished[0].thread_id == "t-9"


def test_interrupt_without_actions_is_rejected() -> None:
    interrupt = PendingInterrupt(id="int-2", value={"unexpected": True})

    with pytest.raises(HostApprovalError, match="action_requests"):
        interrupt_actions(interrupt)
