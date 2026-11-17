"""Chart event markers and bands: SVG shapes, the Events list and the table rows. Pure.

Bands are tinted rects with a per-tone hatch (so tones differ without colour);
markers are dashed lines with a circle pin, bands get a square pin. Every pin
carries the event number; the Events list repeats each event as text, and
`static/chart.js` turns its items into buttons that show the tooltip.
The drawing is shapes (`svg.el`); `static/components/chart.js` builds the DOM.
"""

from dataclasses import dataclass

from varde_pages.blocks_render.chart_model import (
    Event,
    Model,
    where,
)
from varde_pages.blocks_render.chart_scale import CHAR
from varde_pages.blocks_render.common import count_noun
from varde_pages.blocks_render.svg import Shape, el, ellipsize, f1

ROW = 28.0
PIN = 22.0  # pin width; its height is 20 (square) or 22 (circle)
HATCH = {"info": "/", "decision": "\\", "risk": "x", "warning": "-", "success": "|"}
MAX_ROWS = 3
LABEL_CHARS = 14


@dataclass(frozen=True)
class Pin:
    event: Event
    x: float  # centre
    lane: int
    label: str  # shortened text drawn beside the pin; empty when it would overlap


def rows_for(count: int) -> int:
    return 0 if count == 0 else min(MAX_ROWS, 1 + (count - 1) // 4)


def events_top(model: Model) -> float | None:
    """Where the plot starts when there are events, else None."""
    rows = rows_for(len(model.events))
    return 10.0 + ROW * rows if rows else None


def _diagonal_runs(w: float, h: float, gap: float) -> list[tuple[float, float, float]]:
    """(offset, start, end) of each diagonal that crosses a w by h rect."""
    runs: list[tuple[float, float, float]] = []
    c = -h
    while c < w:
        ta, tb = max(0.0, -c), min(h, w - c)
        if ta < tb:
            runs.append((c, ta, tb))
        c += gap
    return runs


def hatch_path(x0: float, y0: float, x1: float, y1: float, style: str) -> str:
    """Hatch lines clipped to a rect: '/' '\\' 'x' (both), '-' or '|'. Gap is 8."""
    gap = 8.0
    runs = _diagonal_runs(x1 - x0, y1 - y0, gap)
    d: list[str] = []
    if style in "/x":
        d += [
            f"M{x0 + c + ta:.1f} {y1 - ta:.1f}L{x0 + c + tb:.1f} {y1 - tb:.1f}"
            for c, ta, tb in runs
        ]
    if style in "\\x":
        d += [
            f"M{x0 + c + ta:.1f} {y0 + ta:.1f}L{x0 + c + tb:.1f} {y0 + tb:.1f}"
            for c, ta, tb in runs
        ]
    if style == "-":
        d += [
            f"M{x0:.1f} {y:.1f}L{x1:.1f} {y:.1f}" for y in _steps(y0 + gap / 2, y1, gap)
        ]
    if style == "|":
        d += [
            f"M{x:.1f} {y0:.1f}L{x:.1f} {y1:.1f}" for x in _steps(x0 + gap / 2, x1, gap)
        ]
    return "".join(d)


def _steps(start: float, stop: float, step: float) -> list[float]:
    count = max(int((stop - start) / step) + 1, 0)
    return [start + step * i for i in range(count) if start + step * i < stop]


def place_pins(
    spans: list[tuple[Event, float, float]], left: float, right: float, rows: int
) -> list[Pin]:
    """Pins on up to three rows; a label that would overlap is dropped, a pin never."""
    half = PIN / 2
    ends = [left - 8.0] * max(rows, 1)
    pins: list[Pin] = []
    for event, x0, _ in spans:
        anchor = x0 if event.end is None else x0 + half
        x = min(max(anchor, left + half), right - half)
        text = ellipsize(event.label, LABEL_CHARS)
        reach = 4 + len(text) * CHAR
        pin = _fit(ends, event, x, text, reach, right)
        pins.append(pin)
    return pins


def _fit(
    ends: list[float], event: Event, x: float, text: str, reach: float, right: float
) -> Pin:
    half = PIN / 2
    for with_label in (True, False):
        extent = reach if with_label else 0.0
        for row, end in enumerate(ends):
            if x - half >= end + 4 and x + half + extent <= right:
                ends[row] = x + half + extent
                return Pin(event, x, row, text if with_label else "")
    row = min(range(len(ends)), key=ends.__getitem__)
    x = min(max(x, ends[row] + 4 + half), right - half)
    ends[row] = max(ends[row], x + half)
    return Pin(event, x, row, "")


def _classes(event: Event, extra: str) -> str:
    return f"vb-ev vb-ev-t-{event.tone} {extra}"


def _band(event: Event, x0: float, x1: float, top: float, bottom: float) -> Shape:
    x1 = max(x1, x0 + 1.0)
    rect = el(
        "rect",
        {
            "class": "vb-band",
            "x": f1(x0),
            "y": f1(top),
            "width": f1(x1 - x0),
            "height": f1(bottom - top),
        },
    )
    path = el(
        "path",
        {"class": "vb-hatch", "d": hatch_path(x0, top, x1, bottom, HATCH[event.tone])},
    )
    rule = el(
        "line",
        {
            "class": "vb-band-rule",
            "x1": f1(x0),
            "y1": f1(top),
            "x2": f1(x1),
            "y2": f1(top),
        },
    )
    attrs = {"class": _classes(event, "vb-ev-band"), "data-event": str(event.n)}
    return el("g", attrs, [rect, path, rule])


def _rule(event: Event, x: float, from_y: float, bottom: float) -> Shape:
    line = el(
        "line",
        {
            "class": "vb-ev-line",
            "x1": f1(x),
            "y1": f1(from_y),
            "x2": f1(x),
            "y2": f1(bottom),
        },
    )
    attrs = {"class": _classes(event, "vb-ev-marker"), "data-event": str(event.n)}
    return el("g", attrs, [line])


def _pin(pin: Pin) -> Shape:
    event, x = pin.event, pin.x
    cy = 15.0 + ROW * pin.lane
    half = PIN / 2
    if event.end is None:
        shape = [
            el(
                "circle",
                {
                    "class": "vb-ev-shape",
                    "cx": f1(x),
                    "cy": f1(cy),
                    "r": f"{half:g}",
                },
            ),
            el(
                "polygon",
                {
                    "class": "vb-ev-glyph",
                    "points": f"{f1(x - 5)},{f1(cy + half)} {f1(x + 5)},{f1(cy + half)}"
                    f" {f1(x)},{f1(cy + half + 6)}",
                },
            ),
        ]
    else:
        shape = [
            el(
                "rect",
                {
                    "class": "vb-ev-shape",
                    "x": f1(x - half),
                    "y": f1(cy - 10),
                    "width": f"{PIN:g}",
                    "height": "20",
                    "rx": "4",
                },
            )
        ]
    number = el(
        "text",
        {
            "class": "vb-ev-no",
            "x": f1(x),
            "y": f1(cy + 5),
            "text-anchor": "middle",
        },
        str(event.n),
    )
    label = (
        [
            el(
                "text",
                {
                    "class": "vb-note-label vb-ev-text",
                    "x": f1(x + half + 4),
                    "y": f1(cy + 5),
                    "text-anchor": "start",
                },
                pin.label,
            )
        ]
        if pin.label
        else []
    )
    kind = "vb-ev-marker" if event.end is None else "vb-ev-band"
    attrs = {
        "class": _classes(event, kind + " vb-ev-pin"),
        "data-event": str(event.n),
    }
    return el("g", attrs, [*shape, number, *label])


def draw_events(
    model: Model,
    spans: list[tuple[Event, float, float]],
    left: float,
    right: float,
    top: float,
    bottom: float,
) -> list[Shape]:
    """Bands first (behind the data), then marker lines, then the pins."""
    bands = [_band(e, x0, x1, top, bottom) for e, x0, x1 in spans if e.end is not None]
    pins = place_pins(spans, left, right, rows_for(len(model.events)))
    lines = [_rule(e, x0, top - 4, bottom) for e, x0, _ in spans if e.end is None]
    return bands + lines + [_pin(p) for p in pins]


def events_sentence(count: int) -> str:
    verb = "is" if count == 1 else "are"
    return f"{count_noun(count, 'event', 'events')} {verb} listed under the chart."


def events_props(model: Model) -> list[dict[str, str | int]]:
    """Each event as the text the list and the table show."""
    return [
        {
            "n": e.n,
            "label": e.label,
            "kind": e.kind,
            "where": where(model, e),
            "tone": e.tone,
            "class": _classes(e, "vb-ev-" + e.kind),
        }
        for e in model.events
    ]
