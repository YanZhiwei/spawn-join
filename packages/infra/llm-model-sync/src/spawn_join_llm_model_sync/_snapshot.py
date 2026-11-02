"""Deterministic snapshot construction, serialization, and atomic writes."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from spawn_join_llm_provider import (
    ConfigurationError,
    ModelCapabilitiesMetadata,
    ModelChannel,
    ModelLimits,
    ModelMetadata,
    ModelMetadataDocument,
    ModelMetadataOverride,
    ModelModalities,
    ModelPricing,
    ModelReasoning,
    ModelSource,
    ModelSourceRef,
    ModelStatus,
    parse_model_metadata_document,
)

from ._source import SyncError


def build_snapshot_mapping(
    *,
    models: dict[str, ModelMetadata],
    channels: dict[str, ModelChannel],
    sources: dict[str, ModelSource],
) -> dict[str, object]:
    """Build and validate the JSON-ready snapshot mapping."""
    mapping: dict[str, object] = {
        "schema_version": 1,
        "sources": {
            source_id: _source_to_mapping(source)
            for source_id, source in sorted(sources.items())
        },
        "models": {
            key: _model_to_mapping(model) for key, model in sorted(models.items())
        },
        "channels": {
            name: _channel_to_mapping(channel)
            for name, channel in sorted(channels.items())
        },
    }
    parse_model_metadata_document(mapping)
    return mapping


def preserve_unchanged_provenance(
    *,
    previous: ModelMetadataDocument | None,
    models: dict[str, ModelMetadata],
    channels: dict[str, ModelChannel],
    sources: dict[str, ModelSource],
) -> dict[str, ModelSource]:
    """Reuse previous fetch times when the snapshot content is unchanged."""
    if previous is None:
        return sources
    if dict(previous.models) != models or dict(previous.channels) != channels:
        return sources
    if set(previous.sources) != set(sources):
        return sources
    for source_id, source in sources.items():
        old = previous.sources[source_id]
        if (old.url, old.revision, old.license) != (
            source.url,
            source.revision,
            source.license,
        ):
            return sources
    return {
        source_id: replace(
            source,
            fetched_at=previous.sources[source_id].fetched_at,
        )
        for source_id, source in sources.items()
    }


def serialize_snapshot(mapping: dict[str, object]) -> str:
    """Serialize a validated snapshot deterministically."""
    return (
        json.dumps(
            mapping,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def write_snapshot_atomic(path: Path, text: str) -> None:
    """Write a snapshot atomically in the destination directory."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SyncError(
            f"cannot prepare snapshot directory {path.parent}: {exc}"
        ) from exc
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )
    except OSError as exc:
        raise SyncError(f"cannot create temporary snapshot for {path}: {exc}") from exc
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary, path)
    except OSError as exc:
        raise SyncError(f"cannot write snapshot {path}: {exc}") from exc
    finally:
        if temporary.exists():
            temporary.unlink(missing_ok=True)


