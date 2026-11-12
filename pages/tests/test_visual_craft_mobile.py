"""The offline visual components remain readable on a narrow screen."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from varde_pages.assemble import assemble_static

FIXTURES = Path(__file__).parent / "fixtures" / "widgets"


@pytest.fixture(scope="module")
def mobile_page(browser_session: Any) -> Iterator[Any]:
    page = browser_session.new_page(viewport={"width": 320, "height": 800})
    yield page
    page.close()


@pytest.mark.slow
def test_offline_chart_labels_and_data_at_320(mobile_page: Any, tmp_path: Path) -> None:
    output = tmp_path / "chart.html"
    output.write_text(assemble_static(FIXTURES / "rich-chart.md"), encoding="utf-8")
    page = mobile_page
    try:
        page.goto(output.as_uri())
        charts = page.locator(".chart")
        assert charts.count() > 1
        for chart in charts.all():
            measurements = chart.locator("svg.vb-chart").evaluate(
                """svg => {
                  const labels = [...svg.querySelectorAll(
                    'text.vb-tick, text.vb-end, text.vb-pct')];
                  const boxes = labels.map(label => label.getBoundingClientRect());
                  const overlap = boxes.some((a, i) => boxes.slice(i + 1).some(b =>
                    Math.min(a.right, b.right) - Math.max(a.left, b.left) > 1 &&
                    Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 1));
                  const sizes = labels.map(label =>
                    parseFloat(getComputedStyle(label).fontSize) *
                      label.getScreenCTM().a);
                  return {overlap, smallest: sizes.length ? Math.min(...sizes) : null};
                }"""
            )
            if measurements["smallest"] is not None:
                assert measurements["smallest"] >= 11
            assert not measurements["overlap"]
            chart.locator(".vb-data summary").click()
            assert chart.locator(".vb-data table").is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    finally:
        page.goto("about:blank")


@pytest.mark.slow
def test_offline_mobile_matrix_shows_all_rows(mobile_page: Any, tmp_path: Path) -> None:
    output = tmp_path / "matrix.html"
    output.write_text(assemble_static(FIXTURES / "rich-matrix.md"), encoding="utf-8")
    page = mobile_page
    try:
        page.goto(output.as_uri())
        regions = page.locator(".vd-matrix .vb-scroll").evaluate_all(
            "regions => regions.map(r => [r.clientHeight, r.scrollHeight])"
        )
        assert regions and all(height == content for height, content in regions)
        assert page.get_by_text("Weighted total", exact=True).first.is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    finally:
        page.goto("about:blank")


@pytest.mark.slow
def test_sticky_recommended_header_has_opaque_background(
    mobile_page: Any, tmp_path: Path
) -> None:
    output = tmp_path / "matrix-wide.html"
    output.write_text(assemble_static(FIXTURES / "rich-matrix.md"), encoding="utf-8")
    page = mobile_page
    page.set_viewport_size({"width": 1200, "height": 800})
    try:
        page.goto(output.as_uri())
        header = page.locator(".vd-matrix thead th.vd-matrix-rec").first
        for scheme in ("light", "dark"):
            page.emulate_media(color_scheme=scheme)
            color = header.evaluate(
                "element => getComputedStyle(element).backgroundColor"
            )
            assert color.startswith("rgb(") or color.endswith(", 1)")
    finally:
        page.set_viewport_size({"width": 320, "height": 800})
        page.goto("about:blank")


@pytest.mark.slow
def test_donut_slices_keep_separators(mobile_page: Any, tmp_path: Path) -> None:
    source = tmp_path / "donut.md"
    source.write_text(
        '```ui\ndonut = chart(kind: "donut", '
        'labels: ["a", "b", "c", "d", '
        '"e", "f", "g"], '
        'series: [{"name": "s", "values": [1, 1, 1, 1, 1, 1, 1]}])\n```\n',
        encoding="utf-8",
    )
    output = tmp_path / "donut.html"
    output.write_text(assemble_static(source), encoding="utf-8")
    page = mobile_page
    try:
        page.goto(output.as_uri())
        strokes = page.locator(".vb-slice").evaluate_all(
            "slices => slices.map(slice => getComputedStyle(slice).stroke)"
        )
        assert len(strokes) == 7 and all(stroke != "none" for stroke in strokes)
    finally:
        page.goto("about:blank")


@pytest.mark.slow
def test_offline_wireframe_notes_and_text_alternative(
    mobile_page: Any, tmp_path: Path
) -> None:
    output = tmp_path / "wireframe.html"
    output.write_text(assemble_static(FIXTURES / "rich-wireframe.md"), encoding="utf-8")
    page = mobile_page
    try:
        page.goto(output.as_uri())
        assert page.locator(".vw-note").first.is_visible()
        page.locator(".wireframe .vb-data summary").first.click()
        assert page.locator(".wireframe .vb-data table").first.is_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    finally:
        page.goto("about:blank")


@pytest.mark.slow
def test_offline_screen_flow_retains_readable_regions_at_320(
    mobile_page: Any, tmp_path: Path
) -> None:
    output = tmp_path / "flow.html"
    html = assemble_static(FIXTURES / "rich-screen-flow.md")
    output.write_text(html, encoding="utf-8")
    page = mobile_page
    try:
        page.goto(output.as_uri())
        assert page.locator(".vd-sf-scroll-hint").first.is_visible()
        assert page.locator(".vd-sf-list").first.is_visible()
        label = page.locator(".vd-sf-down .vw-region-label").first
        size = label.evaluate(
            "el => parseFloat(getComputedStyle(el).fontSize) * el.getScreenCTM().a"
        )
        assert size >= 11
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    finally:
        page.goto("about:blank")
