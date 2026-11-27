"""The chart component: spec, scales, SVG, text forms and slow-tier interactions."""

from __future__ import annotations

import itertools
import re
import threading
import time
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import Any

import pytest
from scene_html import svg_html
from ui_paths import UI_STATIC_DIR

from tavle import (
    COMPONENTS,
    PAGE_SPECS,
    PageServer,
    check_props,
    parse_lines,
    type_text,
)
from tavle.blocks.charts import CHART, MAX_SERIES
from tavle.blocks_render.chart_model import Series, build_model, copy_text
from tavle.blocks_render.chart_scale import (
    compact,
    fmt,
    nice_ticks,
    raw,
    thin_step,
    tick_decimals,
)
from tavle.blocks_render.charts import chart_props as _chart_props


def chart_props(data: dict[str, Any]) -> Any:
    return _chart_props(data)


LABELS = ["before", "after"]
SERIES = [
    {"name": "p50", "values": [120, 80]},
    {"name": "p95", "values": [400, 210]},
]
BASE: dict[str, Any] = {"kind": "bar", "labels": LABELS, "series": SERIES, "unit": "ms"}
KINDS = ("bar", "line", "area", "scatter", "donut", "sparkline", "combo")


def render_chart(data: dict[str, Any]) -> str:
    """The chart's SVG as the browser builds it from the server's shapes."""
    props = chart_props(data)
    cls = "vb-chart" + (" vb-dense" if props["dense"] else "")
    cls += " vb-spark" if props["kind"] == "sparkline" else ""
    return svg_html(props, cls)


def props(kind: str, **more: Any) -> dict[str, Any]:
    out: dict[str, Any] = {**BASE, "kind": kind}
    if kind == "scatter":
        out["series"] = [
            {"name": "a", "x": [1, 2], "values": [3, 4]},
            {"name": "b", "x": [2, 5], "values": [1, 6]},
        ]
        out.pop("labels")
    if kind == "donut":
        out["series"] = [{"name": "share", "values": [30, 70]}]
    if kind == "sparkline":
        out["series"] = SERIES[:1]
    if kind == "combo":
        out["series"] = [SERIES[0], {**SERIES[1], "axis": "right"}]
    return {**out, **more}


def numbers(svg: str, names: tuple[str, ...]) -> list[float]:
    pattern = r"\b(?:" + "|".join(names) + r')="(-?[0-9.]+)"'
    return [float(v) for v in re.findall(pattern, svg)]


def rules(data: dict[str, Any]) -> set[str]:
    return {e.rule for e in check_props("chart", data, 1)}


@pytest.mark.parametrize("kind", KINDS)
def test_each_kind_validates_and_renders_clean_svg(kind: str) -> None:
    data = props(kind)
    assert rules(data) == set()
    out = render_chart(data)
    assert " style=" not in out and "<script" not in out
    assert "nan" not in out.lower() and "inf" not in out.lower().replace("info", "")
    svg = out[out.index("<svg") : out.index("</svg>")]
    box = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]  # type: ignore[union-attr]
    xs = numbers(svg, ("x", "x1", "x2", "cx"))
    ys = numbers(svg, ("y", "y1", "y2", "cy"))
    assert all(-1 <= x <= box[2] + 1 for x in xs), kind
    assert all(-1 <= y <= box[3] + 1 for y in ys), kind
    assert "<desc>" in svg and 'role="img"' in svg
    shown = chart_props(data)
    assert shown["table"]["rows"] and shown["desc"] and shown["copy"]


@pytest.mark.parametrize("kind", KINDS)
def test_each_kind_is_registered_and_marks_carry_hooks(kind: str) -> None:
    assert COMPONENTS["chart"].spec is CHART
    data = props(kind)
    entry = COMPONENTS["chart"]
    assert entry.props is not None
    assert entry.props(data) == chart_props(data)
    marks = re.findall(r'class="[^"]*vb-mark[^"]*"[^>]*>', render_chart(data))
    assert marks
    for mark in marks:
        assert (
            "data-series=" in mark and "data-index=" in mark and "aria-label=" in mark
        )


def test_table_fallback_equals_the_data() -> None:
    table = chart_props(BASE)["table"]
    assert table["head"] == [["Label", None], ["p50", 0], ["p95", 1]]
    assert table["rows"] == [
        {"label": "before", "cells": [["120 ms", 0], ["400 ms", 1]]},
        {"label": "after", "cells": [["80 ms", 0], ["210 ms", 1]]},
    ]


def test_scatter_and_donut_tables_list_each_point_and_slice() -> None:
    scatter = chart_props(props("scatter"))["table"]["rows"]
    assert [row["series"] for row in scatter] == [0, 0, 1, 1]
    donut = chart_props(props("donut"))["table"]["rows"]
    assert donut[1] == {"series": 1, "cells": [["1", None], ["70 ms", None]]} or (
        donut[1]["series"] == 1 and donut[1]["cells"][1] == ["70 ms", None]
    )


def test_copy_entry_gives_csv_text() -> None:
    text = chart_props(BASE)["copy"]
    assert text == "label,p50,p95\nbefore,120,400\nafter,80,210"
    tricky = {**BASE, "labels": ['a,"b"', "c"]}
    assert copy_text(build_model(tricky)).splitlines()[1] == '"a,""b""",120,400'
    scatter = copy_text(build_model(props("scatter")))
    assert scatter.splitlines()[:2] == ["series,x,y", "a,1,3"]


def test_donut_copy_lists_slices_by_label() -> None:
    data = {
        "kind": "donut",
        "labels": ["x", "y"],
        "series": [{"name": "s", "values": [1, 2]}],
    }
    assert copy_text(build_model(data)) == "label,value\nx,1\ny,2"


