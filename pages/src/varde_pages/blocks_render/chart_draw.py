"""SVG shapes for each chart kind: pure functions from a Model to a Drawing.

The browser builds each shape (`components/chart.js`). Everything is class- and
attribute-styled (no `style=`); colours come from the `--vd-series-*` tokens in
`41-chart.css`. Text is 15 viewBox units, so it stays
at or above 11 CSS px while the SVG is at least 264 px wide; labels thin out
instead of overlapping. Marks carry `data-series` and `data-index` for the
script, plus an `aria-label` reading.
"""

import math
from collections.abc import Callable
from dataclasses import dataclass

from varde_pages.blocks_render.chart_events import draw_events, events_top
from varde_pages.blocks_render.chart_model import (
    Model,
    Series,
    colour,
    dash_of,
    marker_of,
    reading,
    show,
)
from varde_pages.blocks_render.chart_scale import (
    CHAR,
    compact,
    nice_ticks,
    thin_step,
    tick_decimals,
)
from varde_pages.blocks_render.svg import Shape, el, ellipsize, f1

W, H = 360.0, 220.0
SPARK_W, SPARK_H = 160.0, 44.0
BOTTOM, NOTE_ROW = 34.0, 17.0
DENSE_POINTS = 24
MAX_END_SERIES = 6


@dataclass(frozen=True)
class Drawing:
    shapes: list[Shape]
    width: float
    height: float
    dense: bool


@dataclass(frozen=True)
class Axis:
    ticks: list[float]
    start: float  # pixel position of the first tick
    end: float  # pixel position of the last tick
    decimals: int

    def at(self, value: float) -> float:
        span = self.ticks[-1] - self.ticks[0]
        return self.start + (value - self.ticks[0]) / span * (self.end - self.start)

    def text(self, value: float) -> str:
        return compact(value, self.decimals)

    def width(self) -> float:
        return max(len(self.text(t)) for t in self.ticks) * CHAR


@dataclass(frozen=True)
class Frame:
    x0: float
    x1: float
    y0: float
    y1: float


def make_axis(
    low: float, high: float, start: float, end: float, zero: bool, decimals: int | None
) -> Axis:
    if zero:
        low, high = min(low, 0.0), max(high, 0.0)
    if low == high == 0:
        high = 1.0
    ticks = nice_ticks(low, high)
    return Axis(
        ticks, start, end, tick_decimals(ticks) if decimals is None else decimals
    )


def _text(
    cls: str,
    x: float,
    y: float,
    anchor: str,
    text: str,
    extra: dict[str, str] | None = None,
) -> Shape:
    attrs = {"class": cls, "x": f1(x), "y": f1(y), "text-anchor": anchor}
    return el("text", {**attrs, **(extra or {})}, text)


def _line(cls: str, x1: float, y1: float, x2: float, y2: float) -> Shape:
    attrs = {"class": cls, "x1": f1(x1), "y1": f1(y1), "x2": f1(x2), "y2": f1(y2)}
    return el("line", attrs)


def _attrs(model: Model, s: Series, i: int) -> dict[str, str]:
    return {
        "data-series": str(s.n),
        "data-index": str(i),
        "data-marker": marker_of(s.n),
        "data-dash": dash_of(s.n),
        "aria-label": reading(model, s, i),
    }


def symbol(
    shape: str,
    cx: float,
    cy: float,
    r: float,
    cls: str,
    attrs: dict[str, str] | None = None,
) -> Shape:
    """One point marker; cross and plus are open strokes, the rest are filled."""

    def tag(name: str, geometry: dict[str, str], extra: str = "") -> Shape:
        return el(name, {"class": f"{cls} vb-sym{extra}", **(attrs or {}), **geometry})

    if shape == "circle":
        return tag("circle", {"cx": f1(cx), "cy": f1(cy), "r": f"{r:g}"})
    if shape == "square":
        side = r * 1.8
        box = {
            "x": f1(cx - side / 2),
            "y": f1(cy - side / 2),
            "width": f1(side),
            "height": f1(side),
        }
        return tag("rect", box)
    if shape == "triangle":
        pts = [
            (cx, cy - r * 1.2),
            (cx + r * 1.1, cy + r * 0.9),
            (cx - r * 1.1, cy + r * 0.9),
        ]
    elif shape == "diamond":
        pts = [
            (cx, cy - r * 1.3),
            (cx + r * 1.3, cy),
            (cx, cy + r * 1.3),
            (cx - r * 1.3, cy),
        ]
    elif shape == "cross":
        d = (
            f"M{cx - r:.1f} {cy - r:.1f}L{cx + r:.1f} {cy + r:.1f}"
            f"M{cx + r:.1f} {cy - r:.1f}L{cx - r:.1f} {cy + r:.1f}"
        )
        return tag("path", {"d": d}, " vb-open")
    else:
        d = (
            f"M{cx - r:.1f} {cy:.1f}L{cx + r:.1f} {cy:.1f}"
            f"M{cx:.1f} {cy - r:.1f}L{cx:.1f} {cy + r:.1f}"
        )
        return tag("path", {"d": d}, " vb-open")
    return tag("polygon", {"points": " ".join(f"{f1(px)},{f1(py)}" for px, py in pts)})


