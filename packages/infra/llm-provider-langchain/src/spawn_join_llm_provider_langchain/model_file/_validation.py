"""Private, path-aware validation for declarative model-file inputs."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, TypeVar, cast

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    ValidationInfo,
    model_validator,
)

from spawn_join_common import FieldReader
from spawn_join_common.validation import validate_with
from spawn_join_llm_provider import ConfigurationError

reader = FieldReader(ConfigurationError)


def input_path(info: ValidationInfo) -> str:
    """Read caller-owned context without exposing input values in errors."""
    context: object = info.context
    if isinstance(context, Mapping):
        path = cast("Mapping[str, object]", context).get("path")
        if isinstance(path, str):
            return path
    return "<root>"


def _field_path(info: ValidationInfo) -> str:
    path = input_path(info)
    return str(info.field_name) if path == "<root>" else f"{path}.{info.field_name}"


def _text(value: object, info: ValidationInfo) -> str:
    return reader.as_str(value, _field_path(info))


def _integer(value: object, info: ValidationInfo) -> int:
    return reader.as_int(value, _field_path(info))


def _number(value: object, info: ValidationInfo) -> float:
    return reader.as_number(value, _field_path(info))


def _boolean(value: object, info: ValidationInfo) -> bool:
    return reader.as_bool(value, _field_path(info))


def _string_tuple(value: object, info: ValidationInfo) -> tuple[str, ...]:
    path = _field_path(info)
    if not isinstance(value, list):
        raise ConfigurationError(f"{path}: must be a list of strings")
    items: list[str] = []
    for index, item in enumerate(cast("list[object]", value)):
        if not isinstance(item, str) or item == "":
            raise ConfigurationError(f"{path}[{index}]: must be a non-empty string")
        items.append(item)
    return tuple(items)


# Validators surround the nullable annotation: omitted defaults are allowed, but
# explicitly supplied null must pass the same strict reader as any other value.
Text = Annotated[str, BeforeValidator(_text)]
Integer = Annotated[int, BeforeValidator(_integer)]
OptionalText = Annotated[str | None, BeforeValidator(_text)]
OptionalInteger = Annotated[int | None, BeforeValidator(_integer)]
OptionalNumber = Annotated[float | None, BeforeValidator(_number)]
OptionalBoolean = Annotated[bool | None, BeforeValidator(_boolean)]
OptionalStrings = Annotated[tuple[str, ...] | None, BeforeValidator(_string_tuple)]


class FileInput(BaseModel):
    """Strict private wire shape; its field declarations own allowed keys."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    @model_validator(mode="before")
    @classmethod
    def _mapping(cls, value: object, info: ValidationInfo) -> dict[str, object]:
        fields = reader.as_mapping(value, input_path(info))
        required = frozenset(
            name for name, field in cls.model_fields.items() if field.is_required()
        )
        reader.require_keys(
            fields,
            required=required,
            optional=frozenset(cls.model_fields).difference(required),
            path=input_path(info),
        )
        return fields


InputT = TypeVar("InputT", bound=FileInput)


def validate_input(schema: type[InputT], value: object, path: str) -> InputT:
    """Validate one wire shape, preserving safe errors and foreign causes."""
    return validate_with(
        lambda: schema.model_validate(value, context={"path": path}),
        error=ConfigurationError,
        # Never render Pydantic's input, context, or arbitrary mapping keys.
        message=lambda _: f"{path}: invalid configuration",
    )