def test_desc_is_the_svg_description_or_a_generated_sentence() -> None:
    given = render_chart({**BASE, "desc": "Latency halves."})
    assert "<desc>Latency halves.</desc>" in given
    made = render_chart(BASE)
    assert re.search(
        r"<desc>Bar chart with 2 series; values run from 80 to 400 ms\.</desc>", made
    )


def test_negative_zero_and_all_equal_ranges_render() -> None:
    negative = render_chart({**BASE, "series": [{"name": "d", "values": [-2, 3]}]})
    assert negative.count("vb-bar") >= 2 and "-2" in negative
    zero = render_chart({**BASE, "series": [{"name": "z", "values": [0, 0]}]})
    flat = render_chart(
        {**BASE, "kind": "line", "series": [{"name": "f", "values": [5, 5]}]}
    )
    for out in (zero, flat):
        assert "nan" not in out.lower() and "<svg" in out
    spark = render_chart(props("sparkline", series=[{"name": "f", "values": [2, 2]}]))
    assert "vb-line" in spark and "nan" not in spark.lower()


def test_stacked_bars_stack_and_horizontal_bars_grow_sideways() -> None:
    stacked = render_chart({**BASE, "stack": True})
    tops = re.findall(
        r'<rect class="vb-bar vb-mark[^>]* y="([0-9.]+)"'
        r' width="[0-9.]+" height="([0-9.]+)"',
        stacked,
    )
    tops = tops[::2]  # the first label's two bars (they are listed series by series)
    assert len(tops) == 2
    (y_a, h_a), (y_b, h_b) = ((float(y), float(h)) for y, h in tops)
    assert abs((y_a + h_a) - y_b) < 0.2 or abs((y_b + h_b) - y_a) < 0.2
    horizontal = render_chart({**BASE, "horizontal": True})
    assert 'class="vb-bar' in horizontal and 'class="vb-col"' in horizontal


def test_combo_has_two_axes_and_notes_draw_a_rule_and_a_label() -> None:
    combo = render_chart(props("combo", right_unit="%", title="T"))
    assert 'text-anchor="start">' in combo
    assert (
        chart_props(props("combo", right_unit="%", title="T"))["heading"]
        == "T (ms / %)"
    )
    assert combo.count('<rect class="vb-bar vb-mark') == 2 and "vb-line" in combo
    noted = render_chart(
        {**BASE, "kind": "line", "notes": [{"x": "after", "label": "patch"}]}
    )
    assert 'class="vb-note"' in noted and ">patch<" in noted
    assert chart_props(
        {**BASE, "kind": "line", "notes": [{"x": "after", "label": "patch"}]}
    )["notes"] == ["after: patch"]


def test_series_differ_by_colour_marker_and_dash() -> None:
    def keys(data: dict[str, Any]) -> list[tuple[str, str, str]]:
        legend = chart_props(data)["legend"]
        return [(i["class"], i["marker"], i["dash"]) for i in legend]

    two = keys({**BASE, "kind": "line"})
    assert len(set(two)) == 2
    assert len({k[1] for k in two}) == 2 and len({k[2] for k in two}) == 2
    twelve = keys(
        {
            **BASE,
            "kind": "line",
            "labels": ["a", "b"],
            "series": [{"name": f"s{i}", "values": [i, 1]} for i in range(12)],
        }
    )
    assert len(twelve) == 12 and len(set(twelve)) == 12


def test_direct_end_labels_appear_only_where_there_is_room() -> None:
    line = render_chart({**BASE, "kind": "line"})
    assert line.count('class="vb-end"') == 2
    many = render_chart(
        {
            **BASE,
            "kind": "line",
            "series": [{"name": f"s{i}", "values": [i, 1]} for i in range(8)],
        }
    )
    assert 'class="vb-end"' not in many
    longer = render_chart(
        {
            **BASE,
            "kind": "line",
            "series": [
                {"name": "x" * 60, "values": [1, 2]},
                {"name": "y", "values": [2, 1]},
            ],
        }
    )
    assert longer.count('class="vb-end"') in (0, 2)


def test_two_hundred_points_and_twelve_series_render_fast_and_thin_labels() -> None:
    labels = [f"label-{i}" for i in range(200)]
    series = [
        {"name": f"s{k}", "values": [float((i * (k + 1)) % 17) for i in range(200)]}
        for k in range(12)
    ]
    data = {"kind": "line", "labels": labels, "series": series}
    assert rules(data) == set()
    started = time.perf_counter()
    out = render_chart(data)
    assert time.perf_counter() - started < 2.0
    assert "vb-dense" in out and "nan" not in out.lower()
    ticks = re.findall(
        r'class="vb-tick" x="([0-9.]+)" y="2[0-9.]+" text-anchor="middle"', out
    )
    xs = [float(x) for x in ticks]
    assert 0 < len(xs) < 40 and all(b - a >= 60 for a, b in itertools.pairwise(xs))
    assert len(chart_props(data)["table"]["rows"]) == 200


CSS = UI_STATIC_DIR / "css/41-chart.css"
FONT_SIZE = r"font-size: calc\(var\(--vd-text-(?:xs|md)\) \* var\(--vb-k\)\)"


def test_label_text_is_small_and_scaled_to_a_fixed_rendered_size() -> None:
    from tavle.blocks_render.chart_draw import W

    css = CSS.read_text()
    for name in ("vb-tick", "vb-end", "vb-pct", "vb-note-label", "vb-ev-no"):
        assert re.search(rf"\.{name}\b[^{{]*\{{[^}}]*{FONT_SIZE}", css), name
    assert f"--vb-w: {W:g}px" in css  # the viewBox width the scale divides by


def test_the_plot_has_no_width_cap() -> None:
    plot = re.search(r"\n\.vb-plot \{[^}]*\}", CSS.read_text())
    assert plot and "max-inline-size" not in plot.group(0)


