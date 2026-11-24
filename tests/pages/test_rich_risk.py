"""The risks component: severity table, unique ids, counts, caps, escaping."""

from __future__ import annotations

from pathlib import Path

from tavle.blocks import check_props
from tavle.blocks_render.registry import COMPONENTS
from ui_paths import UI_STATIC_DIR

from varde.pages.page_check import check
from varde.pages.render import render_page

FIXTURES = Path(__file__).parent / "fixtures" / "widgets"


def _risk(
    n: int, likelihood: str = "low", impact: str = "low", **extra: str
) -> dict[str, object]:
    return {
        "id": f"R{n}",
        "label": f"L{n}",
        "likelihood": likelihood,
        "impact": impact,
        **extra,
    }


def _data(*items: dict[str, object], **props: object) -> dict[str, object]:
    return {"item": list(items), **props}


def test_duplicate_id_and_other_bad_props_are_faults() -> None:
    assert check_props("risks", _data(_risk(1)), 1) == []
    ok = _risk(1, mitigation="m", owner="o")
    assert check_props("risks", _data(ok), 1) == []
    dup = check_props("risks", _data(_risk(1), {**_risk(2), "id": "R1"}), 1)
    assert [f.rule for f in dup] == ["duplicate-id"]
    bads: tuple[dict[str, object], ...] = (
        {**_risk(1), "likelihood": "extreme"},
        {**_risk(1), "impact": "none"},
        {**_risk(1), "id": ""},
        {"id": "a", "label": "b", "likelihood": "low"},
        {**_risk(1), "extra": 1},
        {**_risk(1), "mitigation": ""},
    )
    for bad in bads:
        assert check_props("risks", _data(bad), 1), bad
    assert check_props("risks", _data(), 1)
    assert check_props("risks", _data(_risk(1), extra=1), 1)


def test_item_cap_is_200() -> None:
    items = [_risk(n) for n in range(201)]
    assert check_props("risks", _data(*items), 1)
    assert check_props("risks", _data(*items[:200]), 1) == []


def test_registered_and_renders_through_the_page() -> None:
    assert "risks" in COMPONENTS
    doc = (FIXTURES / "rich-risk.md").read_text()
    assert check(doc) == []
    body = render_page(doc, "t.md").body
    assert body.count('data-mithril="risks"') == 3
    assert "vb-error" not in body


def test_stress_fixture_validates_and_stays_escaped() -> None:
    doc = (FIXTURES / "rich-risk-stress.md").read_text()
    assert check(doc) == []
    body = render_page(doc, "t.md").body
    assert "<img" not in body and "<script>alert" not in body
    assert "style=" not in body and "vb-error" not in body
    assert body.count('data-mithril="risks"') == 3


def test_risk_styles_have_no_status_edge_border() -> None:
    css = (UI_STATIC_DIR / "css/61-risk.css").read_text()
    assert "border-inline-start" not in css


def test_property_faults_are_single_and_name_the_field() -> None:
    row = {"id": "R", "label": "L", "likelihood": "low", "impact": "low"}
    cases = (
        ({**row, "extra": 1}, "extra"),
        ({k: v for k, v in row.items() if k != "label"}, "label"),
        ({**row, "label": 1}, "label"),
        ({**row, "label": " "}, "label"),
    )
    for item, field in cases:
        faults = check_props("risks", {"item": [item]}, 1)
        assert len(faults) == 1
        assert field in faults[0].message
