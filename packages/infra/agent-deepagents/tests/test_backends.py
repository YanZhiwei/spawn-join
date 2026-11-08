"""Backend classification and permission report contracts."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from deepagents.backends import FilesystemBackend, StateBackend
from deepagents.middleware.filesystem import FilesystemPermission
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from spawn_join_agent_deepagents.backends import backend_kind, permission_report
from spawn_join_agent_deepagents.models import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
)
from spawn_join_agent_deepagents.supervisor import SupervisorSpec, build_supervisor


def test_backend_kind_labels_known_and_custom_backends(
    tmp_path: Path,
) -> None:
    assert backend_kind(None) == "default_state"
    assert backend_kind(StateBackend()) == "state"
    assert backend_kind(FilesystemBackend(root_dir=tmp_path)) == "filesystem"
    assert backend_kind(object()) == "custom"  # type: ignore[arg-type]


def test_permission_report_counts_effects() -> None:
    report = permission_report(
        (
            FilesystemPermission(operations=["read"], paths=["/a"]),
            FilesystemPermission(operations=["write"], paths=["/b"], mode="deny"),
            FilesystemPermission(operations=["write"], paths=["/c"], mode="interrupt"),
        )
    )

    assert report.allow == 1
    assert report.deny == 1
    assert report.interrupt == 1


def test_assembly_reports_backend_and_permissions(
    monkeypatch: pytest.MonkeyPatch,
    make_sequence_model: Callable[[list[AIMessage]], BaseChatModel],
) -> None:
    def fake_create(**kwargs: Any) -> object:
        del kwargs
        return object()

    monkeypatch.setattr(
        "spawn_join_agent_deepagents.supervisor._create_deep_agent",
        fake_create,
    )
    supervisor = make_sequence_model([AIMessage(content="unused")])
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

    assembly = build_supervisor(
        SupervisorSpec(
            models=models,
            control_default_subagent=False,
            backend=StateBackend(),
            permissions=(FilesystemPermission(operations=["read"], paths=["/a"]),),
        )
    )

    assert assembly.report.resources.backend_kind == "state"
    assert assembly.report.resources.permissions.allow == 1
