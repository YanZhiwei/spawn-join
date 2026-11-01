"""Tests for model file parsing and catalog resolution."""

import os
import re
from pathlib import Path

import pytest
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from spawn_join_llm_provider import ConfigurationError
from spawn_join_llm_provider_langchain import ModelCatalog, load_model_catalog
from spawn_join_llm_provider_langchain.model_file import (
    _load_yaml_document,  # pyright: ignore[reportPrivateUsage]
)

FIXTURES = Path(__file__).parent / "fixtures"


def _write(tmp_path: Path, text: str, name: str = "model.yaml") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_load_yaml_document_accepts_utf8_bom(tmp_path: Path) -> None:
    path = _write(tmp_path, "\ufeffschema_version: 1\n")

    assert _load_yaml_document(path) == {"schema_version": 1}


def test_load_yaml_document_rejects_duplicate_keys() -> None:
    path = FIXTURES / "model-invalid-duplicate.yaml"

    with pytest.raises(ConfigurationError) as excinfo:
        _load_yaml_document(path)

    message = str(excinfo.value)
    assert "duplicate key" in message
    assert "line 9" in message
    assert "column 3" in message
    assert "fast" not in message


def test_nested_duplicate_key_is_rejected(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "schema_version: 1\n"
        "models:\n"
        "  fast:\n"
        "    options:\n"
        "      temperature: 0.2\n"
        "      temperature: 0.3\n",
    )

    with pytest.raises(ConfigurationError) as excinfo:
        _load_yaml_document(path)

    message = str(excinfo.value)
    assert "duplicate key" in message
    assert "line 6" in message
    assert "temperature" not in message


def test_duplicate_key_inside_sequence_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, "items:\n  - name: a\n    name: b\n")

    with pytest.raises(ConfigurationError) as excinfo:
        _load_yaml_document(path)

    message = str(excinfo.value)
    assert "duplicate key" in message
    assert "line 3" in message
    assert "name" not in message


def test_recursive_alias_is_rejected(tmp_path: Path) -> None:
    path = _write(tmp_path, "value: &a [*a]\n")

    with pytest.raises(ConfigurationError, match="recursive alias"):
        _load_yaml_document(path)


