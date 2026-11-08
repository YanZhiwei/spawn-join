"""Offline P1 example: rubric assembly, backend report, and HITL helpers."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from deepagents.backends import FilesystemBackend
from deepagents.middleware.filesystem import FilesystemPermission
from fake_model import FakeChatModel
from langchain_core.messages import AIMessage
from spawn_join_agent_deepagents import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
    RubricConfiguration,
    SupervisorSpec,
    approve_decision,
    build_supervisor,
    reject_decision,
    resume_batched,
)


def main() -> None:
    supervisor = FakeChatModel(responses=[AIMessage(content="done")])
    grader = FakeChatModel(responses=[AIMessage(content="{}")])
    models = ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )

    with TemporaryDirectory() as raw_root:
        assembly = build_supervisor(
            SupervisorSpec(
                models=models,
                control_default_subagent=False,
                backend=FilesystemBackend(root_dir=Path(raw_root)),
                permissions=(
                    FilesystemPermission(operations=["read"], paths=["/docs"]),
                    FilesystemPermission(
                        operations=["write"],
                        paths=["/secrets"],
                        mode="deny",
                    ),
                ),
                rubric=RubricConfiguration(model=grader, max_iterations=2),
                allow_experimental_rubric=True,
                name="p1-example",
            )
        )

    print("Rubric:", assembly.report.rubric)
    print("Resources:", assembly.report.resources)
    print("Approve:", approve_decision())
    print("Reject:", reject_decision("keep the original"))
    print("Batched resume:", resume_batched([approve_decision()]).resume)


if __name__ == "__main__":
    main()