def _dot(model: Model, s: Series, i: int, x: float, y: float, last: bool) -> Shape:
    cls = f"vb-dot vb-mark vb-s{colour(s.n)}" + (" vb-last" if last else "")
    return symbol(marker_of(s.n), x, y, 4.5, cls, _attrs(model, s, i))


def _outline(s: Series) -> dict[str, str]:
    """A dashed bar outline: invisible on screen, tells series apart in print."""
    dash = dash_of(s.n)
    return {"stroke-dasharray": dash} if dash else {}


def _poly(kind: str, s: Series, points: list[tuple[float, float]], name: str) -> Shape:
    dash = dash_of(s.n)
    attrs = {
        "class": f"vb-{kind} vb-s{colour(s.n)}",
        "data-series": str(s.n),
        "data-marker": marker_of(s.n),
        "data-dash": dash,
        "aria-label": name,
        "points": " ".join(f"{f1(x)},{f1(y)}" for x, y in points),
    }
    if dash and kind == "line":
        attrs["stroke-dasharray"] = dash
    return el("polyline" if kind == "line" else "polygon", attrs)


def _spans(model: Model) -> dict[int, list[tuple[float, float]]]:
    """Each point's (base, top): zero to the value, or stacked for stacked bars."""
    count = len(model.labels)
    pos, neg = [0.0] * count, [0.0] * count
    spans: dict[int, list[tuple[float, float]]] = {}
    for s in model.series:
        if s.kind != "bar" or not model.stack:
            spans[s.n] = [(0.0, v) for v in s.values]
            continue
        pairs = []
        for i, v in enumerate(s.values):
            run = pos if v >= 0 else neg
            pairs.append((run[i], run[i] + v))
            run[i] += v
        spans[s.n] = pairs
    return spans


def _extent(
    group: list[Series], spans: dict[int, list[tuple[float, float]]]
) -> tuple[float, float]:
    values: list[float] = []
    for s in group:
        if s.kind in ("bar", "area"):
            values += [v for pair in spans[s.n] for v in pair]
        else:
            values += s.values
    return min(values), max(values)


def _note_texts(
    notes: list[tuple[str, float]], frame: Frame, top: float
) -> list[Shape]:
    """Note labels on two rows; one that would overlap on both is left to the list."""
    ends = [frame.x0 - 1, frame.x0 - 1]
    out: list[Shape] = []
    for text, x in notes:
        label = ellipsize(text, 22)
        width = len(label) * CHAR
        anchor = "start" if x - frame.x0 < width / 2 + 4 else "middle"
        left = x if anchor == "start" else x - width / 2
        for row in (0, 1):
            if left > ends[row] + 6:
                ends[row] = left + width
                y = top - 6 - row * NOTE_ROW
                out.append(_text("vb-note-label", x, y, anchor, label))
                break
    return out


def _end_labels(
    model: Model, frame: Frame, ys: dict[int, float], room: float
) -> list[Shape]:
    """Direct labels at the right end of each line; none if they cannot all fit."""
    order = sorted(ys.items(), key=lambda kv: kv[1])
    placed: list[tuple[int, float]] = []
    for n, y in order:
        floor = placed[-1][1] + 17 if placed else y
        placed.append((n, max(y, floor)))
    if placed and placed[-1][1] > frame.y1 + 6:
        return []
    names = {s.n: s.name for s in model.series}
    limit = int((room - 6) / CHAR)
    return [
        _text(
            "vb-end",
            frame.x1 + 8,
            y + 5,
            "start",
            ellipsize(names[n], limit),
            {"data-series": str(n)},
        )
        for n, y in placed
    ]


