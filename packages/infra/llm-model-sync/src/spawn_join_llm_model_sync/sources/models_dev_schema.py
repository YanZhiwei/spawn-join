"""Typed models.dev catalog payload, kept separate from canonical metadata."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from types import MappingProxyType

from spawn_join_llm_model_sync._snapshot import status_or_active

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
from spawn_join_llm_provider.parsing import FieldReader

from .._source import ModelHostMetadata, SyncError


class SourcePayloadError(SyncError):
    """The source response was malformed or did not match the expected shape."""


_READER = FieldReader(SourcePayloadError)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SourcePayloadError(f"duplicate key {key!r} in source payload")
        result[key] = value
    return result


@dataclass(frozen=True, slots=True)
class ModelsDevProvider:
    """The provider envelope; model rows stay raw until requested."""

    models: Mapping[str, object]

    @classmethod
    def from_mapping(cls, value: object, path: str) -> ModelsDevProvider:
        fields = _READER.as_mapping(value, path)
        models = _READER.as_mapping(fields.get("models"), f"{path}.models")
        return cls(models=MappingProxyType(models))


@dataclass(frozen=True, slots=True)
class ModelsDevModel:
    """One requested models.dev model row, parsed into canonical value types."""

    path: str
    name: str | None
    raw_type: str | None
    modalities: ModelModalities | None
    capabilities: ModelCapabilitiesMetadata | None
    limits: ModelLimits | None
    pricing: ModelPricing | None
    status: str | None
    canonical_model_id: str | None
    description: str | None
    family: str | None
    license: str | None
    open_weights: bool | None
    interleaved: str | None
    release_date: date | None
    knowledge: str | None
    last_updated: date | None

    @classmethod
    def from_mapping(
        cls,
        value: object,
        path: str,
        warnings: list[str],
    ) -> ModelsDevModel:
        fields = _READER.as_mapping(value, path)
        return cls(
            path=path,
            name=_optional_str(fields, "name", path),
            raw_type=_optional_str(fields, "type", path),
            modalities=_optional_modalities(fields, path, warnings),
            capabilities=_capabilities(fields, path, warnings),
            limits=_limits(fields, path),
            pricing=_pricing(fields, path, warnings),
            status=_optional_str(fields, "status", path),
            canonical_model_id=_optional_str(fields, "canonical_model_id", path),
            description=_optional_str(fields, "description", path),
            family=_optional_str(fields, "family", path),
            license=_optional_str(fields, "license", path),
            open_weights=_optional_bool(fields, "open_weights", path),
            interleaved=_interleaved(fields, path),
            release_date=_optional_date(fields, "release_date", path),
            knowledge=_optional_str(fields, "knowledge", path),
            last_updated=_optional_date(fields, "last_updated", path),
        )

    def to_shared(self, ref: str) -> ModelMetadata:
        if self.name is None:
            raise SourcePayloadError(f"{self.path}.name: must not be empty")
        if self.modalities is None:
            raise SourcePayloadError(f"{self.path}.modalities: must be a mapping")
        model_type = _model_type(self.raw_type, self.modalities)
        return ModelMetadata(
            key=ref,
            name=self.name,
            type=model_type,
            modalities=self.modalities,
            capabilities=self.capabilities or ModelCapabilitiesMetadata(),
            limits=self.limits or ModelLimits(),
            pricing=self.pricing,
            status=status_or_active(self.status),
            description=self.description,
            family=self.family,
            license=self.license,
            open_weights=self.open_weights,
            interleaved=self.interleaved,
            release_date=self.release_date,
            knowledge=self.knowledge,
            last_updated=self.last_updated,
        )

    def to_host(self, provider: str, model: str) -> ModelHostMetadata:
        canonical = self.canonical_model_id
        return ModelHostMetadata(
            canonical_model=(
                canonical if canonical is not None else f"{provider}/{model}"
            ),
            override=ModelMetadataOverride(
                pricing=self.pricing,
                limits=self.limits,
                capabilities=self.capabilities,
                modalities=self.modalities,
                status=None if self.status is None else status_or_active(self.status),
            ),
            canonical_model_inferred=self.canonical_model_id is None,
        )


@dataclass(frozen=True, slots=True)
class ModelsDevCatalog:
    """The requested portion of a models.dev catalog."""

    providers: Mapping[str, ModelsDevProvider]
    models: Mapping[str, object]

    @classmethod
    def from_payload(cls, payload: bytes) -> ModelsDevCatalog:
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
        return cls.from_mapping(raw)

    @classmethod
    def from_mapping(cls, value: object) -> ModelsDevCatalog:
        root = _READER.as_mapping(value, "<catalog>")
        providers_raw = _READER.as_mapping(root.get("providers"), "providers")
        models_raw = _READER.as_mapping(root.get("models"), "models")
        providers = {
            provider_id: ModelsDevProvider.from_mapping(
                provider_value,
                f"providers.{provider_id}",
            )
            for provider_id, provider_value in providers_raw.items()
        }
        return cls(
            providers=MappingProxyType(providers),
            models=MappingProxyType(models_raw),
        )

    @property
    def total_models(self) -> int:
        return len(self.models)

    @property
    def total_providers(self) -> int:
        return len(self.providers)

    def parse_model(self, ref: str, warnings: list[str]) -> ModelsDevModel | None:
        raw = self.models.get(ref)
        if raw is None:
            return None
        return ModelsDevModel.from_mapping(raw, f"models.{ref}", warnings)

    def parse_host(
        self,
        provider_id: str,
        model_id: str,
        warnings: list[str],
    ) -> ModelsDevModel | None:
        provider = self.providers.get(provider_id)
        if provider is None:
            return None
        raw = provider.models.get(model_id)
        if raw is None:
            return None
        return ModelsDevModel.from_mapping(
            raw,
            f"providers.{provider_id}.models.{model_id}",
            warnings,
        )

    def unreferenced(self, translated: set[str]) -> tuple[str, ...]:
        return tuple(sorted(set(self.models).difference(translated)))


def _optional_str(
    fields: Mapping[str, object],
    name: str,
    path: str,
) -> str | None:
    if name not in fields or fields[name] is None:
        return None
    value = _READER.as_str(fields[name], f"{path}.{name}")
    if not value.strip():
        raise SourcePayloadError(f"{path}.{name}: must not be empty")
    return value


def _optional_bool(
    fields: Mapping[str, object],
    name: str,
    path: str,
) -> bool | None:
    if name not in fields or fields[name] is None:
        return None
    return _READER.as_bool(fields[name], f"{path}.{name}")


def _optional_date(
    fields: Mapping[str, object],
    name: str,
    path: str,
) -> date | None:
    text = _optional_str(fields, name, path)
    if text is None:
        return None
    normalized = f"{text}-01" if len(text) == 7 else text
    try:
        return date.fromisoformat(normalized)
    except ValueError:
        return None


def _interleaved(fields: Mapping[str, object], path: str) -> str | None:
    value = fields.get("interleaved")
    if value is None:
        return None
    if isinstance(value, str):
        return value
    mapped = _READER.as_mapping(value, f"{path}.interleaved")
    return _optional_str(mapped, "field", f"{path}.interleaved")


def _modalities(
    value: object,
    path: str,
    warnings: list[str],
) -> ModelModalities:
    fields = _READER.as_mapping(value, path)
    input_values = _modality_list(fields.get("input"), f"{path}.input", warnings)
    output_values = _modality_list(fields.get("output"), f"{path}.output", warnings)
    if not input_values:
        warnings.append(f"{path}.input: no recognized modalities; using text")
        input_values = (Modality.TEXT,)
    return ModelModalities(input=input_values, output=output_values)


def _optional_modalities(
    fields: Mapping[str, object],
    path: str,
    warnings: list[str],
) -> ModelModalities | None:
    if "modalities" not in fields or fields["modalities"] is None:
        return None
    return _modalities(fields["modalities"], f"{path}.modalities", warnings)


def _modality_list(
    value: object,
    path: str,
    warnings: list[str],
) -> tuple[Modality, ...]:
    if value is None:
        return ()
    result: list[Modality] = []
    for index, item in enumerate(_READER.as_list(value, path)):
        raw = _READER.as_str(item, f"{path}[{index}]")
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
    fields: Mapping[str, object],
    path: str,
    warnings: list[str],
) -> ModelReasoning | None:
    if "reasoning" not in fields or fields["reasoning"] is None:
        if "reasoning_options" in fields:
            warnings.append(
                f"{path}.reasoning_options: ignored because reasoning is absent"
            )
        return None
    supported = _READER.as_bool(fields["reasoning"], f"{path}.reasoning")
    options = fields.get("reasoning_options")
    if not supported:
        if options is not None:
            warnings.append(
                f"{path}.reasoning_options: ignored because reasoning is false"
            )
        return ModelReasoning(supported=False)
    if options is None:
        return ModelReasoning(supported=True)
    return _parse_reasoning_options(options, path, warnings)


def _parse_reasoning_options(
    options: object,
    path: str,
    warnings: list[str],
) -> ModelReasoning:
    toggle: bool | None = None
    efforts: list[str] = []
    budget: ModelReasoningBudget | None = None
    option_path = f"{path}.reasoning_options"
    for index, item in enumerate(_READER.as_list(options, option_path)):
        option = _READER.as_mapping(item, f"{option_path}[{index}]")
        kind = _READER.as_str(
            option.get("type"),
            f"{option_path}[{index}].type",
        )
        if kind == "effort":
            values = _READER.as_list(
                option.get("values"),
                f"{option_path}[{index}].values",
            )
            for value_index, effort_value in enumerate(values):
                effort = _READER.as_str(
                    effort_value,
                    f"{option_path}[{index}].values[{value_index}]",
                )
                if effort not in efforts:
                    efforts.append(effort)
        elif kind == "toggle":
            toggle = True
        elif kind == "budget_tokens":
            minimum = _optional_int(
                option.get("min"),
                f"{option_path}[{index}].min",
            )
            maximum = _optional_int(
                option.get("max"),
                f"{option_path}[{index}].max",
            )
            if minimum is not None or maximum is not None:
                budget = ModelReasoningBudget(min_tokens=minimum, max_tokens=maximum)
        else:
            warnings.append(f"{option_path}[{index}]: unknown type {kind!r}")
    return ModelReasoning(
        supported=True,
        toggle=toggle,
        efforts=tuple(efforts),
        budget_tokens=budget,
    )


def _optional_int(value: object, path: str) -> int | None:
    if value is None:
        return None
    return _READER.as_non_negative_int(value, path)


def _capabilities(
    fields: Mapping[str, object],
    path: str,
    warnings: list[str],
) -> ModelCapabilitiesMetadata | None:
    reasoning = _reasoning(fields, path, warnings)
    tools = _optional_bool(fields, "tool_call", path)
    structured = _optional_bool(fields, "structured_output", path)
    temperature = _optional_bool(fields, "temperature", path)
    attachment = _optional_bool(fields, "attachment", path)
    if (
        reasoning is None
        and tools is None
        and structured is None
        and temperature is None
        and attachment is None
    ):
        return None
    return ModelCapabilitiesMetadata(
        reasoning=reasoning,
        tools=tools,
        structured_output=structured,
        temperature=temperature,
        attachment=attachment,
    )


def _limits(fields: Mapping[str, object], path: str) -> ModelLimits | None:
    value = fields.get("limit")
    if value is None:
        return None
    limit = _READER.as_mapping(value, f"{path}.limit")
    context = _optional_int(limit.get("context"), f"{path}.limit.context")
    input_tokens = _optional_int(limit.get("input"), f"{path}.limit.input")
    output = _optional_int(limit.get("output"), f"{path}.limit.output")
    if context is None and input_tokens is None and output is None:
        return None
    return ModelLimits(context=context, input=input_tokens, output=output)


def _rates(
    fields: Mapping[str, object],
    path: str,
) -> tuple[ModelPriceRate, ...]:
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
                    amount=_READER.as_non_negative_number(
                        fields[name], f"{path}.{name}"
                    ),
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
                    amount=_READER.as_non_negative_number(
                        fields[name], f"{path}.{name}"
                    ),
                )
            )
    return tuple(rates)


def _tier_threshold(fields: Mapping[str, object], path: str) -> int | None:
    tier_value = fields.get("tier")
    if tier_value is not None:
        tier = _READER.as_mapping(tier_value, f"{path}.tier")
        kind = _READER.as_str(tier.get("type"), f"{path}.tier.type")
        if kind != "context":
            return None
        size = _READER.as_int(tier.get("size"), f"{path}.tier.size")
        return size if size > 0 else None
    explicit = fields.get("min_input_tokens")
    if explicit is None:
        return None
    size = _READER.as_int(explicit, f"{path}.min_input_tokens")
    return size if size > 0 else None


def _tiers(
    value: object,
    path: str,
    warnings: list[str],
) -> tuple[ModelPriceTier, ...]:
    if value is None:
        return ()
    tiers: list[ModelPriceTier] = []
    for index, item in enumerate(_READER.as_list(value, f"{path}.tiers")):
        fields = _READER.as_mapping(item, f"{path}.tiers[{index}]")
        threshold = _tier_threshold(fields, f"{path}.tiers[{index}]")
        rates = _rates(fields, f"{path}.tiers[{index}]")
        if threshold is None or not rates:
            warnings.append(
                f"{path}.tiers[{index}]: ignored unsupported or empty tier shape"
            )
            continue
        tiers.append(ModelPriceTier(min_input_tokens=threshold, rates=rates))
    return tuple(tiers)


def _pricing(
    fields: Mapping[str, object],
    path: str,
    warnings: list[str],
) -> ModelPricing | None:
    value = fields.get("cost")
    if value is None:
        return None
    cost = _READER.as_mapping(value, f"{path}.cost")
    rates = _rates(cost, f"{path}.cost")
    if not rates:
        return None
    return ModelPricing(
        currency="USD",
        rates=rates,
        tiers=_tiers(cost.get("tiers"), f"{path}.cost", warnings),
    )


def _model_type(raw_type: str | None, modalities: ModelModalities) -> ModelType:
    if raw_type is not None:
        try:
            return ModelType(raw_type)
        except ValueError:
            pass
    if not modalities.output:
        return ModelType.EMBEDDING
    return ModelType.CHAT
