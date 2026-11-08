"""Shared strict readers for untrusted, domain-independent input."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from math import isfinite
from typing import NoReturn, TypeVar, cast

_T = TypeVar("_T")


@dataclass(frozen=True, slots=True)
class FieldReader:
    """Read untrusted mappings and scalars with a caller-owned error type."""

    error: Callable[[str], Exception] = ValueError

    def fail(self, message: str) -> NoReturn:
        raise self.error(message)

    def as_mapping(self, value: object, path: str) -> dict[str, object]:
        if not isinstance(value, Mapping):
            self.fail(f"{path}: must be a mapping")
        result: dict[str, object] = {}
        for key, item in cast("Mapping[object, object]", value).items():
            if not isinstance(key, str):
                self.fail(f"{path}: keys must be strings")
            result[key] = item
        return result

    def require_keys(
        self,
        mapping: Mapping[str, object],
        *,
        required: frozenset[str],
        optional: frozenset[str],
        path: str,
    ) -> None:
        missing = required.difference(mapping)
        unknown = set(mapping).difference(required, optional)
        problems: list[str] = []
        if missing:
            problems.append(f"missing required field(s): {', '.join(sorted(missing))}")
        if unknown:
            problems.append(f"unknown field(s): {', '.join(sorted(unknown))}")
        if problems:
            self.fail(f"{path}: {'; '.join(problems)}")

    def as_str(self, value: object, path: str) -> str:
        if not isinstance(value, str):
            self.fail(f"{path}: must be a string")
        return value

    def as_int(self, value: object, path: str) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            self.fail(f"{path}: must be an integer")
        return value

    def as_non_negative_int(self, value: object, path: str) -> int:
        number = self.as_int(value, path)
        if number < 0:
            self.fail(f"{path}: must be a non-negative integer")
        return number

    def as_number(self, value: object, path: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            self.fail(f"{path}: must be a number")
        return float(value)

    def as_non_negative_number(self, value: object, path: str) -> float:
        number = self.as_number(value, path)
        if not isfinite(number) or number < 0:
            self.fail(f"{path}: must be finite and non-negative")
        return number

    def as_bool(self, value: object, path: str) -> bool:
        if not isinstance(value, bool):
            self.fail(f"{path}: must be a boolean")
        return value

    def as_list(self, value: object, path: str) -> list[object]:
        if not isinstance(value, list):
            self.fail(f"{path}: must be a list")
        return cast("list[object]", value)

    def optional(
        self,
        fields: Mapping[str, object],
        name: str,
        parser: Callable[[object, str], _T],
        path: str,
    ) -> _T | None:
        if name not in fields:
            return None
        return parser(fields[name], f"{path}.{name}")