CHARTS = """# Charts

```ui id=two
two = chart(
  kind: "line",
  title: "Two series",
  labels: ["A", "B", "C", "D"],
  series: [
    {"name": "first", "values": [1, 2, 3, 4]},
    {"name": "second", "values": [4, 3, 2, 1]},
  ],
)
```

```ui id=one
one = chart(
  kind: "bar",
  title: "One series",
  labels: ["A", "B", "C"],
  series: [
    {"name": "only", "values": [3, 5, 2]},
  ],
)
```
"""

MEASURE = """() => [...document.querySelectorAll('.chart')].map((chart) => {
  const card = chart.querySelector('.vb-card');
  const plot = chart.querySelector('.vb-plot');
  const svg = plot.querySelector('svg');
  const tick = svg.querySelector('.vb-tick');
  const cs = getComputedStyle(card);
  const inner = card.getBoundingClientRect().width
    - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight)
    - parseFloat(cs.borderLeftWidth) - parseFloat(cs.borderRightWidth);
  return {
    legend: chart.querySelectorAll('.vb-legend li').length,
    inner,
    plot: plot.getBoundingClientRect().width,
    svg: svg.getBoundingClientRect().width,
    tickPx: parseFloat(getComputedStyle(tick).fontSize)
      * svg.getBoundingClientRect().width / svg.viewBox.baseVal.width,
    bodyPx: parseFloat(getComputedStyle(document.body).fontSize),
    titleInCard: !!card.querySelector('.vb-title') && card.contains(plot),
    border: parseFloat(cs.borderTopWidth),
  };
})"""


@pytest.fixture
def open_charts(tmp_path: Path, shared_page: Any) -> Iterator[Any]:
    doc = tmp_path / "charts.md"
    doc.write_text(CHARTS, encoding="utf-8")
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    shared_page.goto(f"http://127.0.0.1:{server.port}/")
    shared_page.wait_for_selector(".chart .vb-plot svg")
    shared_page.wait_for_timeout(600)  # the live refresh rebuilds widgets once
    shared_page.wait_for_selector(".chart .vb-plot svg")
    yield shared_page
    shared_page.set_viewport_size({"width": 900, "height": 700})
    shared_page.goto("about:blank")
    server.shutdown()
    server.server_close()
    thread.join(5)


@pytest.mark.slow
def test_legend_shows_for_two_series_and_not_for_one(open_charts: Any) -> None:
    two, one = open_charts.evaluate(MEASURE)
    assert two["legend"] == 2 and one["legend"] == 0


@pytest.mark.slow
@pytest.mark.parametrize("width", [1280, 390])
def test_plot_fills_the_block_and_labels_stay_small(
    open_charts: Any, width: int
) -> None:
    open_charts.set_viewport_size({"width": width, "height": 900})
    open_charts.wait_for_timeout(200)
    for chart in open_charts.evaluate(MEASURE):
        assert abs(chart["plot"] - chart["inner"]) <= 1, chart
        assert abs(chart["svg"] - chart["plot"]) <= 1, chart
        assert 11 <= chart["tickPx"] < chart["bodyPx"], chart
        assert chart["titleInCard"] and chart["border"] > 0, chart


def test_every_prop_text_is_escaped() -> None:
    out = render_chart(
        {
            "kind": "line",
            "title": "<t>",
            "unit": "<u>",
            "desc": "<d>",
            "labels": ["<l>", "m"],
            "series": [{"name": "<s>", "values": [1, 2]}],
            "notes": [{"x": "<l>", "label": "<n>"}],
        }
    )
    for tag in ("<t>", "<u>", "<d>", "<l>", "<s>", "<n>"):
        assert tag not in out


def test_props_carry_text_and_shapes_but_no_markup() -> None:
    shown = chart_props({**BASE, "title": "<t>", "desc": "<d>"})
    assert shown["title"] == "<t>" and shown["desc"] == "<d>"  # escaped when built
    assert all(isinstance(shape, list) and len(shape) == 3 for shape in shown["shapes"])


