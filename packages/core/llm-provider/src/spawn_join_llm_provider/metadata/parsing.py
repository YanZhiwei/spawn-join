"""Pydantic-backed parsers for canonical model metadata."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from pydantic import TypeAdapter, ValidationError

from ..errors import ConfigurationError
from .types import _parse_model_key  # pyright: ignore[reportPrivateUsage]
from .types import (
    ModelChannel,
    ModelMetadata,
    ModelMetadataDocument,
    ModelMetadataOverride,
    ModelSource,
)

_OVERRIDE_FIELDS = frozenset(
    {"pricing", "limits", "capabilities", "modalities", "status"}
)
_DOCUMENT_ADAPTER = TypeAdapter(ModelMetadataDocument)
_OVERRIDE_ADAPTER = TypeAdapter(ModelMetadataOverride)
_MODEL_ADAPTER = TypeAdapter(ModelMetadata)
_CHANNEL_ADAPTER = TypeAdapter(ModelChannel)
_SOURCE_ADAPTER = TypeAdapter(ModelSource)


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
    if "override" in channel:
        raise ConfigurationError(f"{path}: unknown field(s): override")
    override = {
        field: channel.pop(field)
        for field in list(channel)
        if field in _OVERRIDE_FIELDS
    }
    channel["override"] = override
    if "source" in channel:
        channel["source"] = _normalize_source(channel["source"])
    return channel


def _normalize_model(value: object, key: str) -> object:
    _parse_model_key(key, f"models.{key}")
    if not isinstance(value, Mapping):
        return value
    model = _mapping(cast("object", value), f"models.{key}")
    if "key" in model and model["key"] is None:
        raise ConfigurationError(f"models.{key}.key: must not be null")
    supplied = model.get("key")
    if supplied is not None and supplied != key:
        raise ConfigurationError(
            f"models.{key}.key: model key must match models map key"
        )
    model["key"] = key
    return model


def _validate_nested(
    adapter: TypeAdapter[Any],
    value: object,
    path: str,
) -> None:
    try:
        adapter.validate_python(value)
    except ValidationError as exc:
        raise ConfigurationError(f"{path}: {_validation_message(exc)}") from exc
    except ConfigurationError as exc:
        raise ConfigurationError(f"{path}: {exc}") from exc


def _normalize_document(value: object) -> object:
    root = _mapping(value, "<metadata>")
    normalized = dict(root)
    models = root.get("models")
    if isinstance(models, Mapping):
        models_map = _mapping(cast("object", models), "<metadata>.models")
        normalized_models: dict[str, object] = {}
        for key, model in models_map.items():
            normalized_model = _normalize_model(model, key)
            _validate_nested(_MODEL_ADAPTER, normalized_model, f"models.{key}")
            normalized_models[key] = normalized_model
        normalized["models"] = normalized_models
    channels = root.get("channels")
    if isinstance(channels, Mapping):
        channels_map = _mapping(cast("object", channels), "<metadata>.channels")
        normalized_channels: dict[str, object] = {}
        for key, channel in channels_map.items():
            normalized_channel = _normalize_channel(channel, key)
            _validate_nested(
                _CHANNEL_ADAPTER,
                normalized_channel,
                f"channels.{key}",
            )
            normalized_channels[key] = normalized_channel
        normalized["channels"] = normalized_channels
    sources = root.get("sources")
    if isinstance(sources, Mapping):
        sources_map = _mapping(cast("object", sources), "<metadata>.sources")
        for key, source in sources_map.items():
            _validate_nested(_SOURCE_ADAPTER, source, f"sources.{key}")
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
    if not isinstance(value, Mapping):
        raise ConfigurationError(f"{path}: must be a mapping")
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
