"""The callout block: spec, registration and its client-side host.

Tones, escaping, Copy text and paragraphs are checked in
`tavle tests/components/callout.test.js` against the former Python renderer's HTML.
"""

from __future__ import annotations

from pathlib import Path

from tavle.blocks import check_props
from tavle.blocks_render.registry import COMPONENTS

from varde.pages.page_check import check
from varde.pages.render import render_page

FIXTURES = Path(__file__).parent / "fixtures" / "widgets"


def test_spec_rejects_bad_props_and_accepts_covers() -> None:
    assert check_props("callout", {"tone": "info", "text": "x"}, 1) == []
    assert (
        check_props("callout", {"tone": "info", "text": "x", "covers": ["a"]}, 1) == []
    )
    assert check_props("callout", {"tone": "loud", "text": "x"}, 1)
    assert check_props("callout", {"tone": "info"}, 1)
    assert check_props("callout", {"tone": "info", "text": "x", "extra": 1}, 1)


def test_registered_and_renders_through_the_page() -> None:
    assert "callout" in COMPONENTS
    doc = (FIXTURES / "rich-callout.md").read_text()
    assert check(doc) == []
    body = render_page(doc, "t.md").body
    assert body.count('data-mithril="callout"') >= 5
    assert "vb-error" not in body


def test_stress_fixture_validates_and_stays_escaped() -> None:
    doc = (FIXTURES / "rich-callout-stress.md").read_text()
    assert check(doc) == []
    body = render_page(doc, "t.md").body
    assert "<img" not in body and "<script>alert" not in body
    assert "<script>" not in body and "style=" not in body
