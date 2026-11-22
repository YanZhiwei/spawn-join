"""Behavioral tests for the standard-library FieldReader contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import FrozenInstanceError
from math import inf
from types import MappingProxyType

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


def test_string_tuple_preserves_values_order_and_duplicates() -> None:
    reader = FieldReader()
    values = ["", " text ", "same", "same"]
    assert reader.as_string_tuple(values, "args") == ("", " text ", "same", "same")
    assert values == ["", " text ", "same", "same"]
    assert reader.as_string_tuple([], "args", allow_empty=False) == ()
    assert reader.as_string_tuple([" "], "stop", allow_empty=False) == (" ",)


@pytest.mark.parametrize("value", [None, "secret-value", ("text",), {"text": "x"}])
def test_string_tuple_rejects_non_list_containers(value: object) -> None:
    with pytest.raises(ValueError) as caught:
        FieldReader().as_string_tuple(value, "args")
    assert str(caught.value) == "args: must be a list of strings"


@pytest.mark.parametrize("item", [None, 1, True, ["secret-value"], {"secret": "x"}])
@pytest.mark.parametrize("allow_empty", [True, False])
def test_string_tuple_uses_safe_indexed_element_errors(
    item: object, allow_empty: bool
) -> None:
    with pytest.raises(ValueError) as caught:
        FieldReader().as_string_tuple(["first", item], "args", allow_empty=allow_empty)
    expected = "a string" if allow_empty else "a non-empty string"
    assert str(caught.value) == f"args[1]: must be {expected}"


def test_string_tuple_keeps_the_callers_error_and_field_path_policies() -> None:
    class InputError(Exception):
        pass

    reader = FieldReader(InputError)
    with pytest.raises(InputError) as caught:
        reader.as_string_tuple(["first", ""], "stop", allow_empty=False)
    assert str(caught.value) == "stop[1]: must be a non-empty string"
    with pytest.raises(InputError) as caught:
        reader.as_string_tuple(["", 1], "args", indexed_errors=False)
    assert str(caught.value) == "args: must be a string"


def test_fields_copy_values_and_preserve_required_optional_contract() -> None:
    original = {"optional": None, "required": "value"}
    copied = FieldReader().as_fields(
        MappingProxyType(original),
        "config",
        required=frozenset({"required"}),
        optional=frozenset({"optional"}),
    )
    assert copied == original and list(copied) == ["optional", "required"]
    copied["required"] = "changed"
    assert original["required"] == "value"
    assert FieldReader().as_fields({}, "config") == {}


def test_fields_preserve_combined_sorted_errors_and_caller_factory() -> None:
    with pytest.raises(ReaderError) as caught:
        FieldReader(make_reader_error).as_fields(
            {"z": "private-value", "extra": 1},
            "config",
            required=frozenset({"beta", "alpha"}),
        )
    assert str(caught.value) == (
        "config: missing required field(s): alpha, beta; unknown field(s): extra, z"
    )


@pytest.mark.parametrize("value", [None, [], "private-value"])
def test_fields_validate_mapping_before_field_presence(value: object) -> None:
    with pytest.raises(ValueError) as caught:
        FieldReader().as_fields(value, "config", required=frozenset({"required"}))
    assert str(caught.value) == "config: must be a mapping"
    with pytest.raises(ValueError) as caught:
        FieldReader().as_fields({1: "private-value"}, "config")
    assert str(caught.value) == "config: keys must be strings"


def test_string_mapping_copies_mapping_without_normalizing_values() -> None:
    original = {"z": "", "a": " value "}
    copied = FieldReader().as_string_mapping(MappingProxyType(original), "headers")
    assert copied == original and list(copied) == ["z", "a"]
    copied["z"] = "changed"
    assert original["z"] == ""
    assert FieldReader().as_string_mapping({}, "headers") == {}


@pytest.mark.parametrize("value", [None, [], "private-value", 1])
def test_string_mapping_rejects_non_mapping_containers(value: object) -> None:
    with pytest.raises(ValueError) as caught:
        FieldReader().as_string_mapping(value, "headers")
    assert str(caught.value) == "headers: must be a mapping"


def test_string_mapping_validates_keys_before_values() -> None:
    with pytest.raises(ValueError) as caught:
        FieldReader().as_string_mapping({"private-key": 1, 2: "value"}, "headers")
    assert str(caught.value) == "headers: keys must be strings"


@pytest.mark.parametrize("value", [None, 1, True, ["private-value"]])
def test_string_mapping_uses_field_only_errors_and_caller_factory(
    value: object,
) -> None:
    with pytest.raises(ReaderError) as caught:
        FieldReader(make_reader_error).as_string_mapping({"private-key": value}, "env")
    assert str(caught.value) == "env: must be a string"
