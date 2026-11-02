"""Instance-based registry for metadata sources."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from spawn_join_llm_provider import ConfigurationError

from ._source import (
    MetadataSource,
    SourceConfig,
    SourceInfo,
    SyncContext,
    SyncResult,
)


class SourceRegistry:
    """A process-local, explicitly populated source registry."""

    def __init__(self, sources: Iterable[MetadataSource] = ()) -> None:
        self._sources: dict[str, MetadataSource] = {}
        for source in sources:
            self.register(source)

    @classmethod
    def with_builtins(cls) -> SourceRegistry:
        """Create a registry containing the package's built-in sources."""
        from .sources import builtin_sources

        return cls(builtin_sources())

    def register(self, source: MetadataSource, *, replace: bool = False) -> None:
        """Register a source, rejecting duplicate IDs unless replaced."""
        info = source.info
        if info.id in self._sources and not replace:
            raise ConfigurationError(f"source {info.id!r} is already registered")
        self._sources[info.id] = source

    def get(self, source_id: str) -> MetadataSource:
        """Return one source or raise a clear error."""
        source = self._sources.get(source_id)
        if source is None:
            available = ", ".join(sorted(self._sources))
            raise ConfigurationError(
                f"unknown source {source_id!r}; available sources: {available}"
            )
        return source

    def list(self) -> tuple[SourceInfo, ...]:
        """Return source descriptions sorted by ID."""
        return tuple(
            self._sources[source_id].info for source_id in sorted(self._sources)
        )

    def sync(
        self,
        *,
        source_id: str,
        model_file: str | Path,
        output: str | Path,
        config: SourceConfig,
        context: SyncContext,
        apply: bool = False,
        check: bool = False,
    ) -> SyncResult:
        """Run one source sync through the shared runner."""
        from ._runner import run_sync

        return run_sync(
            source=self.get(source_id),
            model_file=Path(model_file),
            output=Path(output),
            config=config,
            context=context,
            apply=apply,
            check=check,
        )
