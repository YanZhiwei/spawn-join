"""Merge source catalogs with model.yaml entries."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from spawn_join_llm_provider import (
    ConfigurationError,
    ModelChannel,
    ModelMetadata,
    ModelSourceRef,
)
from spawn_join_llm_provider_langchain import ModelSummary

from ._source import SourceCatalog, SourceHostRef, SourceRequest, SyncError


@dataclass(frozen=True, slots=True, kw_only=True)
class MergedMetadata:
    """The requested models and channel overrides resolved from one source."""

    models: dict[str, ModelMetadata]
    channels: dict[str, ModelChannel]
    matched: tuple[str, ...]
    unmatched: tuple[str, ...]
    ignored_models: int
    ignored_model_ids: tuple[str, ...]
    warnings: tuple[str, ...]


def build_source_request(
    summaries: Iterable[ModelSummary],
    source_id: str,
) -> SourceRequest:
    """Collect unique refs and host coordinates from catalog summaries."""
    refs: list[str] = []
    hosts: list[SourceHostRef] = []
    for summary in summaries:
        ref = summary.metadata_ref
        if ref is None:
            continue
        if ref not in refs:
            refs.append(ref)
        source_ref = summary.metadata_source.get(source_id)
        if source_ref is None:
            continue
        host = SourceHostRef(
            provider=source_ref.provider,
            model=source_ref.model,
        )
        if host not in hosts:
            hosts.append(host)
    return SourceRequest(refs=tuple(refs), hosts=tuple(hosts))


def merge_source(
    *,
    source_id: str,
    catalog: SourceCatalog,
    summaries: Iterable[ModelSummary],
) -> MergedMetadata:
    """Resolve shared models and channel overrides for one source."""
    summary_list = tuple(summaries)
    request = build_source_request(summary_list, source_id)
    models: dict[str, ModelMetadata] = {}
    channels: dict[str, ModelChannel] = {}
    matched: list[str] = []
    unmatched: list[str] = []
    warnings: list[str] = list(catalog.warnings)

    for ref in request.refs:
        model = catalog.models.get(ref)
        if model is None:
            unmatched.append(ref)
            continue
        models[ref] = model
        matched.append(ref)

    for summary in summary_list:
        ref = summary.metadata_ref
        if ref is None:
            continue
        source_ref = summary.metadata_source.get(source_id)
        if source_ref is None:
            continue
        host = catalog.hosts.get(source_ref.provider, {}).get(source_ref.model)
        if host is None:
            warnings.append(
                f"{summary.name}: source {source_id} host "
                f"{source_ref.provider}/{source_ref.model} not found"
            )
            continue
        if host.canonical_model != ref:
            raise SyncError(
                f"{summary.name}: source {source_id} host "
                f"{source_ref.provider}/{source_ref.model} maps to "
                f"{host.canonical_model!r}, expected {ref!r}"
            )
        channels[summary.name] = ModelChannel(
            base_model=ref,
            source=source_ref,
            override=host.override,
        )

    ignored_ids = catalog.unreferenced_models
    ignored = (
        len(ignored_ids)
        if ignored_ids
        else max(catalog.total_models - len(catalog.models), 0)
    )
    return MergedMetadata(
        models=models,
        channels=channels,
        matched=tuple(matched),
        unmatched=tuple(unmatched),
        ignored_models=ignored,
        ignored_model_ids=ignored_ids,
        warnings=tuple(warnings),
    )


def existing_source_ref(
    summary: ModelSummary,
    source_id: str,
) -> ModelSourceRef | None:
    """Return one summary's explicit source reference when present."""
    return summary.metadata_source.get(source_id)


def validate_channel_source(
    channel: ModelChannel,
    summary: ModelSummary,
) -> None:
    """Ensure a channel's base model matches the summary reference."""
    if summary.metadata_ref is None:
        raise ConfigurationError(
            f"models.{summary.name}: channel metadata requires metadata_ref"
        )
    if channel.base_model != summary.metadata_ref:
        raise ConfigurationError(
            f"models.{summary.name}: channel base_model {channel.base_model!r} "
            f"does not match {summary.metadata_ref!r}"
        )
