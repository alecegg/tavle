"""Input blocks render client-side: registration, props, hosts, read-only, validation.

The component DOM is checked in `tests/pages/components/inputs.test.js` against
`components/fixtures/<block>.json`, the HTML the former Python renderers produced.
These tests keep the Python side of that contract: the fixture inputs still produce
the recorded props, the statements render hosts whose no-script fallback is their
source, hostile text stays out of the markup, and a static export disables the hosts.
"""

from __future__ import annotations

import json
import threading
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest
from ui_fence import block_host, example_fence

from varde.pages.blocks.check import COMPONENT_SPECS, check, check_props
from varde.pages.blocks_render.inputs import choice_props, form_props
from varde.pages.blocks_render.inputs_ordered import ranking_props, slider_props
from varde.pages.blocks_render.registry import COMPONENTS
from varde.pages.components import component_bundle
from varde.pages.render import render_page
from varde.pages.serve import PageServer
from varde.pages.template import make_read_only

FIXTURES = Path(__file__).parent / "components" / "fixtures"
BLOCKS = ("choice", "form", "comment", "ranking", "slider")
HOSTILE = '<script>alert(1)</script>"><img src=x onerror=alert(1)>'
DOC = (
    "```ui\n"
    'pick = choice(question: "Which?", options: ["a", {"label": "B", "value": "b"}])\n'
    'setup = form(fields: [{"name": "owner", "label": "Owner", "type": "text"}])\n'
    'note = comment(label: "Anything?")\n'
    'order = ranking(question: "Urgency?", items: ["a", "b"])\n'
    'conf = slider(label: "Confidence", min: 0, max: 10, step: 2)\n'
    "```\n"
)


def _fixture(name: str) -> list[dict[str, Any]]:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("block", BLOCKS)
def test_block_is_client_side_and_bundled(block: str) -> None:
    assert COMPONENTS[block].props is not None
    assert COMPONENTS[block].answer_schema is not None
    assert f'components["{block}"]' in component_bundle()


@pytest.mark.parametrize("block", BLOCKS)
def test_fixture_inputs_still_produce_the_recorded_props(block: str) -> None:
    prepare = COMPONENTS[block].props
    assert prepare is not None
    cases = _fixture(block)
    assert len(cases) >= 4
    for case in cases:
        assert json.loads(json.dumps(prepare(case["input"]))) == case["props"]
        assert case["html"].startswith(f'<div class="vb {block}" data-component=')


def test_statements_render_hosts_with_their_source_as_fallback() -> None:
    body = render_page(DOC, "t.md").body
    for block in BLOCKS:
        assert f'data-mithril="{block}"' in body, block
    assert "vb-error" not in body and body.count("<noscript><pre") == len(BLOCKS)
    assert "conf = slider(label: &quot;Confidence&quot;" in body
    assert 'data-component="' not in body  # the component writes the hydration root


