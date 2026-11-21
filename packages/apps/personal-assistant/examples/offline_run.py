"""Run the personal assistant CLI end to end without any model service.

From the repository root:

    uv run --locked --directory packages/apps/personal-assistant \
        python examples/offline_run.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fake_model import FakeChatModel
from langchain_core.messages import AIMessage
from spawn_join_agent_deepagents import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
)
from spawn_join_personal_assistant import ApprovalBook, main

_TAKE_NOTES = AIMessage(
    content="",
    tool_calls=[
        {
            "name": "write_file",
            "args": {"file_path": "/notes.txt", "content": "note"},
            "id": "call-notes",
            "type": "tool_call",
        }
    ],
)
_DONE = AIMessage(content="笔记已写入工作区。")


def _bindings() -> ModelBindings:
    model = FakeChatModel(responses=[_TAKE_NOTES, _DONE])
    return ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, model=model),
            ModelBinding(ModelPurpose.WORKER, model=model),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )


def _argv(root: Path, *args: str) -> list[str]:
    return ["--root", str(root), *args]


def main_example() -> int:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        (root / "model.yaml").write_text(
            "schema_version: 1\n", encoding="utf-8"
        )
        bindings = _bindings()

        main(_argv(root, "accept", "写一条笔记并保存", "--key", "notes-1"))
        code = main(_argv(root, "run"), bindings=bindings)
        # The write is approval-gated, so the run pauses; approve it.
        with ApprovalBook(root / "data" / "approvals.db") as book:
            record_id = book.pending()[0].id
        code = main(
            _argv(root, "approve", "--record", record_id),
            bindings=bindings,
        )
        main(_argv(root, "report"))
        notes = root / "workspace" / "notes.txt"
        print("notes.txt exists:", notes.is_file())
        return code


if __name__ == "__main__":
    raise SystemExit(main_example())