def load_snapshot_text(path: Path) -> str | None:
    """Read an existing snapshot without treating absence as an error."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except UnicodeError as exc:
        raise SyncError(f"cannot read snapshot {path}: not valid UTF-8") from exc
    except OSError as exc:
        raise SyncError(f"cannot read snapshot {path}: {exc}") from exc


def load_previous_document(path: Path) -> ModelMetadataDocument | None:
    """Load a previous snapshot for preservation of missing referenced models."""
    text = load_snapshot_text(path)
    if text is None:
        return None
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SyncError(
            f"snapshot {path}: not valid JSON at line {exc.lineno}, "
            f"column {exc.colno}"
        ) from exc
    try:
        return parse_model_metadata_document(cast("dict[str, object]", raw))
    except ConfigurationError as exc:
        raise SyncError(f"snapshot {path}: {exc}") from exc


def _model_to_mapping(model: ModelMetadata) -> dict[str, object]:
    mapping: dict[str, object] = {
        "name": model.name,
        "type": model.type.value,
        "modalities": _modalities_to_mapping(model.modalities),
        "status": model.status.value,
    }
    capabilities = _capabilities_to_mapping(model.capabilities)
    if capabilities:
        mapping["capabilities"] = capabilities
    limits = _limits_to_mapping(model.limits)
    if limits:
        mapping["limits"] = limits
    if model.pricing is not None:
        mapping["pricing"] = _pricing_to_mapping(model.pricing)
    for name in (
        "description",
        "family",
        "license",
        "open_weights",
        "interleaved",
        "release_date",
        "knowledge",
        "last_updated",
    ):
        value = getattr(model, name)
        if value is not None:
            mapping[name] = value.isoformat() if hasattr(value, "isoformat") else value
    return mapping


def _channel_to_mapping(channel: ModelChannel) -> dict[str, object]:
    mapping: dict[str, object] = {"base_model": channel.base_model}
    if channel.source is not None:
        mapping["source"] = _source_ref_to_mapping(channel.source)
    mapping.update(_override_to_mapping(channel.override))
    return mapping


def _override_to_mapping(override: ModelMetadataOverride) -> dict[str, object]:
    mapping: dict[str, object] = {}
    if override.pricing is not None:
        mapping["pricing"] = _pricing_to_mapping(override.pricing)
    limits = _limits_to_mapping(override.limits) if override.limits else {}
    if limits:
        mapping["limits"] = limits
    capabilities = (
        _capabilities_to_mapping(override.capabilities) if override.capabilities else {}
    )
    if capabilities:
        mapping["capabilities"] = capabilities
    if override.modalities is not None:
        mapping["modalities"] = _modalities_to_mapping(override.modalities)
    if override.status is not None:
        mapping["status"] = override.status.value
    return mapping


def _modalities_to_mapping(modalities: ModelModalities) -> dict[str, object]:
    return {
        "input": [item.value for item in modalities.input],
        "output": [item.value for item in modalities.output],
    }


def _limits_to_mapping(limits: ModelLimits) -> dict[str, object]:
    mapping: dict[str, object] = {}
    for name in ("context", "input", "output"):
        value = getattr(limits, name)
        if value is not None:
            mapping[name] = value
    return mapping


def _capabilities_to_mapping(
    capabilities: ModelCapabilitiesMetadata,
) -> dict[str, object]:
    mapping: dict[str, object] = {}
    if capabilities.reasoning is not None:
        mapping["reasoning"] = _reasoning_to_mapping(capabilities.reasoning)
    for name in (
        "tools",
        "structured_output",
        "temperature",
        "top_p",
        "top_k",
        "attachment",
    ):
        value = getattr(capabilities, name)
        if value is not None:
            mapping[name] = value
    return mapping


def _reasoning_to_mapping(reasoning: ModelReasoning) -> dict[str, object]:
    mapping: dict[str, object] = {"supported": reasoning.supported}
    if reasoning.toggle is not None:
        mapping["toggle"] = reasoning.toggle
    if reasoning.efforts:
        mapping["efforts"] = list(reasoning.efforts)
    if reasoning.budget_tokens is not None:
        budget: dict[str, object] = {}
        if reasoning.budget_tokens.min_tokens is not None:
            budget["min_tokens"] = reasoning.budget_tokens.min_tokens
        if reasoning.budget_tokens.max_tokens is not None:
            budget["max_tokens"] = reasoning.budget_tokens.max_tokens
        mapping["budget_tokens"] = budget
    return mapping


def _pricing_to_mapping(pricing: ModelPricing) -> dict[str, object]:
    mapping: dict[str, object] = {
        "currency": pricing.currency,
        "rates": [
            {
                "modality": rate.modality.value,
                "direction": rate.direction.value,
                "unit": rate.unit.value,
                "amount": rate.amount,
            }
            for rate in pricing.rates
        ],
    }
    if pricing.tiers:
        mapping["tiers"] = [
            {
                "min_input_tokens": tier.min_input_tokens,
                "rates": [
                    {
                        "modality": rate.modality.value,
                        "direction": rate.direction.value,
                        "unit": rate.unit.value,
                        "amount": rate.amount,
                    }
                    for rate in tier.rates
                ],
            }
            for tier in pricing.tiers
        ]
    return mapping


def _source_ref_to_mapping(source: ModelSourceRef) -> dict[str, object]:
    return {
        "id": source.source_id,
        "provider": source.provider,
        "model": source.model,
    }


def _source_to_mapping(source: ModelSource) -> dict[str, object]:
    return {
        "url": source.url,
        "revision": source.revision,
        "fetched_at": source.fetched_at.astimezone(UTC)
        .isoformat()
        .replace("+00:00", "Z"),
        "license": source.license,
    }


def utc_now() -> datetime:
    """Return the current UTC time for provenance."""
    return datetime.now(UTC)


def status_or_active(value: str | None) -> ModelStatus:
    """Map an optional status string to the model status enum."""
    if value is None:
        return ModelStatus.ACTIVE
    try:
        return ModelStatus(value)
    except ValueError as exc:
        raise SyncError(f"unsupported model status {value!r}") from exc
