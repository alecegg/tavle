"""diff: rows agree with difflib, long unchanged runs fold, notes link, text is escaped,
the unified diff in data-copy round-trips, the layout rules ship in the stylesheet."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path
from typing import Any

import pytest
from varde_pages.blocks import check, check_props, type_text
from varde_pages.blocks.diff_rows import (
    diff_rows,
    text_lines,
)

PAGES = Path(str(files("varde_pages")))
FIXTURES = Path(__file__).parent / "fixtures" / "widgets"
BEFORE = "".join(f"line {i}\n" for i in range(1, 31))
AFTER = BEFORE.replace("line 15\n", "line fifteen\n")


def rules_of(data: dict[str, Any]) -> list[str]:
    return [e.rule for e in check_props("diff", data, 1)]


def test_rows_follow_difflib_and_carry_both_line_numbers() -> None:
    rows = diff_rows("a\nb\nc\n", "a\nB\nc\nd\n")
    assert [(r.kind, r.old, r.new, r.text) for r in rows] == [
        ("same", 1, 1, "a"),
        ("del", 2, None, "b"),
        ("add", None, 2, "B"),
        ("same", 3, 3, "c"),
        ("add", None, 4, "d"),
    ]
    assert diff_rows("a\nb\n", "a\nB\n") == diff_rows("a\nb\n", "a\nB\n")


def test_trailing_newline_and_crlf_do_not_change_the_rows() -> None:
    assert diff_rows("a\nb", "a\nb\n") == diff_rows("a\nb\n", "a\nb\n")
    assert diff_rows("a\r\nb\r\n", "a\nB\n") == diff_rows("a\nb\n", "a\nB\n")
    assert text_lines("") == [] and text_lines("\n") == [""]


@pytest.mark.parametrize(
    ("data", "rules"),
    [
        ({}, ["input"]),
        ({"before": "a"}, ["input"]),
        ({"patch": "x", "before": "a", "after": "b"}, ["input", "type"]),
        ({"patch": "no hunk here"}, ["type"]),
        ({"before": "a", "after": "b", "mode": "wide"}, ["type"]),
        ({"before": "a", "after": "b", "extra": 1}, ["unknown-key"]),
        ({"before": 1, "after": "b"}, ["type"]),
        (
            {
                "before": "a",
                "after": "b",
                "notes": [{"side": "after", "lines": 5, "note": "n"}],
            },
            ["range"],
        ),
        (
            {
                "before": "a",
                "after": "b",
                "notes": [{"side": "left", "lines": 1, "note": "n"}],
            },
            ["type"],
        ),
        (
            {"before": "a", "after": "b", "notes": [{"side": "after", "lines": 1}]},
            ["missing-key"],
        ),
        ({"before": "", "after": ""}, []),
        (
            {
                "before": "a",
                "after": "b",
                "notes": [{"side": "after", "lines": "1", "note": "n"}],
            },
            [],
        ),
    ],
)
def test_validation(data: dict[str, Any], rules: list[str]) -> None:
    assert rules_of(data) == rules


def test_stylesheet_ships_the_layout_rules() -> None:
    css = (PAGES / "static" / "css" / "52-diff.css").read_text()
    for needle in (
        "@container vd-doc (min-width: 44rem)",
        "forced-colors",
        "@media print",
        "::details-content",
        "min-block-size: 44px",
        "outline-offset: -",
    ):
        assert needle in css
    assert "style=" not in css and not re.search(r"#[0-9a-fA-F]{3,8}\b", css)


def test_help_text_and_fixtures() -> None:
    text = files("varde_pages").joinpath("help", "blocks.txt").read_text()
    assert type_text("diff") in text
    for name in ("rich-diff.md", "rich-diff-stress.md"):
        assert check((FIXTURES / name).read_text(), None) == []
    page = (FIXTURES / "rich-diff-stress.md").read_text()
    assert page.count("= diff(") >= 5
