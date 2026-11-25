"""Answer validation for the input components, moved from varde's page tests."""

from __future__ import annotations

import json

import pytest

from tavle.blocks_render.decision import decision_as_choice
from tavle.comments.answers import answer_schema, validate_answer
from tavle.page.page_check import check

ORDERED_DOC = (
    "# Plan\n\nBody.\n\n"
    "```ui\n"
    'order = ranking(question: "Urgency?", items: ["a", {"label": "B", '
    '"detail": "second", "value": "b"}, "c"])\n'
    'conf = slider(label: "Confidence", min: 0, max: 10, step: 2, '
    'labels: ["Low", "High"])\n'
    'frac = slider(label: "Share", min: 0, max: 1, step: 0.1)\n'
    'plain = slider(label: "Plain", min: -5, max: 5)\n'
    "```\n"
)

CHOICE_DOC = (
    "# Plan\n\nBody.\n\n"
    "```ui\n"
    'pick = choice(question: "Which?", options: ["a", {"label": "B", '
    '"detail": "second", "value": "b"}])\n'
    'many = choice(question: "Which?", options: ["x", "y", "z"], multiple: true, '
    "comment: true)\n"
    'setup = form(fields: [{"name": "owner", "label": "Owner", "type": "text", '
    '"required": true, "maxlength": 5}, '
    '{"name": "n", "label": "N", "type": "number", "min": 1, "max": 10}, '
    '{"name": "region", "label": "Region", "type": "select", "options": ["eu", "us"]}, '
    '{"name": "ok", "label": "Ok", "type": "checkbox", "required": true}])\n'
    'note = comment(label: "Anything?")\n'
    "```\n\n"
    '```ui id=ship\nship = decision(question: "Ship?", '
    'options: ["approve", "deny", "comment"])\n```\n'
)
GOOD_FORM = {"owner": "ann", "n": 3, "region": "eu", "ok": True}


def _doc_with(widget: str) -> str:
    return f"# P\n\n```ui\n{widget}\n```\n"


def test_a_maximal_ranking_that_passes_check_is_accepted_by_validate_answer() -> None:
    values = ['"' * 300 + str(i) for i in range(10)]
    items = json.dumps(values)
    doc = _doc_with(f'r = ranking(question: "Q", items: {items})')
    assert check(doc) == []
    validate_answer(doc, "r", values[::-1], "")


@pytest.mark.parametrize(
    ("item", "value"),
    [
        ("order", ["a", "b", "c"]),
        ("order", ["c", "a", "b"]),  # `b` is the second item's value, not its label
        ("conf", 0),
        ("conf", 10),
        ("conf", 4.0),
        ("conf", 6),
        ("frac", 0.3),  # float steps: 0.1 * 3
        ("frac", 0.7),
        ("frac", 1),
        ("plain", -5),
        ("plain", -2),
    ],
)
def test_ordered_answer_accepts(item: str, value: object) -> None:
    validate_answer(ORDERED_DOC, item, value, "")


@pytest.mark.parametrize(
    ("item", "value"),
    [
        ("order", ["a", "b"]),  # missing one
        ("order", ["a", "b", "c", "c"]),  # extra
        ("order", ["a", "a", "b"]),  # repeated
        ("order", ["a", "b", "z"]),  # unknown
        ("order", ["a", "B", "c"]),  # label, not value
        ("order", []),
        ("order", "a"),
        ("order", ["a", "b", 3]),
        ("order", ["a", "b", "c\x00"]),
        ("conf", 11),
        ("conf", -1),
        ("conf", 3),  # off the step of 2
        ("conf", 4.5),
        ("conf", True),
        ("conf", "4"),
        ("conf", None),
        ("conf", float("nan")),
        ("conf", float("inf")),
        ("conf", -float("inf")),
        ("conf", 10**400),
        ("frac", 0.35),
        ("frac", 1.1),
        ("plain", 5.5),
        ("order", 3),
    ],
)
def test_ordered_answer_rejects(item: str, value: object) -> None:
    with pytest.raises(ValueError):
        validate_answer(ORDERED_DOC, item, value, "")


def test_ranking_and_slider_take_no_text() -> None:
    with pytest.raises(ValueError, match="takes no text"):
        validate_answer(ORDERED_DOC, "conf", 4, "why")
    with pytest.raises(ValueError, match="takes no text"):
        validate_answer(ORDERED_DOC, "order", ["a", "b", "c"], "why")


def test_large_magnitude_and_float_steps_are_on_step() -> None:
    doc = _doc_with(
        's = slider(label: "L", min: 1000000000000, max: 1000000000010, step: 0.001)'
    )
    assert check(doc) == []
    for good in (1e12, 1e12 + 0.001, 1e12 + 0.003, 1e12 + 10):
        validate_answer(doc, "s", good, "")
    with pytest.raises(ValueError, match="whole number of"):
        validate_answer(doc, "s", 1e12 + 0.0005, "")  # half a step off
    validate_answer(ORDERED_DOC, "frac", 0.30000000000000004, "")
    with pytest.raises(ValueError):
        validate_answer(ORDERED_DOC, "frac", 0.31, "")


