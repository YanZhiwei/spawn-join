"""Model page validation tests."""

from types import SimpleNamespace

import pytest
from spawn_join_llm_channel._page import InvalidPageError, model_infos, next_cursor


@pytest.mark.parametrize("data", [None, "not-a-list", {}, 1])
def test_model_infos_rejects_non_list_data(data: object) -> None:
    with pytest.raises(InvalidPageError):
        model_infos(SimpleNamespace(data=data))


@pytest.mark.parametrize(
    "item",
    [
        object(),
        SimpleNamespace(id=None),
        SimpleNamespace(id=""),
        SimpleNamespace(id="   "),
        SimpleNamespace(id="a", display_name=1),
    ],
)
def test_model_infos_rejects_invalid_items(item: object) -> None:
    with pytest.raises(InvalidPageError):
        model_infos(SimpleNamespace(data=[item]))


def test_model_infos_accepts_valid_items() -> None:
    infos = model_infos(
        SimpleNamespace(
            data=[
                SimpleNamespace(id="a"),
                SimpleNamespace(id="b", display_name="B"),
            ]
        )
    )
    assert [info.id for info in infos] == ["a", "b"]
    assert infos[1].display_name == "B"


def test_next_cursor_requires_boolean_flag_and_text_id() -> None:
    with pytest.raises(InvalidPageError):
        next_cursor(SimpleNamespace(has_more="yes", last_id=None))
    with pytest.raises(InvalidPageError):
        next_cursor(SimpleNamespace(has_more=True, last_id=1))


def test_next_cursor_returns_last_id_only_when_more() -> None:
    assert next_cursor(SimpleNamespace(has_more=True, last_id="next")) == "next"
    assert next_cursor(SimpleNamespace(has_more=False, last_id="next")) is None
    assert next_cursor(SimpleNamespace(has_more=True, last_id=None)) is None
    assert next_cursor(SimpleNamespace(has_more=True, last_id="")) is None
    assert next_cursor(SimpleNamespace(has_more=True, last_id="   ")) is None
    assert next_cursor(SimpleNamespace(has_more=None, last_id="next")) == "next"
