"""Validated memory and skills context sources.

The package normalizes and validates the source lists, then forwards them to
DeepAgents. It never reads the sources itself: a source may live in a host-owned
or virtual backend.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .errors import ContextConfigurationError


def normalize_sources(sources: Sequence[str], label: str) -> tuple[str, ...]:
    """Return an immutable, non-empty, duplicate-free source tuple."""

    if isinstance(sources, str):
        raise ContextConfigurationError(
            f"{label}.sources: expected a sequence of paths, not a string"
        )
    normalized = tuple(sources)
    if not normalized:
        raise ContextConfigurationError(f"{label}.sources: must not be empty")
    seen: set[str] = set()
    for source in normalized:
        if not source.strip():
            raise ContextConfigurationError(
                f"{label}.sources: every source must be a non-blank string"
            )
        if source in seen:
            raise ContextConfigurationError(
                f"{label}.sources: duplicate source {source!r}"
            )
        seen.add(source)
    return normalized


@dataclass(frozen=True, slots=True)
class MemoryConfiguration:
    """Host-declared memory sources with optional prompt-cache control."""

    sources: Sequence[str]
    add_cache_control: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "sources",
            normalize_sources(self.sources, "memory"),
        )

    @property
    def source_count(self) -> int:
        return len(self.sources)


@dataclass(frozen=True, slots=True)
class SkillsConfiguration:
    """Host-declared skill sources forwarded to DeepAgents middleware."""

    sources: Sequence[str]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "sources",
            normalize_sources(self.sources, "skills"),
        )

    @property
    def source_count(self) -> int:
        return len(self.sources)
