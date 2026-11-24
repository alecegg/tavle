"""checklist: counts, state agreement, empty and large lists, escaping, registration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from varde.pages.page_check import check
from varde.pages.render import render_page
from varde.ui.blocks import check_props
from varde.ui.blocks_render.registry import COMPONENTS

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


def test_status_has_no_inline_start_border() -> None:
    css = (
        Path(__file__).parents[2] / "src/varde/pages/static/css/54-checklist.css"
    ).read_text()
    rules = [part.split("}", 1)[0] for part in css.split(".vd-checklist-item {")[1:]]
    assert rules
    assert all("border-inline-start" not in rule for rule in rules)


def test_progress_remainder_is_the_quiet_line_colour() -> None:
    css = (
        Path(__file__).parents[2] / "src/varde/pages/static/css/54-checklist.css"
    ).read_text()
    screen = css.split("@media (forced-colors: active)", 1)[0]

    def rule(selector: str) -> str:
        return screen.split(selector + " {", 1)[1].split("}", 1)[0]

    assert "background: var(--vd-line)" in rule(".vd-checklist-bar")
    assert "background: var(--vd-line)" in rule(
        ".vd-checklist-bar::-webkit-progress-bar"
    )
    for value in ("::-webkit-progress-value", "::-moz-progress-bar"):
        assert "var(--vd-tone-success-edge)" in rule(".vd-checklist-bar" + value)


def test_property_faults_are_single_and_name_the_field() -> None:
    row = {"label": "L"}
    cases = (
        ({**row, "extra": 1}, "extra"),
        ({k: v for k, v in row.items() if k != "label"}, "label"),
        ({**row, "label": 1}, "label"),
        ({**row, "label": " "}, "label"),
    )
    for item, field in cases:
        faults = check_props("checklist", {"items": [item]}, 1)
        assert len(faults) == 1
        assert field in faults[0].message
