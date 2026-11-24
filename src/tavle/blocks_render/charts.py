"""Charts: the props the browser draws a chart from (SVG shapes, legend, tables).

The drawing is `chart_draw`, the numbers and text forms are `chart_model`; this
module assembles the props for `static/components/chart.js`. `static/chart.js`
adds the tooltip, the live readout, the legend toggles and keyboard reading on top
of the mounted markup.
"""

from varde.ui.blocks_render.chart_draw import draw, symbol
from varde.ui.blocks_render.chart_events import events_props, events_sentence
from varde.ui.blocks_render.chart_model import (
    Model,
    Series,
    build_model,
    colour,
    copy_text,
    csv_rows,
    dash_of,
    marker_of,
    show,
    summary,
)
from varde.ui.blocks_render.chart_scale import fmt
from varde.ui.blocks_render.svg import Shape, el, view_box

__all__ = ["chart_props", "copy_text", "fmt"]

Cell = list[object]  # [text, series number or None]


def _key(s: Series) -> list[Shape]:
    """A legend swatch that differs by shape and dash, not colour alone."""
    c = f"vb-s{colour(s.n)}"
    dash = dash_of(s.n)
    if s.kind in ("bar", "slice", "area"):
        body = el(
            "rect",
            {"class": f"vb-bar {c}", "x": "2", "y": "2", "width": "24", "height": "10"},
        )
    else:
        attrs = {"class": f"vb-line {c}", "x1": "1", "y1": "7", "x2": "27", "y2": "7"}
        body = el("line", {**attrs, **({"stroke-dasharray": dash} if dash else {})})
    return [body, symbol(marker_of(s.n), 14, 7, 3.5, f"vb-key-mark {c}")]


def _legend(model: Model) -> list[dict[str, object]]:
    if model.kind == "sparkline":
        return []
    return [
        {
            "n": s.n,
            "class": f"vb-s{colour(s.n)}",
            "marker": marker_of(s.n),
            "dash": dash_of(s.n),
            "name": s.name,
            "key": _key(s),
        }
        for s in model.series
    ]


def _point_table(model: Model) -> dict[str, object]:
    """The table of a scatter or donut: one row per point or per slice."""
    head: list[Cell] = [[c, None] for c in csv_rows(model)[0]]
    rows = []
    for s in model.series:
        cells = (
            (
                [s.name, fmt(s.xs[i]), show(model, s, s.values[i])]
                for i in range(len(s.values))
            )
            if model.kind == "scatter"
            else ([[s.name, show(model, s, s.values[0])]])
        )
        rows += [{"series": s.n, "cells": [[c, None] for c in row]} for row in cells]
    return {"head": head, "rows": rows}


def _table(model: Model) -> dict[str, object]:
    """Header cells and rows; a series' cells carry its number."""
    if model.kind in ("scatter", "donut"):
        return _point_table(model)
    head = [["Label", None]] + [[s.name, s.n] for s in model.series]
    rows = [
        {
            "label": label,
            "cells": [[show(model, s, s.values[i]), s.n] for s in model.series],
        }
        for i, label in enumerate(model.labels)
    ]
    return {"head": head, "rows": rows}


def _heading(model: Model, props: dict[str, object]) -> str:
    if "title" not in props:
        return ""
    units = [u for u in (model.unit, model.right_unit) if u]
    unit = f" ({' / '.join(units)})" if units else ""
    return model.title + unit


def chart_props(data: dict[str, object]) -> dict[str, object]:
    model = build_model(data)
    drawing = draw(model)
    desc = model.desc or summary(model)
    if model.events:
        desc = f"{desc} {events_sentence(len(model.events))}"
    return {
        "heading": _heading(model, data),
        "kind": model.kind,
        "title": model.title,
        "desc": desc,
        "dense": drawing.dense,
        "box": view_box((0, 0, drawing.width, drawing.height)),
        "shapes": drawing.shapes,
        "legend": _legend(model),
        "events": events_props(model),
        "notes": [] if model.events else [f"{x}: {text}" for x, text in model.notes],
        "table": _table(model),
        "copy": copy_text(model),
    }
