"""Shared strict readers for external LLM configuration and metadata."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from spawn_join_common.parsing import FieldReader as CommonFieldReader

from .errors import ConfigurationError


@dataclass(frozen=True, slots=True)
class FieldReader(CommonFieldReader):
    """Compatibility reader retaining the protocol package's default error."""

    error: Callable[[str], Exception] = ConfigurationError
