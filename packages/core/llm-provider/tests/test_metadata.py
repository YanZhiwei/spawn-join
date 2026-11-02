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
    ModelPricing,
    ModelReasoning,
    ModelStatus,
    ModelType,
    PriceDirection,
    PriceUnit,
    apply_metadata_override,
    parse_model_metadata_document,
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

    with pytest.raises(ConfigurationError, match="finite and non-negative"):
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


def test_channel_must_reference_known_model() -> None:
    document = _valid_document()
    channel = _as_dict(_as_dict(document["channels"])["fast"])
    channel["base_model"] = "openai/unknown"

    with pytest.raises(ConfigurationError, match="unknown model"):
        parse_model_metadata_document(document)


def test_reasoning_controls_must_be_absent_when_unsupported() -> None:
    with pytest.raises(ConfigurationError, match="must be absent"):
        ModelReasoning(supported=False, efforts=("low",))
