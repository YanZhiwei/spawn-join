"""models.dev catalog adapter."""

from __future__ import annotations

from http.client import InvalidURL

from spawn_join_llm_provider import ModelMetadata

from .._source import (
    Fetcher,
    ModelHostMetadata,
    SourceCatalog,
    SourceFetchError,
    SourceInfo,
    SourceRequest,
    SyncContext,
    UrllibFetcher,
)
from .._url import redact_url
from .models_dev_schema import ModelsDevCatalog, SourcePayloadError

__all__ = ["ModelsDevSource", "SourcePayloadError", "builtin_sources"]


class ModelsDevSource:
    """The built-in models.dev catalog source."""

    info = SourceInfo(
        id="models.dev",
        display_name="models.dev",
        homepage="https://models.dev",
        license="MIT",
        default_url="https://models.dev/catalog.json",
        requires_auth=False,
        min_models=100,
    )

    def __init__(
        self,
        *,
        fetcher: Fetcher | None = None,
    ) -> None:
        self._fetcher = UrllibFetcher() if fetcher is None else fetcher

    def fetch(self, context: SyncContext) -> bytes:
        url = context.url or self.info.default_url
        safe_url = redact_url(url)
        try:
            return self._fetcher(url, timeout=context.timeout_seconds)
        except SourceFetchError:
            raise
        except (OSError, InvalidURL) as exc:
            raise SourceFetchError(f"cannot fetch {safe_url}: {exc}") from exc

    def translate(
        self,
        payload: bytes,
        request: SourceRequest,
    ) -> SourceCatalog:
        catalog = ModelsDevCatalog.from_payload(payload)
        warnings: list[str] = []

        translated_models: dict[str, ModelMetadata] = {}
        for ref in request.refs:
            model = catalog.parse_model(ref, warnings)
            if model is not None:
                translated_models[ref] = model.to_shared(ref)

        translated_hosts: dict[str, dict[str, ModelHostMetadata]] = {}
        for host in request.hosts:
            model = catalog.parse_host(host.provider, host.model, warnings)
            if model is not None:
                translated_hosts.setdefault(host.provider, {})[host.model] = (
                    model.to_host(host.provider, host.model)
                )

        return SourceCatalog(
            models=translated_models,
            hosts=translated_hosts,
            total_models=catalog.total_models,
            total_providers=catalog.total_providers,
            unreferenced_models=catalog.unreferenced(set(translated_models)),
            warnings=tuple(warnings),
        )


def builtin_sources() -> tuple[ModelsDevSource, ...]:
    """Return the built-in source instances."""
    return (ModelsDevSource(),)