def test_non_utf8_file_reports_path(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_bytes(b"\xff\xfe\x00")

    with pytest.raises(ConfigurationError) as excinfo:
        _load_yaml_document(path)

    message = str(excinfo.value)
    assert "not valid UTF-8" in message
    assert str(path) in message


def test_yaml_syntax_error_does_not_echo_content(tmp_path: Path) -> None:
    path = _write(tmp_path, "schema_version: 1\nmodels: [sk-sentinel\n")

    with pytest.raises(ConfigurationError) as excinfo:
        _load_yaml_document(path)

    message = str(excinfo.value)
    assert "not valid YAML" in message
    assert re.search(r"at line \d+, column \d+", message) is not None
    assert "sk-sentinel" not in message


def test_missing_file_reports_path(tmp_path: Path) -> None:
    path = tmp_path / "missing.yaml"

    with pytest.raises(ConfigurationError) as excinfo:
        _load_yaml_document(path)

    assert str(path) in str(excinfo.value)


def test_non_mapping_document_is_returned_for_schema_validation(
    tmp_path: Path,
) -> None:
    document = _load_yaml_document(_write(tmp_path, "- one\n- two\n"))

    assert document == ["one", "two"]


def test_null_document_is_returned_for_schema_validation(tmp_path: Path) -> None:
    document = _load_yaml_document(_write(tmp_path, "null\n"))

    assert document is None


def _catalog(tmp_path: Path, text: str) -> ModelCatalog:
    return load_model_catalog(_write(tmp_path, text))


def _single_model_yaml(
    *,
    extra: str = "",
    key: str = "OPENAI_API_KEY",
    protocol: str = "chat_completions",
    endpoint: str = "https://api.example.com/v1",
) -> str:
    return (
        "schema_version: 1\n"
        "models:\n"
        "  fast:\n"
        f"    protocol: {protocol}\n"
        f"    endpoint: {endpoint}\n"
        "    model: gpt-test\n"
        f"    api_key_env: {key}\n"
        f"{extra}"
    )


def _multi_model_yaml() -> str:
    return (
        "schema_version: 1\n"
        "default: fast\n"
        "models:\n"
        "  fast:\n"
        "    protocol: chat_completions\n"
        "    endpoint: https://api.example.com/v1\n"
        "    model: gpt-test\n"
        "    api_key_env: OPENAI_API_KEY\n"
        "  claude:\n"
        "    protocol: anthropic_messages\n"
        "    endpoint: https://api.anthropic.com\n"
        "    model: claude-test\n"
        "    api_key_env: ANTHROPIC_API_KEY\n"
    )


def test_single_model_without_default(tmp_path: Path) -> None:
    catalog = _catalog(
        tmp_path,
        _single_model_yaml(
            extra="    timeout_seconds: 12\n    max_retries: 2\n",
        ),
    )

    assert catalog.default_name == "fast"
    model = catalog.create_chat_model(environ={"OPENAI_API_KEY": "sk-test"})

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-test"
    assert model.openai_api_base == "https://api.example.com/v1"
    assert model.request_timeout == 12.0
    assert model.max_retries == 2


def test_multiple_models_use_default_and_name(tmp_path: Path) -> None:
    catalog = _catalog(tmp_path, _multi_model_yaml())

    default_model = catalog.create_chat_model(environ={"OPENAI_API_KEY": "sk-test"})
    claude = catalog.create_chat_model(
        "claude", environ={"ANTHROPIC_API_KEY": "sk-ant-test"}
    )

    assert isinstance(default_model, ChatOpenAI)
    assert default_model.model_name == "gpt-test"
    assert isinstance(claude, ChatAnthropic)
    assert claude.model == "claude-test"


def test_unknown_model_lists_available_names(tmp_path: Path) -> None:
    catalog = _catalog(tmp_path, _multi_model_yaml())

    with pytest.raises(ConfigurationError) as excinfo:
        catalog.create_chat_model("missing", environ={})

    message = str(excinfo.value)
    assert "Unknown model" in message
    assert "fast" in message
    assert "claude" in message


def test_model_names_are_case_sensitive(tmp_path: Path) -> None:
    catalog = _catalog(tmp_path, _multi_model_yaml())

    with pytest.raises(ConfigurationError, match="Unknown model"):
        catalog.create_chat_model("Fast", environ={"OPENAI_API_KEY": "sk-test"})


def test_unknown_protocol_reports_entry_path(tmp_path: Path) -> None:
    text = _single_model_yaml().replace("chat_completions", "grpc", 1)

    with pytest.raises(ConfigurationError) as excinfo:
        _catalog(tmp_path, text)

    message = str(excinfo.value)
    assert "models.fast.protocol" in message
    assert "unsupported protocol" in message


def test_invalid_endpoint_reports_entry_path(tmp_path: Path) -> None:
    text = _single_model_yaml().replace(
        "https://api.example.com/v1", "ftp://example.com"
    )

    with pytest.raises(ConfigurationError) as excinfo:
        _catalog(tmp_path, text)

    assert "models.fast" in str(excinfo.value)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("timeout_seconds", "true", "must be a number"),
        ("max_retries", "true", "must be an integer"),
    ],
)
def test_boolean_is_rejected_for_numeric_fields(
    tmp_path: Path,
    field: str,
    value: str,
    expected: str,
) -> None:
    text = _single_model_yaml(extra=f"    {field}: {value}\n")

    with pytest.raises(ConfigurationError, match=expected):
        _catalog(tmp_path, text)


def test_missing_api_key_reports_variable_name(tmp_path: Path) -> None:
    catalog = _catalog(tmp_path, _single_model_yaml(key="MISSING_KEY"))

    with pytest.raises(ConfigurationError) as excinfo:
        catalog.create_chat_model(environ={})

    message = str(excinfo.value)
    assert "MISSING_KEY" in message
    assert "not set" in message


def test_empty_api_key_is_rejected(tmp_path: Path) -> None:
    catalog = _catalog(tmp_path, _single_model_yaml(key="EMPTY_KEY"))

    with pytest.raises(ConfigurationError) as excinfo:
        catalog.create_chat_model(environ={"EMPTY_KEY": "   "})

    assert "EMPTY_KEY is empty" in str(excinfo.value)


def test_environ_mapping_supplies_api_key(tmp_path: Path) -> None:
    catalog = _catalog(tmp_path, _single_model_yaml(key="INJECTED_KEY"))

    model = catalog.create_chat_model(environ={"INJECTED_KEY": "sk-injected"})

    assert isinstance(model, ChatOpenAI)
    assert isinstance(model.openai_api_key, SecretStr)
    assert model.openai_api_key.get_secret_value() == "sk-injected"


