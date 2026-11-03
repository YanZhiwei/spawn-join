"""Tests for validated model metadata contracts."""

from datetime import date
from typing import cast

import pytest

from spawn_join_llm_provider import (
    ConfigurationError,
    Modality,
    ModelCapabilitiesMetadata,
    ModelMetadataOverride,
    ModelModalities,
    ModelPriceRate,
    ModelPriceTier,
    ModelPricing,
    ModelReasoning,
    ModelStatus,
    ModelType,
    PriceDirection,
    PriceUnit,
    apply_metadata_override,
    decode_metadata_document,
    parse_model_metadata_document,
    parse_model_metadata_override,
)


def _as_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast("dict[str, object]", value)


def _as_list(value: object) -> list[object]:
    assert isinstance(value, list)
    return cast("list[object]", value)


def _valid_document() -> dict[str, object]:
    return {
        "schema_version": 1,
        "sources": {
            "models.dev": {
                "url": "https://models.dev/catalog.json",
                "revision": "sha256:" + "a" * 64,
                "fetched_at": "2026-11-02T10:00:00Z",
                "license": "MIT",
            }
        },
        "models": {
            "openai/gpt-5": {
                "name": "GPT-5",
                "type": "chat",
                "modalities": {"input": ["text", "image"], "output": ["text"]},
                "capabilities": {
                    "reasoning": {
                        "supported": True,
                        "efforts": ["low", "medium", "high"],
                    },
                    "tools": True,
                    "structured_output": True,
                },
                "limits": {"context": 400000, "input": 272000, "output": 128000},
                "pricing": {
                    "currency": "USD",
                    "rates": [
                        {
                            "modality": "text",
                            "direction": "input",
                            "unit": "per_million_tokens",
                            "amount": 1.25,
                        },
                        {
                            "modality": "text",
                            "direction": "output",
                            "unit": "per_million_tokens",
                            "amount": 10.0,
                        },
                    ],
                },
                "status": "active",
                "release_date": "2025-08-07",
                "knowledge": "2024-09-30",
            }
        },
        "channels": {
            "fast": {
                "base_model": "openai/gpt-5",
                "source": {"id": "models.dev", "provider": "openai", "model": "gpt-5"},
                "pricing": {
                    "currency": "USD",
                    "rates": [
                        {
                            "modality": "text",
                            "direction": "input",
                            "unit": "per_million_tokens",
                            "amount": 1.5,
                        }
                    ],
                },
            }
        },
    }


def test_parse_document_returns_typed_metadata() -> None:
    document = parse_model_metadata_document(_valid_document())

    model = document.models["openai/gpt-5"]
    assert model.name == "GPT-5"
    assert model.type is ModelType.CHAT
    assert model.modalities.input == (Modality.TEXT, Modality.IMAGE)
    assert model.status is ModelStatus.ACTIVE
    assert model.release_date == date(2025, 8, 7)
    assert model.knowledge == "2024-09-30"
    assert model.pricing is not None
    assert model.pricing.rates[0].amount == 1.25
    assert document.channels["fast"].base_model == "openai/gpt-5"


def test_apply_override_replaces_present_sections_only() -> None:
    document = parse_model_metadata_document(_valid_document())
    base = document.models["openai/gpt-5"]
    override = ModelMetadataOverride(
        pricing=ModelPricing(
            currency="USD",
            rates=(
                ModelPriceRate(
                    modality=Modality.TEXT,
                    direction=PriceDirection.INPUT,
                    unit=PriceUnit.PER_MILLION_TOKENS,
                    amount=2.0,
                ),
            ),
        )
    )

    updated = apply_metadata_override(base, override)

    assert updated.pricing is not None
    assert updated.pricing.rates[0].amount == 2.0
    assert updated.limits == base.limits
    assert updated.capabilities == base.capabilities
    assert updated.modalities == base.modalities


def test_reasoning_metadata_is_descriptive() -> None:
    reasoning = ModelReasoning(
        supported=True,
        efforts=("low", "high"),
    )
    capabilities = ModelCapabilitiesMetadata(reasoning=reasoning)
    assert capabilities.reasoning is not None
    assert capabilities.reasoning.efforts == ("low", "high")


