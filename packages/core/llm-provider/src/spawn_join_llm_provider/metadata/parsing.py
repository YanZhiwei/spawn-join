"""Pydantic-backed parsers for canonical model metadata."""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from pydantic import TypeAdapter, ValidationError

from ..errors import ConfigurationError
from .types import ModelMetadataDocument, ModelMetadataOverride

_OVERRIDE_FIELDS = frozenset(
    {"pricing", "limits", "capabilities", "modalities", "status"}
)
_DOCUMENT_ADAPTER = TypeAdapter(ModelMetadataDocument)
_OVERRIDE_ADAPTER = TypeAdapter(ModelMetadataOverride)


def _mapping(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ConfigurationError(f"{path}: must be a mapping")
    result: dict[str, object] = {}
    for key, item in cast("Mapping[object, object]", value).items():
        if not isinstance(key, str):
            raise ConfigurationError(f"{path}: keys must be strings")
        result[key] = item
    return result


def _normalize_source(value: object) -> object:
    if not isinstance(value, Mapping):
        return value
    source = _mapping(cast("object", value), "source")
    if "id" in source and "source_id" not in source:
        source["source_id"] = source.pop("id")
    return source


def _normalize_channel(value: object, name: str) -> object:
    path = f"channels.{name}"
    if not isinstance(value, Mapping):
        return value
    channel = _mapping(cast("object", value), path)
    override = {
        field: channel.pop(field)
        for field in list(channel)
        if field in _OVERRIDE_FIELDS
    }
    if "override" not in channel:
        channel["override"] = override
    if "source" in channel:
        channel["source"] = _normalize_source(channel["source"])
    return channel


def _normalize_model(value: object, key: str) -> object:
    if not isinstance(value, Mapping):
        return value
    model = _mapping(cast("object", value), f"models.{key}")
    model["key"] = key
    return model


def _normalize_document(value: object) -> object:
    root = _mapping(value, "<metadata>")
    normalized = dict(root)
    models = root.get("models")
    if isinstance(models, Mapping):
        models_map = _mapping(cast("object", models), "<metadata>.models")
        normalized["models"] = {
            key: _normalize_model(model, key) for key, model in models_map.items()
        }
    channels = root.get("channels")
    if isinstance(channels, Mapping):
        channels_map = _mapping(cast("object", channels), "<metadata>.channels")
        normalized["channels"] = {
            key: _normalize_channel(channel, key)
            for key, channel in channels_map.items()
        }
    return normalized


def _validation_message(exc: ValidationError) -> str:
    messages: list[str] = []
    for error in exc.errors():
        location = ".".join(str(part) for part in error["loc"])
        kind = error["type"]
        if kind in {"extra_forbidden", "unexpected_keyword_argument"}:
            field = error["loc"][-1] if error["loc"] else "<metadata>"
            messages.append(f"{location}: unknown field(s): {field}")
        elif kind == "missing":
            field = error["loc"][-1] if error["loc"] else "<metadata>"
            messages.append(f"{location}: missing required field(s): {field}")
        else:
            messages.append(f"{location}: {error['msg']}")
    return "; ".join(messages)


def parse_model_metadata_override(
    value: object,
    path: str = "metadata",
) -> ModelMetadataOverride:
    """Parse a channel or inline override mapping."""
    try:
        return _OVERRIDE_ADAPTER.validate_python(value)
    except ValidationError as exc:
        raise ConfigurationError(f"{path}: {_validation_message(exc)}") from exc


def parse_model_metadata_document(value: object) -> ModelMetadataDocument:
    """Parse a metadata snapshot document."""
    try:
        return _DOCUMENT_ADAPTER.validate_python(_normalize_document(value))
    except ValidationError as exc:
        raise ConfigurationError(f"<metadata>: {_validation_message(exc)}") from exc