def test_os_environ_is_not_modified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CATALOG_TEST_KEY", "sk-test")
    before = dict(os.environ)
    catalog = _catalog(tmp_path, _single_model_yaml(key="CATALOG_TEST_KEY"))

    catalog.create_chat_model()

    assert dict(os.environ) == before


def test_literal_api_key_field_is_rejected(tmp_path: Path) -> None:
    text = _single_model_yaml(extra="    api_key: sk-sentinel\n")

    with pytest.raises(ConfigurationError) as excinfo:
        _catalog(tmp_path, text)

    message = str(excinfo.value)
    assert "unknown field(s): api_key" in message
    assert "sk-sentinel" not in message


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2", "only version 1"),
        ("true", "must be an integer"),
    ],
)
def test_schema_version_is_validated(
    tmp_path: Path,
    value: str,
    expected: str,
) -> None:
    text = _single_model_yaml().replace(
        "schema_version: 1", f"schema_version: {value}", 1
    )

    with pytest.raises(ConfigurationError, match=expected):
        _catalog(tmp_path, text)


def test_models_must_not_be_empty(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="at least one model"):
        _catalog(tmp_path, "schema_version: 1\nmodels: {}\n")


def test_default_is_required_for_multiple_models(tmp_path: Path) -> None:
    text = _multi_model_yaml().replace("default: fast\n", "", 1)

    with pytest.raises(ConfigurationError, match="required when multiple"):
        _catalog(tmp_path, text)


def test_default_must_reference_existing_model(tmp_path: Path) -> None:
    text = _multi_model_yaml().replace("default: fast", "default: missing", 1)

    with pytest.raises(ConfigurationError, match="unknown model"):
        _catalog(tmp_path, text)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ('""', "non-empty"),
        ('"   "', "non-empty"),
        ('"bad\\u0007name"', "control characters"),
        ("123", "must be a string"),
    ],
)
def test_display_name_is_validated(
    tmp_path: Path,
    value: str,
    expected: str,
) -> None:
    text = _single_model_yaml(extra=f"    display_name: {value}\n")

    with pytest.raises(ConfigurationError, match=expected):
        _catalog(tmp_path, text)


def test_non_mapping_root_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="<root>: must be a mapping"):
        _catalog(tmp_path, "- one\n")


def test_explicit_null_default_is_rejected(tmp_path: Path) -> None:
    text = _single_model_yaml().replace(
        "schema_version: 1\n", "schema_version: 1\ndefault: null\n", 1
    )

    with pytest.raises(ConfigurationError, match="must be a string"):
        _catalog(tmp_path, text)


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        ("    timeout_seconds: 0\n", "timeout_seconds must be finite and positive"),
        ("    max_retries: -1\n", "max_retries must be non-negative"),
    ],
)
def test_invalid_numeric_values_are_rejected(
    tmp_path: Path,
    extra: str,
    expected: str,
) -> None:
    with pytest.raises(ConfigurationError, match=expected):
        _catalog(tmp_path, _single_model_yaml(extra=extra))


def test_api_key_env_must_be_a_valid_name(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="valid environment variable name"):
        _catalog(tmp_path, _single_model_yaml(key="OPENAI-API-KEY"))


def test_environ_mapping_replaces_process_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-process")
    catalog = _catalog(tmp_path, _single_model_yaml())

    with pytest.raises(ConfigurationError, match="not set"):
        catalog.create_chat_model(environ={})


def test_anthropic_entry_maps_timeout_and_retries(tmp_path: Path) -> None:
    text = _multi_model_yaml().replace(
        "    model: claude-test\n",
        "    model: claude-test\n    timeout_seconds: 45\n    max_retries: 2\n",
        1,
    )
    catalog = _catalog(tmp_path, text)

    claude = catalog.create_chat_model(
        "claude", environ={"ANTHROPIC_API_KEY": "sk-ant-test"}
    )

    assert isinstance(claude, ChatAnthropic)
    assert claude.default_request_timeout == 45.0
    assert claude.max_retries == 2