def _note_xs(model: Model, count: int) -> list[tuple[str, int]]:
    known = [
        (text, model.labels.index(str(x)))
        for x, text in model.notes
        if str(x) in model.labels
    ]
    return known if count else []


def _category_axes(
    model: Model, spans: dict[int, list[tuple[float, float]]], top: float
) -> dict[str, Axis]:
    axes: dict[str, Axis] = {}
    for side in ("left", "right"):
        group = [s for s in model.series if s.axis == side]
        if not group:
            continue
        low, high = _extent(group, spans)
        zero = any(s.kind in ("bar", "area") for s in group)
        axes[side] = make_axis(low, high, H - BOTTOM, top, zero, model.decimals)
    return axes


def _wants_end_labels(
    model: Model, axes: dict[str, Axis], left: float, room: float
) -> bool:
    return (
        model.kind in ("line", "area")
        and 1 < len(model.series) <= MAX_END_SERIES
        and "right" not in axes
        and W - left - 16 - room >= 150
    )


def _line_marks(
    model: Model, s: Series, axis: Axis, cx: Callable[[int], float]
) -> tuple[list[Shape], Shape, list[Shape], float]:
    """Area fill (if any), line, dots and the end height of one line series."""
    count = len(model.labels)
    points = [(cx(i), axis.at(v)) for i, v in enumerate(s.values)]
    fill: list[Shape] = []
    if s.kind == "area":
        base = axis.at(max(axis.ticks[0], min(0.0, axis.ticks[-1])))
        shape = [(points[0][0], base), *points, (points[-1][0], base)]
        fill.append(_poly("area", s, shape, s.name))
    dots = [_dot(model, s, i, x, y, i == count - 1) for i, (x, y) in enumerate(points)]
    return fill, _poly("line", s, points, s.name), dots, points[-1][1]


def _series_marks(
    model: Model,
    axes: dict[str, Axis],
    spans: dict[int, list[tuple[float, float]]],
    cx: Callable[[int], float],
    slot: float,
) -> tuple[list[Shape], list[Shape], list[Shape], dict[int, float]]:
    """Shapes under, over and dotting the plot, and each line's end height."""
    bars = [s for s in model.series if s.kind == "bar"]
    group = 1 if model.stack else max(len(bars), 1)
    width = max(slot * 0.8 / group, 0.6)
    under: list[Shape] = []
    over: list[Shape] = []
    dots: list[Shape] = []
    ends: dict[int, float] = {}
    for s in model.series:
        axis = axes[s.axis]
        if s.kind == "bar":
            k = 0 if model.stack else bars.index(s)
            shift = width * k - width * group / 2
            under += _bars(
                model, s, spans[s.n], axis, lambda i, d=shift: cx(i) + d, width
            )
            continue
        fill, line, line_dots, end = _line_marks(model, s, axis, cx)
        under += fill
        over.append(line)
        dots += line_dots
        ends[s.n] = end
    return under, over, dots, ends


def categorical(model: Model) -> Drawing:
    """Bar, line, area and combined charts over text labels, on one or two axes."""
    count = len(model.labels)
    notes_at = _note_xs(model, count)
    top = events_top(model) or 12.0 + NOTE_ROW * min(2, len(notes_at))
    spans = _spans(model)
    axes = _category_axes(model, spans, top)
    left = axes["left"].width() + 12 if "left" in axes else 12.0
    right = axes["right"].width() + 12 if "right" in axes else 12.0
    room = min(max(len(s.name) for s in model.series), 12) * CHAR + 14
    want_ends = _wants_end_labels(model, axes, left, room)
    if want_ends:
        right = room + 4
    frame = Frame(left, W - right, top, H - BOTTOM)
    slot = (frame.x1 - frame.x0) / max(count, 1)

    def cx(i: int) -> float:
        return frame.x0 + slot * (i + 0.5)

    under, over, dots, ends = _series_marks(model, axes, spans, cx, slot)
    parts = [
        *_grid(frame, axes),
        *(
            _category_events(model, frame, slot, top)
            or _notes([(text, cx(i)) for text, i in notes_at], frame, top)
        ),
        *_category_labels(model, frame, slot),
        *_columns(frame, count, slot),
        *under,
        *over,
        *dots,
    ]
    if want_ends:
        parts += _end_labels(model, frame, ends, room)
    return Drawing(parts, W, H, count > DENSE_POINTS)


