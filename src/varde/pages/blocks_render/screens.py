"""Props for wireframe and ui-states blocks.

A wireframe is a closed grid-region description drawn on the server as SVG shapes: an
optional device frame (browser, phone or tablet), regions with a hatch pattern per
kind and numbered note pins. `static/components/wireframe.js` builds the notes list
and the region table (the text alternative); `static/wireframe.js` adds pan, zoom
and region selection.
"""

import zlib

from varde.pages.blocks_render.common import as_dict, as_list
from varde.pages.blocks_render.svg import Shape, el, wrap_text

Frame = dict[str, object]
Bounds = tuple[int, int, int, int]

CELL_W, CELL_H, PAD = 56, 49, 4  # a one-cell region is at least 52 x 45 CSS px
_REGION_CLASSES = 6
_LINE_H, _CHAR_W = 13, 7.5  # wide enough that a label stays inside its region
_PLAIN = (10, 10, 10, 10)
_SURFACE_MARGINS = {
    "browser": (8, 40, 8, 8),
    "phone": (16, 30, 16, 30),
    "tablet": (18, 18, 18, 30),
}
# kind -> (patternTransform, mark): six hatches that differ by shape, not colour
_KIND_PATTERN = {
    "nav": ("rotate(45)", [el("path", {"d": "M0 4H8"})]),
    "text": ("", [el("path", {"d": "M0 4H4"})]),
    "media": ("rotate(45)", [el("path", {"d": "M0 4H8M4 0V8"})]),
    "input": ("rotate(90)", [el("path", {"d": "M0 4H8"})]),
    "action": ("", [el("circle", {"cx": "4", "cy": "4", "r": "1.4"})]),
    "list": ("rotate(-45)", [el("path", {"d": "M0 4H8"})]),
}