def test_chat_completions_options_are_mapped(tmp_path: Path) -> None:
    extra = (
        "    options:\n"
        "      temperature: 0.2\n"
        "      max_output_tokens: 1024\n"
        "      top_p: 0.9\n"
        '      stop: ["\\n\\n", "END"]\n'
        "      seed: 42\n"
    )
    catalog = _catalog(tmp_path, _single_model_yaml(extra=extra))

    model = catalog.create_chat_model(environ={"OPENAI_API_KEY": "sk-test"})

    assert isinstance(model, ChatOpenAI)
    assert model.temperature == 0.2
    assert model.max_tokens == 1024
    assert model.top_p == 0.9
    assert model.stop == ["\n\n", "END"]
    assert model.seed == 42


def test_responses_options_are_mapped(tmp_path: Path) -> None:
    extra = (
        "    options:\n"
        "      temperature: 0.1\n"
        "      max_output_tokens: 2048\n"
        "      top_p: 0.8\n"
        "      store: false\n"
        "      reasoning_effort: medium\n"
        "      truncation: disabled\n"
    )
    catalog = _catalog(
        tmp_path,
        _single_model_yaml(protocol="responses", extra=extra),
    )

    model = catalog.create_chat_model(environ={"OPENAI_API_KEY": "sk-test"})

    assert isinstance(model, ChatOpenAI)
    assert model.use_responses_api is True
    assert model.temperature == 0.1
    assert model.max_tokens == 2048
    assert model.top_p == 0.8
    assert model.store is False
    assert model.reasoning_effort == "medium"
    assert model.truncation == "disabled"


def test_anthropic_options_are_mapped(tmp_path: Path) -> None:
    extra = (
        "    options:\n"
        "      temperature: 0.5\n"
        "      max_output_tokens: 4096\n"
        "      top_p: 0.7\n"
        "      top_k: 10\n"
        '      stop_sequences: ["\\n\\n"]\n'
        "      thinking:\n"
        "        mode: budget\n"
        "        budget_tokens: 2048\n"
    )
    catalog = _catalog(
        tmp_path,
        _single_model_yaml(
            protocol="anthropic_messages",
            endpoint="https://api.anthropic.com",
            key="ANTHROPIC_API_KEY",
            extra=extra,
        ),
    )

    model = catalog.create_chat_model(environ={"ANTHROPIC_API_KEY": "sk-ant-test"})

    assert isinstance(model, ChatAnthropic)
    assert model.temperature == 0.5
    assert model.max_tokens == 4096
    assert model.top_p == 0.7
    assert model.top_k == 10
    assert model.stop_sequences == ["\n\n"]
    assert model.thinking == {"type": "enabled", "budget_tokens": 2048}


def test_option_from_another_protocol_is_rejected(tmp_path: Path) -> None:
    extra = "    options:\n      store: false\n"

    with pytest.raises(ConfigurationError, match="unknown field"):
        _catalog(tmp_path, _single_model_yaml(extra=extra))


def test_unknown_option_is_rejected(tmp_path: Path) -> None:
    extra = "    options:\n      temperature_v2: 0.2\n"

    with pytest.raises(ConfigurationError, match="unknown field"):
        _catalog(tmp_path, _single_model_yaml(extra=extra))


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        (
            "      thinking:\n"
            "        mode: budget\n"
            "        budget_tokens: 2048\n",
            "max_output_tokens is required",
        ),
        (
            "      max_output_tokens: 2048\n"
            "      thinking:\n"
            "        mode: budget\n"
            "        budget_tokens: 2048\n",
            "must be less than max_output_tokens",
        ),
        (
            "      max_output_tokens: 4096\n"
            "      thinking:\n"
            "        mode: adaptive\n"
            "        budget_tokens: 2048\n",
            "not allowed for adaptive",
        ),
        (
            "      max_output_tokens: 4096\n"
            "      thinking:\n"
            "        mode: other\n",
            "must be 'budget' or 'adaptive'",
        ),
    ],
)
def test_thinking_rules_are_enforced(
    tmp_path: Path,
    options: str,
    expected: str,
) -> None:
    extra = "    options:\n" + options

    with pytest.raises(ConfigurationError, match=expected):
        _catalog(
            tmp_path,
            _single_model_yaml(
                protocol="anthropic_messages",
                endpoint="https://api.anthropic.com",
                key="ANTHROPIC_API_KEY",
                extra=extra,
            ),
        )


def test_stop_must_be_a_list(tmp_path: Path) -> None:
    extra = '    options:\n      stop: "x"\n'

    with pytest.raises(ConfigurationError, match="must be a list of strings"):
        _catalog(tmp_path, _single_model_yaml(extra=extra))


