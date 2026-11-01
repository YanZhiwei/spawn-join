"""Load model catalogs from an explicit YAML file and resolve API keys.

The file boundary is intentionally explicit. The project's existing
``ChatModelConfig`` and protocol options are standard-library dataclasses: they
validate domain rules but do not reject unknown YAML keys or Python bool/str
coercions. Pydantic's dataclass adapter also echoes input values in errors.
Keeping the parsing here preserves strict schema, no-interpolation and
secret-safe diagnostics without defining a second configuration schema.
"""

from __future__ import annotations

import os
import re
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Literal, TypeVar, cast

import yaml
from dotenv import dotenv_values
from langchain_core.language_models import BaseChatModel

from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    AnthropicThinking,
    AnthropicThinkingAdaptive,
    AnthropicThinkingBudget,
    ChatCompletionsOptions,
    ConfigurationError,
    ProtocolKind,
    ProtocolOptions,
    ResponsesOptions,
)

from .config import ChatModelConfig
from .factory import create_chat_model as _create_chat_model

_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_T = TypeVar("_T")

_CHAT_COMPLETIONS_FIELDS = frozenset(
    {"temperature", "max_output_tokens", "top_p", "stop", "seed"}
)
_RESPONSES_FIELDS = frozenset(
    {
        "temperature",
        "max_output_tokens",
        "top_p",
        "store",
        "reasoning_effort",
        "truncation",
    }
)
_ANTHROPIC_FIELDS = frozenset(
    {
        "temperature",
        "max_output_tokens",
        "top_p",
        "top_k",
        "stop_sequences",
        "thinking",
    }
)

_ROOT_REQUIRED_FIELDS = frozenset({"schema_version", "models"})
_ROOT_OPTIONAL_FIELDS = frozenset({"default"})
_ENTRY_REQUIRED_FIELDS = frozenset({"protocol", "endpoint", "model", "api_key_env"})
_ENTRY_OPTIONAL_FIELDS = frozenset(
    {"display_name", "timeout_seconds", "max_retries", "options"}
)


# --- YAML document boundary -------------------------------------------------
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