def test_modalities_are_deduplicated_and_canonically_ordered() -> None:
    modalities = ModelModalities(
        input=(Modality.IMAGE, Modality.TEXT, Modality.IMAGE),
        output=(Modality.TEXT,),
    )
    assert modalities.input == (Modality.TEXT, Modality.IMAGE)


def test_unknown_field_is_rejected() -> None:
    document = _valid_document()
    model = _as_dict(_as_dict(document["models"])["openai/gpt-5"])
    model["unexpected"] = True

    with pytest.raises(ConfigurationError, match="unknown field"):
        parse_model_metadata_document(document)


def test_missing_source_license_is_rejected() -> None:
    document = _valid_document()
    source = _as_dict(_as_dict(document["sources"])["models.dev"])
    del source["license"]

    with pytest.raises(ConfigurationError, match="missing required field"):
        parse_model_metadata_document(document)


def test_negative_price_is_rejected() -> None:
    document = _valid_document()
    model = _as_dict(_as_dict(document["models"])["openai/gpt-5"])
    pricing = _as_dict(model["pricing"])
    first = _as_dict(_as_list(pricing["rates"])[0])
    first["amount"] = -1

    with pytest.raises(ConfigurationError, match="amount"):
        parse_model_metadata_document(document)


def test_duplicate_price_rate_is_rejected() -> None:
    document = _valid_document()
    model = _as_dict(_as_dict(document["models"])["openai/gpt-5"])
    pricing = _as_dict(model["pricing"])
    rates = _as_list(pricing["rates"])
    rates.append(dict(_as_dict(rates[0])))

    with pytest.raises(ConfigurationError, match="duplicate rate"):
        parse_model_metadata_document(document)


def test_unsorted_tiers_are_sorted() -> None:
    document = _valid_document()
    model = _as_dict(_as_dict(document["models"])["openai/gpt-5"])
    pricing = _as_dict(model["pricing"])
    rate = {
        "modality": "text",
        "direction": "input",
        "unit": "per_million_tokens",
        "amount": 2.5,
    }
    pricing["tiers"] = [
        {"min_input_tokens": 500000, "rates": [rate]},
        {"min_input_tokens": 272000, "rates": [dict(rate)]},
    ]

    parsed = parse_model_metadata_document(document)
    parsed_pricing = parsed.models["openai/gpt-5"].pricing
    assert parsed_pricing is not None
    assert [tier.min_input_tokens for tier in parsed_pricing.tiers] == [272000, 500000]


def test_decode_rejects_duplicate_json_keys() -> None:
    with pytest.raises(ConfigurationError, match="duplicate key"):
        decode_metadata_document(
            '{"schema_version":1,"schema_version":1,'
            '"sources":{},"models":{},"channels":{}}'
        )


def test_tier_rates_are_canonically_sorted() -> None:
    output = ModelPriceRate(
        modality=Modality.TEXT,
        direction=PriceDirection.OUTPUT,
        unit=PriceUnit.PER_MILLION_TOKENS,
        amount=10.0,
    )
    cache = ModelPriceRate(
        modality=Modality.TEXT,
        direction=PriceDirection.CACHE_READ,
        unit=PriceUnit.PER_MILLION_TOKENS,
        amount=0.1,
    )
    input_rate = ModelPriceRate(
        modality=Modality.TEXT,
        direction=PriceDirection.INPUT,
        unit=PriceUnit.PER_MILLION_TOKENS,
        amount=1.0,
    )

    tier = ModelPriceTier(
        min_input_tokens=272000,
        rates=(output, cache, input_rate),
    )

    assert [rate.direction for rate in tier.rates] == [
        PriceDirection.CACHE_READ,
        PriceDirection.INPUT,
        PriceDirection.OUTPUT,
    ]


def test_numeric_date_is_rejected() -> None:
    document = _valid_document()
    model = _as_dict(_as_dict(document["models"])["openai/gpt-5"])
    model["release_date"] = 1754524800

    with pytest.raises(ConfigurationError, match="release_date"):
        parse_model_metadata_document(document)


def test_datetime_release_date_is_rejected() -> None:
    document = _valid_document()
    model = _as_dict(_as_dict(document["models"])["openai/gpt-5"])
    model["release_date"] = "2025-08-07T00:00:00"

    with pytest.raises(ConfigurationError, match="release_date"):
        parse_model_metadata_document(document)


