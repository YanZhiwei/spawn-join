"""Private declarative model-file shapes, separate from public domain options."""

from __future__ import annotations

from typing import Annotated, cast

from pydantic import BeforeValidator, ValidationInfo

from spawn_join_llm_provider import (
    AnthropicMessagesOptions,
    AnthropicThinking,
    AnthropicThinkingAdaptive,
    AnthropicThinkingBudget,
    AnthropicThinkingDisabled,
    ChatCompletionsOptions,
    ConfigurationError,
    ResponsesOptions,
)
from spawn_join_llm_provider.options import ReasoningEffort, Truncation

from ._validation import (
    FileInput,
    Integer,
    OptionalBoolean,
    OptionalInteger,
    OptionalNumber,
    OptionalStrings,
    OptionalText,
    Text,
    input_path,
    reader,
    validate_input,
)


class CatalogInput(FileInput):
    schema_version: Integer
    models: object
    default: object = None


class EntryInputV1(FileInput):
    # Entry values are checked in domain-construction order. Validating all
    # scalars eagerly would change which error wins in an invalid configuration.
    protocol: object
    endpoint: object
    model: object
    api_key_env: object
    timeout_seconds: object = None
    max_retries: object = None
    display_name: object = None
    options: object = None


class EntryInputV2(EntryInputV1):
    metadata_ref: object = None
    metadata_source: object = None
    metadata: object = None


class SourceRefInput(FileInput):
    provider: Text
    model: Text


class ThinkingInput(FileInput):
    mode: Text
    budget_tokens: object = None

    def to_thinking(self, path: str) -> AnthropicThinking:
        if self.mode == "adaptive":
            if "budget_tokens" in self.model_fields_set:
                raise ConfigurationError(
                    f"{path}: budget_tokens is not allowed for adaptive thinking"
                )
            return AnthropicThinkingAdaptive()
        if self.mode == "disabled":
            if "budget_tokens" in self.model_fields_set:
                raise ConfigurationError(
                    f"{path}: budget_tokens is not allowed for disabled thinking"
                )
            return AnthropicThinkingDisabled()
        if self.mode != "budget":
            raise ConfigurationError(
                f"{path}.mode: must be 'budget', 'adaptive', or 'disabled'"
            )
        if "budget_tokens" not in self.model_fields_set:
            raise ConfigurationError(
                f"{path}: budget_tokens is required for budget thinking"
            )
        budget = reader.as_int(self.budget_tokens, f"{path}.budget_tokens")
        try:
            return AnthropicThinkingBudget(budget_tokens=budget)
        except ConfigurationError as exc:
            raise ConfigurationError(f"{path}: {exc}") from exc


def _thinking(value: object, info: ValidationInfo) -> AnthropicThinking:
    path = f"{input_path(info)}.thinking"
    return validate_input(ThinkingInput, value, path).to_thinking(path)


class ChatCompletionsInput(FileInput):
    temperature: OptionalNumber = None
    max_output_tokens: OptionalInteger = None
    top_p: OptionalNumber = None
    stop: OptionalStrings = None
    seed: OptionalInteger = None
    reasoning_effort: OptionalText = None

    def to_options(self) -> ChatCompletionsOptions:
        return ChatCompletionsOptions(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            top_p=self.top_p,
            stop=self.stop,
            seed=self.seed,
            reasoning_effort=cast(ReasoningEffort | None, self.reasoning_effort),
        )


class ResponsesInput(FileInput):
    temperature: OptionalNumber = None
    max_output_tokens: OptionalInteger = None
    top_p: OptionalNumber = None
    store: OptionalBoolean = None
    reasoning_effort: OptionalText = None
    truncation: OptionalText = None

    def to_options(self) -> ResponsesOptions:
        return ResponsesOptions(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            top_p=self.top_p,
            store=self.store,
            reasoning_effort=cast(ReasoningEffort | None, self.reasoning_effort),
            truncation=cast(Truncation | None, self.truncation),
        )


class AnthropicInput(FileInput):
    temperature: OptionalNumber = None
    max_output_tokens: OptionalInteger = None
    top_p: OptionalNumber = None
    top_k: OptionalInteger = None
    stop_sequences: OptionalStrings = None
    thinking: Annotated[AnthropicThinking | None, BeforeValidator(_thinking)] = None
    reasoning_effort: OptionalText = None

    def to_options(self) -> AnthropicMessagesOptions:
        return AnthropicMessagesOptions(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            top_p=self.top_p,
            top_k=self.top_k,
            stop_sequences=self.stop_sequences,
            thinking=self.thinking,
            reasoning_effort=cast(ReasoningEffort | None, self.reasoning_effort),
        )
