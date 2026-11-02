"""Parse the model-file schema into validated configuration objects."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Literal, cast

from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    AnthropicThinking,
    AnthropicThinkingAdaptive,
    AnthropicThinkingBudget,
    ChatCompletionsOptions,
    ConfigurationError,
    ModelMetadataOverride,
    ModelSourceRef,
    ProtocolKind,
    ProtocolOptions,
    ResponsesOptions,
    parse_model_metadata_override,
)
from spawn_join_llm_provider.parsing import FieldReader

from ..config import ChatModelConfig
from ._yaml import load_yaml_document

_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_READER = FieldReader(ConfigurationError)
_as_mapping = _READER.as_mapping
_require_keys = _READER.require_keys
_as_str = _READER.as_str
_as_int = _READER.as_int
_as_number = _READER.as_number
_as_bool = _READER.as_bool
_optional = _READER.optional

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
_ENTRY_OPTIONAL_FIELDS_V1 = frozenset(
    {"display_name", "timeout_seconds", "max_retries", "options"}
)
_ENTRY_OPTIONAL_FIELDS_V2 = _ENTRY_OPTIONAL_FIELDS_V1 | frozenset(
    {"metadata_ref", "metadata_source", "metadata"}
)


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


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    name: str
    display_name: str
    config: ChatModelConfig
    api_key_env: str
    options: ProtocolOptions | None
    metadata_ref: str | None
    metadata_source: Mapping[str, ModelSourceRef]
    metadata: ModelMetadataOverride | None


def _parse_entry(name: str, value: object, schema_version: int) -> CatalogEntry:
    """Parse and validate one named model entry."""
    path = f"models.{name}"
    fields = _as_mapping(value, path)
    optional_fields = (
        _ENTRY_OPTIONAL_FIELDS_V1 if schema_version == 1 else _ENTRY_OPTIONAL_FIELDS_V2
    )
    _require_keys(
        fields,
        required=_ENTRY_REQUIRED_FIELDS,
        optional=optional_fields,
        path=path,
    )
    config = _parse_model_config(fields, path)
    metadata_ref = _parse_metadata_ref(fields, path)
    return CatalogEntry(
        name=name,
        display_name=_parse_display_name(fields, name, path),
        config=config,
        api_key_env=_parse_api_key_env(fields, path),
        options=_parse_entry_options(fields, config.protocol, path),
        metadata_ref=metadata_ref,
        metadata_source=_parse_metadata_source(fields, path, metadata_ref),
        metadata=_parse_entry_metadata(fields, path),
    )


def _parse_metadata_ref(
    fields: Mapping[str, object],
    path: str,
) -> str | None:
    """Parse the optional shared-model reference."""
    value = _optional(fields, "metadata_ref", _as_str, path)
    if value is None:
        return None
    if not value or value != value.strip() or "/" not in value:
        raise ConfigurationError(f"{path}.metadata_ref: must use <lab>/<model>")
    return value


def _parse_metadata_source(
    fields: Mapping[str, object],
    path: str,
    metadata_ref: str | None,
) -> Mapping[str, ModelSourceRef]:
    """Parse explicit source IDs mapped to provider/model coordinates."""
    if "metadata_source" not in fields:
        return MappingProxyType({})
    if metadata_ref is None:
        raise ConfigurationError(f"{path}.metadata_source: metadata_ref is required")
    source_fields = _as_mapping(
        fields["metadata_source"],
        f"{path}.metadata_source",
    )
    if not source_fields:
        raise ConfigurationError(f"{path}.metadata_source: must not be empty")
    result: dict[str, ModelSourceRef] = {}
    for source_id, value in source_fields.items():
        ref_path = f"{path}.metadata_source.{source_id}"
        ref_fields = _as_mapping(value, ref_path)
        _require_keys(
            ref_fields,
            required=frozenset({"provider", "model"}),
            optional=frozenset(),
            path=ref_path,
        )
        try:
            result[source_id] = ModelSourceRef(
                source_id=source_id,
                provider=_as_str(ref_fields["provider"], f"{ref_path}.provider"),
                model=_as_str(ref_fields["model"], f"{ref_path}.model"),
            )
        except ConfigurationError as exc:
            raise ConfigurationError(f"{ref_path}: {exc}") from exc
    return MappingProxyType(result)


def _parse_entry_metadata(
    fields: Mapping[str, object],
    path: str,
) -> ModelMetadataOverride | None:
    """Parse the optional inline metadata override."""
    if "metadata" not in fields:
        return None
    return parse_model_metadata_override(fields["metadata"], f"{path}.metadata")


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


def _parse_root(path: str | Path) -> tuple[dict[str, object], int]:
    """Load the YAML document and validate its top-level fields."""
    document = load_yaml_document(Path(path))
    root = _as_mapping(document, "<root>")
    _require_keys(
        root,
        required=_ROOT_REQUIRED_FIELDS,
        optional=_ROOT_OPTIONAL_FIELDS,
        path="<root>",
    )
    schema_version = _as_int(root["schema_version"], "schema_version")
    if schema_version not in {1, 2}:
        raise ConfigurationError("schema_version: only versions 1 and 2 are supported")
    return root, schema_version


def _parse_models(value: object, schema_version: int) -> dict[str, CatalogEntry]:
    """Parse every named entry, rejecting an empty model map."""
    models = _as_mapping(value, "models")
    if not models:
        raise ConfigurationError("models: at least one model is required")

    entries: dict[str, CatalogEntry] = {}
    for name, entry_value in models.items():
        validated_name = _validate_label(name, "models: model name")
        entries[validated_name] = _parse_entry(
            validated_name, entry_value, schema_version
        )
    return entries


def _resolve_default_name(
    root: Mapping[str, object],
    entries: Mapping[str, CatalogEntry],
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


def parse_catalog(path: str | Path) -> tuple[dict[str, CatalogEntry], str]:
    """Parse one YAML document into validated entries and a default name."""
    root, schema_version = _parse_root(path)
    entries = _parse_models(root["models"], schema_version)
    default_name = _resolve_default_name(root, entries)
    return entries, default_name
