"""Load model catalogs from an explicit YAML file and resolve API keys."""

from __future__ import annotations

import os
import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import cast

import yaml
from langchain_core.language_models import BaseChatModel

from spawn_join_llm_provider import ConfigurationError, ProtocolKind

from .config import ChatModelConfig
from .factory import create_chat_model as _create_chat_model

_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _check_duplicate_keys(node: yaml.Node) -> None:
    """Reject literal duplicate keys and recursive aliases in one document."""
    _walk_node(node, active=set(), visited=set())


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
    """Read one YAML document, rejecting duplicate keys and unsafe tags."""
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
            _check_duplicate_keys(node)
        document: object = yaml.safe_load(text)
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

    return document


def _as_mapping(value: object, path: str) -> dict[object, object]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{path}: must be a mapping")
    return cast("dict[object, object]", value)


def _require_string_keys(
    mapping: Mapping[object, object], path: str
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, item in mapping.items():
        if not isinstance(key, str):
            raise ConfigurationError(f"{path}: keys must be strings")
        result[key] = item
    return result


def _require_keys(
    mapping: Mapping[str, object],
    *,
    required: frozenset[str],
    optional: frozenset[str],
    path: str,
) -> None:
    problems: list[str] = []
    missing = required.difference(mapping)
    if missing:
        joined = ", ".join(sorted(missing))
        problems.append(f"missing required field(s): {joined}")

    unknown = set(mapping).difference(required, optional)
    if unknown:
        joined = ", ".join(sorted(unknown))
        problems.append(f"unknown field(s): {joined}")

    if problems:
        raise ConfigurationError(f"{path}: {'; '.join(problems)}")


def _as_str(value: object, path: str) -> str:
    if not isinstance(value, str):
        raise ConfigurationError(f"{path}: must be a string")
    return value


def _as_int(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigurationError(f"{path}: must be an integer")
    return value


def _as_number(value: object, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(f"{path}: must be a number")
    return float(value)


def _validate_label(value: str, path: str) -> str:
    if not value or value != value.strip():
        raise ConfigurationError(
            f"{path}: must be non-empty without surrounding whitespace"
        )
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise ConfigurationError(f"{path}: must not contain control characters")
    return value


def _validate_env_name(value: str, path: str) -> str:
    if _ENV_NAME.fullmatch(value) is None:
        raise ConfigurationError(f"{path}: must be a valid environment variable name")
    return value


def _parse_protocol(value: object, path: str) -> ProtocolKind:
    raw = _as_str(value, path)
    try:
        return ProtocolKind(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{path}: unsupported protocol {raw!r}") from exc


@dataclass(frozen=True, slots=True)
class _ModelEntry:
    name: str
    display_name: str
    config: ChatModelConfig
    api_key_env: str


@dataclass(frozen=True, slots=True, repr=False)
class ModelCatalog:
    """An immutable set of validated model entries plus a default name."""

    _entries: Mapping[str, _ModelEntry] = field(repr=False)
    _default_name: str = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_entries", MappingProxyType(dict(self._entries)))

    @property
    def default_name(self) -> str:
        """Return the name used when no explicit model is requested."""
        return self._default_name

    def create_chat_model(
        self,
        name: str | None = None,
        *,
        environ: Mapping[str, str] | None = None,
    ) -> BaseChatModel:
        """Create a LangChain model for one entry, resolving its API key."""
        entry = self._resolve_entry(name)
        api_key = self._resolve_api_key(entry, environ)
        try:
            return _create_chat_model(entry.config, api_key=api_key)
        except ConfigurationError as exc:
            raise ConfigurationError(f"models.{entry.name}: {exc}") from exc

    def __repr__(self) -> str:
        names = tuple(self._entries)
        return f"ModelCatalog(models={names!r}, default={self._default_name!r})"

    def _resolve_entry(self, name: str | None) -> _ModelEntry:
        selected = self._default_name if name is None else name
        entry = self._entries.get(selected)
        if entry is None:
            available = ", ".join(self._entries)
            raise ConfigurationError(
                f"Unknown model {selected!r}; available models: {available}"
            )
        return entry

    @staticmethod
    def _resolve_api_key(
        entry: _ModelEntry,
        environ: Mapping[str, str] | None,
    ) -> str:
        source = os.environ if environ is None else environ
        value = source.get(entry.api_key_env)
        if value is None:
            raise ConfigurationError(
                f"models.{entry.name}.api_key_env: {entry.api_key_env} is not "
                "set in the environment"
            )
        if not value.strip():
            raise ConfigurationError(
                f"models.{entry.name}.api_key_env: {entry.api_key_env} is empty"
            )
        return value


def _parse_entry(name: str, value: object) -> _ModelEntry:
    path = f"models.{name}"
    fields = _require_string_keys(_as_mapping(value, path), path)
    _require_keys(
        fields,
        required=frozenset({"protocol", "endpoint", "model", "api_key_env"}),
        optional=frozenset({"display_name", "timeout_seconds", "max_retries"}),
        path=path,
    )

    protocol = _parse_protocol(fields["protocol"], f"{path}.protocol")
    endpoint = _as_str(fields["endpoint"], f"{path}.endpoint")
    model = _as_str(fields["model"], f"{path}.model")
    api_key_env = _validate_env_name(
        _as_str(fields["api_key_env"], f"{path}.api_key_env"),
        f"{path}.api_key_env",
    )
    display_name = name
    if "display_name" in fields:
        display_name = _validate_label(
            _as_str(fields["display_name"], f"{path}.display_name"),
            f"{path}.display_name",
        )

    timeout_seconds = 30.0
    if "timeout_seconds" in fields:
        timeout_seconds = _as_number(
            fields["timeout_seconds"], f"{path}.timeout_seconds"
        )

    max_retries = 0
    if "max_retries" in fields:
        max_retries = _as_int(fields["max_retries"], f"{path}.max_retries")

    try:
        config = ChatModelConfig(
            protocol=protocol,
            endpoint=endpoint,
            model=model,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
    except ConfigurationError as exc:
        raise ConfigurationError(f"{path}: {exc}") from exc

    return _ModelEntry(
        name=name,
        display_name=display_name,
        config=config,
        api_key_env=api_key_env,
    )


def load_model_catalog(path: str | Path) -> ModelCatalog:
    """Load and validate a model catalog from an explicit YAML file."""
    document = _load_yaml_document(Path(path))
    root = _require_string_keys(_as_mapping(document, "<root>"), "<root>")
    _require_keys(
        root,
        required=frozenset({"schema_version", "models"}),
        optional=frozenset({"default"}),
        path="<root>",
    )

    schema_version = _as_int(root["schema_version"], "schema_version")
    if schema_version != 1:
        raise ConfigurationError("schema_version: only version 1 is supported")

    models = _require_string_keys(_as_mapping(root["models"], "models"), "models")
    if not models:
        raise ConfigurationError("models: at least one model is required")

    entries: dict[str, _ModelEntry] = {}
    for name, value in models.items():
        validated_name = _validate_label(name, "models: model name")
        entries[validated_name] = _parse_entry(validated_name, value)

    default_value = root.get("default")
    if "default" not in root:
        if len(entries) != 1:
            raise ConfigurationError(
                "default: required when multiple models are defined"
            )
        default_name = next(iter(entries))
    else:
        default_name = _as_str(default_value, "default")
        if default_name not in entries:
            available = ", ".join(entries)
            raise ConfigurationError(
                f"default: unknown model {default_name!r}; available models: "
                f"{available}"
            )

    return ModelCatalog(_entries=entries, _default_name=default_name)
