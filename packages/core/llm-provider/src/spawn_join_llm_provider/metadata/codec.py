"""JSON decoding shared by metadata snapshots and source adapters."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import cast

from ..errors import ConfigurationError
from .parsing import parse_model_metadata_document
from .types import ModelMetadataDocument


class DuplicateKeyError(ValueError):
    """A JSON object contains the same key more than once."""


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build a JSON object while rejecting duplicate keys."""
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def decode_metadata_document(text: str) -> ModelMetadataDocument:
    """Decode and validate one JSON metadata snapshot."""
    try:
        raw = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except DuplicateKeyError as exc:
        raise ConfigurationError(str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationError(
            f"not valid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc
    if not isinstance(raw, Mapping):
        raise ConfigurationError("metadata document must be a JSON object")
    return parse_model_metadata_document(cast("Mapping[str, object]", raw))
