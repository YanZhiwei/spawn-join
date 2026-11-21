"""Command-line interface for the personal assistant host.

Five subcommands drive the durable work loop: ``accept`` records a goal,
``due`` lists unfinished items, ``run`` executes one bounded scheduling
cycle (recovering interrupted runs first), ``report`` shows outcomes, and
``approve`` lists or decides pending HITL requests. Model bindings are a
host-owned resource: by default they are built from the model catalog
(ADR-0008 environment boundary), and the ``bindings`` parameter of ``main``
is the explicit injection seam for offline/alternative execution.

Exit codes: 0 success, 1 for host errors (stable ``personal-assistant:``
prefix on stderr), 1 for usage errors.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn

from langchain_core.messages import HumanMessage
from spawn_join_agent_deepagents import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    pending_interrupts,
)

from spawn_join_llm_provider import ConfigurationError
from spawn_join_llm_provider_langchain import ModelCatalog

from .approvals import ApprovalBook, apply_decision, pause_for_approval
from .config import AppConfig
from .errors import HostError
from .host import HostSession, open_host_session
from .scheduler import Scheduler
from .work.models import WorkItem, WorkStatus
from .work.store import WorkStore

_DEFAULT_ROOT = Path.home() / ".spawn-join-personal-assistant"

# v1 approval policy: writes into the workspace need human approval.
_GATED_TOOLS: dict[str, bool] = {"write_file": True}

_SUMMARY_LIMIT = 200


class _ArgumentParser(argparse.ArgumentParser):
    """Argparse parser that maps usage errors to exit code 1."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def _write(text: str, *, error: bool = False) -> None:
    """Write one user-facing line to stdout or stderr (no print, no logs)."""

    stream = sys.stderr if error else sys.stdout
    stream.write(text if text.endswith("\n") else text + "\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(prog="personal-assistant")
    parser.add_argument(
        "--root",
        type=Path,
        default=_DEFAULT_ROOT,
        help="Host data root (data/, workspace/, model.yaml)",
    )
    parser.add_argument(
        "--model-catalog",
        type=Path,
        default=None,
        help="Model catalog path; defaults to <root>/model.yaml",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    accept = subparsers.add_parser("accept", help="Record a new work item")
    accept.add_argument("goal", help="Natural-language goal for the agent")
    accept.add_argument(
        "--key",
        default=None,
        help="Idempotency key; defaults to a fresh UUID",
    )
    accept.add_argument(
        "--due",
        default=None,
        help="ISO-8601 UTC time when the item becomes runnable",
    )

    subparsers.add_parser("due", help="List unfinished work items")

    run = subparsers.add_parser("run", help="Run one bounded due cycle")
    run.add_argument(
        "--max-concurrency",
        type=int,
        default=2,
        help="Maximum simultaneously running items",
    )
    run.add_argument(
        "--deadline",
        type=float,
        default=None,
        help="Total runtime budget per item in seconds",
    )
    run.add_argument(
        "--supervisor-model",
        default="supervisor",
        help="Catalog entry used for the supervisor purpose",
    )
    run.add_argument(
        "--worker-model",
        default="worker",
        help="Catalog entry used for the worker purpose",
    )

    report = subparsers.add_parser("report", help="Show outcomes")
    report.add_argument(
        "--status",
        default=None,
        help="Only show items with this status",
    )

    approve = subparsers.add_parser("approve", help="Decide pending requests")
    approve.add_argument(
        "--list",
        action="store_true",
        dest="list_records",
        help="List pending approval records",
    )
    approve.add_argument("--record", default=None, help="Approval record id")
    approve.add_argument(
        "--reject",
        action="store_true",
        help="Reject instead of approve",
    )
    approve.add_argument("--message", default=None, help="Rejection message")
    return parser


def _app_config(args: argparse.Namespace) -> AppConfig:
    model_catalog = args.model_catalog
    if model_catalog is None:
        model_catalog = args.root / "model.yaml"
    return AppConfig(
        data_dir=args.root / "data",
        workspace_root=args.root / "workspace",
        model_catalog_path=model_catalog,
    )


def _catalog_bindings(config: AppConfig, args: argparse.Namespace) -> ModelBindings:
    """Build production model bindings from the catalog (ADR-0008)."""

    try:
        catalog = ModelCatalog.from_file(str(config.model_catalog_path))
    except ConfigurationError as exc:
        raise HostError(f"model catalog: {exc}") from exc
    return ModelBindings(
        catalog=catalog,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, catalog=args.supervisor_model),
            ModelBinding(ModelPurpose.WORKER, catalog=args.worker_model),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )


def _describe(item: WorkItem) -> str:
    """One stable, secret-free status line for a work item."""

    if item.status is WorkStatus.COMPLETED:
        return f"completed {item.id}: {item.result_summary or ''}"
    if item.status is WorkStatus.FAILED:
        return f"failed {item.id}: {item.failure_category or 'error'}"
    if item.status is WorkStatus.WAITING_APPROVAL:
        return f"waiting_approval {item.id}: needs human decision"
    return f"{item.status.value} {item.id}: {item.goal[:60]}"


def _accept(config: AppConfig, args: argparse.Namespace) -> int:
    due_at: str | None = None
    if args.due is not None:
        try:
            datetime.fromisoformat(str(args.due))
        except ValueError as exc:
            raise HostError("--due: must be an ISO-8601 datetime") from exc
        due_at = str(args.due)
    key = str(args.key) if args.key else uuid.uuid4().hex
    with WorkStore(config.data_dir / "work.db") as store:
        item = store.accept(str(args.goal), idempotency_key=key, due_at=due_at)
    _write(f"accepted {item.id} key={key}")
    return 0


def _due(config: AppConfig) -> int:
    with WorkStore(config.data_dir / "work.db") as store:
        items = store.pending_recovery()
    for item in items:
        due = item.due_at or "-"
        _write(f"[{item.status.value}] {item.id} due={due} {item.goal[:60]}")
    _write(f"due: {len(items)} unfinished item(s)")
    return 0


def _report(config: AppConfig, args: argparse.Namespace) -> int:
    with WorkStore(config.data_dir / "work.db") as store:
        items = store.list_all()
    status = str(args.status) if args.status else None
    shown = 0
    for item in items:
        if status is not None and item.status.value != status:
            continue
        _write(_describe(item))
        shown += 1
    _write(f"report: {shown} item(s)")
    return 0


async def _drive_to_outcome(
    session: HostSession,
    store: WorkStore,
    book: ApprovalBook,
    *,
    item_id: str,
    thread_id: str,
    invoke_input: Any,
) -> str:
    """Stream one graph run to a pause or a persisted completion.

    The update stream must be fully consumed before any decision: breaking
    early interrupts the underlying run and its checkpoint. An interrupt
    pauses the item for approval; otherwise the final assistant message
    becomes the persisted result summary.
    """

    graph: Any = session.assembly.graph
    graph_config: dict[str, Any] = {"configurable": {"thread_id": thread_id}}
    pending = None
    async for update in graph.astream(
        invoke_input, graph_config, stream_mode="updates", version="v1"
    ):
        found = pending_interrupts(update)
        if found:
            pending = found[0]
    if pending is not None:
        pause_for_approval(
            store,
            book,
            work_item_id=item_id,
            thread_id=thread_id,
            interrupt=pending,
        )
        return "paused"
    state: Any = await graph.aget_state(graph_config)
    messages: Any = state.values.get("messages") or []
    summary = str(messages[-1].content)[:_SUMMARY_LIMIT] if messages else ""
    store.mark(item_id, WorkStatus.COMPLETED, result_summary=summary or "completed")
    return "completed"


async def _run(
    config: AppConfig,
    bindings: ModelBindings | None,
    args: argparse.Namespace,
) -> int:
    models = bindings if bindings is not None else _catalog_bindings(config, args)
    with (
        WorkStore(config.data_dir / "work.db") as store,
        ApprovalBook(config.data_dir / "approvals.db") as book,
    ):
        scheduler = Scheduler(
            store,
            max_concurrency=int(args.max_concurrency),
            deadline_seconds=(
                float(args.deadline) if args.deadline is not None else None
            ),
        )
        requeued = await scheduler.recover_interrupted()
        session = await open_host_session(
            config, models=models, interrupt_on=_GATED_TOOLS
        )
        try:

            async def execute(item: WorkItem) -> None:
                thread_id = item.thread_id or f"work-{item.id}"
                await _drive_to_outcome(
                    session,
                    store,
                    book,
                    item_id=item.id,
                    thread_id=thread_id,
                    invoke_input={"messages": [HumanMessage(content=item.goal)]},
                )

            outcomes = await scheduler.run_due(execute)
        finally:
            await session.aclose()
    for item in requeued:
        _write(f"requeued {item.id}: interrupted run recovered")
    for item in outcomes:
        _write(_describe(item))
    _write(f"run: {len(outcomes)} item(s) processed")
    return 0


async def _approve(
    config: AppConfig,
    bindings: ModelBindings | None,
    args: argparse.Namespace,
) -> int:
    with (
        WorkStore(config.data_dir / "work.db") as store,
        ApprovalBook(config.data_dir / "approvals.db") as book,
    ):
        if args.list_records:
            for record in book.pending():
                names = ",".join(
                    str(action.get("name", "?")) for action in record.actions
                )
                _write(
                    f"record {record.id} work={record.work_item_id} "
                    f"thread={record.thread_id} actions={names}"
                )
            _write(f"approve: {len(book.pending())} pending record(s)")
            return 0
        if not args.record:
            raise HostError("approve: --record or --list is required")
        record = book.get(str(args.record))
        if record is None:
            raise HostError(f"approve: unknown record: {args.record}")
        command = apply_decision(
            store,
            book,
            record_id=record.id,
            work_item_id=record.work_item_id,
            approve=not args.reject,
            message=str(args.message) if args.message else None,
        )
        if args.reject:
            _write(f"rejected {record.work_item_id}: no action executed")
            return 0
        if bindings is None:
            raise HostError("approve: model bindings are required for approval resume")
        session = await open_host_session(
            config, models=bindings, interrupt_on=_GATED_TOOLS
        )
        try:
            outcome = await _drive_to_outcome(
                session,
                store,
                book,
                item_id=record.work_item_id,
                thread_id=record.thread_id,
                invoke_input=command,
            )
        finally:
            await session.aclose()
        _write(f"approved {record.work_item_id}: {outcome}")
    return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    bindings: ModelBindings | None = None,
) -> int:
    """Run the CLI; ``bindings`` is the explicit model injection seam."""

    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        config = _app_config(args)
        if args.command == "accept":
            return _accept(config, args)
        if args.command == "due":
            return _due(config)
        if args.command == "report":
            return _report(config, args)
        if args.command == "run":
            return asyncio.run(_run(config, bindings, args))
        if args.command == "approve":
            return asyncio.run(_approve(config, bindings, args))
    except HostError as exc:
        _write(f"personal-assistant: {exc}", error=True)
        return 1
    return 0
