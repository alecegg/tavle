"""The timeline component: statuses, current step, caps, escaping, registration."""

from __future__ import annotations

from pathlib import Path

from tavle.blocks import check_props
from tavle.blocks_render.registry import COMPONENTS
from ui_paths import UI_STATIC_DIR

from varde.pages.page_check import check
from varde.pages.render import render_page

FIXTURES = Path(__file__).parent / "fixtures" / "widgets"


def _item(n: int, status: str = "planned", **extra: str) -> dict[str, object]:
    return {"when": f"W{n}", "label": f"L{n}", "status": status, **extra}


def _tl(*items: dict[str, object], **props: object) -> dict[str, object]:
    return {"item": list(items), **props}


def test_empty_when_and_other_bad_props_are_faults() -> None:
    assert check_props("timeline", _tl(_item(1)), 1) == []
    assert check_props("timeline", _tl(_item(1, owner="o", note="n")), 1) == []
    bads: tuple[dict[str, object], ...] = (
        {**_item(1), "when": ""},
        {**_item(1), "status": "late"},
        {"when": "a", "label": "b"},
        {**_item(1), "extra": 1},
        {**_item(1), "note": ""},
    )
    for bad in bads:
        assert check_props("timeline", _tl(bad), 1), bad
    assert check_props("timeline", _tl(), 1)
    assert check_props("timeline", _tl(_item(1), orientation="diagonal"), 1)
    assert check_props("timeline", _tl(_item(1), extra=1), 1)


def test_registered_and_renders_through_the_page() -> None:
    assert "timeline" in COMPONENTS
    doc = (FIXTURES / "rich-timeline.md").read_text()
    assert check(doc) == []
    body = render_page(doc, "t.md").body
    assert body.count('data-mithril="timeline"') >= 2
    assert "vb-error" not in body


def test_stress_fixture_validates_and_stays_escaped() -> None:
    doc = (FIXTURES / "rich-timeline-stress.md").read_text()
    assert check(doc) == []
    body = render_page(doc, "t.md").body
    assert "<img" not in body and "<script>alert" not in body
    assert "style=" not in body and "vb-error" not in body
    assert body.count('data-mithril="timeline"') >= 4


def test_status_has_no_inline_start_border() -> None:
    css = (UI_STATIC_DIR / "css/59-timeline.css").read_text()
    rules = [part.split("}", 1)[0] for part in css.split(".vd-timeline-body {")[1:]]
    assert rules
    assert all("border-inline-start" not in rule for rule in rules)


def test_property_faults_are_single_and_name_the_field() -> None:
    row = {"when": "W", "label": "L", "status": "done"}
    cases = (
        ({**row, "extra": 1}, "extra"),
        ({k: v for k, v in row.items() if k != "label"}, "label"),
        ({**row, "label": 1}, "label"),
        ({**row, "label": " "}, "label"),
    )
    for item, field in cases:
        faults = check_props("timeline", {"item": [item]}, 1)
        assert len(faults) == 1
        assert field in faults[0].message