def test_adaptive_thinking_is_mapped(tmp_path: Path) -> None:
    extra = (
        "    options:\n"
        "      max_output_tokens: 4096\n"
        "      thinking:\n"
        "        mode: adaptive\n"
    )
    catalog = _catalog(
        tmp_path,
        _single_model_yaml(
            protocol="anthropic_messages",
            endpoint="https://api.anthropic.com",
            key="ANTHROPIC_API_KEY",
            extra=extra,
        ),
    )

    model = catalog.create_chat_model(environ={"ANTHROPIC_API_KEY": "sk-ant-test"})

    assert isinstance(model, ChatAnthropic)
    assert model.thinking == {"type": "adaptive"}


def test_thinking_must_be_a_mapping(tmp_path: Path) -> None:
    extra = "    options:\n      thinking: adaptive\n"

    with pytest.raises(ConfigurationError, match="must be a mapping"):
        _catalog(
            tmp_path,
            _single_model_yaml(
                protocol="anthropic_messages",
                endpoint="https://api.anthropic.com",
                key="ANTHROPIC_API_KEY",
                extra=extra,
            ),
        )


def test_thinking_unknown_field_is_rejected(tmp_path: Path) -> None:
    extra = (
        "    options:\n"
        "      max_output_tokens: 4096\n"
        "      thinking:\n"
        "        mode: adaptive\n"
        "        extra: true\n"
    )

    with pytest.raises(ConfigurationError, match="unknown field"):
        _catalog(
            tmp_path,
            _single_model_yaml(
                protocol="anthropic_messages",
                endpoint="https://api.anthropic.com",
                key="ANTHROPIC_API_KEY",
                extra=extra,
            ),
        )


def test_option_error_path_is_not_duplicated(tmp_path: Path) -> None:
    extra = "    options:\n      temperature: high\n"

    with pytest.raises(ConfigurationError) as excinfo:
        _catalog(tmp_path, _single_model_yaml(extra=extra))

    assert str(excinfo.value).count("models.fast.options") == 1


def test_model_summaries_expose_display_names_and_order(tmp_path: Path) -> None:
    text = _multi_model_yaml().replace(
        "    model: gpt-test\n",
        "    model: gpt-test\n    display_name: GPT Test Mini\n",
        1,
    )
    catalog = _catalog(tmp_path, text)

    summaries = [(item.name, item.model, item.display_name) for item in catalog.models]

    assert summaries == [
        ("fast", "gpt-test", "GPT Test Mini"),
        ("claude", "claude-test", "claude"),
    ]


def test_duplicate_display_names_are_allowed(tmp_path: Path) -> None:
    text = (
        _multi_model_yaml()
        .replace(
            "    model: gpt-test\n",
            "    model: gpt-test\n    display_name: Shared Name\n",
            1,
        )
        .replace(
            "    model: claude-test\n",
            "    model: claude-test\n    display_name: Shared Name\n",
            1,
        )
    )
    catalog = _catalog(tmp_path, text)

    assert [item.display_name for item in catalog.models] == [
        "Shared Name",
        "Shared Name",
    ]


def test_catalog_repr_hides_keys_and_endpoints(tmp_path: Path) -> None:
    catalog = _catalog(tmp_path, _multi_model_yaml())

    text = repr(catalog)

    assert "fast" in text
    assert "claude" in text
    assert "OPENAI_API_KEY" not in text
    assert "ANTHROPIC_API_KEY" not in text
    assert "api.example.com" not in text
    assert "sk-" not in text


def test_display_name_cannot_be_used_for_lookup(tmp_path: Path) -> None:
    text = _single_model_yaml(extra="    display_name: Friendly Name\n")
    catalog = _catalog(tmp_path, text)

    with pytest.raises(ConfigurationError, match="Unknown model"):
        catalog.create_chat_model(
            "Friendly Name", environ={"OPENAI_API_KEY": "sk-test"}
        )


def test_display_name_cannot_be_used_as_default(tmp_path: Path) -> None:
    text = _single_model_yaml(extra="    display_name: Friendly Name\n").replace(
        "schema_version: 1\n",
        "schema_version: 1\ndefault: Friendly Name\n",
        1,
    )

    with pytest.raises(ConfigurationError, match="unknown model"):
        _catalog(tmp_path, text)