def test_nice_ticks_and_number_forms() -> None:
    assert nice_ticks(0, 87) == [0, 20, 40, 60, 80, 100]
    assert nice_ticks(-3, 3)[0] <= -3 and nice_ticks(-3, 3)[-1] >= 3
    assert nice_ticks(5, 5)[0] < 5 < nice_ticks(5, 5)[-1]
    assert (
        nice_ticks(0, 0.3) == [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
        or nice_ticks(0, 0.3)[-1] >= 0.3
    )
    assert fmt(1234.5) == "1,234.5" and fmt(-0.0) == "0" and fmt(3, 2) == "3.00"
    assert (
        compact(12000) == "12k"
        and compact(1_500_000) == "1.5M"
        and compact(950) == "950"
    )
    assert thin_step(10, 100, 40) == 1 and thin_step(200, 1.5, 60) > 20


@pytest.mark.parametrize(
    ("low", "high", "target", "expected"),
    [
        (0, 10, 1, [0, 10]),
        (0, 10, 10, list(range(11))),
        (0, 0, 5, [-1, -0.5, 0, 0.5, 1]),
    ],
)
def test_nice_ticks_step_follows_the_target(
    low: float, high: float, target: int, expected: list[float]
) -> None:
    assert nice_ticks(low, high, target) == expected


@pytest.mark.parametrize(
    ("ticks", "expected"),
    [([5], 0), ([0, 0.5], 1), ([0, 0.1], 1), ([0, 1e-7], 6)],
)
def test_tick_decimals_follow_the_step(ticks: list[float], expected: int) -> None:
    assert tick_decimals(ticks) == expected


@pytest.mark.parametrize(
    ("count", "slot", "widest", "expected"),
    [
        (1, 10, 100, 1),
        (2, 10, 100, 11),
        (5, 0, 10, 1),
        (5, 1, 10, 18),
        (5, 10, 22, 3),
    ],
)
def test_thin_step_keeps_labels_eight_units_apart(
    count: int, slot: float, widest: float, expected: int
) -> None:
    assert thin_step(count, slot, widest) == expected


def test_csv_numbers_keep_a_lower_case_exponent() -> None:
    assert raw(1e20) == "1e+20"


def test_series_kinds_follow_the_chart_kind() -> None:
    combo = build_model(
        props("combo", series=[{**SERIES[0], "type": "line"}, SERIES[1]])
    )
    assert [s.kind for s in combo.series] == ["line", "line"]
    assert [s.kind for s in build_model(props("sparkline")).series] == ["line"]
    assert build_model(props("donut")).series == [
        Series(0, "before", [30.0], [], "left", "slice"),
        Series(1, "after", [70.0], [], "left", "slice"),
    ]


def test_decimals_title_and_heading_reach_the_text_forms() -> None:
    plain = chart_props(BASE)
    assert plain["title"] == "chart" and plain["heading"] == ""
    out = chart_props({**BASE, "decimals": 1})
    assert out["table"]["rows"][0]["cells"] == [["120.0 ms", 0], ["400.0 ms", 1]]
    assert out["desc"] == "Bar chart with 2 series; values run from 80.0 to 400.0 ms."
    one = chart_props(
        props("donut", labels=["x"], series=[{"name": "s", "values": [5]}])
    )
    assert one["desc"] == "Donut chart with 1 slice; values run from 5 to 5 ms."


@pytest.mark.timeout(2, method="signal")
def test_scatter_event_ends_are_formatted_numbers() -> None:
    data = props(
        "scatter",
        series=[{"name": "s", "x": [0, 2000], "values": [1, 2]}],
        notes=[{"from": 1000, "to": 1500, "label": "n"}],
    )
    assert chart_props(data)["events"][0]["where"] == "1,000 to 1,500"


def test_copy_quotes_only_cells_with_csv_specials() -> None:
    text = copy_text(build_model({**BASE, "labels": ["X-ray", "b"]}))
    assert text.splitlines()[1] == "X-ray,120,400"


def test_spec_example_validates_and_every_kind_is_listed() -> None:
    result = parse_lines(CHART.example)
    assert result.errors == []
    assert check_props("chart", result.statements[0].props, 1) == []
    text = type_text(PAGE_SPECS, "chart")
    assert all(kind in text for kind in KINDS)


def test_old_props_stay_valid_and_new_ones_are_optional() -> None:
    old = {"kind": "line", "labels": ["a"], "series": [{"name": "s", "values": [1]}]}
    assert rules(old) == set()
    assert rules({"kind": "bar", "series": old["series"]}) == {"missing-key"}


def _points(count: int) -> dict[str, Any]:
    return {
        **BASE,
        "labels": [f"l{i}" for i in range(count)],
        "series": [{"name": "s", "values": [1] * count}],
    }


SCATTER_A = {"name": "a", "x": [1, 2], "values": [3, 4]}
FINITE = "values must be a list of finite numbers"
X_LIST = "x must be a list of numbers, one per value"
DECIMALS = "chart.decimals must be a whole number from 0 to 6"


@pytest.mark.parametrize(
    ("data", "faults"),
    [
        (
            {**BASE, "kind": "line", "stack": True},
            [("type", "chart.stack applies to bar or combo charts")],
        ),
        ({**BASE, "kind": "combo", "stack": True}, []),
        (
            {**BASE, "kind": "line", "horizontal": True},
            [("type", "chart.horizontal applies to bar charts")],
        ),
        ({**BASE, "decimals": 0}, []),
        ({**BASE, "decimals": 6}, []),
        ({**BASE, "decimals": -1}, [("type", DECIMALS)]),
        ({**BASE, "decimals": 7}, [("type", DECIMALS)]),
        (
            {"kind": "bar", "series": SERIES},
            [("missing-key", "chart: missing required key 'labels'")],
        ),
        (
            {**BASE, "series": [{"name": "s", "values": [1, float("nan")]}]},
            [("type", f"series[1].{FINITE}")],
        ),
        (_points(500), []),
        (_points(501), [("too-many", "series[1].values: at most 500 numbers")]),
        (
            props("donut", series=[{"name": "s", "values": [1, -1]}]),
            [("donut-negative", "series[1].values must not be negative")],
        ),
        (
            {**BASE, "series": [SERIES[0], {"name": "s", "values": [1]}]},
            [
                (
                    "series-length",
                    "series[2].values has 1 numbers, expected 2 (one per label)",
                )
            ],
        ),
        (props("scatter", labels=["a"]), []),
        (
            props("scatter", series=[SCATTER_A, {"name": "s", "values": [1]}]),
            [("type", f"series[2].{X_LIST}")],
        ),
        (
            props(
                "scatter",
                series=[
                    SCATTER_A,
                    {"name": "b", "x": [1, float("inf")], "values": [1, 2]},
                ],
            ),
            [("type", f"series[2].{X_LIST}")],
        ),
        (
            props(
                "scatter", series=[SCATTER_A, {"name": "b", "x": [1, 2], "values": [1]}]
            ),
            [("series-length", "series[2].x has 2 numbers, expected 1")],
        ),
        (
            props("scatter", series=[{"name": "s", "values": [float("nan")]}]),
            [("type", f"series[1].{FINITE}"), ("type", f"series[1].{X_LIST}")],
        ),
        (
            {
                **BASE,
                "series": [SERIES[0], {**SERIES[1], "axis": "right", "type": "line"}],
            },
            [
                ("type", "series[2].axis applies to combo charts"),
                ("type", "series[2].type applies to combo charts"),
            ],
        ),
        (
            {**BASE, "series": [SERIES[0], {**SERIES[1], "x": [1, 2]}]},
            [("type", "series[2].x applies to scatter charts")],
        ),
        (
            {
                **BASE,
                "labels": ["a"],
                "series": [
                    {"name": f"s{i}", "values": [1]} for i in range(MAX_SERIES + 1)
                ],
            },
            [("too-many", "chart.series: at most 12 series")],
        ),
        (props("donut", series=SERIES), [("type", "chart: a donut takes one series")]),
        (
            props("sparkline", series=SERIES),
            [("type", "chart: a sparkline takes one series")],
        ),
    ],
)
def test_validation_names_each_fault(
    data: dict[str, Any], faults: list[tuple[str, str]]
) -> None:
    assert [(f.rule, f.message) for f in check_props("chart", data, 1)] == faults


def test_other_faults_name_their_rule() -> None:
    assert "unknown-key" in rules({**BASE, "colour": "red"})
    assert "type" in rules({**BASE, "kind": "pie"})
    assert "type" in rules({**BASE, "stack": "yes"})
    assert "type" in rules({**BASE, "series": [{"name": "s", "values": []}]})
    assert "note-x" in rules({**BASE, "notes": [{"x": "nope", "label": "n"}]})
    assert "note-x" in rules(props("scatter", notes=[{"x": "a", "label": "n"}]))


# ---- Drawn geometry ----------------------------------------------------------


def _flat(shapes: list[Any]) -> Iterator[tuple[str, dict[str, str], Any]]:
    for tag, attrs, content in shapes:
        yield tag, attrs, content
        if isinstance(content, list):
            yield from _flat(content)


def _shapes(data: dict[str, Any]) -> list[tuple[str, dict[str, str], Any]]:
    assert check_props("chart", data, 1) == []
    return list(_flat(chart_props(data)["shapes"]))


def _texts(data: dict[str, Any], cls: str) -> list[tuple[float, float, str, str]]:
    """(x, y, anchor, text) of each text element of class `cls`."""
    return [
        (float(a["x"]), float(a["y"]), a["text-anchor"], c)
        for tag, a, c in _shapes(data)
        if tag == "text" and a["class"] == cls
    ]


def _values(data: dict[str, Any], cls: str = "vb-tick") -> list[str]:
    """The value-axis tick texts (anchored at an end, not under a label)."""
    return [t for _, _, anchor, t in _texts(data, cls) if anchor != "middle"]


def _rects(data: dict[str, Any], cls: str) -> list[tuple[float, ...]]:
    keys = ("x", "y", "width", "height")
    return [
        tuple(float(a[k]) for k in keys)
        for tag, a, _ in _shapes(data)
        if tag == "rect" and a["class"].startswith(cls)
    ]


def _attr(data: dict[str, Any], tag: str, cls: str, key: str) -> list[str]:
    return [
        a[key] for t, a, _ in _shapes(data) if t == tag and a["class"].startswith(cls)
    ]


def _chart(kind: str, labels: list[str], *values: Sequence[float], **more: Any) -> Any:
    series = [{"name": f"s{i}", "values": v} for i, v in enumerate(values)]
    return {"kind": kind, "labels": labels, "series": series, **more}


def _labels(count: int) -> list[str]:
    return [f"l{i}" for i in range(count)]


def test_value_axes_reach_zero_for_bars_and_areas_and_keep_decimals() -> None:
    assert _values(_chart("bar", LABELS, [0.5, 0.8])) == [
        "0.0",
        "0.2",
        "0.4",
        "0.6",
        "0.8",
    ]
    assert _values(_chart("bar", LABELS, [-5, -3])) == [
        "-5",
        "-4",
        "-3",
        "-2",
        "-1",
        "0",
    ]
    assert _values(_chart("area", LABELS, [5, 6])) == ["0", "2", "4", "6"]
    line = _chart("line", LABELS, [1, 2], decimals=1)
    assert _values(line) == ["1.0", "1.2", "1.4", "1.6", "1.8", "2.0"]


def test_a_chart_with_only_a_right_axis_starts_at_the_left_edge() -> None:
    right = [
        {"name": "p", "values": [1, 2], "axis": "right"},
        {"name": "q", "values": [2, 3], "axis": "right"},
    ]
    data = {"kind": "combo", "labels": ["a", "b"], "series": right}
    assert _texts(data, "vb-tick") == [
        (345.6, 186.0, "start", "0"),
        (345.6, 128.0, "start", "1"),
        (345.6, 70.0, "start", "2"),
        (345.6, 12.0, "start", "3"),
        (93.9, 203.0, "middle", "a"),
        (257.7, 203.0, "middle", "b"),
    ]


def test_stacks_put_zero_and_small_values_on_the_positive_run() -> None:
    data = _chart("bar", ["a"], [5], [0.5], [0], stack=True)
    assert _rects(data, "vb-bar") == [
        (53.2, 41.0, 262.1, 145.0),
        (53.2, 26.5, 262.1, 14.5),
        (53.2, 26.0, 262.1, 1.0),
    ]


def test_bars_keep_a_one_unit_minimum_and_a_minimum_width() -> None:
    assert _rects(_chart("bar", LABELS, [100, 1]), "vb-bar") == [
        (52.7, 12.0, 124.3, 174.0),
        (208.1, 184.3, 124.3, 1.7),
    ]
    crowded = _chart("bar", _labels(40), *[[1] * 40] * 12)
    assert _rects(crowded, "vb-bar")[0] == (37.5, 12.0, 0.6, 174.0)
    one = _chart("bar", ["a"], [1])
    assert _rects(one, "vb-bar") == [(68.3, 12.0, 248.6, 174.0)]
    assert _rects(one, "vb-col") == [(37.2, 12.0, 310.8, 174.0)]


def test_negative_areas_fill_up_to_zero() -> None:
    area = _chart("area", LABELS, [-5, -3])
    assert _attr(area, "polygon", "vb-area", "points") == [
        "108.6,12.0 108.6,186.0 268.2,116.4 268.2,12.0"
    ]


def test_note_labels_take_two_rows_and_shift_the_plot_down() -> None:
    notes = [
        {"x": "a", "label": "start"},
        {"x": "b", "label": "a much longer note text here"},
        {"x": "c", "label": "third"},
        {"x": "f", "label": "end"},
    ]
    data = _chart("line", list("abcdef"), [1, 2, 3, 4, 5, 6], notes=notes)
    assert _texts(data, "vb-note-label") == [
        (47.7, 40.0, "middle", "start"),
        (102.3, 40.0, "start", "a much longer note te…"),
        (156.9, 23.0, "middle", "third"),
        (320.7, 40.0, "middle", "end"),
    ]
    assert [y for _, y, a, _ in _texts(data, "vb-tick") if a == "end"] == [
        186.0,
        158.0,
        130.0,
        102.0,
        74.0,
        46.0,
    ]


def test_end_labels_stack_apart_and_drop_out_when_they_cannot_fit() -> None:
    close = _chart("line", LABELS, [1, 2], [1, 2.1], [5, 1])
    assert _texts(close, "vb-end") == [
        (333.2, 138.2, "start", "s1"),
        (333.2, 155.2, "start", "s0"),
        (333.2, 186.0, "start", "s2"),
    ]
    crowded = _chart("line", LABELS, [1, 0], [1, 0.01], [1, 0.02], [1, 0.03])
    assert _texts(crowded, "vb-end") == []
    assert _texts(_chart("area", LABELS, [1, 2], [2, 3]), "vb-end") == [
        (333.2, 12.0, "start", "s1"),
        (333.2, 70.0, "start", "s0"),
    ]
    six = _chart("line", LABELS, *[[i, i + 1] for i in range(6)])
    assert len(_texts(six, "vb-end")) == 6


def test_end_labels_need_150_units_of_plot_and_cut_long_names() -> None:
    def pair(names: tuple[str, str], top: float) -> dict[str, Any]:
        series = [
            {"name": names[0], "values": [0, top]},
            {"name": names[1], "values": [top, 0]},
        ]
        return {"kind": "line", "labels": LABELS, "series": series, "decimals": 6}

    exact = pair(("abcdefghijkl", "b"), 5)
    assert _values(exact)[:1] == ["0.000000"]
    assert _texts(exact, "vb-end") == [
        (249.2, 12.0, "start", "abcdefghijkl"),
        (249.2, 186.0, "start", "b"),
    ]
    assert _texts(pair(("abcdefghijkl", "b"), 50), "vb-end") == []
    long = {**pair(("abcdefghijklm", "nopqrstuvwxyz"), 2), "decimals": 0}
    assert _texts(long, "vb-end") == [
        (249.2, 12.0, "start", "abcdefghijk…"),
        (249.2, 186.0, "start", "nopqrstuvwx…"),
    ]


def _noted(count: int, *notes: tuple[int, int]) -> dict[str, Any]:
    """A flat line over `count` labels with notes (label index, text length)."""
    labels = _labels(count)
    marks = [
        {"x": labels[i], "label": chr(97 + n % 26) * size}
        for n, (i, size) in enumerate(notes)
    ]
    return _chart("line", labels, [1] * count, notes=marks)


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        # too wide to centre at the left edge: left to the list
        (_noted(2, (0, 17)), []),
        (_noted(8, (1, 14)), [(102.3, 23.0, "start", "a" * 14)]),
        (
            _noted(6, (2, 1), (3, 12)),
            [(171.6, 40.0, "middle", "a"), (222.0, 23.0, "middle", "b" * 12)],
        ),
        (
            _noted(21, (0, 15), (2, 7)),
            [(52.8, 40.0, "start", "a" * 15), (81.6, 23.0, "middle", "b" * 7)],
        ),
        (
            _noted(21, (1, 20), (11, 4), (19, 22)),
            [(67.2, 40.0, "start", "a" * 20), (211.2, 23.0, "middle", "b" * 4)],
        ),
        (
            _noted(23, (9, 5), (14, 9), (17, 24), (20, 17)),
            [
                (170.5, 40.0, "middle", "a" * 5),
                (236.2, 40.0, "middle", "b" * 9),
                (275.7, 23.0, "middle", "c" * 21 + "…"),
            ],
        ),
    ],
)
def test_note_labels_keep_six_units_apart_or_are_left_to_the_list(
    data: dict[str, Any], expected: list[tuple[float, float, str, str]]
) -> None:
    assert _texts(data, "vb-note-label") == expected


