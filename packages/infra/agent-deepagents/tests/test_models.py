"""Contracts for explicit model-purpose binding."""

from __future__ import annotations

from collections.abc import Callable, Mapping

import pytest
from langchain_core.language_models import BaseChatModel
from spawn_join_agent_deepagents.errors import ModelBindingError
from spawn_join_agent_deepagents.models import (
    ModelBinding,
    ModelBindings,
    ModelPurpose,
)


class FakeCatalog:
    """A structural ModelCatalog test double that records requested names."""

    def __init__(
        self,
        model: BaseChatModel,
        error: Exception | None = None,
    ) -> None:
        self._model = model
        self._error = error
        self.calls: list[str | None] = []

    def create_chat_model(
        self,
        name: str | None = None,
        *,
        environ: Mapping[str, str] | None = None,
    ) -> BaseChatModel:
        del environ
        self.calls.append(name)
        if self._error is not None:
            raise self._error
        return self._model


def test_explicit_inheritance_reuses_one_instance(
    make_fake_model: Callable[[str], BaseChatModel],
) -> None:
    supervisor = make_fake_model("supervisor")
    bindings = ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor),
            ModelBinding(
                ModelPurpose.WORKER,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )

    resolved = bindings.resolve(require_worker=True)

    assert resolved.supervisor is supervisor
    assert resolved.worker is supervisor
    assert resolved.summarization is supervisor
    assert resolved.by_purpose[ModelPurpose.WORKER] is supervisor


def test_catalog_binding_is_created_once_for_inherited_purposes(
    make_fake_model: Callable[[str], BaseChatModel],
) -> None:
    model = make_fake_model("catalog")
    catalog = FakeCatalog(model)
    bindings = ModelBindings(
        catalog=catalog,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, catalog="coordinator"),
            ModelBinding(ModelPurpose.WORKER, inherit_from=ModelPurpose.SUPERVISOR),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )

    resolved = bindings.resolve(require_worker=True)

    assert resolved.supervisor is model
    assert resolved.worker is model
    assert catalog.calls == ["coordinator"]


def test_catalog_failure_is_wrapped_without_exposing_cause_text(
    make_fake_model: Callable[[str], BaseChatModel],
) -> None:
    cause = ValueError("provider detail that must stay in the cause")
    catalog = FakeCatalog(make_fake_model("unused"), error=cause)
    bindings = ModelBindings(
        catalog=catalog,
        bindings=(ModelBinding(ModelPurpose.SUPERVISOR, catalog="broken"),),
        require_summarization=False,
    )

    with pytest.raises(ModelBindingError) as caught:
        bindings.resolve()

    assert caught.value.__cause__ is cause
    assert "provider detail" not in str(caught.value)


def test_missing_summarization_is_rejected(
    make_fake_model: Callable[[str], BaseChatModel],
) -> None:
    bindings = ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(
                ModelPurpose.SUPERVISOR,
                model=make_fake_model("supervisor"),
            ),
        ),
    )

    with pytest.raises(ModelBindingError, match="summarization"):
        bindings.resolve()


def test_missing_worker_is_rejected_only_when_required(
    make_fake_model: Callable[[str], BaseChatModel],
) -> None:
    supervisor = make_fake_model("supervisor")
    bindings = ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )

    with pytest.raises(ModelBindingError, match="worker"):
        bindings.resolve(require_worker=True)

    resolved = bindings.resolve(require_worker=False)
    assert resolved.worker is None


def test_present_optional_worker_is_still_resolved(
    make_fake_model: Callable[[str], BaseChatModel],
) -> None:
    supervisor = make_fake_model("supervisor")
    worker = make_fake_model("worker")
    bindings = ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(ModelPurpose.SUPERVISOR, model=supervisor),
            ModelBinding(ModelPurpose.WORKER, model=worker),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.SUPERVISOR,
            ),
        ),
    )

    resolved = bindings.resolve(require_worker=False)
    assert resolved.worker is worker


def test_inheritance_cycle_is_rejected(
    make_fake_model: Callable[[str], BaseChatModel],
) -> None:
    bindings = ModelBindings(
        catalog=None,
        bindings=(
            ModelBinding(
                ModelPurpose.SUPERVISOR,
                model=make_fake_model("supervisor"),
            ),
            ModelBinding(
                ModelPurpose.WORKER,
                inherit_from=ModelPurpose.SUMMARIZATION,
            ),
            ModelBinding(
                ModelPurpose.SUMMARIZATION,
                inherit_from=ModelPurpose.WORKER,
            ),
        ),
    )

    with pytest.raises(ModelBindingError, match="cycle"):
        bindings.resolve(require_worker=True)


def test_duplicate_purpose_is_rejected(
    make_fake_model: Callable[[str], BaseChatModel],
) -> None:
    model = make_fake_model("supervisor")
    with pytest.raises(ModelBindingError, match="duplicate"):
        ModelBindings(
            catalog=None,
            bindings=(
                ModelBinding(ModelPurpose.SUPERVISOR, model=model),
                ModelBinding(ModelPurpose.SUPERVISOR, model=model),
            ),
        )


def test_exactly_one_binding_source_is_required(
    make_fake_model: Callable[[str], BaseChatModel],
) -> None:
    with pytest.raises(ModelBindingError, match="exactly one"):
        ModelBinding(ModelPurpose.SUPERVISOR)

    with pytest.raises(ModelBindingError, match="exactly one"):
        ModelBinding(
            ModelPurpose.SUPERVISOR,
            model=make_fake_model("supervisor"),
            catalog="also-a-catalog",
        )


def test_supervisor_cannot_inherit() -> None:
    with pytest.raises(ModelBindingError, match="directly bound"):
        ModelBinding(
            ModelPurpose.SUPERVISOR,
            inherit_from=ModelPurpose.WORKER,
        )


def test_self_inheritance_is_rejected() -> None:
    with pytest.raises(ModelBindingError, match="itself"):
        ModelBinding(
            ModelPurpose.WORKER,
            inherit_from=ModelPurpose.WORKER,
        )


def test_blank_catalog_name_is_rejected() -> None:
    with pytest.raises(ModelBindingError, match="blank"):
        ModelBinding(ModelPurpose.SUPERVISOR, catalog="   ")


def test_catalog_is_required_for_catalog_binding() -> None:
    with pytest.raises(ModelBindingError, match="requires a configured"):
        ModelBindings(
            catalog=None,
            bindings=(ModelBinding(ModelPurpose.SUPERVISOR, catalog="coordinator"),),
            require_summarization=False,
        )
