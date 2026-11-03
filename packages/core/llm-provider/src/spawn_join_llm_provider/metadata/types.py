"""Validated model metadata contracts shared by sync tooling and adapters."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from dataclasses import field, replace
from datetime import UTC, date, datetime
from enum import StrEnum
from math import isfinite
from types import MappingProxyType
from typing import Annotated

from pydantic import (
    BeforeValidator,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    field_validator,
)
from pydantic.dataclasses import dataclass

from ..errors import ConfigurationError
from ..parsing import FieldReader

_METADATA_CONFIG = ConfigDict(extra="forbid")

_MODEL_KEY = re.compile(r"^[^/\s]+/[^/\s].*$")
_REVISION = re.compile(r"^sha256:[0-9a-f]{64}$")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MONTH = re.compile(r"^\d{4}-\d{2}$")
_CURRENCY = re.compile(r"^[A-Z]{3}$")
_SOURCE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_MODALITY_ORDER = ("text", "image", "audio", "video", "pdf")
_READER = FieldReader(ConfigurationError)
_as_str = _READER.as_str


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


def _as_non_empty_str(value: object, path: str) -> str:
    text = _as_str(value, path)
    if not text or text != text.strip():
        raise ConfigurationError(
            f"{path}: must be non-empty without surrounding whitespace"
        )
    if any(unicodedata.category(character).startswith("C") for character in text):
        raise ConfigurationError(f"{path}: must not contain control characters")
    return text


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


def _strict_date(value: object) -> date:
    if isinstance(value, datetime):
        raise ValueError("must be a YYYY-MM-DD string")
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise ValueError("must be a YYYY-MM-DD string")
    if _DATE.fullmatch(value) is None:
        raise ValueError("must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("must be a valid date") from exc


def _strict_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise ValueError("must be an ISO 8601 datetime string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("must be an ISO 8601 datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise ValueError("must include a UTC offset")
    return parsed


StrictDate = Annotated[date, BeforeValidator(_strict_date)]
StrictDatetime = Annotated[datetime, BeforeValidator(_strict_datetime)]


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelPriceRate:
    """One billable rate for a modality and direction."""

    modality: Modality
    direction: PriceDirection
    unit: PriceUnit
    amount: Annotated[StrictFloat, Field(ge=0, allow_inf_nan=False)]

    def __post_init__(self) -> None:
        amount = float(self.amount)
        if not isfinite(amount) or amount < 0:
            raise ConfigurationError("price amount must be finite and non-negative")
        object.__setattr__(self, "amount", amount)


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelPriceTier:
    """A long-context price tier."""

    min_input_tokens: Annotated[StrictInt, Field(gt=0)]
    rates: Annotated[tuple[ModelPriceRate, ...], Field(min_length=1)]

    @field_validator("rates")
    @classmethod
    def _validate_tier_rates(
        cls,
        rates: tuple[ModelPriceRate, ...],
    ) -> tuple[ModelPriceRate, ...]:
        try:
            _validate_unique_rates(rates, "price tier")
        except ConfigurationError as exc:
            raise ValueError(str(exc)) from exc
        return tuple(sorted(rates, key=_rate_sort_key))

    def __post_init__(self) -> None:
        if self.min_input_tokens <= 0:
            raise ConfigurationError("price tier min_input_tokens must be positive")
        if not self.rates:
            raise ConfigurationError("price tier must contain at least one rate")
        _validate_unique_rates(self.rates, "price tier")
        object.__setattr__(
            self,
            "rates",
            tuple(sorted(self.rates, key=_rate_sort_key)),
        )


def _rate_sort_key(rate: ModelPriceRate) -> tuple[int, str, str]:
    return (
        _MODALITY_ORDER.index(rate.modality.value),
        rate.direction.value,
        rate.unit.value,
    )


def _validate_unique_rates(rates: tuple[ModelPriceRate, ...], path: str) -> None:
    seen: set[tuple[Modality, PriceDirection, PriceUnit]] = set()
    for rate in rates:
        key = (rate.modality, rate.direction, rate.unit)
        if key in seen:
            raise ConfigurationError(f"{path}: duplicate rate {key}")
        seen.add(key)


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelPricing:
    """A currency and a deterministic set of rates and tiers."""

    currency: Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
    rates: Annotated[tuple[ModelPriceRate, ...], Field(min_length=1)]
    tiers: tuple[ModelPriceTier, ...] = ()

    @field_validator("rates")
    @classmethod
    def _validate_pricing_rates(
        cls,
        rates: tuple[ModelPriceRate, ...],
    ) -> tuple[ModelPriceRate, ...]:
        try:
            _validate_unique_rates(rates, "pricing")
        except ConfigurationError as exc:
            raise ValueError(str(exc)) from exc
        return tuple(sorted(rates, key=_rate_sort_key))

    @field_validator("tiers")
    @classmethod
    def _validate_tiers(
        cls,
        tiers: tuple[ModelPriceTier, ...],
    ) -> tuple[ModelPriceTier, ...]:
        thresholds: set[int] = set()
        for tier in tiers:
            if tier.min_input_tokens in thresholds:
                raise ValueError("pricing tier thresholds must be unique")
            thresholds.add(tier.min_input_tokens)
        return tuple(sorted(tiers, key=lambda tier: tier.min_input_tokens))

    def __post_init__(self) -> None:
        _parse_currency(self.currency, "pricing currency")
        if not self.rates:
            raise ConfigurationError("pricing must contain at least one rate")
        _validate_unique_rates(self.rates, "pricing")
        sorted_rates = tuple(sorted(self.rates, key=_rate_sort_key))
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


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelModalities:
    """Input and output modalities with canonical ordering."""

    input: Annotated[tuple[Modality, ...], Field(min_length=1)]
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


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelReasoningBudget:
    """Optional minimum and maximum reasoning token budgets."""

    min_tokens: StrictInt | None = None
    max_tokens: StrictInt | None = None

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


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelReasoning:
    """Whether reasoning is supported and which controls are exposed."""

    supported: StrictBool
    toggle: StrictBool | None = None
    efforts: tuple[str, ...] = ()
    budget_tokens: ModelReasoningBudget | None = None

    @field_validator("efforts")
    @classmethod
    def _validate_efforts(cls, efforts: tuple[str, ...]) -> tuple[str, ...]:
        result: list[str] = []
        for effort in efforts:
            try:
                text = _as_non_empty_str(effort, "reasoning effort")
            except ConfigurationError as exc:
                raise ValueError(str(exc)) from exc
            if text not in result:
                result.append(text)
        return tuple(result)

    def __post_init__(self) -> None:
        if not self.supported and (
            self.toggle is not None or self.efforts or self.budget_tokens is not None
        ):
            raise ConfigurationError(
                "reasoning controls must be absent when reasoning is unsupported"
            )


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelCapabilitiesMetadata:
    """Descriptive capability facts; never used for runtime negotiation."""

    reasoning: ModelReasoning | None = None
    tools: StrictBool | None = None
    structured_output: StrictBool | None = None
    temperature: StrictBool | None = None
    top_p: StrictBool | None = None
    top_k: StrictBool | None = None
    attachment: StrictBool | None = None


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelLimits:
    """Context and token limits; None means unknown."""

    context: Annotated[StrictInt | None, Field(ge=0)] = None
    input: Annotated[StrictInt | None, Field(ge=0)] = None
    output: Annotated[StrictInt | None, Field(ge=0)] = None

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


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelMetadata:
    """Model-level facts independent of a serving channel."""

    key: Annotated[str, Field(pattern=r"^[^/\s]+/[^/\s].*$")]
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
    open_weights: StrictBool | None = None
    interleaved: str | None = None
    release_date: StrictDate | None = None
    knowledge: str | None = None
    last_updated: StrictDate | None = None

    @field_validator("key")
    @classmethod
    def _validate_key(cls, value: str) -> str:
        try:
            return _parse_model_key(value, "metadata key")
        except ConfigurationError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        try:
            return _as_non_empty_str(value, "metadata name")
        except ConfigurationError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("description", "family", "license", "interleaved")
    @classmethod
    def _validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return _as_non_empty_str(value, "metadata text")
        except ConfigurationError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("knowledge")
    @classmethod
    def _validate_knowledge(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return _parse_knowledge(value, "metadata knowledge")
        except ConfigurationError as exc:
            raise ValueError(str(exc)) from exc

    def __post_init__(self) -> None:
        if _MODEL_KEY.fullmatch(self.key) is None:
            raise ConfigurationError("metadata key must use <lab>/<model>")
        _validate_optional_metadata_strings(self)


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelMetadataOverride:
    """A channel-specific replacement for selected metadata sections."""

    pricing: ModelPricing | None = None
    limits: ModelLimits | None = None
    capabilities: ModelCapabilitiesMetadata | None = None
    modalities: ModelModalities | None = None
    status: ModelStatus | None = None


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelSourceRef:
    """The source-specific coordinates for one channel override."""

    source_id: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")]
    provider: str
    model: str

    @field_validator("provider", "model")
    @classmethod
    def _validate_coordinate(cls, value: str) -> str:
        try:
            return _as_non_empty_str(value, "source coordinate")
        except ConfigurationError as exc:
            raise ValueError(str(exc)) from exc

    def __post_init__(self) -> None:
        _parse_source_id(self.source_id, "source id")
        _as_non_empty_str(self.provider, "source provider")
        _as_non_empty_str(self.model, "source model")


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelSource:
    """Provenance for one metadata source."""

    url: Annotated[str, Field(min_length=1)]
    revision: Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
    fetched_at: StrictDatetime
    license: Annotated[str, Field(min_length=1)]

    @field_validator("url", "license")
    @classmethod
    def _validate_source_text(cls, value: str) -> str:
        try:
            return _as_non_empty_str(value, "source text")
        except ConfigurationError as exc:
            raise ValueError(str(exc)) from exc

    def __post_init__(self) -> None:
        _as_non_empty_str(self.url, "source url")
        _parse_revision(self.revision, "source revision")
        if (
            self.fetched_at.tzinfo is None
            or self.fetched_at.utcoffset() != UTC.utcoffset(self.fetched_at)
        ):
            raise ConfigurationError("source fetched_at must include a UTC offset")
        _as_non_empty_str(self.license, "source license")


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelChannel:
    """A channel override linked to one shared model."""

    base_model: Annotated[str, Field(pattern=r"^[^/\s]+/[^/\s].*$")]
    override: ModelMetadataOverride
    source: ModelSourceRef | None = None

    @field_validator("base_model")
    @classmethod
    def _validate_base_model(cls, value: str) -> str:
        try:
            return _parse_model_key(value, "channel base_model")
        except ConfigurationError as exc:
            raise ValueError(str(exc)) from exc

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


@dataclass(frozen=True, slots=True, kw_only=True, config=_METADATA_CONFIG)
class ModelMetadataDocument:
    """A validated metadata snapshot."""

    schema_version: StrictInt
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
