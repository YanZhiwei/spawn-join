"""Runtime catalog object for validated model entries."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

from langchain_core.language_models import BaseChatModel

from spawn_join_llm_provider import ConfigurationError

from ._model_env import load_env_snapshot
from ._model_schema import CatalogEntry, parse_catalog
from .factory import create_chat_model as _create_chat_model


@dataclass(frozen=True, slots=True)
class ModelSummary:
    """A display-ready view of one catalog entry."""

    name: str
    model: str
    display_name: str


@dataclass(frozen=True, slots=True, repr=False)
class ModelCatalog:
    """An immutable set of validated model entries plus a default name."""

    _entries: Mapping[str, CatalogEntry] = field(repr=False)
    _default_name: str = field(repr=False)
    _env_file: Path | None = field(repr=False)
    _env_values: Mapping[str, str] = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_entries", MappingProxyType(dict(self._entries)))
        object.__setattr__(
            self, "_env_values", MappingProxyType(dict(self._env_values))
        )

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        *,
        env_file: str | Path | None = None,
    ) -> ModelCatalog:
        """Load and validate a catalog from an explicit YAML file."""
        entries, default_name = parse_catalog(path)
        referenced = {entry.api_key_env for entry in entries.values()}
        env_path, env_values = load_env_snapshot(env_file, referenced)
        return cls(
            _entries=entries,
            _default_name=default_name,
            _env_file=env_path,
            _env_values=env_values,
        )

    @property
    def models(self) -> tuple[ModelSummary, ...]:
        """Return display summaries in the order defined by the file."""
        return tuple(
            ModelSummary(
                name=entry.name,
                model=entry.config.model,
                display_name=entry.display_name,
            )
            for entry in self._entries.values()
        )

    @property
    def default_name(self) -> str:
        """Return the name used when no explicit model is requested."""
        return self._default_name

    def create_chat_model(
        self,
        name: str | None = None,
        *,
        environ: Mapping[str, str] | None = None,
    ) -> BaseChatModel:
        """Create a LangChain model for one entry, resolving its API key."""
        entry = self._resolve_entry(name)
        api_key = self._resolve_api_key(entry, environ)
        try:
            return _create_chat_model(
                entry.config, api_key=api_key, options=entry.options
            )
        except ConfigurationError as exc:
            raise ConfigurationError(f"models.{entry.name}: {exc}") from exc

    def __repr__(self) -> str:
        names = tuple(self._entries)
        return f"ModelCatalog(models={names!r}, default={self._default_name!r})"

    def _resolve_entry(self, name: str | None) -> CatalogEntry:
        selected = self._default_name if name is None else name
        entry = self._entries.get(selected)
        if entry is None:
            available = ", ".join(self._entries)
            raise ConfigurationError(
                f"Unknown model {selected!r}; available models: {available}"
            )
        return entry

    def _resolve_api_key(
        self,
        entry: CatalogEntry,
        environ: Mapping[str, str] | None,
    ) -> str:
        source = os.environ if environ is None else environ
        value = source.get(entry.api_key_env)
        if value is None:
            value = self._env_values.get(entry.api_key_env)
        if value is None:
            location = "the environment"
            if self._env_file is not None:
                location = f"the environment or {self._env_file}"
            raise ConfigurationError(
                f"models.{entry.name}.api_key_env: {entry.api_key_env} is not "
                f"set in {location}"
            )
        if not value.strip():
            raise ConfigurationError(
                f"models.{entry.name}.api_key_env: {entry.api_key_env} is empty"
            )
        return value
