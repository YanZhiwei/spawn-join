"""Project validated model-file inputs into existing domain configuration."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from pydantic import ValidationError

from spawn_join_llm_provider import (
    ConfigurationError,
    ModelMetadataOverride,
    ModelSourceRef,
    ProtocolKind,
    ProtocolOptions,
    parse_model_metadata_override,
)

from ..config import ChatModelConfig
from ._input import (
    AnthropicInput,
    CatalogInput,
    ChatCompletionsInput,
    EntryInputV1,
    EntryInputV2,
    ResponsesInput,
    SourceRefInput,
)
from ._validation import reader, validate_input
from ._yaml import load_yaml_document

_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_OPTION_INPUTS: dict[
    ProtocolKind, type[ChatCompletionsInput | ResponsesInput | AnthropicInput]
] = {
    ProtocolKind.CHAT_COMPLETIONS: ChatCompletionsInput,
    ProtocolKind.RESPONSES: ResponsesInput,
    ProtocolKind.ANTHROPIC_MESSAGES: AnthropicInput,
}


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


def _validate_label(value: str, path: str) -> str:
    if not value or value != value.strip():
        raise ConfigurationError(
            f"{path}: must be non-empty without surrounding whitespace"
        )
    if any(unicodedata.category(character).startswith("C") for character in value):
        raise ConfigurationError(f"{path}: must not contain control characters")
    return value


def _model_config(fields: EntryInputV1, path: str) -> ChatModelConfig:
    raw_protocol = reader.as_str(fields.protocol, f"{path}.protocol")
    try:
        protocol = ProtocolKind(raw_protocol)
    except ValueError as exc:
        raise ConfigurationError(
            f"{path}.protocol: unsupported protocol {raw_protocol!r}"
        ) from exc
    endpoint = reader.as_str(fields.endpoint, f"{path}.endpoint")
    model = reader.as_str(fields.model, f"{path}.model")
    timeout = (
        reader.as_number(fields.timeout_seconds, f"{path}.timeout_seconds")
        if "timeout_seconds" in fields.model_fields_set
        else 30.0
    )
    retries = (
        reader.as_int(fields.max_retries, f"{path}.max_retries")
        if "max_retries" in fields.model_fields_set
        else 0
    )
    try:
        return ChatModelConfig(
            protocol=protocol,
            endpoint=endpoint,
            model=model,
            timeout_seconds=timeout,
            max_retries=retries,
        )
    except ConfigurationError as exc:
        raise ConfigurationError(f"{path}: {exc}") from exc


def _options(protocol: ProtocolKind, value: object, path: str) -> ProtocolOptions:
    fields = validate_input(_OPTION_INPUTS[protocol], value, path)
    try:
        return fields.to_options()
    except ConfigurationError as exc:
        raise ConfigurationError(f"{path}: {exc}") from exc


def _metadata_ref(fields: EntryInputV1, path: str) -> str | None:
    if (
        not isinstance(fields, EntryInputV2)
        or "metadata_ref" not in fields.model_fields_set
    ):
        return None
    value = reader.as_str(fields.metadata_ref, f"{path}.metadata_ref")
    if not value or value != value.strip() or "/" not in value:
        raise ConfigurationError(f"{path}.metadata_ref: must use <lab>/<model>")
    return value


def _source_refs(value: object, path: str) -> Mapping[str, ModelSourceRef]:
    source_fields = reader.as_mapping(value, f"{path}.metadata_source")
    if not source_fields:
        raise ConfigurationError(f"{path}.metadata_source: must not be empty")
    refs: dict[str, ModelSourceRef] = {}
    for source_id, source_value in source_fields.items():
        ref_path = f"{path}.metadata_source.{source_id}"
        fields = validate_input(SourceRefInput, source_value, ref_path)
        try:
            refs[source_id] = ModelSourceRef(
                source_id=source_id, provider=fields.provider, model=fields.model
            )
        except ValidationError as exc:
            # Only schema-owned field names may enter the public error message.
            locations = {error["loc"] for error in exc.errors(include_input=False)}
            error_path = f"{path}.metadata_source"
            if ("source_id",) not in locations:
                field = "provider" if ("provider",) in locations else "model"
                error_path = f"{ref_path}.{field}"
            raise ConfigurationError(f"{error_path}: invalid source reference") from exc
        except ConfigurationError as exc:
            raise ConfigurationError(f"{ref_path}: {exc}") from exc
    return MappingProxyType(refs)


def _entry(name: str, value: object, schema_version: int) -> CatalogEntry:
    path = f"models.{name}"
    schema = EntryInputV1 if schema_version == 1 else EntryInputV2
    fields = validate_input(schema, value, path)
    config = _model_config(fields, path)
    metadata_ref = _metadata_ref(fields, path)
    display_name = (
        name
        if "display_name" not in fields.model_fields_set
        else _validate_label(
            reader.as_str(fields.display_name, f"{path}.display_name"),
            f"{path}.display_name",
        )
    )
    api_key_env = reader.as_str(fields.api_key_env, f"{path}.api_key_env")
    if _ENV_NAME.fullmatch(api_key_env) is None:
        raise ConfigurationError(
            f"{path}.api_key_env: must be a valid environment variable name"
        )
    options = (
        _options(config.protocol, fields.options, f"{path}.options")
        if "options" in fields.model_fields_set
        else None
    )
    sources: Mapping[str, ModelSourceRef] = MappingProxyType({})
    metadata = None
    if isinstance(fields, EntryInputV2):
        if "metadata_source" in fields.model_fields_set:
            if metadata_ref is None:
                raise ConfigurationError(
                    f"{path}.metadata_source: metadata_ref is required"
                )
            sources = _source_refs(fields.metadata_source, path)
        if "metadata" in fields.model_fields_set:
            metadata = parse_model_metadata_override(
                fields.metadata, f"{path}.metadata"
            )
    return CatalogEntry(
        name=name,
        display_name=display_name,
        config=config,
        api_key_env=api_key_env,
        options=options,
        metadata_ref=metadata_ref,
        metadata_source=sources,
        metadata=metadata,
    )


def _default_name(root: CatalogInput, entries: Mapping[str, CatalogEntry]) -> str:
    if "default" not in root.model_fields_set:
        if len(entries) != 1:
            raise ConfigurationError(
                "default: required when multiple models are defined"
            )
        return next(iter(entries))
    name = reader.as_str(root.default, "default")
    if name not in entries:
        available = ", ".join(entries)
        raise ConfigurationError(
            f"default: unknown model {name!r}; available models: {available}"
        )
    return name


def parse_catalog(path: str | Path) -> tuple[dict[str, CatalogEntry], str]:
    """Load one strict v1/v2 file and construct the existing immutable entries."""
    root = validate_input(CatalogInput, load_yaml_document(Path(path)), "<root>")
    if root.schema_version not in {1, 2}:
        raise ConfigurationError("schema_version: only versions 1 and 2 are supported")
    models = reader.as_mapping(root.models, "models")
    if not models:
        raise ConfigurationError("models: at least one model is required")
    entries = {
        _validate_label(name, "models: model name"): _entry(
            name, value, root.schema_version
        )
        for name, value in models.items()
    }
    return entries, _default_name(root, entries)
