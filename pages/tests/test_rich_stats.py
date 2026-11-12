"""The stats component: tones, flat, item counts, escaping, registration."""

from __future__ import annotations

from pathlib import Path

import pytest
from varde_pages.blocks import check, check_props
from varde_pages.blocks_render.registry import COMPONENTS
from varde_pages.render import render_page

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