@pytest.mark.parametrize(
    "ends",
    [
        [(10, 0.75), (1, 5.75), (0, 1.25), (3, 1.25)],
        [(10, 6.25), (9, 6.0)],
    ],
)
def test_end_labels_that_would_run_below_the_plot_are_all_dropped(
    ends: list[tuple[float, float]],
) -> None:
    assert _texts(_chart("line", ["a", "b"], *map(list, ends)), "vb-end") == []


def _lengths(*sizes: int) -> dict[str, Any]:
    labels = [chr(97 + i % 26) * n for i, n in enumerate(sizes)]
    return _chart("bar", labels, [1] * len(sizes))


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (
            _lengths(9, 11, 8, 11, 2, 4, 15),
            [(59.4, "a" * 9), (192.6, "d" * 11), (304.6, "g" * 11 + "…")],
        ),
        (
            _lengths(
                15, 12, 6, 11, 12, 12, 7, 15, 2, 14, 5, 11, 3, 13, 6, 17, 10, 17, 12
            ),
            [(55.4, "a" * 11 + "…"), (274.4, "o" * 6)],
        ),
        (
            _lengths(
                *(12, 16, 16, 6, 11, 16, 9, 11, 15, 6, 12, 12, 10, 7, 10, 9, 16, 9, 10),
                *(11, 16, 4, 5, 3, 5, 17, 8, 9, 12, 17, 15, 7, 9, 9, 5, 17, 13, 4, 17),
            ),
            [(55.4, "a" * 12), (152.8, "o" * 10), (264.3, "c" * 12)],
        ),
    ],
)
def test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour(
    data: dict[str, Any], expected: list[tuple[float, str]]
) -> None:
    ticks = _texts(data, "vb-tick")
    assert [(x, t) for x, _, anchor, t in ticks if anchor == "middle"] == expected