def _category_events(
    model: Model, frame: Frame, slot: float, top: float
) -> list[Shape]:
    """Bands and markers over text labels; empty when the chart has no events."""
    spans = []
    for event in model.events:
        first = model.labels.index(str(event.start))
        last = first if event.end is None else model.labels.index(str(event.end))
        x0 = frame.x0 + slot * (first + (0.5 if event.end is None else 0.0))
        x1 = frame.x0 + slot * (last + (0.5 if event.end is None else 1.0))
        spans.append((event, x0, x1))
    return draw_events(model, spans, frame.x0, frame.x1, top, frame.y1) if spans else []


def _grid(frame: Frame, axes: dict[str, Axis]) -> list[Shape]:
    out = []
    for side, axis in axes.items():
        for t in axis.ticks:
            y = axis.at(t)
            if axis is next(iter(axes.values())):
                out.append(
                    _line("vb-axis" if t == 0 else "vb-grid", frame.x0, y, frame.x1, y)
                )
            anchor, x = (
                ("end", frame.x0 - 6) if side == "left" else ("start", frame.x1 + 6)
            )
            out.append(_text("vb-tick", x, y + 5, anchor, axis.text(t)))
    out.append(_line("vb-axis", frame.x0, frame.y1, frame.x1, frame.y1))
    return out


def _category_labels(model: Model, frame: Frame, slot: float) -> list[Shape]:
    shown = [ellipsize(label, 12) for label in model.labels]
    widest = max(len(label) for label in shown) * CHAR
    step = thin_step(len(shown), slot, widest)
    out = []
    reach = 0.0  # right edge of the last label drawn
    for i in range(0, len(shown), step):
        half = len(shown[i]) * CHAR / 2
        x = min(max(frame.x0 + slot * (i + 0.5), half), W - half)  # stay inside the SVG
        if x - half < reach + 4 and out:
            continue  # clamping must not push a label onto its neighbour
        reach = x + half
        out.append(_text("vb-tick", x, frame.y1 + 22, "middle", shown[i]))
    return out


def _column(i: int, x: float, y: str, width: float, height: str) -> Shape:
    return el(
        "rect",
        {
            "class": "vb-col",
            "data-index": str(i),
            "x": f1(x),
            "y": y,
            "width": f1(width),
            "height": height,
        },
    )


def _columns(frame: Frame, count: int, slot: float) -> list[Shape]:
    return [
        _column(i, frame.x0 + slot * i, f1(frame.y0), slot, f1(frame.y1 - frame.y0))
        for i in range(count)
    ]


def _bar(
    model: Model, s: Series, i: int, box: tuple[float, float, float, float]
) -> Shape:
    x, y, width, height = box
    attrs = {
        "class": f"vb-bar vb-mark vb-s{colour(s.n)}",
        **_attrs(model, s, i),
        **_outline(s),
        "x": f1(x),
        "y": f1(y),
        "width": f1(width),
        "height": f1(height),
    }
    return el("rect", attrs)


def _bars(
    model: Model,
    s: Series,
    spans: list[tuple[float, float]],
    axis: Axis,
    x_of: Callable[[int], float],
    width: float,
) -> list[Shape]:
    out = []
    for i, (base, top) in enumerate(spans):
        a, b = axis.at(base), axis.at(top)
        height = max(abs(a - b), 1.0)
        y = min(a, b) if abs(a - b) >= 1.0 else a - 0.5
        out.append(_bar(model, s, i, (x_of(i), y, width, height)))
    return out


def _notes(marked: list[tuple[str, float]], frame: Frame, top: float) -> list[Shape]:
    rules = [
        el(
            "line",
            {
                "class": "vb-note",
                "x1": f1(x),
                "y1": f1(top - 4),
                "x2": f1(x),
                "y2": f1(frame.y1),
            },
        )
        for _, x in marked
    ]
    return rules + _note_texts(marked, frame, top)


def _hbar_axis(axis: Axis, frame: Frame) -> list[Shape]:
    out: list[Shape] = []
    for t in axis.ticks:
        x = axis.at(t)
        out.append(_line("vb-axis" if t == 0 else "vb-grid", x, frame.y0, x, frame.y1))
        out.append(_text("vb-tick", x, frame.y1 + 22, "middle", axis.text(t)))
    out.append(_line("vb-axis", frame.x0, frame.y0, frame.x0, frame.y1))
    return out


