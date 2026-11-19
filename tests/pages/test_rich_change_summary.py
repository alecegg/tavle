"""The change-summary component: counts, plurals, order, empty state, escaping."""

from __future__ import annotations

import re
from pathlib import Path

from varde.pages.blocks import check_props
from varde.pages.blocks.change_summary import (
    EMPTY,
    collect_markers,
    markers_of,
    sentence,
    summarize,
)
from varde.pages.blocks_render.registry import COMPONENTS
from varde.pages.render import render_page

FIXTURES = Path(__file__).parent / "fixtures" / "widgets"
SUMMARY = 'k = change-summary(title: "T")\n'
FILES = (
    'f = file-tree(entries: [{"path": "a.py", "change": "added"},'
    ' {"path": "b.py", "change": "added"}, {"path": "c.py"}])\n'
)


def _page(*statements: str) -> str:
    return "".join(f"```ui\n{s}```\n\n" for s in statements)


def _text(html: str) -> str:
    found = re.search(r'vd-change-summary-text">([^<]*)<', html)
    assert found
    return found.group(1)


def test_counts_per_kind_and_change_in_stable_order() -> None:
    markers = [
        ("field", "removed"),
        ("endpoint", "modified"),
        ("file", "added"),
        ("file", "added"),
    ]
    assert sentence(markers) == "2 files added, 1 endpoint changed, 1 field removed"
    assert summarize(markers)[0] == ("2 files added", 2)


def test_state_order_within_a_kind_and_plural_forms() -> None:
    markers = [("entity", c) for c in ("renamed", "removed", "added", "modified")]
    assert sentence(markers) == (
        "1 entity added, 1 entity changed, 1 entity removed, 1 entity renamed"
    )
    assert sentence([("entity", "added")] * 2) == "2 entities added"
    assert sentence([("response", "added")]) == "1 response added"


def test_no_markers_gives_the_empty_sentence() -> None:
    assert sentence([]) == EMPTY == "No changes marked on this page."


def test_markers_of_each_component() -> None:
    model = {
        "entity": [
            {
                "name": "a",
                "change": "added",
                "fields": {"x": "t", "y": {"change": "removed"}},
            }
        ]
    }
    assert markers_of("data-model", model) == [
        ("entity", "added"),
        ("field", "removed"),
    ]
    endpoint = {
        "change": "modified",
        "request": {"p": {"type": "t", "change": "added"}},
        "responses": [{"status": 200, "change": "removed"}, {"status": 500}],
    }
    assert markers_of("endpoint", endpoint) == [
        ("endpoint", "modified"), ("parameter", "added"), ("response", "removed"),
    ]  # fmt: skip
    assert markers_of(
        "file-tree", {"entries": [{"path": "a", "change": "renamed"}]}
    ) == [("file", "renamed")]
    assert markers_of("callout", {"change": "added"}) == []
    assert markers_of("endpoint", {"responses": "bad", "request": 3}) == []
    assert collect_markers([("file-tree", {"entries": 1}), ("endpoint", {})]) == []


def test_props_are_optional_title_only() -> None:
    assert check_props("change-summary", {}, 1) == []
    assert check_props("change-summary", {"title": "T"}, 1) == []
    assert check_props("change-summary", {"title": 3}, 1)
    assert check_props("change-summary", {"other": "x"}, 1)
    assert "change-summary" in COMPONENTS


def test_other_blocks_and_anchors_are_unchanged_by_the_block() -> None:
    without = render_page(_page(FILES), "d")
    with_block = render_page(_page(FILES, SUMMARY), "d")
    assert [b.anchor for b in with_block.blocks][:1] == [
        b.anchor for b in without.blocks
    ]
    assert [b.hash for b in with_block.blocks][:1] == [b.hash for b in without.blocks]
    first_block = re.search(
        r'<div class="block".*?</div>\s*(?=<div|$)', without.body, re.DOTALL
    )
    assert first_block and first_block.group(0) in with_block.body


def test_invalid_props_show_an_error_card_not_a_sentence() -> None:
    page = render_page(_page("k = change-summary(title: 3)\n"), "d").body
    assert "vd-change-summary-text" not in page


ENDPOINT = (
    'e = endpoint(method: "GET", path: "/x", auth: "none", change: "modified",'
    ' responses: [{"status": 200, "body": "ok"}])\n'
)
TABS = (
    't = tabs(tab: [{"label": "A", "blocks": ["f"]},'
    ' {"label": "B", "blocks": ["e"]}])\n'
)
COLUMNS = (
    'c = columns(col: [{"label": "A", "blocks": ["f"]},'
    ' {"label": "B", "blocks": ["e"]}])\n'
)