def test_more_than_24_points_is_dense() -> None:
    assert not chart_props(_chart("line", _labels(24), list(range(24))))["dense"]
    assert chart_props(_chart("line", _labels(25), list(range(25))))["dense"]
    assert not chart_props(_chart("bar", _labels(24), [1] * 24, horizontal=True))[
        "dense"
    ]


def test_horizontal_bars_stack_or_group_per_row() -> None:
    stacked = _chart("bar", ["a", "b"], [5, 1], [2, 0.01], horizontal=True, stack=True)
    assert chart_props(stacked)["box"] == "0 0 360 88"
    assert _rects(stacked, "vb-bar") == [
        (21.2, 10.3, 203.0, 18.4),
        (21.2, 33.3, 40.6, 18.4),
        (224.2, 10.3, 81.2, 18.4),
        (61.3, 33.3, 1.0, 18.4),
    ]
    grouped = _chart("bar", ["a", "b"], [5, 1], [2, 0.01], horizontal=True)
    assert chart_props(grouped)["box"] == "0 0 360 96"
    assert _rects(grouped, "vb-bar") == [
        (21.2, 10.7, 324.8, 10.8),
        (21.2, 37.7, 65.0, 10.8),
        (21.2, 21.5, 129.9, 10.8),
        (20.7, 48.5, 1.0, 10.8),
    ]
    # A bar one to two units wide starts at zero, not half a unit before it.
    narrow = _chart("bar", ["a", "b"], [1, 0.005], horizontal=True)
    assert _rects(narrow, "vb-bar")[1] == (21.2, 33.3, 1.6, 18.4)