def test_slider_rejections_name_the_range_or_the_step() -> None:
    with pytest.raises(ValueError, match="between 0 and 10"):
        validate_answer(ORDERED_DOC, "conf", 11, "")
    with pytest.raises(ValueError, match="whole number of 2"):
        validate_answer(ORDERED_DOC, "conf", 3, "")
    with pytest.raises(ValueError, match="number"):
        validate_answer(ORDERED_DOC, "conf", float("nan"), "")


@pytest.mark.parametrize(
    ("item", "value", "text"),
    [
        ("pick", "a", ""),
        ("pick", "b", ""),  # the second option's `value`, not its label
        ("many", ["x", "z"], "why"),
        ("many", ["x", "y", "z"], ""),
        ("setup", {**GOOD_FORM, "region": ""}, ""),  # blank optional select
        ("setup", GOOD_FORM, ""),
        ("setup", {**GOOD_FORM, "n": None}, ""),
        ("note", "commented", "hello"),
        ("ship", "approved", ""),
    ],
)
def test_choice_form_comment_answer_accepts(
    item: str, value: object, text: str
) -> None:
    validate_answer(CHOICE_DOC, item, value, text)


@pytest.mark.parametrize(
    ("item", "value", "text"),
    [
        ("pick", "B", ""),  # the label is not the value
        ("pick", ["a"], ""),
        ("pick", "a", "text"),  # no `comment` prop, so no text
        ("pick", "a\x00", ""),
        ("many", ["x", "q"], ""),
        ("many", "x", ""),
        ("many", [], ""),  # a picked set holds at least one member
        ("many", ["x", "x"], ""),  # and each member once
        ("pick", "", ""),
        ("many", ["x"], "bad\x1b[2J"),
        ("note", "commented", ""),
        ("note", "other", "hello"),
        ("setup", {**GOOD_FORM, "extra": 1}, ""),
        ("setup", {"owner": "ann"}, ""),
        ("setup", {**GOOD_FORM, "owner": ""}, ""),  # required
        ("setup", {**GOOD_FORM, "owner": "toolong"}, ""),  # maxlength 5
        ("setup", {**GOOD_FORM, "owner": "a\x07"}, ""),
        ("setup", {**GOOD_FORM, "n": 0}, ""),  # below min
        ("setup", {**GOOD_FORM, "n": 11}, ""),  # above max
        ("setup", {**GOOD_FORM, "n": float("nan")}, ""),
        ("setup", {**GOOD_FORM, "n": float("inf")}, ""),
        ("setup", {**GOOD_FORM, "n": 10**400}, ""),
        ("setup", {**GOOD_FORM, "n": True}, ""),
        ("setup", {**GOOD_FORM, "n": "3"}, ""),
        ("setup", {**GOOD_FORM, "region": "asia"}, ""),
        ("setup", {**GOOD_FORM, "ok": False}, ""),  # required checkbox
        ("setup", {**GOOD_FORM, "ok": "yes"}, ""),
        ("setup", ["owner"], ""),
        ("missing", "a", ""),
    ],
)
def test_choice_form_comment_answer_rejects(
    item: str, value: object, text: str
) -> None:
    with pytest.raises(ValueError):
        validate_answer(CHOICE_DOC, item, value, text)


def test_decision_is_a_choice_preset_and_old_rows_still_validate() -> None:
    props = {"question": "Ship?", "options": ["approve", "comment"]}
    as_choice = decision_as_choice(props)
    assert as_choice["options"] == [
        {"label": "Approve", "value": "approved"},
        {"label": "Comment", "value": "commented"},
    ]
    assert as_choice["comment"] is True
    schema = answer_schema(CHOICE_DOC, "ship")
    assert schema is not None and schema.allowed == ("approved", "denied", "commented")
    with pytest.raises(ValueError):
        validate_answer(CHOICE_DOC, "ship", "commented", "")  # a comment needs text
    in_ui = _doc_with('go = decision(question: "Go?", options: ["deny"])')
    validate_answer(in_ui, "go", "denied", "")
    with pytest.raises(ValueError):
        validate_answer(in_ui, "go", "approved", "")


def test_required_select_refuses_the_blank_choice() -> None:
    doc = _doc_with(
        'w = form(fields: [{"name": "r", "label": "R", "type": "select", '
        '"options": ["a"], "required": true}])'
    )
    validate_answer(doc, "w", {"r": "a"}, "")
    with pytest.raises(ValueError):
        validate_answer(doc, "w", {"r": ""}, "")


def test_a_maximal_form_that_passes_check_is_accepted_by_validate_answer() -> None:
    names = [f"f{i}" for i in range(6)]
    fields = ", ".join(
        f'{{"name": "{n}", "label": "L", "type": "text", "maxlength": 600}}'
        for n in names
    )
    doc = _doc_with(f"w = form(fields: [{fields}])")
    assert check(doc) == []
    for worst in ('"' * 600, "\\" * 600, "é" * 600):  # escapes, non-ASCII
        validate_answer(doc, "w", dict.fromkeys(names, worst), "")
