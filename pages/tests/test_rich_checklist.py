"""checklist: counts, state agreement, empty and large lists, escaping, registration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from varde_pages.blocks import check, check_props
from varde_pages.blocks_render.registry import COMPONENTS
from varde_pages.render import render_page

FIXTURES = Path(__file__).parent / "fixtures" / "widgets"


def rules_of(data: dict[str, Any]) -> list[str]:
    return [e.rule for e in check_props("checklist", data, 1)]


def test_checked_and_status_conflict_is_a_fault() -> None:
    bad = {"items": [{"label": "a", "checked": True, "status": "open"}]}
    assert "conflict" in rules_of(bad)
    bad = {"items": [{"label": "a", "checked": False, "status": "done"}]}
    assert "conflict" in rules_of(bad)
    ok = {"label": "a", "checked": True, "status": "done"}
    assert rules_of({"items": [ok]}) == []
    ok = {"label": "a", "checked": False, "status": "blocked"}
    assert rules_of({"items": [ok]}) == []


def test_props_are_validated() -> None:
    assert rules_of({"items": [{"label": "a"}], "covers": ["x"]}) == []
    assert rules_of({}) == ["missing-key"]
    assert rules_of({"items": [{"note": "n"}]}) == ["missing-key"]
    assert rules_of({"items": [{"label": "a", "status": "later"}]})
    assert rules_of({"items": [{"label": "a", "checked": "yes"}]})
    assert rules_of({"items": [{"label": "a", "extra": 1}]})
    assert rules_of({"items": "a"})
    assert "limit" in rules_of({"items": [{"label": "a"}] * 501})


def test_registered_and_fixtures_render() -> None:
    assert "checklist" in COMPONENTS
    for name in ("rich-checklist", "rich-checklist-stress"):
        doc = (FIXTURES / f"{name}.md").read_text()
        assert check(doc) == []
        body = render_page(doc, "t.md").body
        assert "vb-error" not in body and "<img" not in body
        assert "<script>alert" not in body and "style=" not in body
        assert 'data-mithril="checklist"' in body


@pytest.mark.parametrize("name", ["rich-checklist", "rich-checklist-stress"])
def test_fixture_family_exists(name: str) -> None:
    assert (FIXTURES / f"{name}.md").exists()
