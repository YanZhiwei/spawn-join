"""models.dev catalog adapter."""

from __future__ import annotations

import json
from datetime import date
from typing import cast

from spawn_join_llm_provider import (
    Modality,
    ModelCapabilitiesMetadata,
    ModelLimits,
    ModelMetadata,
    ModelMetadataOverride,
    ModelModalities,
    ModelPriceRate,
    ModelPriceTier,
    ModelPricing,
    ModelReasoning,
    ModelReasoningBudget,
    ModelType,
    PriceDirection,
    PriceUnit,
)

from .._snapshot import status_or_active
from .._source import (
    Fetcher,
    ModelHostMetadata,
    SourceCatalog,
    SourceFetchError,
    SourceInfo,
    SourceRequest,
    SyncContext,
    SyncError,
    UrllibFetcher,
)


class SourcePayloadError(SyncError):
    """The source response was malformed or did not match the expected shape."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SourcePayloadError(f"duplicate key {key!r} in source payload")
        result[key] = value
    return result


def _mapping(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise SourcePayloadError(f"{path}: must be a mapping")
    return cast("dict[str, object]", value)


def _list(value: object, path: str) -> list[object]:
    if not isinstance(value, list):
        raise SourcePayloadError(f"{path}: must be a list")
    return cast("list[object]", value)


def _str(value: object, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourcePayloadError(f"{path}: must be a non-empty string")
    return value


def _number(value: object, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SourcePayloadError(f"{path}: must be a number")
    number = float(value)
    if number < 0:
        raise SourcePayloadError(f"{path}: must be non-negative")
    return number


def _int(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SourcePayloadError(f"{path}: must be a non-negative integer")
    return value


def _bool(value: object, path: str) -> bool:
    if not isinstance(value, bool):
        raise SourcePayloadError(f"{path}: must be a boolean")
    return value


def _date(value: object, path: str) -> date | None:
    if value is None:
        return None
    text = _str(value, path)
    if len(text) == 7:
        text = f"{text}-01"
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _modalities(value: object, path: str, warnings: list[str]) -> ModelModalities:
    fields = _mapping(value, path)
    input_values = _modality_list(fields.get("input"), f"{path}.input", warnings)
    output_values = _modality_list(fields.get("output"), f"{path}.output", warnings)
    if not input_values:
        warnings.append(f"{path}.input: no recognized modalities; using text")
        input_values = (Modality.TEXT,)
    return ModelModalities(input=input_values, output=output_values)


def _modality_list(
    value: object,
    path: str,
    warnings: list[str],
) -> tuple[Modality, ...]:
    if value is None:
        return ()
    result: list[Modality] = []
    for index, item in enumerate(_list(value, path)):
        raw = _str(item, f"{path}[{index}]")
        if raw == "file":
            raw = "pdf"
        try:
            modality = Modality(raw)
        except ValueError:
            warnings.append(f"{path}[{index}]: unknown modality {raw!r}")
            continue
        if modality not in result:
            result.append(modality)
    return tuple(result)


def _reasoning(
    raw: dict[str, object],
    path: str,
    warnings: list[str],
) -> ModelReasoning:
    supported = bool(raw.get("reasoning", False))
    options = raw.get("reasoning_options")
    if not supported:
        return ModelReasoning(supported=False)
    toggle: bool | None = None
    efforts: list[str] = []
    budget: ModelReasoningBudget | None = None
    if options is not None:
        for index, item in enumerate(_list(options, f"{path}.reasoning_options")):
            option = _mapping(item, f"{path}.reasoning_options[{index}]")
            kind = _str(option.get("type"), f"{path}.reasoning_options[{index}].type")
            if kind == "effort":
                values = _list(
                    option.get("values"),
                    f"{path}.reasoning_options[{index}].values",
                )
                for value_index, value in enumerate(values):
                    effort = _str(
                        value,
                        f"{path}.reasoning_options[{index}].values[{value_index}]",
                    )
                    if effort not in efforts:
                        efforts.append(effort)
            elif kind == "toggle":
                toggle = True
            elif kind == "budget_tokens":
                minimum = _optional_int(
                    option.get("min"),
                    f"{path}.reasoning_options[{index}].min",
                )
                maximum = _optional_int(
                    option.get("max"),
                    f"{path}.reasoning_options[{index}].max",
                )
                if minimum is not None or maximum is not None:
                    budget = ModelReasoningBudget(
                        min_tokens=minimum,
                        max_tokens=maximum,
                    )
            else:
                warnings.append(
                    f"{path}.reasoning_options[{index}]: unknown type {kind!r}"
                )
    return ModelReasoning(
        supported=True,
        toggle=toggle,
        efforts=tuple(efforts),
        budget_tokens=budget,
    )


def _optional_int(value: object, path: str) -> int | None:
    if value is None:
        return None
    return _int(value, path)


def _capabilities(
    raw: dict[str, object],
    path: str,
    warnings: list[str],
) -> ModelCapabilitiesMetadata:
    return ModelCapabilitiesMetadata(
        reasoning=_reasoning(raw, path, warnings),
        tools=_optional_bool(raw.get("tool_call"), f"{path}.tool_call"),
        structured_output=_optional_bool(
            raw.get("structured_output"), f"{path}.structured_output"
        ),
        temperature=_optional_bool(raw.get("temperature"), f"{path}.temperature"),
        attachment=_optional_bool(raw.get("attachment"), f"{path}.attachment"),
    )


def _optional_bool(value: object, path: str) -> bool | None:
    if value is None:
        return None
    return _bool(value, path)


def _limits(
    raw: dict[str, object],
    path: str,
) -> ModelLimits:
    limit = raw.get("limit")
    if limit is None:
        return ModelLimits()
    fields = _mapping(limit, f"{path}.limit")
    return ModelLimits(
        context=_optional_int(fields.get("context"), f"{path}.limit.context"),
        input=_optional_int(fields.get("input"), f"{path}.limit.input"),
        output=_optional_int(fields.get("output"), f"{path}.limit.output"),
    )


def _pricing(
    raw: dict[str, object],
    path: str,
) -> ModelPricing | None:
    cost = raw.get("cost")
    if cost is None:
        return None
    fields = _mapping(cost, f"{path}.cost")
    rates: list[ModelPriceRate] = []
    text_fields = {
        "input": PriceDirection.INPUT,
        "output": PriceDirection.OUTPUT,
        "cache_read": PriceDirection.CACHE_READ,
        "cache_write": PriceDirection.CACHE_WRITE,
        "reasoning": PriceDirection.REASONING,
    }
    for name, direction in text_fields.items():
        if name in fields:
            rates.append(
                ModelPriceRate(
                    modality=Modality.TEXT,
                    direction=direction,
                    unit=PriceUnit.PER_MILLION_TOKENS,
                    amount=_number(fields[name], f"{path}.cost.{name}"),
                )
            )
    audio_fields = {
        "input_audio": PriceDirection.INPUT,
        "output_audio": PriceDirection.OUTPUT,
    }
    for name, direction in audio_fields.items():
        if name in fields:
            rates.append(
                ModelPriceRate(
                    modality=Modality.AUDIO,
                    direction=direction,
                    unit=PriceUnit.PER_MILLION_TOKENS,
                    amount=_number(fields[name], f"{path}.cost.{name}"),
                )
            )
    if not rates:
        return None
    pricing = ModelPricing(currency="USD", rates=tuple(rates))
    tiers = fields.get("tiers")
    if tiers is not None:
        tier_rates: list[ModelPriceTier] = []
        for index, item in enumerate(_list(tiers, f"{path}.cost.tiers")):
            tier_fields = _mapping(item, f"{path}.cost.tiers[{index}]")
            threshold = _int(
                tier_fields.get("min_input_tokens"),
                f"{path}.cost.tiers[{index}].min_input_tokens",
            )
            tier_rates.append(
                ModelPriceTier(
                    min_input_tokens=threshold,
                    rates=tuple(
                        ModelPriceRate(
                            modality=Modality.TEXT,
                            direction=direction,
                            unit=PriceUnit.PER_MILLION_TOKENS,
                            amount=_number(
                                tier_fields[name],
                                f"{path}.cost.tiers[{index}].{name}",
                            ),
                        )
                        for name, direction in text_fields.items()
                        if name in tier_fields
                    ),
                )
            )
        if tier_rates:
            pricing = ModelPricing(
                currency=pricing.currency,
                rates=pricing.rates,
                tiers=tuple(tier_rates),
            )
    return pricing


def _type_for(raw: dict[str, object], modalities: ModelModalities) -> ModelType:
    raw_type = raw.get("type")
    if isinstance(raw_type, str):
        try:
            return ModelType(raw_type)
        except ValueError:
            pass
    if not modalities.output:
        return ModelType.EMBEDDING
    return ModelType.CHAT


def _model_from_raw(
    ref: str,
    raw: dict[str, object],
    path: str,
    warnings: list[str],
) -> ModelMetadata:
    modalities = _modalities(raw.get("modalities"), f"{path}.modalities", warnings)
    return ModelMetadata(
        key=ref,
        name=_str(raw.get("name"), f"{path}.name"),
        type=_type_for(raw, modalities),
        modalities=modalities,
        capabilities=_capabilities(raw, path, warnings),
        limits=_limits(raw, path),
        status=status_or_active(_optional_str(raw.get("status"), f"{path}.status")),
        description=_optional_str(raw.get("description"), f"{path}.description"),
        family=_optional_str(raw.get("family"), f"{path}.family"),
        license=_optional_str(raw.get("license"), f"{path}.license"),
        open_weights=_optional_bool(raw.get("open_weights"), f"{path}.open_weights"),
        interleaved=_interleaved(raw.get("interleaved"), f"{path}.interleaved"),
        release_date=_date(raw.get("release_date"), f"{path}.release_date"),
        knowledge=_optional_str(raw.get("knowledge"), f"{path}.knowledge"),
        last_updated=_date(raw.get("last_updated"), f"{path}.last_updated"),
    )


def _optional_str(value: object, path: str) -> str | None:
    if value is None:
        return None
    return _str(value, path)


def _interleaved(value: object, path: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    fields = _mapping(value, path)
    field = fields.get("field")
    return None if field is None else _str(field, f"{path}.field")


def _host_from_raw(
    provider: str,
    model: str,
    raw: dict[str, object],
    path: str,
    warnings: list[str],
) -> ModelHostMetadata:
    canonical = raw.get("canonical_model_id")
    canonical_model = (
        _str(canonical, f"{path}.canonical_model_id")
        if canonical is not None
        else f"{provider}/{model}"
    )
    status_text = _optional_str(raw.get("status"), f"{path}.status")
    override = ModelMetadataOverride(
        pricing=_pricing(raw, path),
        limits=_limits(raw, path),
        capabilities=_capabilities(raw, path, warnings),
        status=None if status_text is None else status_or_active(status_text),
    )
    return ModelHostMetadata(
        canonical_model=canonical_model,
        override=override,
    )


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
        url: str | None = None,
    ) -> None:
        self._fetcher = UrllibFetcher() if fetcher is None else fetcher
        self._url = url

    def fetch(self, context: SyncContext) -> bytes:
        url = context.url or self._url or self.info.default_url
        try:
            return self._fetcher(url, timeout=context.timeout_seconds)
        except SourceFetchError:
            raise
        except OSError as exc:
            raise SourceFetchError(f"cannot fetch {url}: {exc}") from exc

    def translate(
        self,
        payload: bytes,
        request: SourceRequest,
    ) -> SourceCatalog:
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SourcePayloadError("source payload is not valid UTF-8") from exc
        try:
            raw = json.loads(text, object_pairs_hook=_unique_object)
        except json.JSONDecodeError as exc:
            raise SourcePayloadError(
                f"source payload is not valid JSON at line {exc.lineno}, "
                f"column {exc.colno}"
            ) from exc
        root = _mapping(raw, "<catalog>")
        providers = _mapping(root.get("providers"), "providers")
        models = _mapping(root.get("models"), "models")
        warnings: list[str] = []

        translated_models: dict[str, ModelMetadata] = {}
        for ref in request.refs:
            raw_model = models.get(ref)
            if raw_model is None:
                continue
            translated_models[ref] = _model_from_raw(
                ref,
                _mapping(raw_model, f"models.{ref}"),
                f"models.{ref}",
                warnings,
            )

        translated_hosts: dict[str, dict[str, ModelHostMetadata]] = {}
        for host in request.hosts:
            provider_raw = providers.get(host.provider)
            if provider_raw is None:
                continue
            provider_fields = _mapping(
                provider_raw,
                f"providers.{host.provider}",
            )
            provider_models = _mapping(
                provider_fields.get("models"),
                f"providers.{host.provider}.models",
            )
            raw_model = provider_models.get(host.model)
            if raw_model is None:
                continue
            translated_hosts.setdefault(host.provider, {})[host.model] = _host_from_raw(
                host.provider,
                host.model,
                _mapping(
                    raw_model,
                    f"providers.{host.provider}.models.{host.model}",
                ),
                f"providers.{host.provider}.models.{host.model}",
                warnings,
            )

        return SourceCatalog(
            models=translated_models,
            hosts=translated_hosts,
            total_models=len(models),
            total_providers=len(providers),
            warnings=tuple(warnings),
        )


def builtin_sources() -> tuple[ModelsDevSource, ...]:
    """Return the built-in source instances."""
    return (ModelsDevSource(),)


__all__ = ["ModelsDevSource", "builtin_sources"]