def test_horizontal_axis_rows_and_labels() -> None:
    def hbar(labels: list[str], values: list[float], **more: Any) -> Any:
        return _chart("bar", labels, values, horizontal=True, **more)

    ticks = _texts(hbar(["a", "b"], [5, 6], decimals=1), "vb-tick")
    assert [t for *_, t in ticks] == ["0.0", "2.0", "4.0", "6.0", "a", "b"]
    one = hbar(["a"], [5])
    assert _rects(one, "vb-bar") == [(21.2, 10.2, 324.8, 17.6)]
    assert _rects(one, "vb-col") == [(21.2, 8.0, 324.8, 22.0)]
    tall = hbar(_labels(155), [1] * 155)
    assert chart_props(tall)["box"] == "0 0 360 1400"
    assert len([t for *_, a, t in _texts(tall, "vb-tick") if a == "end"]) == 78
    cut = _texts(hbar(["abcdefghijklmno", "b"], [1, 2]), "vb-tick")
    assert [t for *_, a, t in cut if a == "end"] == ["abcdefghijklm…", "b"]
    thin = _chart("bar", _labels(60), *[[1] * 60] * 12, horizontal=True)
    assert _rects(thin, "vb-bar")[0] == (39.7, 10.3, 306.3, 1.5)


def test_scatter_notes_inside_the_x_ticks_draw_a_rule() -> None:
    xs = (0, 1, 9, 10)
    notes = [{"x": x, "label": f"n{x}"} for x in xs]
    data = {
        "kind": "scatter",
        "series": [{"name": "s", "x": [0, 10], "values": [5, 6]}],
        "notes": notes,
    }
    assert _attr(data, "line", "vb-note", "x1") == ["37.2", "68.1", "315.1", "346.0"]
    assert [y for _, y, a, _ in _texts(data, "vb-tick") if a == "end"][-1] == 46.0
    assert _values({**data, "decimals": 2})[:2] == ["5.00", "5.20"]


def test_scatter_x_axis_does_not_reach_zero() -> None:
    data = {"kind": "scatter", "series": [{"name": "s", "x": [5, 6], "values": [5, 6]}]}
    bottom = [t for _, _, a, t in _texts(data, "vb-tick") if a == "middle"]
    assert bottom == ["5.0", "5.2", "5.4", "5.6", "5.8", "6.0"]


def test_sparkline_spreads_points_or_centres_one() -> None:
    def spark(values: list[float]) -> dict[str, Any]:
        labels = _labels(len(values))
        return {
            "kind": "sparkline",
            "labels": labels,
            "series": [{"name": "s", "values": values}],
        }

    assert _attr(spark([3]), "polyline", "vb-line", "points") == ["80.0,22.0"]
    assert _attr(spark([3, 4]), "polyline", "vb-line", "points") == [
        "6.0,38.0 154.0,6.0"
    ]
    assert _rects(spark([3, 4]), "vb-col") == [
        (0.0, 0.0, 80.0, 44.0),
        (80.0, 0.0, 80.0, 44.0),
    ]


def _donut(*values: float) -> dict[str, Any]:
    return {
        "kind": "donut",
        "labels": _labels(len(values)),
        "series": [{"name": "s", "values": list(values)}],
    }