def _hbar_rows(shown: list[str], frame: Frame, slot: float) -> list[Shape]:
    out: list[Shape] = []
    step = max(1, math.ceil(17 / slot))
    for i, label in enumerate(shown):
        y = frame.y0 + slot * (i + 0.5)
        out.append(
            _column(i, frame.x0, f1(frame.y0 + slot * i), frame.x1 - frame.x0, f1(slot))
        )
        if i % step == 0:
            out.append(_text("vb-tick", frame.x0 - 6, y + 5, "end", label))
    return out


def _hbar_marks(
    model: Model,
    spans: dict[int, list[tuple[float, float]]],
    axis: Axis,
    frame: Frame,
    slot: float,
) -> list[Shape]:
    group = 1 if model.stack else len(model.series)
    width = max(slot * 0.8 / group, 0.6)
    out: list[Shape] = []
    for s in model.series:
        for i, (base, top) in enumerate(spans[s.n]):
            a, b = axis.at(base), axis.at(top)
            length = max(abs(a - b), 1.0)
            x = min(a, b) if abs(a - b) >= 1.0 else a - 0.5
            k = 0 if model.stack else s.n
            y = frame.y0 + slot * (i + 0.5) - width * group / 2 + width * k
            out.append(_bar(model, s, i, (x, y, length, width)))
    return out


def horizontal_bars(model: Model) -> Drawing:
    """Bars growing rightwards from a zero line, one row per label."""
    count, group = len(model.labels), 1 if model.stack else len(model.series)
    row = max(24.0, group * 14.0)
    height = min(40.0 + count * row, 1400.0)
    spans = _spans(model)
    low, high = _extent(model.series, spans)
    shown = [ellipsize(label, 14) for label in model.labels]
    left = max(len(label) for label in shown) * CHAR + 12
    frame = Frame(left, W - 14, 8.0, height - BOTTOM)
    axis = make_axis(low, high, frame.x0, frame.x1, True, model.decimals)
    slot = (frame.y1 - frame.y0) / max(count, 1)
    out = _hbar_axis(axis, frame) + _hbar_rows(shown, frame, slot)
    out += _hbar_marks(model, spans, axis, frame, slot)
    return Drawing(out, W, height, count > DENSE_POINTS)


def _scatter_dots(model: Model, xaxis: Axis, yaxis: Axis) -> list[Shape]:
    out: list[Shape] = []
    for s in model.series:
        for i, (x, y) in enumerate(zip(s.xs, s.values, strict=True)):
            px, py = xaxis.at(x), yaxis.at(y)
            hit = el(
                "circle", {"class": "vb-hit", "cx": f1(px), "cy": f1(py), "r": "14"}
            )
            sym = symbol(marker_of(s.n), px, py, 4.5, "")
            cls = f"vb-dot vb-mark vb-s{colour(s.n)}"
            out.append(el("g", {"class": cls, **_attrs(model, s, i)}, [hit, sym]))
    return out


def _scatter_notes(
    model: Model, xaxis: Axis, frame: Frame, top: float, wanted: list[tuple[str, float]]
) -> list[Shape]:
    inside = [
        (t, xaxis.at(x)) for t, x in wanted if xaxis.ticks[0] <= x <= xaxis.ticks[-1]
    ]
    return _value_events(model, xaxis, frame, top) or _notes(inside, frame, top)


def scatter(model: Model) -> Drawing:
    """Points on two numeric axes; each point is a mark with its own hit circle."""
    xs = [x for s in model.series for x in s.xs]
    ys = [v for s in model.series for v in s.values]
    wanted = [(t, float(x)) for x, t in model.notes if isinstance(x, int | float)]
    top = events_top(model) or 12.0 + NOTE_ROW * min(2, len(wanted))
    yaxis = make_axis(min(ys), max(ys), H - BOTTOM, top, False, model.decimals)
    left = yaxis.width() + 12
    xaxis = make_axis(min(xs), max(xs), left, W - 14, False, None)
    frame = Frame(left, W - 14, top, H - BOTTOM)
    out = _grid(frame, {"left": yaxis})
    out += [
        _text("vb-tick", xaxis.at(t), frame.y1 + 22, "middle", xaxis.text(t))
        for t in xaxis.ticks
    ]
    out += _scatter_notes(model, xaxis, frame, top, wanted)
    out += _scatter_dots(model, xaxis, yaxis)
    return Drawing(out, W, H, False)


