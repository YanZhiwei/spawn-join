"""Validate Provider model pages before exposing them through the contract."""

from typing import cast

from spawn_join_llm_provider import ConfigurationError, ModelInfo


class InvalidPageError(Exception):
    """A Provider returned a model page that does not match the contract."""


def model_infos(page: object) -> tuple[ModelInfo, ...]:
    """Return validated model identifiers from one SDK page."""
    data = getattr(page, "data", None)
    if not isinstance(data, list):
        raise InvalidPageError("model page data is not a list")
    infos: list[ModelInfo] = []
    for item in cast(list[object], data):
        model_id = getattr(item, "id", None)
        display_name = getattr(item, "display_name", None)
        if not isinstance(model_id, str) or not model_id.strip():
            raise InvalidPageError("model page item has no valid id")
        if display_name is not None and not isinstance(display_name, str):
            raise InvalidPageError("model page item has an invalid display name")
        try:
            infos.append(ModelInfo(id=model_id, display_name=display_name))
        except ConfigurationError as exc:
            raise InvalidPageError("model page item is invalid") from exc
    return tuple(infos)


def next_cursor(page: object) -> str | None:
    """Return a validated Anthropic cursor, or None when there is no next page."""
    has_more = getattr(page, "has_more", None)
    last_id = getattr(page, "last_id", None)
    if has_more is not None and not isinstance(has_more, bool):
        raise InvalidPageError("model page has an invalid has_more flag")
    if last_id is not None and not isinstance(last_id, str):
        raise InvalidPageError("model page has an invalid last_id")
    return last_id if has_more else None
