"""Explicit model-purpose binding and resolution.

The package owns the mapping from a product purpose (supervisor, worker,
summarization) to a LangChain model. Configured models are created through the
public ``ModelCatalog`` contract; the package never reads model files or
credentials itself.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Protocol

from langchain_core.language_models import BaseChatModel

from .errors import ModelBindingError


class ModelCatalogLike(Protocol):
    """Structural contract implemented by ``ModelCatalog``.

    Only the public creation method is needed; tests can provide a small fake
    without importing the concrete catalog class.
    """

    def create_chat_model(
        self,
        name: str | None = None,
        *,
        environ: Mapping[str, str] | None = None,
    ) -> BaseChatModel: ...


class ModelPurpose(StrEnum):
    """Stable product purposes used by the supervisor assembly."""

    SUPERVISOR = "supervisor"
    WORKER = "worker"
    SUMMARIZATION = "summarization"


@dataclass(frozen=True, slots=True)
class ModelBinding:
    """One purpose bound directly, through a catalog, or by explicit inheritance."""

    purpose: ModelPurpose
    model: BaseChatModel | None = None
    catalog: str | None = None
    inherit_from: ModelPurpose | None = None

    def __post_init__(self) -> None:
        sources = (
            self.model is not None,
            self.catalog is not None,
            self.inherit_from is not None,
        )
        if sum(sources) != 1:
            raise ModelBindingError(
                f"models.{self.purpose}: exactly one of model, catalog, or "
                "inherit_from is required"
            )
        if self.catalog is not None and not self.catalog.strip():
            raise ModelBindingError(
                f"models.{self.purpose}: catalog entry name must not be blank"
            )
        if self.purpose == ModelPurpose.SUPERVISOR and self.inherit_from is not None:
            raise ModelBindingError(
                "models.supervisor: the supervisor model must be directly bound; "
                "inherit_from is not allowed"
            )
        if self.inherit_from == self.purpose:
            raise ModelBindingError(
                f"models.{self.purpose}: a purpose cannot inherit from itself"
            )


@dataclass(frozen=True, slots=True)
class ModelBindings:
    """A validated collection of purpose bindings and an optional catalog."""

    catalog: ModelCatalogLike | None
    bindings: Sequence[ModelBinding]
    require_summarization: bool = True
    require_worker: bool | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "bindings", tuple(self.bindings))
        by_purpose: dict[ModelPurpose, ModelBinding] = {}
        for binding in self.bindings:
            if binding.purpose in by_purpose:
                raise ModelBindingError(
                    f"models.{binding.purpose}: duplicate purpose binding"
                )
            by_purpose[binding.purpose] = binding
        if ModelPurpose.SUPERVISOR not in by_purpose:
            raise ModelBindingError("models.supervisor: a direct binding is required")
        if self.catalog is None and any(
            binding.catalog is not None for binding in self.bindings
        ):
            raise ModelBindingError(
                "models: a catalog binding requires a configured ModelCatalog"
            )

    def resolve(
        self,
        *,
        require_worker: bool | None = None,
    ) -> ResolvedModelBindings:
        """Resolve every present purpose and enforce the required-purpose rules."""

        by_purpose = {binding.purpose: binding for binding in self.bindings}
        self._validate_required(by_purpose, require_worker)
        cache: dict[ModelPurpose, BaseChatModel] = {}
        supervisor = self._resolve_purpose(
            by_purpose, ModelPurpose.SUPERVISOR, (), cache
        )
        worker = (
            self._resolve_purpose(by_purpose, ModelPurpose.WORKER, (), cache)
            if ModelPurpose.WORKER in by_purpose
            else None
        )
        summarization = (
            self._resolve_purpose(by_purpose, ModelPurpose.SUMMARIZATION, (), cache)
            if ModelPurpose.SUMMARIZATION in by_purpose
            else None
        )
        return ResolvedModelBindings(
            supervisor=supervisor,
            worker=worker,
            summarization=summarization,
        )

    def _validate_required(
        self,
        by_purpose: Mapping[ModelPurpose, ModelBinding],
        require_worker: bool | None,
    ) -> None:
        effective_worker = (
            self.require_worker if require_worker is None else require_worker
        )
        required = {ModelPurpose.SUPERVISOR}
        if self.require_summarization:
            required.add(ModelPurpose.SUMMARIZATION)
        if effective_worker:
            required.add(ModelPurpose.WORKER)

        missing = sorted(str(purpose) for purpose in required - by_purpose.keys())
        if missing:
            raise ModelBindingError(
                "models: missing required purpose binding(s): " + ", ".join(missing)
            )

    def _resolve_purpose(
        self,
        by_purpose: Mapping[ModelPurpose, ModelBinding],
        purpose: ModelPurpose,
        seen: tuple[ModelPurpose, ...],
        cache: dict[ModelPurpose, BaseChatModel],
    ) -> BaseChatModel:
        cached = cache.get(purpose)
        if cached is not None:
            return cached
        if purpose in seen:
            path = " -> ".join(str(item) for item in (*seen, purpose))
            raise ModelBindingError(
                f"models.{purpose}: explicit inheritance cycle: {path}"
            )
        binding = by_purpose.get(purpose)
        if binding is None:
            raise ModelBindingError(
                f"models.{purpose}: no binding is available for inheritance"
            )
        if binding.inherit_from is not None:
            value = self._resolve_purpose(
                by_purpose,
                binding.inherit_from,
                (*seen, purpose),
                cache,
            )
        elif binding.model is not None:
            value = binding.model
        else:
            value = self._create_catalog_model(purpose, binding)
        cache[purpose] = value
        return value

    def _create_catalog_model(
        self,
        purpose: ModelPurpose,
        binding: ModelBinding,
    ) -> BaseChatModel:
        catalog = self.catalog
        name = binding.catalog
        if catalog is None or name is None:
            raise ModelBindingError(f"models.{purpose}: catalog binding is incomplete")
        try:
            return catalog.create_chat_model(name)
        except Exception as exc:
            raise ModelBindingError(
                f"models.{purpose}: failed to create catalog entry {name!r}"
            ) from exc


@dataclass(frozen=True, slots=True)
class ResolvedModelBindings:
    """Resolved LangChain models for the configured purposes."""

    supervisor: BaseChatModel
    worker: BaseChatModel | None
    summarization: BaseChatModel | None

    @property
    def by_purpose(self) -> Mapping[ModelPurpose, BaseChatModel]:
        """Return a safe read-only view of the resolved purposes."""

        values: dict[ModelPurpose, BaseChatModel] = {
            ModelPurpose.SUPERVISOR: self.supervisor
        }
        if self.worker is not None:
            values[ModelPurpose.WORKER] = self.worker
        if self.summarization is not None:
            values[ModelPurpose.SUMMARIZATION] = self.summarization
        return MappingProxyType(values)
