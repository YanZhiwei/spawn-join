"""Load optional metadata snapshots and resolve per-entry metadata."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import cast

from spawn_join_llm_provider import (
    ConfigurationError,
    ModelMetadata,
    ModelMetadataDocument,
    apply_metadata_override,
    parse_model_metadata_document,
)

from ._schema import CatalogEntry


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigurationError(f"metadata: duplicate key {key!r}")
        result[key] = value
    return result


def load_metadata_document(path: str | Path) -> ModelMetadataDocument:
    """Load and validate an explicit JSON metadata snapshot."""
    metadata_path = Path(path)
    try:
        text = metadata_path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise ConfigurationError(
            f"metadata file {metadata_path}: not valid UTF-8"
        ) from exc
    except OSError as exc:
        raise ConfigurationError(
            f"metadata file {metadata_path}: cannot be read"
        ) from exc
    try:
        raw = json.loads(text, object_pairs_hook=_unique_object)
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"metadata file {metadata_path}: not valid JSON at line "
            f"{exc.lineno}, column {exc.colno}"
        ) from exc
    except ConfigurationError as exc:
        raise ConfigurationError(f"metadata file {metadata_path}: {exc}") from exc
    try:
        return parse_model_metadata_document(cast("Mapping[str, object]", raw))
    except ConfigurationError as exc:
        raise ConfigurationError(f"metadata file {metadata_path}: {exc}") from exc


def resolve_metadata(
    entry: CatalogEntry,
    document: ModelMetadataDocument | None,
    metadata_file: Path | None = None,
) -> ModelMetadata | None:
    """Resolve shared, channel, and inline metadata for one entry."""
    if document is None or entry.metadata_ref is None:
        return None
    shared = document.models.get(entry.metadata_ref)
    if shared is None:
        return None
    channel = document.channels.get(entry.name)
    if channel is not None:
        if channel.base_model != entry.metadata_ref:
            location = (
                f"metadata file {metadata_file}: " if metadata_file is not None else ""
            )
            raise ConfigurationError(
                f"{location}models.{entry.name}.metadata_ref: metadata channel "
                f"base_model {channel.base_model!r} does not match "
                f"{entry.metadata_ref!r}"
            )
        shared = apply_metadata_override(shared, channel.override)
    if entry.metadata is not None:
        shared = apply_metadata_override(shared, entry.metadata)
    return shared
