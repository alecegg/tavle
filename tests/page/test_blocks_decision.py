"""Decision blocks: schema faults, duplicate ids and the choice they render as."""

from __future__ import annotations

import pytest
from ui_fence import ui_fence

from tavle import PAGE_SPECS, blocks
from tavle.blocks_render.decision import decision_as_choice
from tavle.page import page_check

VALID = 'question = "Ship it?"\n'


def fenced(body: str, id_: str = "d1", before: str = "") -> str:
    return before + ui_fence("decision", body, id_)


def rules(doc: str) -> list[str]:
    return [e.rule for e in page_check.check(doc)]


def test_minimal_block_is_valid():
    assert page_check.check(fenced(VALID)) == []


@pytest.mark.parametrize(
    ("body", "rule"),
    [
        (VALID + 'options = ["approve", "maybe"]\n', "type"),
        (VALID + 'options = ["deny", "deny"]\n', "option-duplicate"),
        ('options = ["approve"]\n', "missing-key"),
        (VALID + '[[evidence]]\nlabel = "a"\n', "missing-key"),
        (VALID + "extra = 1\n", "unknown-key"),
        ("question = 1\n", "type"),
        ('question = " "\n', "type"),
    ],
    ids=[
        "unknown-option",
        "duplicate-option",
        "missing-question",
        "evidence-row-without-text",
        "unknown-key",
        "question-not-text",
        "blank-question",
    ],
)
def test_a_bad_decision_reports_one_rule(body, rule):
    assert rules(fenced(body)) == [rule]


def test_duplicate_id_reports_line():
    doc = fenced(VALID) + fenced(VALID)
    errors = page_check.check(doc)
    assert [e.rule for e in errors] == ["id-duplicate"]
    assert errors[0].line == 7


def test_decision_without_options_offers_all_three_verdicts():
    assert decision_as_choice({}) == {
        "question": "",
        "options": [
            {"label": "Approve", "value": "approved"},
            {"label": "Deny", "value": "denied"},
            {"label": "Comment", "value": "commented"},
        ],
        "comment": True,
    }


def test_decision_with_one_option_keeps_the_question_and_takes_no_comment():
    assert decision_as_choice({"question": "Ship?", "options": ["deny"]}) == {
        "question": "Ship?",
        "options": [{"label": "Deny", "value": "denied"}],
        "comment": False,
    }


def test_blocks_command_prints_fields_and_example(capsys):
    text = blocks.type_text(PAGE_SPECS, "decision")
    assert "question" in text and "options" in text and "evidence" in text
    assert 'question: "' in text
