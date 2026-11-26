"""Backend classification and permission report contracts."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from deepagents.backends import (CompositeBackend, ContextHubBackend,
                                 FilesystemBackend, LangSmithSandbox,
                                 LocalShellBackend, StateBackend, StoreBackend)
from deepagents.backends.sandbox import BaseSandbox
from deepagents.middleware.filesystem import FilesystemPermission
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage

from spawn_join_agent_deepagents.backends import (backend_kind,
                                                  permission_report)
from spawn_join_agent_deepagents.models import (ModelBinding, ModelBindings,
                                                ModelPurpose)
from spawn_join_agent_deepagents.supervisor import (SupervisorSpec,
                                                    build_supervisor)


class _GenericSandbox(BaseSandbox):
    @property
    def id(self) -> str:
        return "generic"

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        return None

    def upload_files(self, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        return None

    def download_files(self, *args: Any, **kwargs: Any) -> Any:
        del args, kwargs
        return None


def test_backend_kind_labels_known_and_custom_backends(
    tmp_path: Path,
) -> None:
    assert backend_kind(None) == "default_state"
    assert backend_kind(StateBackend()) == "state"
    assert backend_kind(FilesystemBackend(root_dir=tmp_path)) == "filesystem"
    assert backend_kind(LocalShellBackend()) == "local_shell"
    assert backend_kind(LangSmithSandbox.__new__(LangSmithSandbox)) == "sandbox"
    assert backend_kind(_GenericSandbox()) == "sandbox"
    assert backend_kind(StoreBackend.__new__(StoreBackend)) == "store"
    assert (
        backend_kind(CompositeBackend(default=StateBackend(), routes={})) == "composite"
    )
    assert backend_kind(ContextHubBackend("hub")) == "context_hub"
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
    assert report.other == 0


def test_permission_report_counts_unknown_modes() -> None:
    report = permission_report(
        (SimpleNamespace(mode="future-mode"),)  # type: ignore[arg-type]
    )

    assert report.other == 1


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
