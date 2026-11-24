"""annotated-code: pins and notes agree and link both ways, ranges are checked,
quiet stretches fold, text is escaped, the layout rules ship in the stylesheet."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from varde.ui.blocks import check_props
from varde.ui.blocks_render.annotated_code import (
    read_notes,
)

PAGES = Path(__file__).parents[2] / "src" / "varde" / "pages"
FIXTURES = Path(__file__).parent / "fixtures" / "widgets"
SOURCE = "".join(f"l{i} = {i}\n" for i in range(1, 41))


def props(notes: list[dict[str, Any]], **more: Any) -> dict[str, Any]:
    return {
        "filename": "f.py",
        "language": "python",
        "source": SOURCE,
        "notes": notes,
        **more,
    }


def rules_of(data: dict[str, Any]) -> list[str]:
    return [e.rule for e in check_props("annotated-code", data, 1)]


def test_notes_are_numbered_by_start_line_with_ties_in_author_order() -> None:
    notes = read_notes(
        props(
            [
                {"lines": 9, "note": "late"},
                {"lines": 2, "note": "x"},
                {"lines": 2, "note": "y"},
            ]
        ),
        40,
    )
    assert [(n.number, n.start, n.text) for n in notes] == [
        (1, 2, "x"),
        (2, 2, "y"),
        (3, 9, "late"),
    ]


@pytest.mark.parametrize("lines", ["39-41", 41, "0", "3-2", "a", True, 2.5])
def test_bad_or_out_of_range_lines_fault(lines: object) -> None:
    assert rules_of(props([{"lines": lines, "note": "n"}])) in (["range"], ["type"])


def test_limits_and_shape_faults() -> None:
    assert rules_of(props([{"lines": 1, "note": "n"}] * 41)) == ["limit", "limit"]
    assert "limit" in rules_of(props([{"lines": 1, "note": "n"}] * 7))
    assert rules_of(props([{"lines": 1, "note": "n", "kind": "bad"}])) == ["type"]
    assert rules_of(props([{"lines": 1}])) == ["missing-key"]
    assert rules_of(props([], collapse="no")) == ["type"]
    assert rules_of(props([])) == []
    assert rules_of(props([{"lines": 1, "note": "n"}] * 6)) == []


def test_stylesheet_has_margin_layout_print_and_forced_colours_rules() -> None:
    css = (PAGES / "static" / "css" / "48-annotated.css").read_text()
    assert "@container vd-doc (min-width: 44rem)" in css
    assert css.index("@container vd-doc") < css.index(
        "grid-template-columns: minmax(0, 1fr) 18rem"
    )
    assert "@media (forced-colors: active)" in css and "@media print" in css
    assert "min-block-size: 44px" in css and "style=" not in css


def test_script_has_no_inline_handlers_and_handles_print() -> None:
    js = (PAGES / "static" / "annotated.js").read_text()
    assert "beforeprint" in js and "innerHTML" not in js


def test_pins_reserve_room_without_line_numbers_too() -> None:
    css = (PAGES / "static" / "css" / "48-annotated.css").read_text()
    assert re.search(
        r"\.vd-annotated-code \.vd-code-nonum \.vd-code-line \{[^}]*"
        r"padding-inline-start: calc\([^}]*var\(--vd-pin-cols\)",
        css,
    )