# --- Schema field parsing ---------------------------------------------------
def _as_mapping(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{path}: must be a mapping")
    result: dict[str, object] = {}
    for key, item in cast("dict[object, object]", value).items():
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


def _as_bool(value: object, path: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigurationError(f"{path}: must be a boolean")
    return value


def _as_string_tuple(value: object, path: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ConfigurationError(f"{path}: must be a list of strings")
    items = cast("list[object]", value)
    result: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str) or item == "":
            raise ConfigurationError(f"{path}[{index}]: must be a non-empty string")
        result.append(item)
    return tuple(result)


def _optional(
    fields: Mapping[str, object],
    name: str,
    parser: Callable[[object, str], _T],
    path: str,
) -> _T | None:
    if name not in fields:
        return None
    return parser(fields[name], f"{path}.{name}")


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


def _parse_thinking(value: object, path: str) -> AnthropicThinking:
    fields = _as_mapping(value, path)
    _require_keys(
        fields,
        required=frozenset({"mode"}),
        optional=frozenset({"budget_tokens"}),
        path=path,
    )
    mode = _as_str(fields["mode"], f"{path}.mode")

    if mode == "adaptive":
        if "budget_tokens" in fields:
            raise ConfigurationError(
                f"{path}: budget_tokens is not allowed for adaptive thinking"
            )
        return AnthropicThinkingAdaptive()

    if mode == "budget":
        if "budget_tokens" not in fields:
            raise ConfigurationError(
                f"{path}: budget_tokens is required for budget thinking"
            )
        budget = _as_int(fields["budget_tokens"], f"{path}.budget_tokens")
        try:
            return AnthropicThinkingBudget(budget_tokens=budget)
        except ConfigurationError as exc:
            raise ConfigurationError(f"{path}: {exc}") from exc

    raise ConfigurationError(f"{path}.mode: must be 'budget' or 'adaptive'")


def _parse_options(
    protocol: ProtocolKind,
    value: object,
    path: str,
) -> ProtocolOptions:
    """Parse one protocol's options mapping into its typed dataclass."""
    fields = _as_mapping(value, path)
    match protocol:
        case ProtocolKind.CHAT_COMPLETIONS:
            return _parse_chat_completions_options(fields, path)
        case ProtocolKind.RESPONSES:
            return _parse_responses_options(fields, path)
        case ProtocolKind.ANTHROPIC_MESSAGES:
            return _parse_anthropic_options(fields, path)
        case _:
            raise ConfigurationError(f"Unsupported protocol: {protocol}")


def _parse_chat_completions_options(
    fields: Mapping[str, object],
    path: str,
) -> ChatCompletionsOptions:
    """Parse options for the OpenAI Chat Completions protocol."""
    _require_keys(
        fields,
        required=frozenset(),
        optional=_CHAT_COMPLETIONS_FIELDS,
        path=path,
    )
    temperature = _optional(fields, "temperature", _as_number, path)
    max_output_tokens = _optional(fields, "max_output_tokens", _as_int, path)
    top_p = _optional(fields, "top_p", _as_number, path)
    stop = _optional(fields, "stop", _as_string_tuple, path)
    seed = _optional(fields, "seed", _as_int, path)

    try:
        return ChatCompletionsOptions(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=top_p,
            stop=stop,
            seed=seed,
        )
    except ConfigurationError as exc:
        raise ConfigurationError(f"{path}: {exc}") from exc


def _parse_responses_options(
    fields: Mapping[str, object],
    path: str,
) -> ResponsesOptions:
    """Parse options for the OpenAI Responses protocol."""
    _require_keys(
        fields,
        required=frozenset(),
        optional=_RESPONSES_FIELDS,
        path=path,
    )
    temperature = _optional(fields, "temperature", _as_number, path)
    max_output_tokens = _optional(fields, "max_output_tokens", _as_int, path)
    top_p = _optional(fields, "top_p", _as_number, path)
    store = _optional(fields, "store", _as_bool, path)
    reasoning_effort = cast(
        "Literal['low', 'medium', 'high'] | None",
        _optional(fields, "reasoning_effort", _as_str, path),
    )
    truncation = cast(
        "Literal['auto', 'disabled'] | None",
        _optional(fields, "truncation", _as_str, path),
    )

    try:
        return ResponsesOptions(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=top_p,
            store=store,
            reasoning_effort=reasoning_effort,
            truncation=truncation,
        )
    except ConfigurationError as exc:
        raise ConfigurationError(f"{path}: {exc}") from exc


def _parse_anthropic_options(
    fields: Mapping[str, object],
    path: str,
) -> AnthropicMessagesOptions:
    """Parse options for the Anthropic Messages protocol."""
    _require_keys(
        fields,
        required=frozenset(),
        optional=_ANTHROPIC_FIELDS,
        path=path,
    )
    temperature = _optional(fields, "temperature", _as_number, path)
    max_output_tokens = _optional(fields, "max_output_tokens", _as_int, path)
    top_p = _optional(fields, "top_p", _as_number, path)
    top_k = _optional(fields, "top_k", _as_int, path)
    stop_sequences = _optional(fields, "stop_sequences", _as_string_tuple, path)
    thinking = (
        _parse_thinking(fields["thinking"], f"{path}.thinking")
        if "thinking" in fields
        else None
    )

    try:
        return AnthropicMessagesOptions(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            top_p=top_p,
            top_k=top_k,
            stop_sequences=stop_sequences,
            thinking=thinking,
        )
    except ConfigurationError as exc:
        raise ConfigurationError(f"{path}: {exc}") from exc


# --- Catalog runtime --------------------------------------------------------
@dataclass(frozen=True, slots=True)
class ModelSummary:
    """A display-ready view of one catalog entry."""

    name: str
    model: str
    display_name: str


@dataclass(frozen=True, slots=True)
class _CatalogEntry:
    name: str
    display_name: str
    config: ChatModelConfig
    api_key_env: str
    options: ProtocolOptions | None


@dataclass(frozen=True, slots=True, repr=False)
class ModelCatalog:
    """An immutable set of validated model entries plus a default name."""

    _entries: Mapping[str, _CatalogEntry] = field(repr=False)
    _default_name: str = field(repr=False)
    _env_file: Path | None = field(repr=False)
    _env_values: Mapping[str, str] = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_entries", MappingProxyType(dict(self._entries)))
        object.__setattr__(
            self, "_env_values", MappingProxyType(dict(self._env_values))
        )

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        *,
        env_file: str | Path | None = None,
    ) -> ModelCatalog:
        """Load and validate a catalog from an explicit YAML file."""
        root = _parse_root(path)
        entries = _parse_models(root["models"])
        default_name = _resolve_default_name(root, entries)
        env_path, env_values = _load_env_snapshot(env_file, entries)
        return cls(
            _entries=entries,
            _default_name=default_name,
            _env_file=env_path,
            _env_values=env_values,
        )

    @property
    def models(self) -> tuple[ModelSummary, ...]:
        """Return display summaries in the order defined by the file."""
        return tuple(
            ModelSummary(
                name=entry.name,
                model=entry.config.model,
                display_name=entry.display_name,
            )
            for entry in self._entries.values()
        )

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
            return _create_chat_model(
                entry.config, api_key=api_key, options=entry.options
            )
        except ConfigurationError as exc:
            raise ConfigurationError(f"models.{entry.name}: {exc}") from exc

    def __repr__(self) -> str:
        names = tuple(self._entries)
        return f"ModelCatalog(models={names!r}, default={self._default_name!r})"

    def _resolve_entry(self, name: str | None) -> _CatalogEntry:
        selected = self._default_name if name is None else name
        entry = self._entries.get(selected)
        if entry is None:
            available = ", ".join(self._entries)
            raise ConfigurationError(
                f"Unknown model {selected!r}; available models: {available}"
            )
        return entry

    def _resolve_api_key(
        self,
        entry: _CatalogEntry,
        environ: Mapping[str, str] | None,
    ) -> str:
        source = os.environ if environ is None else environ
        value = source.get(entry.api_key_env)
        if value is None:
            value = self._env_values.get(entry.api_key_env)
        if value is None:
            location = "the environment"
            if self._env_file is not None:
                location = f"the environment or {self._env_file}"
            raise ConfigurationError(
                f"models.{entry.name}.api_key_env: {entry.api_key_env} is not "
                f"set in {location}"
            )
        if not value.strip():
            raise ConfigurationError(
                f"models.{entry.name}.api_key_env: {entry.api_key_env} is empty"
            )
        return value


def _parse_entry(name: str, value: object) -> _CatalogEntry:
    """Parse and validate one named model entry."""
    path = f"models.{name}"
    fields = _as_mapping(value, path)
    _require_keys(
        fields,
        required=_ENTRY_REQUIRED_FIELDS,
        optional=_ENTRY_OPTIONAL_FIELDS,
        path=path,
    )
    config = _parse_model_config(fields, path)
    return _CatalogEntry(
        name=name,
        display_name=_parse_display_name(fields, name, path),
        config=config,
        api_key_env=_parse_api_key_env(fields, path),
        options=_parse_entry_options(fields, config.protocol, path),
    )


def _parse_model_config(
    fields: Mapping[str, object],
    path: str,
) -> ChatModelConfig:
    """Build the endpoint/model configuration for one entry."""
    protocol = _parse_protocol(fields["protocol"], f"{path}.protocol")
    endpoint = _as_str(fields["endpoint"], f"{path}.endpoint")
    model = _as_str(fields["model"], f"{path}.model")
    timeout_seconds = _optional(fields, "timeout_seconds", _as_number, path)
    max_retries = _optional(fields, "max_retries", _as_int, path)

    try:
        return ChatModelConfig(
            protocol=protocol,
            endpoint=endpoint,
            model=model,
            timeout_seconds=30.0 if timeout_seconds is None else timeout_seconds,
            max_retries=0 if max_retries is None else max_retries,
        )
    except ConfigurationError as exc:
        raise ConfigurationError(f"{path}: {exc}") from exc


def _parse_display_name(
    fields: Mapping[str, object],
    name: str,
    path: str,
) -> str:
    """Return the explicit display name or fall back to the selection name."""
    value = _optional(fields, "display_name", _as_str, path)
    if value is None:
        return name
    return _validate_label(value, f"{path}.display_name")


def _parse_api_key_env(fields: Mapping[str, object], path: str) -> str:
    """Validate and return the environment variable that references the key."""
    field_path = f"{path}.api_key_env"
    return _validate_env_name(_as_str(fields["api_key_env"], field_path), field_path)


def _parse_entry_options(
    fields: Mapping[str, object],
    protocol: ProtocolKind,
    path: str,
) -> ProtocolOptions | None:
    """Parse options only when the entry declares them."""
    if "options" not in fields:
        return None
    return _parse_options(protocol, fields["options"], f"{path}.options")


# --- Environment snapshot and public loading API ----------------------------
def _read_env_file(path: Path, referenced: set[str]) -> Mapping[str, str]:
    if not path.is_file():
        raise ConfigurationError(f"Env file not found: {path}")
    try:
        values = dotenv_values(path, encoding="utf-8-sig", interpolate=False)
    except (OSError, UnicodeError) as exc:
        raise ConfigurationError(f"Env file could not be read: {path}") from exc
    return {
        key: value
        for key, value in values.items()
        if key in referenced and value is not None
    }


def load_model_catalog(
    path: str | Path,
    *,
    env_file: str | Path | None = None,
) -> ModelCatalog:
    """Load and validate a model catalog from an explicit YAML file."""
    return ModelCatalog.from_file(path, env_file=env_file)


def _parse_root(path: str | Path) -> dict[str, object]:
    """Load the YAML document and validate its top-level fields."""
    document = _load_yaml_document(Path(path))
    root = _as_mapping(document, "<root>")
    _require_keys(
        root,
        required=_ROOT_REQUIRED_FIELDS,
        optional=_ROOT_OPTIONAL_FIELDS,
        path="<root>",
    )
    schema_version = _as_int(root["schema_version"], "schema_version")
    if schema_version != 1:
        raise ConfigurationError("schema_version: only version 1 is supported")
    return root


def _parse_models(value: object) -> dict[str, _CatalogEntry]:
    """Parse every named entry, rejecting an empty model map."""
    models = _as_mapping(value, "models")
    if not models:
        raise ConfigurationError("models: at least one model is required")

    entries: dict[str, _CatalogEntry] = {}
    for name, entry_value in models.items():
        validated_name = _validate_label(name, "models: model name")
        entries[validated_name] = _parse_entry(validated_name, entry_value)
    return entries


def _resolve_default_name(
    root: Mapping[str, object],
    entries: Mapping[str, _CatalogEntry],
) -> str:
    """Resolve the explicit default, or the sole model's name."""
    if "default" not in root:
        if len(entries) != 1:
            raise ConfigurationError(
                "default: required when multiple models are defined"
            )
        return next(iter(entries))

    name = _as_str(root["default"], "default")
    if name not in entries:
        available = ", ".join(entries)
        raise ConfigurationError(
            f"default: unknown model {name!r}; available models: {available}"
        )
    return name


def _load_env_snapshot(
    env_file: str | Path | None,
    entries: Mapping[str, _CatalogEntry],
) -> tuple[Path | None, Mapping[str, str]]:
    """Read an explicit env file, keeping only referenced variables."""
    if env_file is None:
        return None, {}
    env_path = Path(env_file)
    referenced = {entry.api_key_env for entry in entries.values()}
    return env_path, _read_env_file(env_path, referenced)
