"""Compatibility tests for the public protocol FieldReader entry point."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from spawn_join_common import FieldReader as CommonFieldReader
from spawn_join_llm_provider import ConfigurationError
from spawn_join_llm_provider.parsing import FieldReader


class ReaderError(Exception):
    """Caller-owned error type used to test factory injection."""


def test_default_error_remains_configuration_error() -> None:
    with pytest.raises(ConfigurationError, match="value: must be an integer"):
        FieldReader().as_int(True, "value")


def test_custom_error_factory_still_overrides_the_default() -> None:
    with pytest.raises(ReaderError, match="value: must be a boolean"):
        FieldReader(ReaderError).as_bool(1, "value")


def test_compatibility_reader_stays_frozen_and_slotted() -> None:
    reader = FieldReader()

    with pytest.raises(FrozenInstanceError):
        reader.__setattr__("error", ReaderError)

    assert not hasattr(reader, "__dict__")


def test_common_reader_default_is_not_the_protocol_error() -> None:
    with pytest.raises(ValueError) as error:
        CommonFieldReader().as_int("1", "value")

    assert not isinstance(error.value, ConfigurationError)


def test_inherited_optional_and_path_behavior_matches() -> None:
    reader = FieldReader()

    assert reader.optional({}, "value", reader.as_str, "config") is None
    with pytest.raises(ConfigurationError, match="config.value: must be a string"):
        reader.optional({"value": None}, "value", reader.as_str, "config")