def test_negative_price_error_contains_model_and_field_path() -> None:
    document = _valid_document()
    model = _as_dict(_as_dict(document["models"])["openai/gpt-5"])
    pricing = _as_dict(model["pricing"])
    rate = _as_dict(_as_list(pricing["rates"])[0])
    rate["amount"] = -1

    with pytest.raises(ConfigurationError) as excinfo:
        parse_model_metadata_document(document)

    message = str(excinfo.value)
    assert "models.openai/gpt-5" in message
    assert "amount" in message


def test_model_key_mismatch_is_rejected() -> None:
    document = _valid_document()
    model = _as_dict(_as_dict(document["models"])["openai/gpt-5"])
    model["key"] = "other/model"

    with pytest.raises(ConfigurationError, match="must match"):
        parse_model_metadata_document(document)


def test_channel_override_key_is_rejected() -> None:
    document = _valid_document()
    channel = _as_dict(_as_dict(document["channels"])["fast"])
    channel["override"] = {}

    with pytest.raises(ConfigurationError, match="unknown field"):
        parse_model_metadata_document(document)


def test_duplicate_efforts_are_deduplicated() -> None:
    document = _valid_document()
    model = _as_dict(_as_dict(document["models"])["openai/gpt-5"])
    capabilities = _as_dict(model["capabilities"])
    reasoning = _as_dict(capabilities["reasoning"])
    reasoning["efforts"] = ["low", "low", "high"]

    parsed = parse_model_metadata_document(document)
    parsed_reasoning = parsed.models["openai/gpt-5"].capabilities.reasoning
    assert parsed_reasoning is not None
    assert parsed_reasoning.efforts == ("low", "high")


def test_override_requires_mapping() -> None:
    with pytest.raises(ConfigurationError, match="must be a mapping"):
        parse_model_metadata_override(None)


def test_name_error_contains_model_path() -> None:
    document = _valid_document()
    model = _as_dict(_as_dict(document["models"])["openai/gpt-5"])
    model["name"] = " GPT-5"

    with pytest.raises(ConfigurationError) as excinfo:
        parse_model_metadata_document(document)

    message = str(excinfo.value)
    assert "models.openai/gpt-5" in message
    assert "name" in message


def test_duplicate_rate_error_contains_model_path() -> None:
    document = _valid_document()
    model = _as_dict(_as_dict(document["models"])["openai/gpt-5"])
    pricing = _as_dict(model["pricing"])
    rates = _as_list(pricing["rates"])
    rates.append(dict(_as_dict(rates[0])))

    with pytest.raises(ConfigurationError) as excinfo:
        parse_model_metadata_document(document)

    message = str(excinfo.value)
    assert "models.openai/gpt-5" in message
    assert "rates" in message


def test_invalid_model_map_key_is_rejected() -> None:
    document = _valid_document()
    models = _as_dict(document["models"])
    models["openai/gpt-5 "] = models.pop("openai/gpt-5")

    with pytest.raises(ConfigurationError, match="whitespace|must use"):
        parse_model_metadata_document(document)


def test_null_model_key_is_rejected() -> None:
    document = _valid_document()
    model = _as_dict(_as_dict(document["models"])["openai/gpt-5"])
    model["key"] = None

    with pytest.raises(ConfigurationError, match="null"):
        parse_model_metadata_document(document)


def test_channel_limit_error_contains_channel_path() -> None:
    document = _valid_document()
    channel = _as_dict(_as_dict(document["channels"])["fast"])
    channel["limits"] = {"context": -1}

    with pytest.raises(ConfigurationError) as excinfo:
        parse_model_metadata_document(document)

    message = str(excinfo.value)
    assert "channels.fast" in message
    assert "context" in message


def test_channel_must_reference_known_model() -> None:
    document = _valid_document()
    channel = _as_dict(_as_dict(document["channels"])["fast"])
    channel["base_model"] = "openai/unknown"

    with pytest.raises(ConfigurationError, match="unknown model"):
        parse_model_metadata_document(document)


def test_reasoning_controls_must_be_absent_when_unsupported() -> None:
    with pytest.raises(ConfigurationError, match="must be absent"):
        ModelReasoning(supported=False, efforts=("low",))
