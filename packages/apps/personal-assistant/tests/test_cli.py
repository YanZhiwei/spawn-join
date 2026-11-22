"""CLI 冒烟测试：子命令、输出与稳定退出码。"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Callable
from pathlib import Path

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from pytest import CaptureFixture
from spawn_join_agent_deepagents import ModelBindings
from spawn_join_personal_assistant import WorkStatus, WorkStore, main
from spawn_join_personal_assistant.cli import (
    _serve,  # pyright: ignore[reportPrivateUsage]
)
from spawn_join_personal_assistant.config import AppConfig


def _root(tmp_path: Path) -> Path:
    root = tmp_path / "host"
    catalog = root / "model.yaml"
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text("schema_version: 1\n", encoding="utf-8")
    return root


def _argv(root: Path, *args: str) -> list[str]:
    return ["--root", str(root), *args]


def test_accept_then_due_and_report(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    root = _root(tmp_path)

    assert main(_argv(root, "accept", "整理发票", "--key", "k1")) == 0
    assert main(_argv(root, "accept", "第二件事", "--key", "k2")) == 0

    out = capsys.readouterr().out
    assert "key=k1" in out

    assert main(_argv(root, "due")) == 0
    out = capsys.readouterr().out
    assert "[queued]" in out
    assert "unfinished item(s)" in out

    assert main(_argv(root, "report")) == 0
    out = capsys.readouterr().out
    assert "report: 2 item(s)" in out


def test_accept_replay_rejected_with_stable_error(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    root = _root(tmp_path)

    assert main(_argv(root, "accept", "任务A", "--key", "k1")) == 0
    capsys.readouterr()

    assert main(_argv(root, "accept", "任务B", "--key", "k1")) == 1
    err = capsys.readouterr().err
    assert err.startswith("personal-assistant:")
    assert "idempotency_key" in err

    with WorkStore(root / "data" / "work.db") as store:
        assert store.count_by_status(WorkStatus.QUEUED) == 1


def test_accept_rejects_blank_goal(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    root = _root(tmp_path)

    assert main(_argv(root, "accept", "   ", "--key", "k1")) == 1
    err = capsys.readouterr().err
    assert "goal" in err


def test_accept_rejects_bad_due(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    root = _root(tmp_path)

    assert main(_argv(root, "accept", "任务A", "--key", "k1", "--due", "nope")) == 1
    err = capsys.readouterr().err
    assert "--due" in err


def test_missing_catalog_fails_with_stable_error(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    root = tmp_path / "host"
    root.mkdir()

    assert main(_argv(root, "accept", "任务A")) == 1
    err = capsys.readouterr().err
    assert "personal-assistant:" in err


def test_empty_due_and_report_succeed(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    root = _root(tmp_path)

    assert main(_argv(root, "due")) == 0
    out = capsys.readouterr().out
    assert "0 unfinished item(s)" in out

    assert main(_argv(root, "report")) == 0
    out = capsys.readouterr().out
    assert "0 item(s)" in out


def test_approve_requires_record_or_list(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    root = _root(tmp_path)

    assert main(_argv(root, "approve")) == 1
    err = capsys.readouterr().err
    assert "--record or --list" in err


def test_approve_unknown_record_fails_stably(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    root = _root(tmp_path)

    assert main(_argv(root, "approve", "--record", "missing-id")) == 1
    err = capsys.readouterr().err
    assert "unknown record" in err


def test_run_without_bindings_fails_stably(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    root = _root(tmp_path)
    root.mkdir(exist_ok=True)
    (root / "model.yaml").write_text("schema_version: 1\n", encoding="utf-8")
    assert main(_argv(root, "accept", "任务A", "--key", "k1")) == 0
    capsys.readouterr()

    assert main(_argv(root, "run")) == 1
    err = capsys.readouterr().err
    assert "personal-assistant:" in err


def test_usage_error_exits_one() -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--no-such-flag"])
    assert excinfo.value.code == 1


def test_run_with_injected_bindings_smoke(
    tmp_path: Path,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    make_models: Callable[[BaseChatModel], ModelBindings],
    capsys: CaptureFixture[str],
) -> None:
    root = _root(tmp_path)
    assert main(_argv(root, "accept", "总结一句话", "--key", "k1")) == 0
    capsys.readouterr()

    bindings = make_models(make_sequence_model([AIMessage(content="整理完成：1 项")]))

    assert main(_argv(root, "run"), bindings=bindings) == 0
    out = capsys.readouterr().out
    assert "completed" in out
    assert "1 item(s) processed" in out


def test_serve_bounded_smoke_with_injected_bindings(
    tmp_path: Path,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    make_models: Callable[[BaseChatModel], ModelBindings],
    capsys: CaptureFixture[str],
) -> None:
    root = _root(tmp_path)
    assert main(_argv(root, "accept", "总结一句话", "--key", "k1")) == 0
    capsys.readouterr()

    bindings = make_models(make_sequence_model([AIMessage(content="整理完成：1 项")]))

    assert (
        main(
            _argv(root, "serve", "--max-cycles", "1", "--poll-interval", "0.01"),
            bindings=bindings,
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "completed" in out
    assert "serve: 1 cycle(s), 1 item(s) processed" in out


def test_serve_rejects_invalid_poll_interval(
    tmp_path: Path, capsys: CaptureFixture[str]
) -> None:
    root = _root(tmp_path)
    assert main(_argv(root, "serve", "--poll-interval", "0")) == 1
    err = capsys.readouterr().err
    assert "--poll-interval" in err


def test_serve_rejects_zero_cycles(tmp_path: Path, capsys: CaptureFixture[str]) -> None:
    root = _root(tmp_path)
    assert main(_argv(root, "serve", "--max-cycles", "0")) == 1
    err = capsys.readouterr().err
    assert "--max-cycles" in err


def test_serve_stops_when_event_is_set(
    tmp_path: Path,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
    make_models: Callable[[BaseChatModel], ModelBindings],
) -> None:
    root = _root(tmp_path)
    config = AppConfig(
        data_dir=root / "data",
        workspace_root=root / "workspace",
        model_catalog_path=root / "model.yaml",
    )
    bindings = make_models(make_sequence_model([]))
    args = argparse.Namespace(
        max_concurrency=1,
        deadline=None,
        supervisor_model="supervisor",
        worker_model="worker",
        poll_interval=0.01,
        max_cycles=None,
    )
    stop = asyncio.Event()
    stop.set()
    assert asyncio.run(_serve(config, bindings, args, stop=stop)) == 0