def test_donut_arcs_skip_empty_slices_and_flag_large_ones() -> None:
    whole = "M180.0 30.0A80 80 0 1 1 180.0 30.0L180.0 60.0A50 50 0 1 0 180.0 60.0Z"
    assert _attr(_donut(0, 0), "path", "vb-slice", "d") == []
    assert _texts(_donut(0, 0), "vb-center") == [(180.0, 110.0, "middle", "0")]
    assert _attr(_donut(0, 5), "path", "vb-slice", "d") == [whole]
    assert _texts(_donut(0, 5), "vb-pct") == [(180.0, 202.0, "middle", "100%")]
    assert _texts(_donut(5), "vb-center") == [(180.0, 110.0, "middle", "5")]
    assert _attr(_donut(1, 1), "path", "vb-slice", "d") == [
        "M180.0 30.0A80 80 0 0 1 180.0 190.0L180.0 160.0A50 50 0 0 0 180.0 60.0Z",
        "M180.0 190.0A80 80 0 0 1 180.0 30.0L180.0 60.0A50 50 0 0 0 180.0 160.0Z",
    ]
    keys = [a for _, a, _ in _shapes(_donut(1, 24)) if "vb-slice-key" in a["class"]]
    assert len(keys) == 2


# ---- Chromium (slow tier) ---------------------------------------------------

DOC = """# Chart

```ui id=c
c = chart(
  kind: "line",
  title: "Trend",
  unit: "ms",
  labels: ["A", "B", "C", "D"],
  series: [
    {"name": "first", "values": [1, 2, 3, 4]},
    {"name": "second", "values": [4, 3, 2, 1]},
  ],
)
```
"""


@pytest.fixture(scope="module")
def shared_page(browser_session: Any) -> Any:
    page = browser_session.new_page(
        viewport={"width": 900, "height": 700}, has_touch=True
    )
    page.set_default_timeout(10_000)
    return page


@pytest.fixture
def open_page(tmp_path: Path, shared_page: Any) -> Iterator[Any]:
    doc = tmp_path / "plan.md"
    doc.write_text(DOC, encoding="utf-8")
    server = PageServer(doc, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    problems: list[str] = []
    shared_page.on("pageerror", lambda error: problems.append(str(error)))
    shared_page.goto(f"http://127.0.0.1:{server.port}/")
    shared_page.wait_for_selector(".vb-series-toggle")
    shared_page.wait_for_timeout(600)  # the live refresh rebuilds widgets once
    shared_page.wait_for_selector(".vb-series-toggle")
    yield shared_page
    assert problems == []
    shared_page.goto("about:blank")
    server.shutdown()
    server.server_close()
    thread.join(5)


def readout(page: Any) -> str:
    return page.locator(".vb-readout").inner_text()


@pytest.mark.slow
def test_interact_hover_and_tap_show_a_tooltip_and_a_live_readout(
    open_page: Any,
) -> None:
    page = open_page
    assert page.locator(".vb-readout").get_attribute("aria-live") == "polite"
    page.locator(".vb-col").nth(1).hover()
    assert page.locator(".vb-tip").count() == 1
    assert "B" in readout(page) and "first: 2" in readout(page)
    page.locator(".vb-col").nth(2).tap()
    assert "C" in readout(page) and page.locator(".vb-tip").count() == 1


@pytest.mark.slow
def test_interact_arrow_keys_home_end_and_escape_move_across_points(
    open_page: Any,
) -> None:
    page = open_page
    page.locator(".vb-plot").focus()
    page.keyboard.press("Home")
    assert readout(page).startswith("A")
    page.keyboard.press("ArrowRight")
    assert readout(page).startswith("B")
    page.keyboard.press("End")
    assert readout(page).startswith("D")
    page.keyboard.press("ArrowLeft")
    assert readout(page).startswith("C")
    page.keyboard.press("Escape")
    assert page.locator(".vb-tip").count() == 0 and "Hover" in readout(page)
    assert page.locator(".vb-plot").get_attribute("role") == "region"


@pytest.mark.slow
def test_interact_legend_toggle_hides_a_series_and_the_table_follows(
    open_page: Any,
) -> None:
    page = open_page
    page.locator(".chart .vb-data summary").click()
    toggle = page.locator(".vb-series-toggle").first
    assert toggle.get_attribute("aria-pressed") == "true"
    toggle.click()
    assert toggle.get_attribute("aria-pressed") == "false"
    assert "vb-off" in (
        page.locator('.vb-line[data-series="0"]').get_attribute("class") or ""
    )
    assert page.locator('.vb-data th[data-series="0"]').is_hidden()
    assert page.locator('.vb-data th[data-series="1"]').is_visible()
    toggle.click()
    assert page.locator('.vb-data th[data-series="0"]').is_visible()
    page.locator(".chart .vb-data summary").click()


@pytest.mark.slow
def test_interact_legend_targets_are_at_least_44px(open_page: Any) -> None:
    page = open_page
    for toggle in page.locator(".vb-series-toggle").all():
        box = toggle.bounding_box()
        assert box["width"] >= 44 and box["height"] >= 44, box
    page.set_viewport_size({"width": 320, "height": 700})
    for toggle in page.locator(".vb-series-toggle").all():
        box = toggle.bounding_box()
        assert box["width"] >= 44 and box["height"] >= 44, box
    page.set_viewport_size({"width": 900, "height": 700})


@pytest.mark.slow
def test_interact_tooltip_is_not_clipped_at_320(open_page: Any) -> None:
    page = open_page
    page.set_viewport_size({"width": 320, "height": 700})
    for index in (0, 3):
        page.locator(".vb-col").nth(index).hover()
        inside = page.evaluate(
            """() => {
              const s = document.querySelector('svg.vb-chart').getBoundingClientRect();
              const t = document.querySelector('.vb-tip').getBoundingClientRect();
              return [t.left - s.left, s.right - t.right,
                t.top - s.top, s.bottom - t.bottom];
            }"""
        )
        assert all(gap >= -0.5 for gap in inside), inside
    page.set_viewport_size({"width": 900, "height": 700})


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (9999, "9,999"),
        (10000, "10k"),
        (12_345, "12.3k"),
        (99_900, "99.9k"),
        (-10000, "-10k"),
        (1_000_000, "1M"),
        (1_000_000_000, "1G"),
    ],
)
def test_compact_scale_boundaries(value: float, expected: str) -> None:
    assert compact(value) == expected
