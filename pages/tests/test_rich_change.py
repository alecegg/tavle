"""The change vocabulary on data-model and endpoint: enum, was, escaping, identity."""

from __future__ import annotations

from pathlib import Path

import pytest
from varde_pages.blocks import check, check_props
from varde_pages.blocks.change import CHANGES, change_faults
from varde_pages.blocks_render.backend import data_model_props, endpoint_props
from varde_pages.blocks_render.change import copy_line
from varde_pages.render import render_page

FIXTURES = Path(__file__).parent / "fixtures" / "widgets"
PLAIN_MODEL: dict[str, object] = {
    "entity": [
        {
            "name": "order",
            "key": "id",
            "fields": {"id": "uuid", "total": "cents"},
            "relations": [{"to": "order", "kind": "one-to-one"}],
        }
    ]
}
PLAIN_ENDPOINT: dict[str, object] = {
    "method": "GET",
    "path": "/x",
    "auth": "none",
    "request": {"q": "text"},
    "responses": [{"status": 200, "body": "ok"}],
}


def model_with(field: object) -> dict[str, object]:
    return {
        "entity": [{"name": "a", "key": "id", "fields": {"id": "uuid", "f": field}}]
    }


def test_enum_and_was_rules() -> None:
    assert change_faults({"change": "added"}, "x") == []
    assert change_faults({"change": "renamed", "was": "a"}, "x") == []
    assert change_faults({"change": "modified", "was": "a"}, "x") == []
    unknown = change_faults({"change": "moved"}, "x")
    assert unknown and all(c in unknown[0].message for c in CHANGES)
    assert change_faults({"change": "renamed"}, "x")
    assert change_faults({"change": "removed", "was": "a"}, "x")
    assert change_faults({"was": "a"}, "x")
    assert change_faults({"change": "modified", "was": ""}, "x")


def test_spec_checks_every_place_a_change_can_sit() -> None:
    bad_field = model_with({"type": "text", "change": "renamed"})
    assert check_props("data-model", bad_field, 1)
    assert (
        check_props("data-model", model_with({"type": "t", "change": "added"}), 1) == []
    )
    assert check_props("data-model", model_with({"change": "added"}), 1)
    assert check_props("data-model", model_with(3), 1)
    entity = {"name": "a", "key": "id", "fields": {"id": "uuid"}, "change": "gone"}
    assert check_props("data-model", {"entity": [entity]}, 1)
    endpoint = {**PLAIN_ENDPOINT, "change": "removed", "was": "x"}
    assert check_props("endpoint", endpoint, 1)
    row = {"status": 200, "change": "renamed"}
    assert check_props("endpoint", {**PLAIN_ENDPOINT, "responses": [row]}, 1)
    request = {"q": {"type": "text", "change": "bad"}}
    assert check_props("endpoint", {**PLAIN_ENDPOINT, "request": request}, 1)


def test_documents_without_change_carry_no_change_props() -> None:
    model = data_model_props(PLAIN_MODEL)
    endpoint = endpoint_props(PLAIN_ENDPOINT)
    for props in (model, endpoint):
        assert props["legend"] == "" and props["copy"] is None
    assert model["summary"] == "1 entity, 1 relation"
    assert endpoint["summary"] == "GET /x: auth none, 1 response"
    assert model["entities"][0]["fields"][0] == {  # type: ignore[index]
        "name": "id",
        "type": "uuid",
        "change": "",
        "was": "",
        "key": True,
    }
    assert endpoint["request"] == [
        {"name": "q", "type": "text", "change": "", "was": "", "key": False}
    ]


def test_renamed_field_carries_old_and_new_name() -> None:
    field = {"type": "text", "change": "renamed", "was": "name"}
    props = data_model_props(model_with(field))
    row = props["entities"][0]["fields"][1]  # type: ignore[index]
    assert (row["name"], row["change"], row["was"]) == ("f", "renamed", "name")
    assert props["legend"] == "Changes: 1 renamed"


def test_removed_field_keeps_its_type() -> None:
    props = data_model_props(model_with({"type": "text", "change": "removed"}))
    row = props["entities"][0]["fields"][1]  # type: ignore[index]
    assert (row["type"], row["change"]) == ("text", "removed")


def test_copy_text_lists_each_changed_row() -> None:
    assert copy_line("renamed", "a.f", "name") == "renamed a.f (was name)"
    assert copy_line("added", "a.f", "") == "added a.f"
    field = {"type": "text", "change": "renamed", "was": "name"}
    assert data_model_props(model_with(field))["copy"] == "renamed a.f (was name)"
    endpoint = {
        **PLAIN_ENDPOINT,
        "change": "modified",
        "was": "GET /y",
        "responses": [{"status": 404, "change": "added"}],
    }
    copy = endpoint_props(endpoint)["copy"]
    assert copy == "modified GET /x (was GET /y)\nadded response 404"


def test_two_hundred_changed_fields_each_get_a_change() -> None:
    fields = {f"f{i}": {"type": "t", "change": "added"} for i in range(200)}
    props = data_model_props({"entity": [{"name": "a", "key": "f0", "fields": fields}]})
    assert [f["change"] for f in props["entities"][0]["fields"]] == ["added"] * 200  # type: ignore[index]
    assert props["legend"] == "Changes: 200 added"


@pytest.mark.parametrize("name", ["rich-change.md", "rich-change-stress.md"])
def test_fixtures_validate_and_render_without_errors(name: str) -> None:
    doc = (FIXTURES / name).read_text()
    assert check(doc) == []
    body = render_page(doc, "t.md").body
    assert "vb-error" not in body and '"change": "' in body
    assert "<img" not in body and "<script>alert" not in body and "style=" not in body
