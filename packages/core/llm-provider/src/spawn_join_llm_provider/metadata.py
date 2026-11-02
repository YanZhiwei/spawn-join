"""Validated model metadata contracts shared by sync tooling and adapters."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime
from enum import StrEnum
from math import isfinite
from types import MappingProxyType
from typing import TypeVar, cast

from .errors import ConfigurationError

_MODEL_KEY = re.compile(r"^[^/\s]+/[^/\s].*$")
_REVISION = re.compile(r"^sha256:[0-9a-f]{64}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MONTH = re.compile(r"^\d{4}-\d{2}$")
_CURRENCY = re.compile(r"^[A-Z]{3}$")
_SOURCE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_MODALITY_ORDER = ("text", "image", "audio", "video", "pdf")
_T = TypeVar("_T")
_EnumT = TypeVar("_EnumT", bound=StrEnum)


class ModelType(StrEnum):
    """The kind of model the metadata describes."""

    CHAT = "chat"
    EMBEDDING = "embedding"
    IMAGE_GENERATION = "image_generation"
    RERANK = "rerank"
    SPEECH = "speech"
    TRANSCRIPTION = "transcription"


class Modality(StrEnum):
    """An input or output modality."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    PDF = "pdf"


class ModelStatus(StrEnum):
    """Lifecycle status reported by the upstream source."""

    ACTIVE = "active"
    ALPHA = "alpha"
    BETA = "beta"
    DEPRECATED = "deprecated"


class PriceDirection(StrEnum):
    """The billable direction of a price rate."""

    INPUT = "input"
    OUTPUT = "output"
    CACHE_READ = "cache_read"
    CACHE_WRITE = "cache_write"
    REASONING = "reasoning"


class PriceUnit(StrEnum):
    """The unit a price amount is expressed in."""

    PER_MILLION_TOKENS = "per_million_tokens"
    PER_IMAGE = "per_image"
    PER_SECOND = "per_second"
    PER_REQUEST = "per_request"


