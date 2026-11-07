"""Optional Pydantic validation-error conversion."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from pydantic import ValidationError

_T = TypeVar("_T")

__all__ = ["validate_with"]


def validate_with(
    operation: Callable[[], _T],
    *,
    error: Callable[[str], Exception],
    message: Callable[[ValidationError], str],
) -> _T:
    """Run an operation and convert only Pydantic validation failures."""
    try:
        return operation()
    except ValidationError as exc:
        raise error(message(exc)) from exc