def _bounds(rows: list[str], letter: str) -> Bounds:
    hits = [
        (r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch == letter
    ]
    rs, cs = [h[0] for h in hits], [h[1] for h in hits]
    return min(rs), min(cs), max(rs), max(cs)


def _rows(frame: Frame) -> list[str]:
    return [r for r in as_list(frame["grid"]) if isinstance(r, str)]


def _used(frame: Frame) -> list[str]:
    rows = _rows(frame)
    return [k for k in as_dict(frame["regions"]) if any(k in row for row in rows)]


def _kind(frame: Frame, letter: str) -> str:
    return str(as_dict(frame.get("kinds")).get(letter, ""))


def _notes(frame: Frame) -> list[tuple[int, str, str]]:
    """(number, region letter, text) in props order, numbered from 1."""
    used = set(_used(frame))
    notes = [as_dict(n) for n in as_list(frame.get("notes"))]
    return [
        (n, str(note["region"]), str(note["text"]))
        for n, note in enumerate(notes, 1)
        if str(note.get("region")) in used
    ]


def _pattern(uid: str, kind: str) -> Shape:
    transform, marks = _KIND_PATTERN[kind]
    attrs = {
        "id": f"vw-{uid}-{kind}",
        "class": f"vw-k-{kind}",
        "width": "8",
        "height": "8",
        "patternUnits": "userSpaceOnUse",
    }
    if transform:
        attrs["patternTransform"] = transform
    return el("pattern", attrs, marks)


def _tspans(lines: list[tuple[str, str]], cx: float, top: float) -> list[Shape]:
    """One `<text>` per line (class, text), the block centred on `top`."""
    return [
        el(
            "text",
            {
                "class": cls,
                "x": f"{cx:g}",
                "y": f"{top + n * _LINE_H:g}",
                "text-anchor": "middle",
            },
            text,
        )
        for n, (cls, text) in enumerate(lines)
    ]


def _label_lines(label: str, kind: str, w: float, h: float) -> list[tuple[str, str]]:
    room = max(1, int((h - 8) // _LINE_H))
    chars = max(4, int((w - 10) // _CHAR_W))
    lines = wrap_text(label, chars)
    extra = 1 if kind and len(lines) < room else 0
    shown = lines[: room - extra]
    if len(shown) < len(lines):
        shown[-1] = shown[-1][: max(chars - 1, 1)] + "…"
    out = [("vw-region-label", t) for t in shown]
    return out + ([("vw-kind", f"[{kind}]")] if extra else [])


def _pins(numbers: list[int], x: float, y: float, w: float) -> list[Shape]:
    """Numbered pins along the top edge, squeezed so they stay inside the region."""
    gap = 24 if len(numbers) < 2 else min(24, (w - 28) / (len(numbers) - 1))
    return [
        el(
            "g",
            {"class": "vw-pin", "aria-hidden": "true"},
            [
                el(
                    "circle",
                    {"cx": f"{x + 14 + k * gap:g}", "cy": f"{y + 14:g}", "r": "10"},
                ),
                el(
                    "text",
                    {
                        "x": f"{x + 14 + k * gap:g}",
                        "y": f"{y + 14:g}",
                        "text-anchor": "middle",
                        "dominant-baseline": "central",
                    },
                    str(n),
                ),
            ],
        )
        for k, n in enumerate(numbers)
    ]


def _region(
    frame: Frame, letter: str, index: int, uid: str, origin: tuple[int, int]
) -> Shape:
    r0, c0, r1, c1 = _bounds(_rows(frame), letter)
    x, y = origin[0] + c0 * CELL_W + PAD, origin[1] + r0 * CELL_H + PAD
    w, h = (c1 - c0 + 1) * CELL_W - PAD, (r1 - r0 + 1) * CELL_H - PAD
    label = str(as_dict(frame["regions"])[letter])
    kind = _kind(frame, letter)
    box = {"x": str(x), "y": str(y), "width": str(w), "height": str(h), "rx": "4"}
    colour = f"vb-r{index % _REGION_CLASSES}"
    inner = [el("title", {}, f"{label} ({kind})" if kind else label)]
    inner.append(el("rect", {"class": f"vw-box vb-region {colour}", **box}))
    if kind:
        hatch = {"class": "vw-hatch", **box, "fill": f"url(#vw-{uid}-{kind})"}
        inner.append(el("rect", hatch))
    numbers = [n for n, region, _ in _notes(frame) if region == letter]
    lines = _label_lines(label, kind, w, h)
    top = y + h / 2 - (len(lines) - 1) * _LINE_H / 2 + 4 + (8 if numbers else 0)
    inner += _tspans(lines, x + w / 2, top) + _pins(numbers, x, y, w)
    return el("g", {"class": f"vw-region {colour}", "data-region": letter}, inner)


def _rect(cls: str, x: float, y: float, w: float, h: float, rx: float) -> Shape:
    attrs = {"x": f"{x:g}", "y": f"{y:g}", "width": f"{w:g}", "height": f"{h:g}"}
    return el("rect", {"class": cls, **attrs, "rx": f"{rx:g}"})


def _circle(cls: str, cx: float, cy: float, r: float) -> Shape:
    return el("circle", {"class": cls, "cx": f"{cx:g}", "cy": f"{cy:g}", "r": f"{r:g}"})


def _device(surface: str, width: float, height: float) -> list[Shape]:
    """Bezel and chrome of a browser, phone or tablet, drawn from tokens only."""
    if not surface:
        return []
    mid = width / 2
    radius = {"browser": 8, "phone": 28, "tablet": 18}[surface]
    shapes = [_rect("vw-bezel", 1, 1, width - 2, height - 2, radius)]
    if surface == "browser":
        shapes += [_circle("vw-dot", 20 + 14 * i, 20, 4) for i in range(3)]
        if width > 120:
            shapes.append(_rect("vw-bar", 70, 11, width - 84, 18, 9))
    if surface == "phone":
        shapes.append(_rect("vw-bar", mid - 18, 10, 36, 6, 3))
        shapes.append(_rect("vw-bar", mid - 22, height - 16, 44, 4, 2))
    if surface == "tablet":
        shapes.append(_circle("vw-dot", mid, 9, 3))
        shapes.append(_circle("vw-bar", mid, height - 15, 7))
    return [el("g", {"class": "vw-device", "aria-hidden": "true"}, shapes)]


def frame_size(frame: Frame, surface: str) -> tuple[int, int]:
    """Width and height of the frame drawing."""
    left, top, right, bottom = _SURFACE_MARGINS.get(surface, _PLAIN)
    cols = max((len(r) for r in _rows(frame)), default=1)
    rows = max(len(_rows(frame)), 1)
    return (
        left + cols * CELL_W + PAD + right,
        top + rows * CELL_H + PAD + bottom,
    )


def frame_shape(frame: Frame, surface: str, uid: str, title: str) -> Shape:
    """The `<svg>` of one wireframe: device, screen, hatches and regions."""
    left, top, right, bottom = _SURFACE_MARGINS.get(surface, _PLAIN)
    width, height = frame_size(frame, surface)
    kinds = sorted({_kind(frame, k) for k in _used(frame)} - {""})
    inner_w, inner_h = width - left - right, height - top - bottom
    body: list[Shape] = []
    if kinds:
        body.append(el("defs", {}, [_pattern(uid, k) for k in kinds]))
    body += _device(surface, width, height)
    if surface:
        body.append(_rect("vw-screen", left - 2, top - 2, inner_w + 4, inner_h + 4, 0))
    body += [_region(frame, k, n, uid, (left, top)) for n, k in enumerate(_used(frame))]
    where = f"{surface} " if surface else ""
    desc = f"{where}wireframe with {len(_used(frame))} regions"
    names = ", ".join(str(as_dict(frame["regions"])[k]) for k in _used(frame))
    head = [el("title", {}, title), el("desc", {}, f"{desc}: {names}")]
    attrs = {
        "class": "vb-wire vw-svg",
        "width": str(width),
        "height": str(height),
        "viewBox": f"0 0 {width} {height}",
        "role": "img",
        "aria-label": title,
    }
    return el("svg", attrs, head + body)


def _position(rows: list[str], letter: str) -> str:
    r0, c0, r1, c1 = _bounds(rows, letter)
    span = lambda a, b: f"{a + 1}" if a == b else f"{a + 1}-{b + 1}"  # noqa: E731
    return f"rows {span(r0, r1)}, columns {span(c0, c1)}"


def _region_rows(frame: Frame) -> list[list[object]]:
    regions = as_dict(frame["regions"])
    notes = _notes(frame)
    rows = _rows(frame)
    return [
        [
            regions[k],
            _kind(frame, k) or "none",
            _position(rows, k),
            "; ".join(f"{n}. {text}" for n, region, text in notes if region == k)
            or "none",
        ]
        for k in _used(frame)
    ]


def _note_items(frame: Frame) -> list[dict[str, object]]:
    regions = as_dict(frame["regions"])
    return [
        {"n": n, "region": region, "name": str(regions[region]), "text": text}
        for n, region, text in _notes(frame)
    ]


def _figure(
    frame: Frame, data: dict[str, object], caption: str, uid: str
) -> dict[str, object]:
    surface = str(data.get("surface", ""))
    base = str(data.get("title", "Wireframe"))
    title = f"{base}: {caption.lower()}" if caption else base
    return {
        "caption": caption,
        "title": title,
        "svg": frame_shape(frame, surface, uid, title),
        "notes": _note_items(frame),
        "summary": f"{caption}: regions as text" if caption else "Regions as text",
        "alt": f"{len(_used(frame))} regions",
        "rows": _region_rows(frame),
    }


def _frames(data: dict[str, object]) -> list[tuple[str, Frame]]:
    after = data.get("compare")
    if not isinstance(after, dict):
        return [("", data)]
    return [("Before", data), ("After", after)]


def copy_text(data: dict[str, object]) -> str:
    """Plain text for the Copy entry: each frame's regions, then its notes."""
    surface = str(data.get("surface", "")) + " " if data.get("surface") else ""
    lines = [f"{data.get('title', 'Wireframe')} ({surface}wireframe)"]
    for caption, frame in _frames(data):
        regions = as_dict(frame["regions"])
        lines.append(f"{caption}:" if caption else "Regions:")
        for k in _used(frame):
            kind = _kind(frame, k)
            lines.append(f"- {regions[k]}" + (f" [{kind}]" if kind else ""))
        notes = _notes(frame)
        if notes:
            lines.append("Notes:")
        lines += [f"{n}. {regions[r]}: {text}" for n, r, text in notes]
    return "\n".join(lines)


def wireframe_props(data: dict[str, object]) -> dict[str, object]:
    seed = zlib.crc32(repr(sorted(data.items())).encode())
    return {
        "heading": str(data["title"]) if "title" in data else "",
        "compare": isinstance(data.get("compare"), dict),
        "unit": f"{min(CELL_W, CELL_H) - PAD:g}",
        "frames": [
            _figure(frame, data, caption, f"{seed:08x}{n}")
            for n, (caption, frame) in enumerate(_frames(data))
        ],
        "copy": copy_text(data),
    }


def ui_states_copy(data: dict[str, object]) -> str:
    lines = [f"{data.get('screen', 'Screen')} (ui-states)"]
    for name, state in data.items():
        if not isinstance(state, dict):
            continue
        said = f"n/a, {state['na']}" if "na" in state else state["shows"]
        lines.append(f"- {name}: {said}")
    return "\n".join(lines)


def ui_states_props(data: dict[str, object]) -> dict[str, object]:
    tiles = [
        {
            "name": name,
            "na": str(s["na"]) if "na" in s else None,
            "shows": "" if "na" in s else str(s["shows"]),
        }
        for name, s in data.items()
        if isinstance(s, dict)
    ]
    return {
        "heading": str(data["screen"]) if "screen" in data else "",
        "layout": str(data["layout"]) if "layout" in data else None,
        "tiles": tiles,
        "copy": ui_states_copy(data),
    }
