"""Input blocks render client-side: registration, props, hosts, read-only, validation.

The component DOM is checked in `tavle tests/components/inputs.test.js` against
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
from ui_fence import block_host
from ui_paths import UI_FIXTURES

from tavle import COMPONENTS, PageServer, check_props, make_read_only
from tavle.blocks.inputs import no_faults, option_list
from tavle.blocks.reference import type_text
from tavle.blocks.spec import BlockSpec
from tavle.blocks_render.inputs import choice_props, form_props
from tavle.blocks_render.inputs_ordered import ranking_props, slider_props
from tavle.page.render import render_page

FIXTURES = UI_FIXTURES
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


def _rewrite(doc: Path, text: str) -> None:
    # The server thread can read between write_text's truncate and its write, and
    # an empty page drops every block. Editors save by rename; so does this.
    temp = doc.with_suffix(".tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(doc)


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
    _rewrite(doc, LIVE.format(n=1).replace("Lead 1", "Lead 2"))
    page.get_by_text("Lead 2.").wait_for()
    assert page.evaluate("document.activeElement.className") == "comment-text"
    assert page.evaluate("document.activeElement.dataset.same") == "yes"
    assert box.input_value() == "draft"
    assert page.locator("[data-field='owner']").input_value() == "ann"
    assert page.locator("input[value='a']").is_checked()

    # one widget's own edit remounts that widget (fresh, as before); the others stay
    _rewrite(doc, LIVE.format(n=3))
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
    ("choice", {**_CHOICE, "options": "aa"}, "options"),
    ("choice", {**_CHOICE, "multiple": "yes"}, "multiple"),
    ("form", {"fields": 5}, "fields"),
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
    ("form", _in_field(type="select", options="aa"), "options"),
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
]


@pytest.mark.parametrize(("block", "props", "field"), PROPERTY_CASES)
def test_a_property_mistake_gets_one_fault_naming_the_field(
    block: str, props: dict[str, Any], field: str
) -> None:
    faults = check_props(block, props, 1)
    assert len(faults) == 1, faults
    assert field in faults[0].message


def _faults(block: str, props: dict[str, Any]) -> list[tuple[str, str]]:
    return [(f.rule, f.message) for f in check_props(block, props, 1)]


def _choice(*options: object) -> dict[str, Any]:
    return {"question": "Q", "options": list(options)}


def _select(options: list[str], **changes: Any) -> dict[str, Any]:
    return _in_field(type="select", options=options, **changes)


def _number(**changes: Any) -> dict[str, Any]:
    return _in_field(type="number", **changes)


def _fields(*changes: dict[str, Any]) -> dict[str, Any]:
    return {"fields": [{**_FIELD, **change} for change in changes]}


def _numbered(count: int) -> list[str]:
    return [f"o{i}" for i in range(count)]


def _texts(count: int, maxlength: int = 600) -> list[dict[str, Any]]:
    return [{**_FIELD, "name": f"f{i}", "maxlength": maxlength} for i in range(count)]


def _ranked(last: int) -> dict[str, Any]:
    """Fifteen distinct items; with `last` 259 the answer is at most 8000 long."""
    sizes = [265] * 14 + [last]
    return {**_RANKING, "items": [chr(97 + i) * n for i, n in enumerate(sizes)]}


def _sized_form(maxlength: int) -> dict[str, Any]:
    """Six full text fields and one more; at `maxlength` 253 the bound is 8000."""
    tail = {**_FIELD, "name": "gg", "maxlength": maxlength}
    return {"fields": [*_texts(6), tail]}


# one field of every kind; each adds its own share to the answer's JSON bound
_EVERY_KIND = [
    *_texts(7),
    {"name": "s", "label": "L", "type": "select", "options": ["ab", "abcd"]},
    {"name": "n", "label": "L", "type": "number"},
    {"name": "c", "label": "L", "type": "checkbox"},
    {"name": "e", "label": "L", "type": "select"},
]


_FORM_SIZE = (
    "form: fields can add up to {} characters of answer; "
    "the limit is 8000 (lower maxlength or drop fields)"
)
_RANKING_SIZE = (
    "ranking: the answer can reach 8002 characters; the limit is 8000 "
    "(shorten the values or drop items)"
)
_AT = "choice.options[1]"
_IN = "form.fields[1]"
_LONG = "x" * 601
_TOO_LONG = "must be at most 600 characters, no controls"
_NAME_RULE = "must match ^[a-z][a-z0-9_-]{0,47}$"
_STEP_RANGE = "slider.step must be above 0 and within max - min"
_BELOW_MAX = "slider: min must be below max"
_NOT_TABLE = "must be a string or a table with a label"

WIDGET_CASES = [
    ("choice", _choice(1), [("type", f"{_AT} {_NOT_TABLE}")]),
    (
        "choice",
        _choice(1, 2),
        [
            ("type", f"{_AT} {_NOT_TABLE}"),
            ("type", f"choice.options[2] {_NOT_TABLE}"),
        ],
    ),
    ("choice", _choice(_LONG), [("type", f"{_AT} {_TOO_LONG}")]),
    (
        "choice",
        _choice({"label": "a", "extra": 1}),
        [("unknown-key", f"{_AT}: unknown key 'extra'")],
    ),
    (
        "choice",
        _choice({"label": ""}),
        [("type", f"{_AT}.label must be a non-empty string")],
    ),
    (
        "choice",
        _choice({"label": "a", "recommended": "y"}),
        [("type", f"{_AT}.recommended must be true or false")],
    ),
    (
        "choice",
        _choice({"label": "a", "detail": 1}),
        [("type", f"{_AT}.detail must be a non-empty string")],
    ),
    (
        "choice",
        _choice({"label": "a", "value": 1}),
        [("type", f"{_AT}.value must be a non-empty string")],
    ),
    (
        "choice",
        _choice(*_numbered(51)),
        [("type", "choice.options must be a list of 1-50")],
    ),
    (
        "choice",
        _choice("a", "a"),
        [("option-duplicate", "choice.options: value 'a' is listed twice")],
    ),
    (
        "choice",
        _choice(
            {"label": "a", "recommended": True}, {"label": "b", "recommended": True}
        ),
        [("recommended-many", "choice.options: at most one option is recommended")],
    ),
    ("form", _in_field(min=1), [("unknown-key", f"{_IN}: unknown key 'min'")]),
    (
        "form",
        _in_field(label="x" * 300),
        [("type", f"{_IN}.label must be at most 200 characters, no controls")],
    ),
    ("form", _in_field(name="A b"), [("type", f"{_IN}.name {_NAME_RULE}")]),
    (
        "form",
        _fields({"name": "A"}, {"name": "B"}),
        [
            ("type", f"{_IN}.name {_NAME_RULE}"),
            ("type", f"form.fields[2].name {_NAME_RULE}"),
        ],
    ),
    (
        "form",
        _in_field(maxlength=0),
        [("type", f"{_IN}.maxlength must be a whole number 1-600")],
    ),
    (
        "form",
        _in_field(maxlength=601),
        [("type", f"{_IN}.maxlength must be a whole number 1-600")],
    ),
    (
        "form",
        _number(min=float("inf")),
        [("type", f"{_IN}.min must be a finite number")],
    ),
    ("form", _number(min=5, max=1), [("range", f"{_IN}: min is above max")]),
    (
        "form",
        _number(maxlength=5, min=5, max=1),
        [
            ("unknown-key", f"{_IN}: unknown key 'maxlength'"),
            ("range", f"{_IN}: min is above max"),
        ],
    ),
    (
        "form",
        _in_field(type="select"),
        [("missing-key", f"{_IN}: select needs 'options'")],
    ),
    (
        "form",
        _select(_numbered(51)),
        [("type", f"{_IN}.options must be a list of 1-50")],
    ),
    (
        "form",
        _select([_LONG, "y\x07"]),
        [("type", f"{_IN}.options {_TOO_LONG}")] * 2,
    ),
    (
        "form",
        _select(["a", "a"]),
        [("option-duplicate", f"{_IN}.options: 'a' is listed twice")],
    ),
    (
        "form",
        _select(["a", "a"], min=1),
        [
            ("unknown-key", f"{_IN}: unknown key 'min'"),
            ("option-duplicate", f"{_IN}.options: 'a' is listed twice"),
        ],
    ),
    (
        "form",
        _fields(*({"name": n} for n in _numbered(31))),
        [("type", "form.fields must be a list of 1-30")],
    ),
    (
        "form",
        _fields({}, {}),
        [("field-duplicate", "form.fields: name 'n' is used twice")],
    ),
    (
        "form",
        {"fields": _EVERY_KIND},
        [
            ("missing-key", "form.fields[11]: select needs 'options'"),
            ("size", _FORM_SIZE.format(8866)),
        ],
    ),
    (
        "form",
        _sized_form(254),
        [("size", _FORM_SIZE.format(8002))],
    ),
    (
        "ranking",
        {**_RANKING, "items": ["a"]},
        [("type", "ranking.items must be a list of 2-50")],
    ),
    (
        "ranking",
        {**_RANKING, "items": [1, 2]},
        [
            ("type", f"ranking.items[1] {_NOT_TABLE}"),
            ("type", f"ranking.items[2] {_NOT_TABLE}"),
        ],
    ),
    (
        "ranking",
        {**_RANKING, "items": ["a", "a"]},
        [("option-duplicate", "ranking.items: value 'a' is listed twice")],
    ),
    (
        "ranking",
        _ranked(260),
        [("size", _RANKING_SIZE)],
    ),
    (
        "slider",
        {**_SLIDER, "min": float("nan")},
        [("type", "slider.min must be a finite number")],
    ),
    (
        "slider",
        {**_SLIDER, "step": float("inf")},
        [("type", "slider.step must be a finite number")],
    ),
    ("slider", {**_SLIDER, "min": 9}, [("range", _BELOW_MAX)]),
    ("slider", {**_SLIDER, "min": 5}, [("range", _BELOW_MAX)]),
    ("slider", {**_SLIDER, "step": 9}, [("range", _STEP_RANGE)]),
    (
        "slider",
        {**_SLIDER, "max": 20000},
        [("range", "slider: more than 10000 steps; raise the step")],
    ),
    (
        "slider",
        {**_SLIDER, "labels": ["a"]},
        [("type", "slider.labels must be two texts: low end, high end")],
    ),
    (
        "slider",
        {**_SLIDER, "labels": ["a", " "]},
        [("type", "slider.labels must be a non-empty string")],
    ),
]


@pytest.mark.parametrize(("block", "props", "expected"), WIDGET_CASES)
def test_a_widget_fault_names_the_rule_and_the_place(
    block: str, props: dict[str, Any], expected: list[tuple[str, str]]
) -> None:
    assert _faults(block, props) == expected


@pytest.mark.parametrize(
    ("block", "props"),
    [
        ("choice", _choice(*_numbered(50))),
        ("form", _select(_numbered(50))),
        ("form", _in_field(maxlength=1)),
        ("form", _number(min=3, max=3)),
        ("form", _sized_form(253)),
        ("ranking", _ranked(259)),
        ("slider", {**_SLIDER, "step": 5}),
    ],
)
def test_props_exactly_at_a_limit_are_valid(block: str, props: dict[str, Any]) -> None:
    assert _faults(block, props) == []


def test_an_option_list_is_a_required_non_empty_list_of_anything() -> None:
    spec = BlockSpec("t", "S", (), "x", no_faults, properties=(option_list("picks"),))

    def faults(props: dict[str, object]) -> list[tuple[str, str]]:
        errors = check_props("t", props, 1, specs={"t": spec})
        return [(f.rule, f.message) for f in errors]

    assert faults({"picks": ["a", {"label": "b"}, 3]}) == []
    assert faults({}) == [("missing-key", "missing required key 'picks'")]
    assert faults({"picks": []}) == [("type", "'picks' must not be empty")]
    assert faults({"picks": "a"}) == [("type", "'picks' must be list")]
    assert "picks  required  list of any, nonempty" in type_text({"t": spec}, "t")
