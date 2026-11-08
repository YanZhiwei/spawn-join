"""Behavioral tests for the optional Pydantic error-conversion helper."""

from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from spawn_join_common.validation import validate_with


class WrappedError(Exception):
    """Caller-owned error type for conversion tests."""


def test_validate_with_returns_the_original_typed_result_and_runs_once() -> None:
    result = {"status": "ok"}
    call_count = 0

    def operation() -> dict[str, str]:
        nonlocal call_count
        call_count += 1
        return result

    returned = validate_with(
        operation,
        error=lambda message: WrappedError(message),
        message=lambda exc: "unused",
    )

    assert returned is result
    assert call_count == 1


def test_validation_error_uses_safe_caller_callbacks_and_preserves_cause() -> None:
    adapter: TypeAdapter[int] = TypeAdapter(int)
    operation_errors: list[ValidationError] = []
    message_errors: list[ValidationError] = []
    error_messages: list[str] = []
    call_count = 0

    def operation() -> int:
        nonlocal call_count
        call_count += 1
        try:
            return adapter.validate_python("secret-input")
        except ValidationError as exc:
            operation_errors.append(exc)
            raise

    def message(exc: ValidationError) -> str:
        message_errors.append(exc)
        return "safe validation failure"

    def error(text: str) -> Exception:
        error_messages.append(text)
        return WrappedError(text)

    with pytest.raises(WrappedError) as exc_info:
        validate_with(operation, error=error, message=message)

    assert call_count == 1
    assert len(operation_errors) == 1
    assert message_errors == operation_errors
    assert error_messages == ["safe validation failure"]
    assert str(exc_info.value) == "safe validation failure"
    assert "secret-input" not in str(exc_info.value)
    assert exc_info.value.__cause__ is operation_errors[0]


def test_non_pydantic_exception_propagates_as_the_same_object() -> None:
    direct = ValueError("direct failure")
    callback_calls: list[str] = []

    def operation() -> int:
        raise direct

    def error(message: str) -> Exception:
        callback_calls.append(f"error:{message}")
        return WrappedError(message)

    def message(exc: ValidationError) -> str:
        callback_calls.append(f"message:{exc}")
        return "should not be called"

    with pytest.raises(ValueError) as exc_info:
        validate_with(operation, error=error, message=message)

    assert exc_info.value is direct
    assert callback_calls == []
