"""Tests for the models.dev adapter."""

from __future__ import annotations

import json

import pytest
from spawn_join_llm_model_sync import ModelsDevSource, SourceHostRef, SourceRequest
from spawn_join_llm_model_sync.sources.models_dev import SourcePayloadError

from spawn_join_llm_provider import Modality


def test_translate_only_requested_records(catalog_payload: bytes) -> None:
    request = SourceRequest(
        refs=("openai/gpt-5", "missing/model"),
        hosts=(
            SourceHostRef(provider="openai", model="gpt-5"),
            SourceHostRef(provider="backup", model="gpt-5"),
        ),
    )

    catalog = ModelsDevSource().translate(catalog_payload, request)

    assert set(catalog.models) == {"openai/gpt-5"}
    assert catalog.total_models == 2
    assert catalog.total_providers == 2
    shared = catalog.models["openai/gpt-5"]
    assert shared.name == "GPT-5"
    assert shared.release_date is not None
    assert shared.capabilities.reasoning is not None
    assert shared.capabilities.reasoning.supported is True

    host = catalog.hosts["openai"]["gpt-5"]
    assert host.canonical_model == "openai/gpt-5"
    assert host.override.pricing is not None
    input_rate = next(
        rate for rate in host.override.pricing.rates if rate.direction.value == "input"
    )
    assert input_rate.amount == 1.25
    assert host.override.capabilities is not None
    assert host.override.capabilities.reasoning is not None
    assert host.override.capabilities.reasoning.efforts == (
        "low",
        "medium",
        "high",
    )
    backup = catalog.hosts["backup"]["gpt-5"]
    assert backup.override.pricing is not None
    assert backup.override.pricing.rates[0].amount == 1.8
    assert backup.override.modalities is not None
    assert backup.override.modalities.input == (Modality.TEXT,)
    assert catalog.unreferenced_models == ("openai/other",)


def test_price_only_host_omits_capabilities(catalog_payload: bytes) -> None:
    data = json.loads(catalog_payload)
    data["providers"]["backup"]["models"]["gpt-5"] = {
        "canonical_model_id": "openai/gpt-5",
        "cost": {"input": 1.8},
    }
    request = SourceRequest(
        refs=("openai/gpt-5",),
        hosts=(SourceHostRef(provider="backup", model="gpt-5"),),
    )

    catalog = ModelsDevSource().translate(
        json.dumps(data).encode("utf-8"),
        request,
    )

    host = catalog.hosts["backup"]["gpt-5"]
    assert host.override.capabilities is None
    assert host.override.modalities is None


def test_reasoning_must_be_a_boolean(catalog_payload: bytes) -> None:
    data = json.loads(catalog_payload)
    data["models"]["openai/gpt-5"]["reasoning"] = "true"
    request = SourceRequest(refs=("openai/gpt-5",))

    with pytest.raises(SourcePayloadError, match="must be a boolean"):
        ModelsDevSource().translate(
            json.dumps(data).encode("utf-8"),
            request,
        )


def test_canonical_model_id_fallback(catalog_payload: bytes) -> None:
    data = json.loads(catalog_payload)
    del data["providers"]["openai"]["models"]["gpt-5"]["canonical_model_id"]
    request = SourceRequest(
        refs=("openai/gpt-5",),
        hosts=(SourceHostRef(provider="openai", model="gpt-5"),),
    )

    catalog = ModelsDevSource().translate(
        json.dumps(data).encode("utf-8"),
        request,
    )

    assert catalog.hosts["openai"]["gpt-5"].canonical_model == "openai/gpt-5"


def test_unknown_reasoning_option_is_a_warning(catalog_payload: bytes) -> None:
    data = json.loads(catalog_payload)
    data["providers"]["openai"]["models"]["gpt-5"]["reasoning_options"].append(
        {"type": "future-control"}
    )
    request = SourceRequest(
        refs=("openai/gpt-5",),
        hosts=(SourceHostRef(provider="openai", model="gpt-5"),),
    )

    catalog = ModelsDevSource().translate(
        json.dumps(data).encode("utf-8"),
        request,
    )

    assert any("future-control" in warning for warning in catalog.warnings)


def test_invalid_json_is_a_payload_error(catalog_payload: bytes) -> None:
    with pytest.raises(SourcePayloadError, match="not valid JSON"):
        ModelsDevSource().translate(
            b"{not-json",
            SourceRequest(refs=("openai/gpt-5",)),
        )


def test_nested_context_tier_shape_is_translated(catalog_payload: bytes) -> None:
    data = json.loads(catalog_payload)
    data["providers"]["openai"]["models"]["gpt-5"]["cost"]["tiers"] = [
        {
            "input": 3.0,
            "output": 15.0,
            "tier": {"type": "context", "size": 272000},
        }
    ]
    request = SourceRequest(
        refs=("openai/gpt-5",),
        hosts=(SourceHostRef(provider="openai", model="gpt-5"),),
    )

    catalog = ModelsDevSource().translate(
        json.dumps(data).encode("utf-8"),
        request,
    )

    pricing = catalog.hosts["openai"]["gpt-5"].override.pricing
    assert pricing is not None
    assert pricing.tiers[0].min_input_tokens == 272000
    assert pricing.tiers[0].rates[0].amount == 3.0


def test_unknown_tier_shape_is_a_warning(catalog_payload: bytes) -> None:
    data = json.loads(catalog_payload)
    data["providers"]["openai"]["models"]["gpt-5"]["cost"]["tiers"] = [
        {"input": 3.0, "tier": {"type": "future", "size": 1}}
    ]
    request = SourceRequest(
        refs=("openai/gpt-5",),
        hosts=(SourceHostRef(provider="openai", model="gpt-5"),),
    )

    catalog = ModelsDevSource().translate(
        json.dumps(data).encode("utf-8"),
        request,
    )

    assert any("unsupported or empty tier shape" in item for item in catalog.warnings)
    pricing = catalog.hosts["openai"]["gpt-5"].override.pricing
    assert pricing is not None
    assert pricing.tiers == ()


def test_duplicate_json_key_is_rejected(catalog_payload: bytes) -> None:
    with pytest.raises(SourcePayloadError, match="duplicate key"):
        ModelsDevSource().translate(
            b'{"providers": {}, "models": {}, "models": {}}',
            SourceRequest(refs=("openai/gpt-5",)),
        )
