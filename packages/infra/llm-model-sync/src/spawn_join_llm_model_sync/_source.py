"""Metadata source contract and sync result types."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from http.client import InvalidURL
from math import isfinite
from pathlib import Path
from types import MappingProxyType
from typing import Protocol, runtime_checkable
from urllib.error import URLError
from urllib.request import Request, urlopen

from spawn_join_llm_provider import (
    ConfigurationError,
    ModelMetadata,
    ModelMetadataOverride,
)

from ._url import redact_url, validate_source_url

_SOURCE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_USER_AGENT = "spawn-join-model-sync/0.1"


class SyncError(Exception):
    """A sync failure that maps to CLI exit code 3."""


class SourceFetchError(SyncError):
    """A source could not be fetched."""


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceInfo:
    """Stable description of a metadata source."""

    id: str
    display_name: str
    homepage: str
    license: str
    default_url: str
    requires_auth: bool = False
    min_models: int = 1

    def __post_init__(self) -> None:
        if _SOURCE_ID.fullmatch(self.id) is None:
            raise ConfigurationError("source id must match [a-z0-9][a-z0-9._-]*")
        for name in ("display_name", "homepage", "license", "default_url"):
            value = getattr(self, name)
            if not value or not value.strip():
                raise ConfigurationError(f"source {name} must not be empty")
        object.__setattr__(
            self,
            "default_url",
            validate_source_url(self.default_url),
        )
        if self.min_models <= 0:
            raise ConfigurationError("source min_models must be positive")


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceConfig:
    """Per-run source configuration."""

    url: str | None = None
    timeout_seconds: float = 30.0
    min_models: int | None = None

    def __post_init__(self) -> None:
        if not isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ConfigurationError("source timeout_seconds must be positive")
        if self.min_models is not None and self.min_models <= 0:
            raise ConfigurationError("source min_models must be positive")
        if self.url is not None:
            object.__setattr__(self, "url", validate_source_url(self.url))


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceHostRef:
    """A provider/model coordinate inside a source."""

    provider: str
    model: str

    def __post_init__(self) -> None:
        for name in ("provider", "model"):
            value = getattr(self, name)
            if not value or not value.strip():
                raise ConfigurationError(f"source host {name} must not be empty")


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceRequest:
    """The canonical refs and host coordinates needed by one sync."""

    refs: tuple[str, ...]
    hosts: tuple[SourceHostRef, ...] = ()

    def __post_init__(self) -> None:
        normalized_refs: list[str] = []
        for ref in self.refs:
            if not ref or not ref.strip() or "/" not in ref:
                raise ConfigurationError("source ref must use <lab>/<model>")
            if ref not in normalized_refs:
                normalized_refs.append(ref)
        normalized_hosts: list[SourceHostRef] = []
        for host in self.hosts:
            if host not in normalized_hosts:
                normalized_hosts.append(host)
        object.__setattr__(self, "refs", tuple(normalized_refs))
        object.__setattr__(self, "hosts", tuple(normalized_hosts))


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelHostMetadata:
    """One provider/model row translated into canonical metadata."""

    canonical_model: str
    override: ModelMetadataOverride
    canonical_model_inferred: bool = False

    def __post_init__(self) -> None:
        if not self.canonical_model or "/" not in self.canonical_model:
            raise ConfigurationError("host canonical_model must use <lab>/<model>")


@dataclass(frozen=True, slots=True, kw_only=True)
class SourceCatalog:
    """The requested portion of one upstream catalog."""

    models: Mapping[str, ModelMetadata]
    hosts: Mapping[str, Mapping[str, ModelHostMetadata]]
    total_models: int
    total_providers: int
    unreferenced_models: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.total_models < 0 or self.total_providers < 0:
            raise ConfigurationError("source catalog counts must be non-negative")
        for key, model in self.models.items():
            if key != model.key:
                raise ConfigurationError("source models key must match model key")
        unreferenced = tuple(sorted(set(self.unreferenced_models)))
        for ref in unreferenced:
            if not ref or not ref.strip():
                raise ConfigurationError("unreferenced source models must not be empty")
        if len(unreferenced) > self.total_models:
            raise ConfigurationError(
                "unreferenced source models must not exceed total_models"
            )
        hosts: dict[str, Mapping[str, ModelHostMetadata]] = {}
        for provider, models in self.hosts.items():
            if not provider or not provider.strip():
                raise ConfigurationError("source host provider must not be empty")
            hosts[provider] = MappingProxyType(dict(models))
        object.__setattr__(self, "models", MappingProxyType(dict(self.models)))
        object.__setattr__(self, "hosts", MappingProxyType(hosts))
        object.__setattr__(self, "unreferenced_models", unreferenced)


def _empty_environ() -> dict[str, str]:
    return {}


@dataclass(frozen=True, slots=True, kw_only=True)
class SyncContext:
    """Runtime context passed to a source fetch."""

    cache_dir: Path
    timeout_seconds: float = 30.0
    environ: Mapping[str, str] = field(default_factory=_empty_environ)
    url: str | None = None

    def __post_init__(self) -> None:
        if not isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ConfigurationError("sync timeout_seconds must be positive")
        if self.url is not None:
            object.__setattr__(self, "url", validate_source_url(self.url))
        object.__setattr__(self, "environ", MappingProxyType(dict(self.environ)))


@dataclass(frozen=True, slots=True, kw_only=True)
class SyncResult:
    """The observable outcome of one sync run."""

    source_id: str
    changed: bool
    written: bool
    output_path: Path
    matched: tuple[str, ...]
    unmatched: tuple[str, ...]
    ignored_models: int
    warnings: tuple[str, ...]
    exit_code: int
    report_path: Path | None = None
    ignored_model_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.exit_code not in {0, 1, 2, 3}:
            raise ConfigurationError("sync exit_code must be 0, 1, 2, or 3")
        if self.ignored_models < 0:
            raise ConfigurationError("sync ignored_models must be non-negative")
        for ref in self.ignored_model_ids:
            if not ref or not ref.strip():
                raise ConfigurationError("sync ignored_model_ids must not be empty")


class Fetcher(Protocol):
    """Minimal HTTP fetch contract for source adapters and tests."""

    def __call__(self, url: str, *, timeout: float) -> bytes: ...


class UrllibFetcher:
    """Default fetcher using the Python standard library."""

    def __call__(self, url: str, *, timeout: float) -> bytes:
        safe_url = redact_url(url)
        try:
            validate_source_url(url)
        except ConfigurationError as exc:
            raise SourceFetchError(f"invalid source URL: {exc}") from exc
        request = Request(url, headers={"User-Agent": _USER_AGENT})
        try:
            with urlopen(request, timeout=timeout) as response:  # noqa: S310
                return response.read()
        except (URLError, OSError, InvalidURL) as exc:
            raise SourceFetchError(f"cannot fetch {safe_url}: {exc}") from exc


@runtime_checkable
class MetadataSource(Protocol):
    """A source that fetches raw bytes and translates requested records."""

    info: SourceInfo

    def fetch(self, context: SyncContext) -> bytes:
        """Fetch the raw upstream payload."""
        ...

    def translate(
        self,
        payload: bytes,
        request: SourceRequest,
    ) -> SourceCatalog:
        """Translate only the requested refs and hosts."""
        ...