def _value_events(model: Model, xaxis: Axis, frame: Frame, top: float) -> list[Shape]:
    """Bands and markers on a numeric x axis; empty when the chart has no events."""
    spans = []
    for event in model.events:
        x0 = xaxis.at(float(event.start))  # type: ignore[arg-type]
        x1 = x0 if event.end is None else xaxis.at(float(event.end))  # type: ignore[arg-type]
        spans.append((event, x0, x1))
    return draw_events(model, spans, frame.x0, frame.x1, top, frame.y1) if spans else []


def sparkline(model: Model) -> Drawing:
    """A bare line with no axes: the first series only, hit columns for reading."""
    s = model.series[0]
    low, high = min(s.values), max(s.values)
    if high == low:
        low, high = low - 1, high + 1
    count = len(s.values)
    frame = Frame(6.0, SPARK_W - 6, 6.0, SPARK_H - 6)
    slot = (frame.x1 - frame.x0) / max(count - 1, 1)
    pts = [
        (
            frame.x0 + slot * i if count > 1 else SPARK_W / 2,
            frame.y1 - (v - low) / (high - low) * (frame.y1 - frame.y0),
        )
        for i, v in enumerate(s.values)
    ]
    cols = [
        _column(
            i,
            max(0.0, x - slot / 2),
            "0",
            min(SPARK_W, x + slot / 2) - max(0.0, x - slot / 2),
            f"{SPARK_H:g}",
        )
        for i, (x, _) in enumerate(pts)
    ]
    marks = [_dot(model, s, i, x, y, i == count - 1) for i, (x, y) in enumerate(pts)]
    return Drawing(
        [*cols, _poly("line", s, pts, s.name), *marks], SPARK_W, SPARK_H, True
    )


def donut(model: Model) -> Drawing:
    """A ring of slices; each slice is a series so the legend toggles it."""
    cx, cy, outer, inner = W / 2, H / 2, 80.0, 50.0
    total = sum(s.values[0] for s in model.series)
    out = []
    angle = -math.pi / 2
    for s in model.series:
        share = s.values[0] / total if total else 0.0
        if share <= 0:
            continue
        sweep = min(share, 0.99999) * 2 * math.pi
        a0, a1 = angle, angle + sweep
        angle = a1
        large = 1 if sweep > math.pi else 0
        p = lambda r, a: f"{cx + r * math.cos(a):.1f} {cy + r * math.sin(a):.1f}"  # noqa: E731
        d = (
            f"M{p(outer, a0)}A{outer:g} {outer:g} 0 {large} 1 {p(outer, a1)}"
            f"L{p(inner, a1)}A{inner:g} {inner:g} 0 {large} 0 {p(inner, a0)}Z"
        )
        cls = f"vb-slice vb-mark vb-s{colour(s.n)}"
        out.append(el("path", {"class": cls, **_attrs(model, s, 0), "d": d}))
        mid = (a0 + a1) / 2
        if share >= 0.04:
            mx, my = (
                cx + (inner + outer) / 2 * math.cos(mid),
                cy + (inner + outer) / 2 * math.sin(mid),
            )
            key = {
                "data-series": str(s.n),
                "data-marker": marker_of(s.n),
                "data-dash": dash_of(s.n),
                "aria-label": s.name,
            }
            out.append(symbol(marker_of(s.n), mx, my, 4.5, "vb-slice-key", key))
            tx, ty = (
                cx + (outer + 12) * math.cos(mid),
                cy + (outer + 12) * math.sin(mid),
            )
            anchor = (
                "start"
                if math.cos(mid) > 0.2
                else "end"
                if math.cos(mid) < -0.2
                else "middle"
            )
            out.append(
                _text(
                    "vb-pct",
                    tx,
                    ty + 5,
                    anchor,
                    f"{share * 100:.0f}%",
                    {"data-series": str(s.n)},
                )
            )
    out.append(
        _text("vb-center", cx, cy + 5, "middle", show(model, model.series[0], total))
    )
    return Drawing(out, W, H, False)


def draw(model: Model) -> Drawing:
    if model.kind == "donut":
        return donut(model)
    if model.kind == "scatter":
        return scatter(model)
    if model.kind == "sparkline":
        return sparkline(model)
    if model.horizontal:
        return horizontal_bars(model)
    return categorical(model)