class _Unsafe(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.found: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        bad_attr = [n for n, _ in attrs if n.startswith("on") or n == "style"]
        self.found += bad_attr + ([tag] if tag in ("img", "iframe") else [])


def test_hostile_text_stays_in_escaped_props_and_fallback() -> None:
    text = json.dumps(HOSTILE)
    doc = (
        "```ui\n"
        f"c = choice(question: {text}, "
        f'options: [{{"label": {text}, "detail": {text}}}])\n'
        f"s = slider(label: {text}, min: 0, max: 3, "
        f'labels: [{text}, "H"])\n'
        "```\n"
    )
    body = render_page(doc, "t.md").body
    unsafe = _Unsafe()
    unsafe.feed(body)
    assert unsafe.found == [] and "<img" not in body and "alert(1)</script>" not in body
    assert "\\u003cscript>alert(1)" in body


def test_choice_marks_the_recommended_option_and_keeps_values() -> None:
    props = choice_props(
        {
            "question": "Q",
            "options": ["a", {"label": "B", "value": "b", "recommended": True}],
        }
    )
    assert [o["value"] for o in props["options"]] == ["a", "b"]  # type: ignore[attr-defined]
    assert [o["recommended"] for o in props["options"]] == [False, True]  # type: ignore[attr-defined]


def test_form_hands_the_client_only_its_whitelisted_field_keys() -> None:
    props = form_props(
        {
            "fields": [
                {"name": "n", "label": "N", "type": "number", "min": 1, "max": 9},
                {"name": "r", "label": "R", "type": "select", "options": ["a"]},
                {"name": "t", "label": "T", "type": "text", "maxlength": 5},
            ]
        }
    )
    fields = props["fields"]
    assert fields[1]["client"] == {"name": "r", "type": "select"}  # type: ignore[index]
    assert fields[0]["client"] == {"name": "n", "type": "number", "min": 1, "max": 9}  # type: ignore[index]
    assert fields[0]["hint"] == "From 1 to 9." and fields[2]["limit"] == 5  # type: ignore[index]


def test_form_label_drops_the_fields_own_key_in_parentheses() -> None:
    props = form_props(
        {
            "fields": [
                {
                    "name": "review_date",
                    "label": "Review date (review_date), x",
                    "type": "text",
                },
                {"name": "n", "label": "Hours (about 3)", "type": "number"},
            ]
        }
    )
    labels = [f["label"] for f in props["fields"]]  # type: ignore[attr-defined]
    assert labels == ["Review date, x", "Hours (about 3)"]


def test_ranking_names_twins_apart_and_slider_reports_text_and_ticks() -> None:
    ranked = ranking_props(
        {"question": "Q", "items": [{"label": "Same", "value": "x"}, "b"]}
    )
    assert [i["name"] for i in ranked["items"]] == ["Same (x)", "b"]  # type: ignore[attr-defined]
    even = slider_props({"label": "L", "min": 0, "max": 10, "step": 2})
    assert even["ticks"] == 6 and even["stepText"] == "2"
    assert slider_props({"label": "L", "min": 0, "max": 100})["ticks"] == 0  # too many
    assert slider_props({"label": "L", "min": 0, "max": 1, "step": 0.3})["ticks"] == 0
    assert slider_props({"label": "L", "min": 0.0, "max": 3.0})["minText"] == "0.0"


def test_read_only_page_marks_every_input_host() -> None:
    hosts = [
        block_host("comment", {"label": "L"}),
        block_host("ranking", {"question": "Q", "items": ["a", "b"]}),
        block_host("slider", {"label": "L", "min": 0, "max": 3}),
    ]
    out = make_read_only("".join(hosts))
    assert out.count("data-readonly data-mithril=") == len(hosts)


LIVE = (
    "# Page\n\nLead {n}.\n\n```ui\n"
    'pick = choice(question: "Which?", options: ["a", "b{n}"])\n'
    'setup = form(fields: [{{"name": "owner", "label": "Owner", "type": "text"}}])\n'
    'note = comment(label: "Anything?")\n'
    "```\n"
)


@pytest.fixture
def live_site(tmp_path: Path, browser_session: Any) -> Any:
    doc = tmp_path / "page.md"
    doc.write_text(LIVE.format(n=1), encoding="utf-8")
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    page = browser_session.new_page()
    page.set_default_timeout(10_000)
    page.goto(f"http://127.0.0.1:{server.port}/")
    page.wait_for_selector(".comment[data-hydrated]")
    yield page, doc
    page.close()
    server.shutdown()
    server.server_close()
    thread.join(5)


@pytest.mark.slow
def test_live_update_keeps_what_the_reader_entered_and_remounts_changed_blocks(
    live_site: Any,
) -> None:
    page, doc = live_site
    page.locator("[data-item='setup'] [data-field='owner']").fill("ann")
    page.get_by_text("a", exact=True).click()
    box = page.locator(".comment-text")
    box.fill("draft")
    page.evaluate("document.querySelector('.comment-text').dataset.same = 'yes'")
    box.focus()

    # an edit elsewhere on the page: no widget changes, so none is touched
    doc.write_text(LIVE.format(n=1).replace("Lead 1", "Lead 2"), encoding="utf-8")
    page.get_by_text("Lead 2.").wait_for()
    assert page.evaluate("document.activeElement.className") == "comment-text"
    assert page.evaluate("document.activeElement.dataset.same") == "yes"
    assert box.input_value() == "draft"
    assert page.locator("[data-field='owner']").input_value() == "ann"
    assert page.locator("input[value='a']").is_checked()

    # one widget's own edit remounts that widget (fresh, as before); the others stay
    doc.write_text(LIVE.format(n=3), encoding="utf-8")
    page.get_by_text("b3", exact=True).wait_for()
    assert not page.locator("input[value='a']").is_checked()
    assert page.locator("[data-field='owner']").input_value() == "ann"
    assert box.input_value() == "draft"
    page.locator(".choice-send").click()
    assert "Pick an option" in page.locator(".choice-error").inner_text()


_CHOICE = {"question": "Q", "options": ["a"]}
_FIELD = {"name": "n", "label": "L", "type": "text"}
_FORM = {"fields": [_FIELD]}
_COMMENT = {"label": "L"}
_RANKING = {"question": "Q", "items": ["a", "b"]}
_SLIDER = {"label": "L", "min": 0, "max": 5}


def _without(props: dict[str, Any], key: str) -> dict[str, Any]:
    return {k: v for k, v in props.items() if k != key}


def _in_field(**changes: Any) -> dict[str, Any]:
    return {"fields": [{**_FIELD, **changes}]}


PROPERTY_CASES = [
    # an unknown field
    ("choice", {**_CHOICE, "extra": 1}, "extra"),
    ("form", {**_FORM, "extra": 1}, "extra"),
    ("form", _in_field(extra=1), "extra"),
    ("comment", {**_COMMENT, "extra": 1}, "extra"),
    ("ranking", {**_RANKING, "extra": 1}, "extra"),
    ("slider", {**_SLIDER, "extra": 1}, "extra"),
    # a missing required field
    ("choice", _without(_CHOICE, "question"), "question"),
    ("choice", _without(_CHOICE, "options"), "options"),
    ("form", {}, "fields"),
    ("form", {"fields": [_without(_FIELD, "label")]}, "label"),
    ("form", {"fields": [_without(_FIELD, "name")]}, "name"),
    ("form", {"fields": [_without(_FIELD, "type")]}, "type"),
    ("comment", {}, "label"),
    ("ranking", _without(_RANKING, "items"), "items"),
    ("slider", _without(_SLIDER, "min"), "min"),
    ("slider", _without(_SLIDER, "label"), "label"),
    # a wrong type
    ("choice", {**_CHOICE, "question": 1}, "question"),
    ("choice", {**_CHOICE, "options": "a"}, "options"),
    ("choice", {**_CHOICE, "multiple": "yes"}, "multiple"),
    ("form", {"fields": "x"}, "fields"),
    ("form", {"fields": ["x"]}, "fields[1]"),
    ("form", _in_field(label=1), "label"),
    ("form", _in_field(required="yes"), "required"),
    ("form", _in_field(maxlength="9"), "maxlength"),
    ("form", _in_field(maxlength=None), "maxlength"),
    ("form", _in_field(type="date"), "type"),
    ("comment", {"label": 1}, "label"),
    ("ranking", {**_RANKING, "items": "ab"}, "items"),
    ("slider", {**_SLIDER, "min": "a"}, "min"),
    ("slider", {**_SLIDER, "step": True}, "step"),
    ("slider", {**_SLIDER, "labels": "ab"}, "labels"),
    ("slider", {**_SLIDER, "labels": ["a", 1]}, "labels"),
    ("form", _in_field(type="number", min="a"), "min"),
    ("form", _in_field(type="select", options="ab"), "options"),
    ("form", _in_field(type="select", options=["a", 1]), "options"),
    # a blank value
    ("choice", {**_CHOICE, "question": " "}, "question"),
    ("choice", {**_CHOICE, "options": []}, "options"),
    ("form", {"fields": []}, "fields"),
    ("form", {**_FORM, "title": " "}, "title"),
    ("form", {**_FORM, "submit": ""}, "submit"),
    ("form", _in_field(label=" "), "label"),
    ("form", _in_field(name=""), "name"),
    ("form", _in_field(type="select", options=[]), "options"),
    ("form", _in_field(type="select", options=["a", " "]), "options"),
    ("comment", {"label": " "}, "label"),
    ("comment", {**_COMMENT, "submit": " "}, "submit"),
    ("ranking", {**_RANKING, "question": ""}, "question"),
    ("ranking", {**_RANKING, "items": []}, "items"),
    ("slider", {**_SLIDER, "label": " "}, "label"),
    ("slider", {**_SLIDER, "labels": ["a", " "]}, "labels"),
    # a mistake only the widget sees: still one fault
    ("form", _in_field(min=1), "min"),
    ("form", _in_field(maxlength=0), "maxlength"),
    ("form", _in_field(name="A b"), "name"),
    ("form", _in_field(label="x" * 300), "label"),
    ("form", _in_field(type="number", min=float("inf")), "min"),
    ("form", _in_field(type="number", min=5, max=1), "min"),
    ("form", _in_field(type="select"), "options"),
    ("choice", {**_CHOICE, "options": ["a", "a"]}, "options"),
    ("ranking", {**_RANKING, "items": ["a"]}, "items"),
    ("slider", {**_SLIDER, "min": float("nan")}, "min"),
    ("slider", {**_SLIDER, "step": float("inf")}, "step"),
    ("slider", {**_SLIDER, "labels": ["a"]}, "labels"),
    ("slider", {**_SLIDER, "min": 9}, "min"),
]


@pytest.mark.parametrize(("block", "props", "field"), PROPERTY_CASES)
def test_a_property_mistake_gets_one_fault_naming_the_field(
    block: str, props: dict[str, Any], field: str
) -> None:
    faults = check_props(block, props, 1)
    assert len(faults) == 1, faults
    assert field in faults[0].message


@pytest.mark.parametrize("block", BLOCKS)
def test_each_example_is_valid(block: str) -> None:
    assert check(example_fence(COMPONENT_SPECS[block].example)) == []
