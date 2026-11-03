"""Metadata-only model.yaml reader shared by the sync tool.

The runtime LangChain adapter remains the authority for protocol, endpoint,
option and key validation. This reader extracts the v2 metadata projection and
deliberately avoids importing LangChain.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast

import yaml

from spawn_join_llm_provider import (
    ConfigurationError,
    ModelMetadataOverride,
    ModelSourceRef,
    parse_model_metadata_override,
)
from spawn_join_llm_provider.parsing import FieldReader

_READER = FieldReader(ConfigurationError)
_MODEL_KEY = r"^[^/\s]+/[^/\s].*$"
_METADATA_FIELDS = frozenset({"metadata_ref", "metadata_source", "metadata"})
_SOURCE_ID = r"^[a-z0-9][a-z0-9._-]*$"


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelMetadataEntry:
    """The metadata-relevant view of one model.yaml entry."""

    name: str
    metadata_ref: str | None
    metadata_source: Mapping[str, ModelSourceRef]
    metadata: ModelMetadataOverride | None


def _walk_node(
    node: yaml.Node,
    *,
    active: set[int],
    visited: set[int],
) -> None:
    node_id = id(node)
    if node_id in active:
        raise ConfigurationError("Model file contains a recursive alias")
    if node_id in visited:
        return
    active.add(node_id)
    try:
        if isinstance(node, yaml.MappingNode):
            seen: set[str] = set()
            for key_node, value_node in node.value:
                if isinstance(key_node, yaml.ScalarNode):
                    if key_node.value in seen:
                        line = key_node.start_mark.line + 1
                        column = key_node.start_mark.column + 1
                        raise ConfigurationError(
                            f"Model file contains a duplicate key at line {line}, "
                            f"column {column}"
                        )
                    seen.add(key_node.value)
                _walk_node(key_node, active=active, visited=visited)
                _walk_node(value_node, active=active, visited=visited)
        elif isinstance(node, yaml.SequenceNode):
            for item in node.value:
                _walk_node(item, active=active, visited=visited)
    finally:
        active.remove(node_id)
    visited.add(node_id)


def _load_yaml_document(path: Path) -> object:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeError as exc:
        raise ConfigurationError(f"Model file is not valid UTF-8: {path}") from exc
    except OSError as exc:
        raise ConfigurationError(f"Model file could not be read: {path}") from exc
    try:
        node = cast(
            "yaml.Node | None",
            yaml.compose(  # pyright: ignore[reportUnknownMemberType]
                text, Loader=yaml.SafeLoader
            ),
        )
        if node is not None:
            _walk_node(node, active=set(), visited=set())
        return yaml.safe_load(text)
    except yaml.MarkedYAMLError as exc:
        problem = exc.problem or "invalid YAML"
        mark = exc.problem_mark
        location = ""
        if mark is not None:
            location = f" at line {mark.line + 1}, column {mark.column + 1}"
        raise ConfigurationError(
            f"Model file is not valid YAML{location}: {problem}"
        ) from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError("Model file is not valid YAML") from exc


def _parse_metadata_ref(
    fields: Mapping[str, object],
    path: str,
) -> str | None:
    value = _READER.optional(fields, "metadata_ref", _READER.as_str, path)
    if value is None:
        return None
    if not value or value != value.strip():
        raise ConfigurationError(
            f"{path}.metadata_ref: must be non-empty without surrounding whitespace"
        )
    if "/" not in value:
        raise ConfigurationError(f"{path}.metadata_ref: must use <lab>/<model>")
    return value


def _parse_source_ref(value: object, path: str, source_id: str) -> ModelSourceRef:
    fields = _READER.as_mapping(value, path)
    _READER.require_keys(
        fields,
        required=frozenset({"provider", "model"}),
        optional=frozenset(),
        path=path,
    )
    return ModelSourceRef(
        source_id=source_id,
        provider=_READER.as_str(fields["provider"], f"{path}.provider"),
        model=_READER.as_str(fields["model"], f"{path}.model"),
    )


def _parse_metadata_source(
    fields: Mapping[str, object],
    path: str,
    metadata_ref: str | None,
) -> Mapping[str, ModelSourceRef]:
    if "metadata_source" not in fields:
        return MappingProxyType({})
    if metadata_ref is None:
        raise ConfigurationError(f"{path}.metadata_source: metadata_ref is required")
    source_fields = _READER.as_mapping(
        fields["metadata_source"],
        f"{path}.metadata_source",
    )
    if not source_fields:
        raise ConfigurationError(f"{path}.metadata_source: must not be empty")
    result: dict[str, ModelSourceRef] = {}
    for source_id, source_value in source_fields.items():
        if not source_id or not source_id.strip():
            raise ConfigurationError(
                f"{path}.metadata_source: source ID must not be empty"
            )
        result[source_id] = _parse_source_ref(
            source_value,
            f"{path}.metadata_source.{source_id}",
            source_id,
        )
    return MappingProxyType(result)


def _validate_name(name: str) -> None:
    if not name or name != name.strip():
        raise ConfigurationError(
            "models: model name must be non-empty without surrounding whitespace"
        )
    if any(ord(character) < 32 for character in name):
        raise ConfigurationError(
            "models: model name must not contain control characters"
        )


def _parse_entry(
    name: str,
    value: object,
    schema_version: int,
) -> ModelMetadataEntry:
    path = f"models.{name}"
    _validate_name(name)
    fields = _READER.as_mapping(value, path)
    if schema_version == 1:
        v2_fields = sorted(set(fields).intersection(_METADATA_FIELDS))
        if v2_fields:
            raise ConfigurationError(
                f"{path}: unknown field(s): {', '.join(v2_fields)}"
            )
    metadata_ref = _parse_metadata_ref(fields, path)
    metadata_source = _parse_metadata_source(fields, path, metadata_ref)
    metadata = (
        parse_model_metadata_override(fields["metadata"], f"{path}.metadata")
        if "metadata" in fields
        else None
    )
    return ModelMetadataEntry(
        name=name,
        metadata_ref=metadata_ref,
        metadata_source=metadata_source,
        metadata=metadata,
    )


def load_model_metadata_entries(path: str | Path) -> tuple[ModelMetadataEntry, ...]:
    """Load the metadata projection of an explicit model.yaml file."""
    document = _load_yaml_document(Path(path))
    root = _READER.as_mapping(document, "<root>")
    schema_version = _READER.as_int(root.get("schema_version"), "schema_version")
    if schema_version not in {1, 2}:
        raise ConfigurationError("schema_version: only versions 1 and 2 are supported")
    models = _READER.as_mapping(root.get("models"), "models")
    if not models:
        raise ConfigurationError("models: at least one model is required")
    return tuple(
        _parse_entry(name, value, schema_version) for name, value in models.items()
    )
