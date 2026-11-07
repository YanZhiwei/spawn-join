"""Behavioral tests for the standard-library FieldReader contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import FrozenInstanceError
from math import inf

import pytest

from spawn_join_common import FieldReader


class ReaderError(Exception):
    """Error used to prove that construction belongs to the caller."""


def make_reader_error(message: str) -> Exception:
    return ReaderError(message)


def test_default_and_custom_error_factories() -> None:
    with pytest.raises(ValueError, match="value: must be a string"):
        FieldReader().as_str(42, "value")

    with pytest.raises(ReaderError, match="value: must be a string"):
        FieldReader(make_reader_error).as_str(42, "value")


def test_reader_is_frozen_and_slotted() -> None:
    reader = FieldReader()

    with pytest.raises(FrozenInstanceError):
        reader.__setattr__("error", make_reader_error)

    assert not hasattr(reader, "__dict__")


def test_mapping_is_copied_in_iteration_order_and_requires_string_keys() -> None:
    original: Mapping[object, object] = {"z": 1, "a": 2}
    copied = FieldReader().as_mapping(original, "settings")

    assert copied == {"z": 1, "a": 2}
    assert list(copied) == ["z", "a"]
    assert copied is not original
    copied["z"] = 99
    assert original["z"] == 1

    with pytest.raises(ValueError, match="settings: keys must be strings"):
        FieldReader().as_mapping({"ok": 1, 3: "bad"}, "settings")


def test_mapping_and_list_type_errors_include_their_paths() -> None:
    reader = FieldReader()

    with pytest.raises(ValueError, match="settings: must be a mapping"):
        reader.as_mapping([], "settings")
    with pytest.raises(ValueError, match="items: must be a list"):
        reader.as_list((1, 2), "items")

    items = [object(), None]
    assert reader.as_list(items, "items") is items


def test_required_and_unknown_fields_are_sorted_and_combined() -> None:
    reader = FieldReader()

    with pytest.raises(
        ValueError,
        match=(
            r"config: missing required field\(s\): beta; "
            r"unknown field\(s\): extra, mystery"
        ),
    ):
        reader.require_keys(
            {"alpha": 1, "extra": 2, "mystery": 3},
            required=frozenset({"beta", "alpha"}),
            optional=frozenset({"optional"}),
            path="config",
        )


def test_scalar_readers_are_strict_and_keep_checks_separate() -> None:
    reader = FieldReader()

    assert reader.as_str("text", "value") == "text"
    assert reader.as_int(-2, "count") == -2
    assert reader.as_number(-2, "ratio") == -2.0
    assert reader.as_number(inf, "ratio") == inf
    assert reader.as_non_negative_int(0, "count") == 0
    assert reader.as_non_negative_number(2, "ratio") == 2.0

    with pytest.raises(ValueError, match="count: must be an integer"):
        reader.as_int(True, "count")
    with pytest.raises(ValueError, match="count: must be an integer"):
        reader.as_int("2", "count")
    with pytest.raises(ValueError, match="ratio: must be a number"):
        reader.as_number(False, "ratio")
    with pytest.raises(ValueError, match="ratio: must be a number"):
        reader.as_number("2", "ratio")
    with pytest.raises(ValueError, match="count: must be a non-negative integer"):
        reader.as_non_negative_int(-1, "count")
    with pytest.raises(ValueError, match="ratio: must be finite and non-negative"):
        reader.as_non_negative_number(inf, "ratio")
    with pytest.raises(ValueError, match="ratio: must be finite and non-negative"):
        reader.as_non_negative_number(float("nan"), "ratio")
    with pytest.raises(ValueError, match="ratio: must be finite and non-negative"):
        reader.as_non_negative_number(-0.1, "ratio")


def test_boolean_reader_does_not_coerce_integers() -> None:
    reader = FieldReader()

    assert reader.as_bool(True, "enabled") is True
    with pytest.raises(ValueError, match="enabled: must be a boolean"):
        reader.as_bool(1, "enabled")


def test_optional_skips_only_missing_and_parses_present_null() -> None:
    reader = FieldReader()
    seen: list[tuple[object, str]] = []

    def parse(value: object, path: str) -> str:
        seen.append((value, path))
        return f"{path}:{value!s}"

    assert reader.optional({}, "value", parse, "config") is None
    assert seen == []
    assert (
        reader.optional({"value": None}, "value", parse, "config")
        == "config.value:None"
    )
    assert seen == [(None, "config.value")]
