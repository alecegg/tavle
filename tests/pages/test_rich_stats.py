"""The stats component: tones, flat, item counts, escaping, registration."""

from __future__ import annotations

from pathlib import Path

import pytest

from varde.pages.blocks import check_props
from varde.pages.blocks_render.registry import COMPONENTS
from varde.pages.page_check import check
from varde.pages.render import render_page

FIXTURES = Path(__file__).parent / "fixtures" / "widgets"


def _stats(*items: dict[str, object]) -> dict[str, object]:
    return {"item": list(items)}


def _pair(first: dict[str, object]) -> dict[str, object]:
    return _stats({"label": "L", "value": 1, **first}, {"label": "M", "value": 2})


@pytest.mark.parametrize("count", [1, 7])
def test_other_item_counts_are_a_fault(count: int) -> None:
    items = [{"label": f"L{n}", "value": n} for n in range(count)]
    assert check_props("stats", {"item": items}, 1)


def test_spec_rejects_bad_props() -> None:
    ok = [{"label": "a", "value": 1}, {"label": "b", "value": 2}]
    assert check_props("stats", {"item": ok, "covers": ["x"]}, 1) == []
    for bad in (
        {"label": "a"},
        {"label": "a", "value": 1, "direction": "sideways"},
        {"label": "a", "value": 1, "good": "flat"},
        {"label": "a", "value": 1, "tone": "loud"},
        {"label": "a", "value": 1, "delta": "12%"},
        {"label": "a", "value": 1, "decimals": 9},
        {"label": "a", "value": True},
        {"label": "a", "value": 1, "extra": 1},
    ):
        assert check_props("stats", {"item": [bad, ok[1]]}, 1), bad
    assert check_props("stats", {"item": ok, "extra": 1}, 1)


def test_registered_and_renders_through_the_page() -> None:
    assert "stats" in COMPONENTS
    doc = (FIXTURES / "rich-stats.md").read_text()
    assert check(doc) == []
    body = render_page(doc, "t.md").body
    assert body.count('data-mithril="stats"') == 2
    assert "vb-error" not in body


def test_stress_fixture_validates_and_stays_escaped() -> None:
    doc = (FIXTURES / "rich-stats-stress.md").read_text()
    assert check(doc) == []
    body = render_page(doc, "t.md").body
    assert "<img" not in body and "<script>alert" not in body
    assert "style=" not in body and "vb-error" not in body


STATIC = Path(__file__).parents[2] / "src" / "varde" / "pages" / "static"


def test_sentence_value_is_marked_long_and_set_below_heading_size() -> None:
    js = (STATIC / "components" / "stats.js").read_text()
    assert "LONG_VALUE_CHARS = 16" in js and "dd.vd-stats-value.vd-stats-long" in js
    rule = next(
        line
        for line in (STATIC / "css" / "58-stats.css").read_text().splitlines()
        if line.startswith(".vd-stats-long")
    )
    assert "clamp" not in rule and "overflow" not in rule  # never hide text
    size = rule.split("font-size:")[1].split(";")[0].strip()
    assert size == "var(--vd-text-md)"
    tokens = (STATIC / "css" / "00-tokens.css").read_text()
    assert (
        "--vd-text-md: 1rem;" in tokens and "--vd-heading-3: clamp(1.125rem" in tokens
    )
    stats = (STATIC / "css" / "58-stats.css").read_text()
    assert (
        "font-size: var(--vd-text-2xl)" in stats
    )  # short and numeric values keep the big size
