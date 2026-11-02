"""Orchestrate one manual model metadata sync."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

from spawn_join_llm_provider import (
    ConfigurationError,
    ModelChannel,
    ModelMetadata,
    ModelMetadataDocument,
    ModelSource,
)
from spawn_join_llm_provider_langchain import ModelCatalog, ModelSummary

from ._cache import (
    default_cache_dir,
    write_raw_payload,
    write_report,
    write_state,
)
from ._merge import build_source_request, merge_source
from ._snapshot import (
    build_snapshot_mapping,
    load_previous_document,
    load_snapshot_text,
    preserve_unchanged_provenance,
    serialize_snapshot,
    utc_now,
    write_snapshot_atomic,
)
from ._source import (
    MetadataSource,
    SourceCatalog,
    SourceConfig,
    SyncContext,
    SyncError,
    SyncResult,
)
from ._url import redact_url, validate_source_url


def run_sync(
    *,
    source: MetadataSource,
    model_file: Path,
    output: Path,
    config: SourceConfig,
    context: SyncContext,
    apply: bool = False,
    check: bool = False,
) -> SyncResult:
    """Fetch, merge, validate, diff, and optionally write one snapshot."""
    if apply and check:
        raise ConfigurationError("--apply and --check are mutually exclusive")

    catalog = ModelCatalog.from_file(model_file, env_file=None)
    summaries = catalog.models
    request = build_source_request(summaries, source.info.id)
    if not request.refs:
        raise SyncError(
            "model.yaml has no metadata_ref entries; nothing to synchronize"
        )

    previous = load_previous_document(output) if output.exists() else None
    effective_url = config.url or context.url or source.info.default_url
    validate_source_url(effective_url)

    fetch_context = SyncContext(
        cache_dir=context.cache_dir,
        timeout_seconds=config.timeout_seconds,
        environ=context.environ,
        url=config.url or context.url,
    )
    payload = source.fetch(fetch_context)
    try:
        source_catalog = source.translate(payload, request)
    except ConfigurationError as exc:
        raise SyncError(f"source translation failed: {exc}") from exc
    _require_source_size(source_catalog, source=source, config=config)

    merged = merge_source(
        source_id=source.info.id,
        catalog=source_catalog,
        summaries=summaries,
    )
    _require_matched_models(merged.matched, source_id=source.info.id)

    models: dict[str, ModelMetadata] = dict(merged.models)
    channels = dict(merged.channels)
    warnings = list(merged.warnings)
    if previous is not None:
        _guard_channel_shrink(
            previous=previous,
            summaries=summaries,
            source_id=source.info.id,
            candidate_channels=channels,
        )
        _preserve_missing_models(
            previous=previous,
            missing=merged.unmatched,
            models=models,
            warnings=warnings,
        )
        _preserve_previous_channels(
            previous=previous,
            summaries=summaries,
            source_id=source.info.id,
            models=models,
            channels=channels,
            warnings=warnings,
        )

    revision = f"sha256:{hashlib.sha256(payload).hexdigest()}"
    source_record = ModelSource(
        url=redact_url(effective_url),
        revision=revision,
        fetched_at=utc_now(),
        license=source.info.license,
    )
    sources: dict[str, ModelSource] = {source.info.id: source_record}
    if previous is not None:
        _retain_source_provenance(
            previous=previous,
            current_source_id=source.info.id,
            channels=channels,
            sources=sources,
        )
    sources = preserve_unchanged_provenance(
        previous=previous,
        models=models,
        channels=channels,
        sources=sources,
    )

    try:
        mapping = build_snapshot_mapping(
            models=models,
            channels=channels,
            sources=sources,
        )
    except ConfigurationError as exc:
        raise SyncError(f"snapshot validation failed: {exc}") from exc
    text = serialize_snapshot(mapping)
    existing = load_snapshot_text(output)
    changed = existing != text
    written = False
    if apply and changed:
        write_snapshot_atomic(output, text)
        written = True

    result = SyncResult(
        source_id=source.info.id,
        changed=changed,
        written=written,
        output_path=output,
        matched=merged.matched,
        unmatched=merged.unmatched,
        ignored_models=merged.ignored_models,
        ignored_model_ids=merged.ignored_model_ids,
        warnings=tuple(warnings),
        exit_code=0 if (written or (apply and not changed)) else (2 if changed else 0),
    )
    result = _persist_observability(
        context=context,
        payload=payload,
        revision=revision,
        result=result,
        write_state_file=apply,
    )
    if check:
        result = replace(
            result,
            written=False,
            exit_code=2 if result.changed else 0,
        )
    return result


def _require_source_size(
    source_catalog: SourceCatalog,
    *,
    source: MetadataSource,
    config: SourceConfig,
) -> None:
    minimum = config.min_models or source.info.min_models
    if source_catalog.total_models < minimum:
        raise SyncError(
            f"source returned {source_catalog.total_models} models, "
            f"below the safety minimum {minimum}"
        )


def _require_matched_models(matched: tuple[str, ...], *, source_id: str) -> None:
    if not matched:
        raise SyncError(f"source {source_id} returned none of the referenced models")


def _referenced_summaries(
    summaries: tuple[ModelSummary, ...],
) -> dict[str, ModelSummary]:
    return {
        summary.name: summary
        for summary in summaries
        if summary.metadata_ref is not None
    }


def _previous_source_channels(
    *,
    previous: ModelMetadataDocument,
    summaries: tuple[ModelSummary, ...],
    source_id: str,
) -> dict[str, ModelChannel]:
    """Return prior channels still owned by the source and model.yaml."""
    summary_map = _referenced_summaries(summaries)
    result: dict[str, ModelChannel] = {}
    for name, channel in previous.channels.items():
        summary = summary_map.get(name)
        if summary is None or summary.metadata_ref != channel.base_model:
            continue
        if channel.source is None or channel.source.source_id != source_id:
            continue
        if source_id not in summary.metadata_source:
            continue
        result[name] = channel
    return result


def _guard_channel_shrink(
    *,
    previous: ModelMetadataDocument,
    summaries: tuple[ModelSummary, ...],
    source_id: str,
    candidate_channels: dict[str, ModelChannel],
) -> None:
    """Reject a source response that removes too many referenced channels."""
    expected = _previous_source_channels(
        previous=previous,
        summaries=summaries,
        source_id=source_id,
    )
    if not expected:
        return
    candidate_count = len(candidate_channels)
    if candidate_count == 0 or candidate_count * 2 < len(expected):
        raise SyncError(
            f"source {source_id} maps only {candidate_count} of "
            f"{len(expected)} previously referenced channel(s); "
            "refusing to write an abnormal channel shrink"
        )


def _preserve_missing_models(
    *,
    previous: ModelMetadataDocument,
    missing: tuple[str, ...],
    models: dict[str, ModelMetadata],
    warnings: list[str],
) -> None:
    """Keep previous shared facts when the current source omits a reference."""
    for ref in missing:
        previous_model = previous.models.get(ref)
        if previous_model is None:
            continue
        models[ref] = previous_model
        warnings.append(
            f"{ref}: missing from the source; preserved the previous snapshot entry"
        )


def _preserve_previous_channels(
    *,
    previous: ModelMetadataDocument,
    summaries: tuple[ModelSummary, ...],
    source_id: str,
    models: dict[str, ModelMetadata],
    channels: dict[str, ModelChannel],
    warnings: list[str],
) -> None:
    """Keep still-referenced channels that another source, or a partial response, owns."""
    summary_map = _referenced_summaries(summaries)
    for name, channel in previous.channels.items():
        summary = summary_map.get(name)
        if summary is None or summary.metadata_ref != channel.base_model:
            continue
        if name in channels:
            continue
        owner = None if channel.source is None else channel.source.source_id
        if owner is not None and owner not in summary.metadata_source:
            continue
        channels[name] = channel
        if channel.base_model not in models:
            previous_model = previous.models.get(channel.base_model)
            if previous_model is not None:
                models[channel.base_model] = previous_model
            else:
                warnings.append(
                    f"{name}: previous channel has no previous shared model; "
                    "the snapshot may fail validation"
                )
        if owner == source_id:
            warnings.append(
                f"{name}: source {source_id} no longer maps this channel; "
                "preserved the previous entry"
            )
        elif owner is not None:
            warnings.append(
                f"{name}: channel from source {owner} preserved because "
                f"source {source_id} does not map it"
            )


def _retain_source_provenance(
    *,
    previous: ModelMetadataDocument,
    current_source_id: str,
    channels: dict[str, ModelChannel],
    sources: dict[str, ModelSource],
) -> None:
    """Keep provenance for retained channels owned by other sources."""
    for channel in channels.values():
        if channel.source is None:
            continue
        owner = channel.source.source_id
        if owner == current_source_id:
            continue
        previous_source = previous.sources.get(owner)
        if previous_source is not None:
            sources.setdefault(owner, previous_source)


def _persist_observability(
    *,
    context: SyncContext,
    payload: bytes,
    revision: str,
    result: SyncResult,
    write_state_file: bool,
) -> SyncResult:
    """Persist cache, report and state; post-commit failures become warnings."""
    cache_dir = context.cache_dir or default_cache_dir()
    report_path = result.report_path
    try:
        write_raw_payload(cache_dir, result.source_id, payload)
        report_path = write_report(cache_dir, result)
        if write_state_file:
            write_state(cache_dir, result, revision)
    except OSError as exc:
        message = f"cannot write sync cache under {cache_dir}: {exc}"
        if result.written:
            return replace(
                result,
                warnings=result.warnings + (f"post-commit {message}",),
                report_path=report_path,
            )
        raise SyncError(message) from exc
    return replace(result, report_path=report_path)
