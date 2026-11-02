"""Orchestrate one manual model metadata sync."""

from __future__ import annotations

import hashlib
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
    serialize_snapshot,
    utc_now,
    write_snapshot_atomic,
)
from ._source import (
    MetadataSource,
    SourceConfig,
    SyncContext,
    SyncError,
    SyncResult,
)


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
    minimum = config.min_models or source.info.min_models
    if source_catalog.total_models < minimum:
        raise SyncError(
            f"source returned {source_catalog.total_models} models, "
            f"below the safety minimum {minimum}"
        )

    merged = merge_source(
        source_id=source.info.id,
        catalog=source_catalog,
        summaries=summaries,
    )
    if not merged.matched:
        raise SyncError("none of the referenced models were found in the source")

    models: dict[str, ModelMetadata] = dict(merged.models)
    channels = dict(merged.channels)
    warnings = list(merged.warnings)
    previous = load_previous_document(output) if output.exists() else None
    if previous is not None:
        _preserve_missing(
            previous=previous,
            summaries=summaries,
            missing=merged.unmatched,
            models=models,
            channels=channels,
            warnings=warnings,
        )

    revision = f"sha256:{hashlib.sha256(payload).hexdigest()}"
    source_record = ModelSource(
        url=config.url or source.info.default_url,
        revision=revision,
        fetched_at=utc_now(),
        license=source.info.license,
    )
    try:
        mapping = build_snapshot_mapping(
            models=models,
            channels=channels,
            sources={source.info.id: source_record},
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
        result = SyncResult(
            source_id=result.source_id,
            changed=result.changed,
            written=False,
            output_path=result.output_path,
            matched=result.matched,
            unmatched=result.unmatched,
            ignored_models=result.ignored_models,
            warnings=result.warnings,
            exit_code=2 if result.changed else 0,
            report_path=result.report_path,
        )
    return result


def _preserve_missing(
    *,
    previous: ModelMetadataDocument,
    summaries: tuple[ModelSummary, ...],
    missing: tuple[str, ...],
    models: dict[str, ModelMetadata],
    channels: dict[str, ModelChannel],
    warnings: list[str],
) -> None:
    referenced = {
        summary.name: summary.metadata_ref
        for summary in summaries
        if summary.metadata_ref is not None
    }
    for ref in missing:
        previous_model = previous.models.get(ref)
        if previous_model is None:
            continue
        models[ref] = previous_model
        for name, channel in previous.channels.items():
            if channel.base_model == ref and referenced.get(name) == ref:
                channels[name] = channel
        warnings.append(
            f"{ref}: missing from the source; preserved the previous snapshot entry"
        )


def _persist_observability(
    *,
    context: SyncContext,
    payload: bytes,
    revision: str,
    result: SyncResult,
    write_state_file: bool,
) -> SyncResult:
    cache_dir = context.cache_dir or default_cache_dir()
    try:
        write_raw_payload(cache_dir, result.source_id, payload)
        report_path = write_report(cache_dir, result)
        if write_state_file:
            write_state(cache_dir, result, revision)
    except OSError as exc:
        raise SyncError(f"cannot write sync cache under {cache_dir}: {exc}") from exc
    return SyncResult(
        source_id=result.source_id,
        changed=result.changed,
        written=result.written,
        output_path=result.output_path,
        matched=result.matched,
        unmatched=result.unmatched,
        ignored_models=result.ignored_models,
        warnings=result.warnings,
        exit_code=result.exit_code,
        report_path=report_path,
    )
