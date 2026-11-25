"""The change vocabulary on data-model and endpoint: enum, was, escaping, identity."""

from __future__ import annotations

from pathlib import Path

import pytest
from tavle.blocks import check_props
from tavle.blocks.change import CHANGES, change_rule_faults
from tavle.blocks_render.backend import data_model_props, endpoint_props
from tavle.blocks_render.change import copy_line
from ui_paths import UI_STATIC_DIR

from varde.pagelib.page.page_check import check
from varde.pagelib.page.render import render_page

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


def test_was_rules() -> None:
    assert change_rule_faults({"change": "added"}, "x") == []
    assert change_rule_faults({"change": "renamed", "was": "a"}, "x") == []
    assert change_rule_faults({"change": "modified", "was": "a"}, "x") == []
    assert change_rule_faults({"change": "renamed"}, "x")
    assert change_rule_faults({"change": "removed", "was": "a"}, "x")
    assert change_rule_faults({"was": "a"}, "x")


def test_enum_and_blank_was_come_from_the_properties() -> None:
    response = {"status": 200, "change": "moved"}
    unknown = check_props("endpoint", {**PLAIN_ENDPOINT, "responses": [response]}, 1)
    assert len(unknown) == 1
    assert "responses[1].change" in unknown[0].message
    assert all(c in unknown[0].message for c in CHANGES)
    blank = {"status": 200, "change": "modified", "was": ""}
    faults = check_props("endpoint", {**PLAIN_ENDPOINT, "responses": [blank]}, 1)
    assert len(faults) == 1 and "responses[1].was" in faults[0].message
    field = model_with({"type": "t", "change": "modified", "was": " "})
    faults = check_props("data-model", field, 1)
    assert len(faults) == 1 and "'was'" in faults[0].message


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


def test_change_has_no_inline_start_border() -> None:
    css = (UI_STATIC_DIR / "css/47-change.css").read_text()
    assert "border-inline-start" not in css
    assert "border-left" not in css


ENTITY: dict[str, object] = {"name": "a", "key": "id", "fields": {"id": "uuid"}}
RELATION = {"to": "a", "kind": "one-to-one"}
RESPONSE = {"status": 200}


def entity_with(**changes: object) -> dict[str, object]:
    return {"entity": [{**ENTITY, **changes}]}


def without(table: dict[str, object], key: str) -> dict[str, object]:
    return {k: v for k, v in table.items() if k != key}


def test_data_model_property_faults_are_single_and_name_the_field() -> None:
    cases: list[tuple[dict[str, object], str]] = [
        (entity_with(extra=1), "entity[1].extra"),
        ({"entity": [without(ENTITY, "key")]}, "entity[1].key"),
        (entity_with(key=1), "entity[1].key"),
        (entity_with(name=" "), "entity[1].name"),
        (entity_with(fields="x"), "entity[1].fields"),
        (entity_with(relations={}), "entity[1].relations"),
        (entity_with(relations=[{"to": "a"}]), "entity[1].relations[1].kind"),
        (entity_with(relations=[{**RELATION, "kind": "some"}]), "relations[1].kind"),
        (entity_with(relations=[{**RELATION, "to": ""}]), "relations[1].to"),
        ({**entity_with(), "layout": "ring"}, "layout"),
        ({"entity": []}, "entity"),
        ({}, "entity"),
    ]
    for data, field in cases:
        faults = check_props("data-model", data, 1)
        assert len(faults) == 1, (data, faults)
        assert field in faults[0].message


def test_endpoint_property_faults_are_single_and_name_the_field() -> None:
    cases: list[tuple[dict[str, object], str]] = [
        ({**PLAIN_ENDPOINT, "extra": 1}, "extra"),
        (without(PLAIN_ENDPOINT, "auth"), "auth"),
        ({**PLAIN_ENDPOINT, "auth": 1}, "auth"),
        ({**PLAIN_ENDPOINT, "path": " "}, "path"),
        ({**PLAIN_ENDPOINT, "path": "x"}, "path"),
        ({**PLAIN_ENDPOINT, "method": "FETCH"}, "method"),
        ({**PLAIN_ENDPOINT, "request": []}, "request"),
        ({**PLAIN_ENDPOINT, "request": {}}, "request"),
        ({**PLAIN_ENDPOINT, "responses": []}, "responses"),
        ({**PLAIN_ENDPOINT, "responses": [{**RESPONSE, "x": 1}]}, "responses[1].x"),
        ({**PLAIN_ENDPOINT, "responses": [{"body": "b"}]}, "responses[1].status"),
        ({**PLAIN_ENDPOINT, "responses": [{"status": "200"}]}, "responses[1].status"),
        ({**PLAIN_ENDPOINT, "responses": [{"status": 99}]}, "responses[1].status"),
        ({**PLAIN_ENDPOINT, "responses": [{**RESPONSE, "body": " "}]}, "body"),
    ]
    for data, field in cases:
        faults = check_props("endpoint", data, 1)
        assert len(faults) == 1, (data, faults)
        assert field in faults[0].message


def test_request_and_field_items_keep_their_own_checks() -> None:
    cases = [
        {"q": {"type": "t", "x": 1}},
        {"q": {"change": "added"}},
        {"q": {"type": ""}},
        {"q": {"type": "t", "change": "moved"}},
        {"q": 3},
    ]
    for request in cases:
        faults = check_props("endpoint", {**PLAIN_ENDPOINT, "request": request}, 1)
        assert len(faults) == 1, (request, faults)
        assert "endpoint.request.q" in faults[0].message
