"""Offline end-to-end: user stories US1-US4 through the real CLI loop."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from pytest import CaptureFixture
from spawn_join_agent_deepagents import ModelBindings
from spawn_join_personal_assistant import (
    ApprovalBook,
    WorkStatus,
    WorkStore,
    main,
)


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "host"
    (root / "model.yaml").parent.mkdir(parents=True, exist_ok=True)
    (root / "model.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    return root


def _argv(root: Path, *args: str) -> list[str]:
    return ["--root", str(root), *args]


def _write_call(file_path: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": "write_file",
                "args": {"file_path": file_path, "content": "note"},
                "id": f"call-{file_path.replace('/', '-')}",
                "type": "tool_call",
            }
        ],
    )


def test_us1_accept_run_report_completes(
    tmp_path: Path,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    make_models: Callable[[BaseChatModel], ModelBindings],
    capsys: CaptureFixture[str],
) -> None:
    root = _root(tmp_path)
    assert main(_argv(root, "accept", "整理发票并汇总", "--key", "k1")) == 0
    capsys.readouterr()

    bindings = make_models(
        make_sequence_model([AIMessage(content="汇总完成：12 张发票")])
    )
    assert main(_argv(root, "run"), bindings=bindings) == 0
    out = capsys.readouterr().out
    assert "completed" in out
    assert "汇总完成" in out

    assert main(_argv(root, "report")) == 0
    out = capsys.readouterr().out
    assert "[completed]" in out or "completed " in out
    assert "汇总完成" in out


def test_us1_idempotency_replay_leaves_one_item(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    root = _root(tmp_path)
    assert main(_argv(root, "accept", "任务A", "--key", "k1")) == 0
    capsys.readouterr()
    assert main(_argv(root, "accept", "任务B", "--key", "k1")) == 1
    capsys.readouterr()

    with WorkStore(root / "data" / "work.db") as store:
        assert store.count_by_status(WorkStatus.QUEUED) == 1


def test_us2_interrupted_run_recovered_exactly_once(
    tmp_path: Path,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    make_models: Callable[[BaseChatModel], ModelBindings],
    capsys: CaptureFixture[str],
) -> None:
    root = _root(tmp_path)
    assert main(_argv(root, "accept", "长任务", "--key", "k1")) == 0
    capsys.readouterr()

    # Simulate a hard-killed process: the item stays RUNNING in the store.
    with WorkStore(root / "data" / "work.db") as store:
        item = store.get_by_idempotency_key("k1")
        assert item is not None
        store.mark(item.id, WorkStatus.RUNNING, increment_attempt=True)

    bindings = make_models(make_sequence_model([AIMessage(content="重跑完成")]))
    assert main(_argv(root, "run"), bindings=bindings) == 0
    out = capsys.readouterr().out
    assert "requeued" in out
    assert "completed" in out

    with WorkStore(root / "data" / "work.db") as store:
        recovered = store.get_by_idempotency_key("k1")
        assert recovered is not None
        assert recovered.status is WorkStatus.COMPLETED
        assert recovered.attempts == 2
        assert recovered.result_summary == "重跑完成"


def test_us3_approve_flow_executes_the_action(
    tmp_path: Path,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    make_models: Callable[[BaseChatModel], ModelBindings],
    capsys: CaptureFixture[str],
) -> None:
    root = _root(tmp_path)
    assert main(_argv(root, "accept", "写一条笔记", "--key", "k1")) == 0
    capsys.readouterr()

    bindings = make_models(
        make_sequence_model(
            [_write_call("/notes.txt"), AIMessage(content="笔记已写入")]
        )
    )
    assert main(_argv(root, "run"), bindings=bindings) == 0
    out = capsys.readouterr().out
    assert "waiting_approval" in out

    assert main(_argv(root, "due")) == 0
    out = capsys.readouterr().out
    assert "[waiting_approval]" in out

    assert main(_argv(root, "approve", "--list")) == 0
    out = capsys.readouterr().out
    assert "record" in out
    assert "write_file" in out

    with ApprovalBook(root / "data" / "approvals.db") as book:
        record_id = book.pending()[0].id

    assert main(_argv(root, "approve", "--record", record_id), bindings=bindings) == 0
    out = capsys.readouterr().out
    assert "approved" in out

    assert (root / "workspace" / "notes.txt").is_file()
    assert (root / "workspace" / "notes.txt").read_text(encoding="utf-8") == "note"

    with WorkStore(root / "data" / "work.db") as store:
        item = store.get_by_idempotency_key("k1")
        assert item is not None
        assert item.status is WorkStatus.COMPLETED


def test_us3_reject_flow_fails_without_executing(
    tmp_path: Path,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    make_models: Callable[[BaseChatModel], ModelBindings],
    capsys: CaptureFixture[str],
) -> None:
    root = _root(tmp_path)
    assert main(_argv(root, "accept", "写一条笔记", "--key", "k1")) == 0
    capsys.readouterr()

    bindings = make_models(
        make_sequence_model([_write_call("/notes.txt"), AIMessage(content="不会执行")])
    )
    assert main(_argv(root, "run"), bindings=bindings) == 0
    capsys.readouterr()

    with ApprovalBook(root / "data" / "approvals.db") as book:
        record_id = book.pending()[0].id

    assert (
        main(
            _argv(root, "approve", "--record", record_id, "--reject"),
            bindings=bindings,
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "rejected" in out

    assert not (root / "workspace" / "notes.txt").exists()
    with WorkStore(root / "data" / "work.db") as store:
        item = store.get_by_idempotency_key("k1")
        assert item is not None
        assert item.status is WorkStatus.FAILED
        assert item.failure_category == "rejected"


def test_us1_escape_write_is_confined_even_when_approved(
    tmp_path: Path,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    make_models: Callable[[BaseChatModel], ModelBindings],
    capsys: CaptureFixture[str],
) -> None:
    root = _root(tmp_path)
    assert main(_argv(root, "accept", "写工作区外文件", "--key", "k1")) == 0
    capsys.readouterr()

    bindings = make_models(
        make_sequence_model(
            [
                _write_call("../../escape.txt"),
                AIMessage(content="写完了"),
            ]
        )
    )
    assert main(_argv(root, "run"), bindings=bindings) == 0
    capsys.readouterr()

    with ApprovalBook(root / "data" / "approvals.db") as book:
        record_id = book.pending()[0].id

    assert main(_argv(root, "approve", "--record", record_id), bindings=bindings) == 0
    capsys.readouterr()

    assert not (root / "escape.txt").exists()
    assert not (tmp_path / "escape.txt").exists()
    listed = list((root / "workspace").rglob("*"))
    assert not any(entry.name == "escape.txt" for entry in listed)