def _as_mapping(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ConfigurationError(f"{path}: must be a mapping")
    result: dict[str, object] = {}
    for key, item in cast("Mapping[object, object]", value).items():
        if not isinstance(key, str):
            raise ConfigurationError(f"{path}: keys must be strings")
        result[key] = item
    return result


def _require_keys(
    mapping: Mapping[str, object],
    *,
    required: frozenset[str],
    optional: frozenset[str],
    path: str,
) -> None:
    missing = required.difference(mapping)
    unknown = set(mapping).difference(required, optional)
    problems: list[str] = []
    if missing:
        problems.append(f"missing required field(s): {', '.join(sorted(missing))}")
    if unknown:
        problems.append(f"unknown field(s): {', '.join(sorted(unknown))}")
    if problems:
        raise ConfigurationError(f"{path}: {'; '.join(problems)}")


def _as_str(value: object, path: str) -> str:
    if not isinstance(value, str):
        raise ConfigurationError(f"{path}: must be a string")
    return value


def _as_non_empty_str(value: object, path: str) -> str:
    text = _as_str(value, path)
    if not text or text != text.strip():
        raise ConfigurationError(
            f"{path}: must be non-empty without surrounding whitespace"
        )
    if any(unicodedata.category(character).startswith("C") for character in text):
        raise ConfigurationError(f"{path}: must not contain control characters")
    return text


def _as_int(value: object, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigurationError(f"{path}: must be an integer")
    return value


def _as_non_negative_int(value: object, path: str) -> int:
    number = _as_int(value, path)
    if number < 0:
        raise ConfigurationError(f"{path}: must be non-negative")
    return number


def _as_number(value: object, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(f"{path}: must be a number")
    number = float(value)
    if not isfinite(number) or number < 0:
        raise ConfigurationError(f"{path}: must be finite and non-negative")
    return number


def _as_bool(value: object, path: str) -> bool:
    if not isinstance(value, bool):
        raise ConfigurationError(f"{path}: must be a boolean")
    return value


def _as_date(value: object, path: str) -> date:
    text = _as_non_empty_str(value, path)
    if _DATE.fullmatch(text) is None:
        raise ConfigurationError(f"{path}: must use YYYY-MM-DD")
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise ConfigurationError(f"{path}: must be a valid date") from exc


def _as_datetime(value: object, path: str) -> datetime:
    text = _as_non_empty_str(value, path)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ConfigurationError(f"{path}: must be an ISO 8601 datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ConfigurationError(f"{path}: must include a UTC offset")
    return parsed


def _as_enum(enum_type: type[_EnumT], value: object, path: str) -> _EnumT:
    raw = _as_non_empty_str(value, path)
    try:
        return enum_type(raw)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in enum_type)
        raise ConfigurationError(f"{path}: must be one of: {allowed}") from exc


def _as_string_tuple(value: object, path: str, *, non_empty: bool) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ConfigurationError(f"{path}: must be a list of strings")
    result: list[str] = []
    for index, item in enumerate(cast("list[object]", value)):
        text = _as_non_empty_str(item, f"{path}[{index}]")
        if text not in result:
            result.append(text)
    if non_empty and not result:
        raise ConfigurationError(f"{path}: must not be empty")
    return tuple(result)


def _optional(
    fields: Mapping[str, object],
    name: str,
    parser: Callable[[object, str], _T],
    path: str,
) -> _T | None:
    if name not in fields:
        return None
    return parser(fields[name], f"{path}.{name}")


def _parse_model_key(value: object, path: str) -> str:
    key = _as_non_empty_str(value, path)
    if _MODEL_KEY.fullmatch(key) is None:
        raise ConfigurationError(f"{path}: must use <lab>/<model>")
    return key


def _parse_source_id(value: object, path: str) -> str:
    source_id = _as_non_empty_str(value, path)
    if _SOURCE_ID.fullmatch(source_id) is None:
        raise ConfigurationError(f"{path}: must match [a-z0-9][a-z0-9._-]*")
    return source_id


def _parse_currency(value: object, path: str) -> str:
    currency = _as_non_empty_str(value, path)
    if _CURRENCY.fullmatch(currency) is None:
        raise ConfigurationError(f"{path}: must be a 3-letter uppercase currency")
    return currency


def _parse_revision(value: object, path: str) -> str:
    revision = _as_non_empty_str(value, path)
    if _REVISION.fullmatch(revision) is None:
        raise ConfigurationError(f"{path}: must be sha256:<64 lowercase hex>")
    return revision


def _parse_knowledge(value: object, path: str) -> str:
    text = _as_non_empty_str(value, path)
    if _MONTH.fullmatch(text) is not None:
        try:
            date.fromisoformat(f"{text}-01")
        except ValueError as exc:
            raise ConfigurationError(f"{path}: must be a valid month") from exc
        return text
    if _DATE.fullmatch(text) is not None:
        try:
            date.fromisoformat(text)
        except ValueError as exc:
            raise ConfigurationError(f"{path}: must be a valid date") from exc
        return text
    raise ConfigurationError(f"{path}: must use YYYY-MM or YYYY-MM-DD")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelPriceRate:
    """One billable rate for a modality and direction."""

    modality: Modality
    direction: PriceDirection
    unit: PriceUnit
    amount: float

    def __post_init__(self) -> None:
        amount = float(self.amount)
        if not isfinite(amount) or amount < 0:
            raise ConfigurationError("price amount must be finite and non-negative")
        object.__setattr__(self, "amount", amount)


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelPriceTier:
    """A long-context price tier."""

    min_input_tokens: int
    rates: tuple[ModelPriceRate, ...]

    def __post_init__(self) -> None:
        if self.min_input_tokens <= 0:
            raise ConfigurationError("price tier min_input_tokens must be positive")
        if not self.rates:
            raise ConfigurationError("price tier must contain at least one rate")
        _validate_unique_rates(self.rates, "price tier")


def _validate_unique_rates(rates: tuple[ModelPriceRate, ...], path: str) -> None:
    seen: set[tuple[Modality, PriceDirection, PriceUnit]] = set()
    for rate in rates:
        key = (rate.modality, rate.direction, rate.unit)
        if key in seen:
            raise ConfigurationError(f"{path}: duplicate rate {key}")
        seen.add(key)


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelPricing:
    """A currency and a deterministic set of rates and tiers."""

    currency: str
    rates: tuple[ModelPriceRate, ...]
    tiers: tuple[ModelPriceTier, ...] = ()

    def __post_init__(self) -> None:
        if _CURRENCY.fullmatch(self.currency) is None:
            raise ConfigurationError("pricing currency must be a 3-letter code")
        if not self.rates:
            raise ConfigurationError("pricing must contain at least one rate")
        _validate_unique_rates(self.rates, "pricing")
        sorted_rates = tuple(
            sorted(
                self.rates,
                key=lambda rate: (
                    _MODALITY_ORDER.index(rate.modality.value),
                    rate.direction.value,
                    rate.unit.value,
                ),
            )
        )
        object.__setattr__(self, "rates", sorted_rates)

        thresholds: set[int] = set()
        for tier in self.tiers:
            if tier.min_input_tokens in thresholds:
                raise ConfigurationError("pricing tier thresholds must be unique")
            thresholds.add(tier.min_input_tokens)
        object.__setattr__(
            self,
            "tiers",
            tuple(sorted(self.tiers, key=lambda tier: tier.min_input_tokens)),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelModalities:
    """Input and output modalities with canonical ordering."""

    input: tuple[Modality, ...]
    output: tuple[Modality, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "input", _normalize_modalities(self.input, "input"))
        object.__setattr__(self, "output", _normalize_modalities(self.output, "output"))
        if not self.input:
            raise ConfigurationError("modalities.input must not be empty")


def _normalize_modalities(
    values: tuple[Modality, ...],
    field_name: str,
) -> tuple[Modality, ...]:
    seen: set[Modality] = set()
    for value in values:
        seen.add(value)
    return tuple(
        modality
        for name in _MODALITY_ORDER
        for modality in (Modality(name),)
        if modality in seen
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelReasoningBudget:
    """Optional minimum and maximum reasoning token budgets."""

    min_tokens: int | None = None
    max_tokens: int | None = None

    def __post_init__(self) -> None:
        if self.min_tokens is None and self.max_tokens is None:
            raise ConfigurationError("reasoning budget must define min or max tokens")
        if self.min_tokens is not None and self.min_tokens < 0:
            raise ConfigurationError("reasoning budget min_tokens must be non-negative")
        if self.max_tokens is not None and self.max_tokens < 0:
            raise ConfigurationError("reasoning budget max_tokens must be non-negative")
        if (
            self.min_tokens is not None
            and self.max_tokens is not None
            and self.min_tokens > self.max_tokens
        ):
            raise ConfigurationError("reasoning budget min_tokens must not exceed max")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelReasoning:
    """Whether reasoning is supported and which controls are exposed."""

    supported: bool
    toggle: bool | None = None
    efforts: tuple[str, ...] = ()
    budget_tokens: ModelReasoningBudget | None = None

    def __post_init__(self) -> None:
        for effort in self.efforts:
            _as_non_empty_str(effort, "reasoning effort")
        if not self.supported and (
            self.toggle is not None or self.efforts or self.budget_tokens is not None
        ):
            raise ConfigurationError(
                "reasoning controls must be absent when reasoning is unsupported"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelCapabilitiesMetadata:
    """Descriptive capability facts; never used for runtime negotiation."""

    reasoning: ModelReasoning | None = None
    tools: bool | None = None
    structured_output: bool | None = None
    temperature: bool | None = None
    top_p: bool | None = None
    top_k: bool | None = None
    attachment: bool | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelLimits:
    """Context and token limits; None means unknown."""

    context: int | None = None
    input: int | None = None
    output: int | None = None

    def __post_init__(self) -> None:
        for name in ("context", "input", "output"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise ConfigurationError(f"limits.{name} must be non-negative or None")


def _validate_optional_metadata_strings(metadata: object) -> None:
    for name in ("description", "family", "license", "interleaved", "knowledge"):
        value = getattr(metadata, name)
        if value is not None:
            _as_non_empty_str(value, f"metadata {name}")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelMetadata:
    """Model-level facts independent of a serving channel."""

    key: str
    name: str
    type: ModelType
    modalities: ModelModalities
    capabilities: ModelCapabilitiesMetadata = field(
        default_factory=ModelCapabilitiesMetadata
    )
    limits: ModelLimits = field(default_factory=ModelLimits)
    pricing: ModelPricing | None = None
    status: ModelStatus = ModelStatus.ACTIVE
    description: str | None = None
    family: str | None = None
    license: str | None = None
    open_weights: bool | None = None
    interleaved: str | None = None
    release_date: date | None = None
    knowledge: str | None = None
    last_updated: date | None = None

    def __post_init__(self) -> None:
        if _MODEL_KEY.fullmatch(self.key) is None:
            raise ConfigurationError("metadata key must use <lab>/<model>")
        _as_non_empty_str(self.name, "metadata name")
        _validate_optional_metadata_strings(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelMetadataOverride:
    """A channel-specific replacement for selected metadata sections."""

    pricing: ModelPricing | None = None
    limits: ModelLimits | None = None
    capabilities: ModelCapabilitiesMetadata | None = None
    modalities: ModelModalities | None = None
    status: ModelStatus | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelSourceRef:
    """The source-specific coordinates for one channel override."""

    source_id: str
    provider: str
    model: str

    def __post_init__(self) -> None:
        _parse_source_id(self.source_id, "source id")
        _as_non_empty_str(self.provider, "source provider")
        _as_non_empty_str(self.model, "source model")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelSource:
    """Provenance for one metadata source."""

    url: str
    revision: str
    fetched_at: datetime
    license: str

    def __post_init__(self) -> None:
        _as_non_empty_str(self.url, "source url")
        _parse_revision(self.revision, "source revision")
        if (
            self.fetched_at.tzinfo is None
            or self.fetched_at.utcoffset() != UTC.utcoffset(self.fetched_at)
        ):
            raise ConfigurationError("source fetched_at must include a UTC offset")
        _as_non_empty_str(self.license, "source license")


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelChannel:
    """A channel override linked to one shared model."""

    base_model: str
    override: ModelMetadataOverride
    source: ModelSourceRef | None = None

    def __post_init__(self) -> None:
        if _MODEL_KEY.fullmatch(self.base_model) is None:
            raise ConfigurationError("channel base_model must use <lab>/<model>")


def _validate_sources(sources: Mapping[str, ModelSource]) -> None:
    for source_id in sources:
        _parse_source_id(source_id, "sources key")


def _validate_models(models: Mapping[str, ModelMetadata]) -> None:
    for key, model in models.items():
        if _MODEL_KEY.fullmatch(key) is None:
            raise ConfigurationError("models keys must use <lab>/<model>")
        if model.key != key:
            raise ConfigurationError("models key must match model key")


def _validate_channels(
    channels: Mapping[str, ModelChannel],
    models: Mapping[str, ModelMetadata],
    sources: Mapping[str, ModelSource],
) -> None:
    for name, channel in channels.items():
        _as_non_empty_str(name, "channels key")
        if channel.base_model not in models:
            raise ConfigurationError(
                f"channels.{name}.base_model: unknown model {channel.base_model!r}"
            )
        if channel.source is not None and channel.source.source_id not in sources:
            raise ConfigurationError(
                f"channels.{name}.source.id: unknown source "
                f"{channel.source.source_id!r}"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelMetadataDocument:
    """A validated metadata snapshot."""

    schema_version: int
    sources: Mapping[str, ModelSource]
    models: Mapping[str, ModelMetadata]
    channels: Mapping[str, ModelChannel]

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ConfigurationError(
                "metadata schema_version: only version 1 is supported"
            )
        if not self.sources:
            raise ConfigurationError("metadata sources must not be empty")
        _validate_sources(self.sources)
        _validate_models(self.models)
        _validate_channels(self.channels, self.models, self.sources)
        object.__setattr__(self, "sources", MappingProxyType(dict(self.sources)))
        object.__setattr__(self, "models", MappingProxyType(dict(self.models)))
        object.__setattr__(self, "channels", MappingProxyType(dict(self.channels)))


def apply_metadata_override(
    base: ModelMetadata,
    override: ModelMetadataOverride,
) -> ModelMetadata:
    """Return a new model with the override's present sections applied."""
    return replace(
        base,
        pricing=base.pricing if override.pricing is None else override.pricing,
        limits=base.limits if override.limits is None else override.limits,
        capabilities=(
            base.capabilities
            if override.capabilities is None
            else override.capabilities
        ),
        modalities=(
            base.modalities if override.modalities is None else override.modalities
        ),
        status=base.status if override.status is None else override.status,
    )


def _parse_modalities(value: object, path: str) -> ModelModalities:
    fields = _as_mapping(value, path)
    _require_keys(
        fields,
        required=frozenset({"input", "output"}),
        optional=frozenset(),
        path=path,
    )
    input_values = _parse_modality_tuple(fields["input"], f"{path}.input")
    output_values = _parse_modality_tuple(fields["output"], f"{path}.output")
    return ModelModalities(input=input_values, output=output_values)


def _parse_modality_tuple(value: object, path: str) -> tuple[Modality, ...]:
    if not isinstance(value, list):
        raise ConfigurationError(f"{path}: must be a list of modalities")
    result: list[Modality] = []
    for index, item in enumerate(cast("list[object]", value)):
        modality = _as_enum(Modality, item, f"{path}[{index}]")
        if modality not in result:
            result.append(modality)
    return tuple(result)


def _parse_reasoning(value: object, path: str) -> ModelReasoning:
    fields = _as_mapping(value, path)
    _require_keys(
        fields,
        required=frozenset({"supported"}),
        optional=frozenset({"toggle", "efforts", "budget_tokens"}),
        path=path,
    )
    supported = _as_bool(fields["supported"], f"{path}.supported")
    toggle = _optional(fields, "toggle", _as_bool, path)
    efforts = (
        _as_string_tuple(fields["efforts"], f"{path}.efforts", non_empty=False)
        if "efforts" in fields
        else ()
    )
    budget: ModelReasoningBudget | None = None
    if "budget_tokens" in fields:
        budget_fields = _as_mapping(fields["budget_tokens"], f"{path}.budget_tokens")
        _require_keys(
            budget_fields,
            required=frozenset(),
            optional=frozenset({"min_tokens", "max_tokens"}),
            path=f"{path}.budget_tokens",
        )
        budget = ModelReasoningBudget(
            min_tokens=_optional(
                budget_fields,
                "min_tokens",
                _as_non_negative_int,
                f"{path}.budget_tokens",
            ),
            max_tokens=_optional(
                budget_fields,
                "max_tokens",
                _as_non_negative_int,
                f"{path}.budget_tokens",
            ),
        )
    return ModelReasoning(
        supported=supported,
        toggle=toggle,
        efforts=efforts,
        budget_tokens=budget,
    )


def _parse_capabilities(value: object, path: str) -> ModelCapabilitiesMetadata:
    fields = _as_mapping(value, path)
    _require_keys(
        fields,
        required=frozenset(),
        optional=frozenset(
            {
                "reasoning",
                "tools",
                "structured_output",
                "temperature",
                "top_p",
                "top_k",
                "attachment",
            }
        ),
        path=path,
    )
    reasoning = (
        _parse_reasoning(fields["reasoning"], f"{path}.reasoning")
        if "reasoning" in fields
        else None
    )
    return ModelCapabilitiesMetadata(
        reasoning=reasoning,
        tools=_optional(fields, "tools", _as_bool, path),
        structured_output=_optional(fields, "structured_output", _as_bool, path),
        temperature=_optional(fields, "temperature", _as_bool, path),
        top_p=_optional(fields, "top_p", _as_bool, path),
        top_k=_optional(fields, "top_k", _as_bool, path),
        attachment=_optional(fields, "attachment", _as_bool, path),
    )


def _parse_limits(value: object, path: str) -> ModelLimits:
    fields = _as_mapping(value, path)
    _require_keys(
        fields,
        required=frozenset(),
        optional=frozenset({"context", "input", "output"}),
        path=path,
    )
    return ModelLimits(
        context=_optional(fields, "context", _as_non_negative_int, path),
        input=_optional(fields, "input", _as_non_negative_int, path),
        output=_optional(fields, "output", _as_non_negative_int, path),
    )


def _parse_price_rate(value: object, path: str) -> ModelPriceRate:
    fields = _as_mapping(value, path)
    _require_keys(
        fields,
        required=frozenset({"modality", "direction", "unit", "amount"}),
        optional=frozenset(),
        path=path,
    )
    return ModelPriceRate(
        modality=_as_enum(Modality, fields["modality"], f"{path}.modality"),
        direction=_as_enum(PriceDirection, fields["direction"], f"{path}.direction"),
        unit=_as_enum(PriceUnit, fields["unit"], f"{path}.unit"),
        amount=_as_number(fields["amount"], f"{path}.amount"),
    )


def _parse_pricing(value: object, path: str) -> ModelPricing:
    fields = _as_mapping(value, path)
    _require_keys(
        fields,
        required=frozenset({"currency", "rates"}),
        optional=frozenset({"tiers"}),
        path=path,
    )
    rates = _parse_rates(fields["rates"], f"{path}.rates")
    tiers: tuple[ModelPriceTier, ...] = ()
    if "tiers" in fields:
        if not isinstance(fields["tiers"], list):
            raise ConfigurationError(f"{path}.tiers: must be a list")
        parsed_tiers: list[ModelPriceTier] = []
        for index, item in enumerate(cast("list[object]", fields["tiers"])):
            tier_fields = _as_mapping(item, f"{path}.tiers[{index}]")
            _require_keys(
                tier_fields,
                required=frozenset({"min_input_tokens", "rates"}),
                optional=frozenset(),
                path=f"{path}.tiers[{index}]",
            )
            parsed_tiers.append(
                ModelPriceTier(
                    min_input_tokens=_as_int(
                        tier_fields["min_input_tokens"],
                        f"{path}.tiers[{index}].min_input_tokens",
                    ),
                    rates=_parse_rates(
                        tier_fields["rates"], f"{path}.tiers[{index}].rates"
                    ),
                )
            )
        tiers = tuple(parsed_tiers)
    return ModelPricing(
        currency=_parse_currency(fields["currency"], f"{path}.currency"),
        rates=rates,
        tiers=tiers,
    )


def _parse_rates(value: object, path: str) -> tuple[ModelPriceRate, ...]:
    if not isinstance(value, list):
        raise ConfigurationError(f"{path}: must be a list")
    return tuple(
        _parse_price_rate(item, f"{path}[{index}]")
        for index, item in enumerate(cast("list[object]", value))
    )


def _parse_source_ref(value: object, path: str) -> ModelSourceRef:
    fields = _as_mapping(value, path)
    _require_keys(
        fields,
        required=frozenset({"id", "provider", "model"}),
        optional=frozenset(),
        path=path,
    )
    return ModelSourceRef(
        source_id=_parse_source_id(fields["id"], f"{path}.id"),
        provider=_as_non_empty_str(fields["provider"], f"{path}.provider"),
        model=_as_non_empty_str(fields["model"], f"{path}.model"),
    )


def parse_model_metadata_override(
    value: object, path: str = "metadata"
) -> ModelMetadataOverride:
    """Parse a channel or inline override mapping."""
    fields = _as_mapping(value, path)
    _require_keys(
        fields,
        required=frozenset(),
        optional=frozenset(
            {"pricing", "limits", "capabilities", "modalities", "status"}
        ),
        path=path,
    )
    return ModelMetadataOverride(
        pricing=(
            _parse_pricing(fields["pricing"], f"{path}.pricing")
            if "pricing" in fields
            else None
        ),
        limits=(
            _parse_limits(fields["limits"], f"{path}.limits")
            if "limits" in fields
            else None
        ),
        capabilities=(
            _parse_capabilities(fields["capabilities"], f"{path}.capabilities")
            if "capabilities" in fields
            else None
        ),
        modalities=(
            _parse_modalities(fields["modalities"], f"{path}.modalities")
            if "modalities" in fields
            else None
        ),
        status=(
            _as_enum(ModelStatus, fields["status"], f"{path}.status")
            if "status" in fields
            else None
        ),
    )


def _parse_model_metadata(value: object, path: str) -> ModelMetadata:
    fields = _as_mapping(value, path)
    _require_keys(
        fields,
        required=frozenset({"name", "type", "modalities"}),
        optional=frozenset(
            {
                "key",
                "capabilities",
                "limits",
                "pricing",
                "status",
                "description",
                "family",
                "license",
                "open_weights",
                "interleaved",
                "release_date",
                "knowledge",
                "last_updated",
            }
        ),
        path=path,
    )
    key = (
        _parse_model_key(fields["key"], f"{path}.key")
        if "key" in fields
        else _parse_model_key(path.split(".", 1)[-1], f"{path}.key")
    )
    return ModelMetadata(
        key=key,
        name=_as_non_empty_str(fields["name"], f"{path}.name"),
        type=_as_enum(ModelType, fields["type"], f"{path}.type"),
        modalities=_parse_modalities(fields["modalities"], f"{path}.modalities"),
        capabilities=(
            _parse_capabilities(fields["capabilities"], f"{path}.capabilities")
            if "capabilities" in fields
            else ModelCapabilitiesMetadata()
        ),
        limits=(
            _parse_limits(fields["limits"], f"{path}.limits")
            if "limits" in fields
            else ModelLimits()
        ),
        pricing=(
            _parse_pricing(fields["pricing"], f"{path}.pricing")
            if "pricing" in fields
            else None
        ),
        status=(
            _as_enum(ModelStatus, fields["status"], f"{path}.status")
            if "status" in fields
            else ModelStatus.ACTIVE
        ),
        description=_optional(fields, "description", _as_non_empty_str, path),
        family=_optional(fields, "family", _as_non_empty_str, path),
        license=_optional(fields, "license", _as_non_empty_str, path),
        open_weights=_optional(fields, "open_weights", _as_bool, path),
        interleaved=_optional(fields, "interleaved", _as_non_empty_str, path),
        release_date=_optional(fields, "release_date", _as_date, path),
        knowledge=_optional(fields, "knowledge", _parse_knowledge, path),
        last_updated=_optional(fields, "last_updated", _as_date, path),
    )


def _parse_source(value: object, path: str) -> ModelSource:
    fields = _as_mapping(value, path)
    _require_keys(
        fields,
        required=frozenset({"url", "revision", "fetched_at", "license"}),
        optional=frozenset(),
        path=path,
    )
    return ModelSource(
        url=_as_non_empty_str(fields["url"], f"{path}.url"),
        revision=_parse_revision(fields["revision"], f"{path}.revision"),
        fetched_at=_as_datetime(fields["fetched_at"], f"{path}.fetched_at"),
        license=_as_non_empty_str(fields["license"], f"{path}.license"),
    )


def _parse_channel(value: object, path: str) -> ModelChannel:
    fields = _as_mapping(value, path)
    _require_keys(
        fields,
        required=frozenset({"base_model"}),
        optional=frozenset(
            {
                "source",
                "pricing",
                "limits",
                "capabilities",
                "modalities",
                "status",
            }
        ),
        path=path,
    )
    override_fields = {
        key: item
        for key, item in fields.items()
        if key in {"pricing", "limits", "capabilities", "modalities", "status"}
    }
    return ModelChannel(
        base_model=_parse_model_key(fields["base_model"], f"{path}.base_model"),
        source=(
            _parse_source_ref(fields["source"], f"{path}.source")
            if "source" in fields
            else None
        ),
        override=parse_model_metadata_override(override_fields, path),
    )


def parse_model_metadata_document(value: object) -> ModelMetadataDocument:
    """Parse a strict metadata snapshot document."""
    root = _as_mapping(value, "<metadata>")
    _require_keys(
        root,
        required=frozenset({"schema_version", "sources", "models", "channels"}),
        optional=frozenset(),
        path="<metadata>",
    )
    schema_version = _as_int(root["schema_version"], "schema_version")
    sources_fields = _as_mapping(root["sources"], "sources")
    sources: dict[str, ModelSource] = {}
    for source_id, source_value in sources_fields.items():
        sources[_parse_source_id(source_id, f"sources.{source_id}")] = _parse_source(
            source_value, f"sources.{source_id}"
        )
    models_fields = _as_mapping(root["models"], "models")
    models: dict[str, ModelMetadata] = {}
    for key, model_value in models_fields.items():
        model_key = _parse_model_key(key, f"models.{key}")
        models[model_key] = _parse_model_metadata(model_value, f"models.{key}")
    channels_fields = _as_mapping(root["channels"], "channels")
    channels: dict[str, ModelChannel] = {}
    for name, channel_value in channels_fields.items():
        channels[_as_non_empty_str(name, f"channels.{name}")] = _parse_channel(
            channel_value, f"channels.{name}"
        )
    return ModelMetadataDocument(
        schema_version=schema_version,
        sources=sources,
        models=models,
        channels=channels,
    )
