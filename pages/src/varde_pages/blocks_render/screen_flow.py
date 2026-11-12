"""Props for the screen-flow block: wireframe screens joined by arrows.

Each screen is the wireframe frame drawing (`screens.frame_shape`) in a
tile with a numbered caption. The layout is computed on the server
(`screen_flow_layout`): ranks come from the diagram layout, a step joins neighbouring
ranks of one lane. Two drawings are sent, across and down; CSS shows the second on
phones. Below them an ordered list gives each screen, its regions, its notes and
what comes next: the text alternative, the print form and the copy text.
`static/components/screen-flow.js` builds the DOM; `static/screen_flow.js` adds
pan, zoom, selection and the notes panel.
"""

import zlib
from collections.abc import Mapping, Sequence
from typing import Any

from varde_pages.blocks_render.common import (
    as_dict,
    as_list,
    count_noun,
)
from varde_pages.blocks_render.diagram_layout import Box
from varde_pages.blocks_render.diagrams import _head, _text
from varde_pages.blocks_render.screen_flow_layout import (
    CAPTION_H,
    Band,
    Link,
    Plan,
    Screen,
    Tile,
    clip_lines,
    plan_flow,
)
from varde_pages.blocks_render.screens import _notes, _used, frame_shape, frame_size
from varde_pages.blocks_render.svg import Shape, el, f1, view_box

Props = Mapping[str, Any]
SCALE = 1.0
CAPTION_CW = 6.4
CAPTION_LINE = 13.0
LANE_TITLE_CHARS = 48
_DIRECTIONS = (("LR", "across", "h"), ("TB", "down", "v"))


def _screens(data: Props) -> list[Props]:
    """Screens in document order; a repeated id keeps its first screen."""
    seen: dict[str, Props] = {}
    for screen in map(as_dict, as_list(data.get("screens"))):
        seen.setdefault(str(screen["id"]), screen)
    return list(seen.values())


def _steps(data: Props, ids: set[str]) -> list[tuple[str, str, str]]:
    steps = map(as_dict, as_list(data.get("steps")))
    return [
        (str(s["from"]), str(s["to"]), str(s.get("label", "")))
        for s in steps
        if str(s["from"]) in ids and str(s["to"]) in ids
    ]


def _lanes(data: Props, screens: Sequence[Props]) -> tuple[dict[str, int], list[str]]:
    """Lane index per screen id and the lane titles; one untitled lane by default."""
    lanes = [as_dict(x) for x in as_list(data.get("lanes"))]
    if not lanes:
        return {str(s["id"]): 0 for s in screens}, [""]
    of = {
        str(m): k for k, lane in enumerate(lanes) for m in as_list(lane.get("screens"))
    }
    return of, [str(lane["title"]) for lane in lanes]


def _natural(frame: Props) -> tuple[float, float]:
    width, height = frame_size(dict(frame), str(frame.get("surface", "")))
    return float(width), float(height)


def _plan(data: Props, direction: str) -> tuple[Plan, list[Props]]:
    screens = _screens(data)
    of, titles = _lanes(data, screens)
    ids = {str(s["id"]) for s in screens}
    sizes = {str(s["id"]): _natural(s) for s in screens}
    placed = [
        Screen(i, (w * SCALE, h * SCALE), of.get(i, 0)) for i, (w, h) in sizes.items()
    ]
    return plan_flow(placed, _steps(data, ids), titles, direction), screens


def _caption(tile: Tile, order: int, title: str) -> Shape:
    chars = max(4, int((tile.box.w - 8) // CAPTION_CW))
    lines = clip_lines(f"{order}. {title}", chars, 2)
    y = tile.box.y + tile.box.h - CAPTION_H / 2 + 2
    return _text(lines, "vd-sf-caption", tile.box.x + tile.box.w / 2, y, CAPTION_LINE)


def _tile(tile: Tile, order: int, screen: Props, uid: str, total: int) -> Shape:
    box, title = tile.box, str(screen["title"])
    frame = frame_shape(dict(screen), str(screen.get("surface", "")), uid, title)
    at = f"translate({f1(tile.thumb_at[0])} {f1(tile.thumb_at[1])}) scale({SCALE:g})"
    rect = {"class": "vd-sf-tile", "x": f1(box.x), "y": f1(box.y)}
    rect |= {"width": f1(box.w), "height": f1(box.h), "rx": "6"}
    thumb = {"class": "vd-sf-thumb", "aria-hidden": "true", "transform": at}
    return el(
        "g",
        {"class": "vd-sf-screen", "data-screen": str(screen["id"])},
        [
            el("title", {}, f"{title}, screen {order} of {total}"),
            el("rect", rect),
            el("g", thumb, [frame]),
            _caption(tile, order, title),
        ],
    )


def _label(box: Box, lines: tuple[str, ...]) -> list[Shape]:
    rect = {"class": "vd-sf-label-bg", "x": f1(box.x), "y": f1(box.y)}
    rect |= {"width": f1(box.w), "height": f1(box.h), "rx": "3"}
    text = _text(lines, "vd-sf-edge-label", box.x + box.w / 2, box.y + box.h / 2, 14.0)
    return [el("rect", rect), text]


def _link(link: Link, said: str) -> Shape:
    (x1, y1), (x2, y2) = link.points
    path = {"class": "vd-sf-line", "d": f"M{f1(x1)} {f1(y1)} L{f1(x2)} {f1(y2)}"}
    label = _label(link.label, link.lines) if link.label else []
    return el(
        "g",
        {"class": "vd-sf-edge"},
        [
            el("title", {}, said),
            el("path", path),
            _head(link.points, "vd-sf-head"),
            *label,
        ],
    )


def _band(band: Band, title: str, down: bool) -> Shape:
    box = band.box
    if down:
        chars = max(4, int((box.w - 16) // CAPTION_CW))
        lines = clip_lines(title, chars, 2)
        x, y, anchor = box.x + 8, box.y + 12, {}
    else:
        lines = clip_lines(title, LANE_TITLE_CHARS, 1)
        x, y = box.x + 10, box.y + band.head / 2
        anchor = {"dominant-baseline": "central"}
    spans = [
        el("tspan", {"x": f1(x), "y": f1(y + n * CAPTION_LINE)}, line)
        for n, line in enumerate(lines)
    ]
    rect = {"class": "vd-sf-band", "x": f1(box.x), "y": f1(box.y)}
    rect |= {"width": f1(box.w), "height": f1(box.h), "rx": "8"}
    return el(
        "g",
        {"class": "vd-sf-lane"},
        [
            el("title", {}, title),
            el("rect", rect),
            el("text", {"class": "vd-sf-lane-title", **anchor}, spans),
        ],
    )


def _next_pairs(
    steps: Sequence[tuple[str, str, str]], titles: Mapping[str, str], me: str
) -> list[str]:
    """`Title (label)` for each step leaving `me`, in step order."""
    return [
        titles[b] + (f" ({label})" if label else "") for a, b, label in steps if a == me
    ]


def _drawing(data: Props, direction: str, name: str, desc: str, tag: str) -> Shape:
    plan, screens = _plan(data, direction)
    by_id = {str(s["id"]): s for s in screens}
    ids = set(by_id)
    steps = _steps(data, ids)
    _, titles = _lanes(data, screens)
    seed = zlib.crc32(repr(sorted(data.items())).encode())
    down = direction == "TB"
    body = [_band(b, titles[b.index], down) for b in plan.bands]
    for link in plan.links:
        said = f"{by_id[link.source]['title']} to {by_id[link.target]['title']}"
        label = next(
            (x for a, b, x in steps if (a, b) == (link.source, link.target)), ""
        )
        body.append(_link(link, said + (f" on {label}" if label else "")))
    body += [
        _tile(t, n, by_id[t.id], f"sf{seed:08x}{tag}{n}", len(screens))
        for n, t in enumerate(plan.tiles, 1)
    ]
    attrs = {
        "class": "vd-sf-svg",
        "width": f"{plan.width:g}",
        "height": f"{plan.height:g}",
        "viewBox": view_box((0.0, 0.0, plan.width, plan.height)),
        "role": "img",
        "aria-label": name,
    }
    head = [el("title", {}, name), el("desc", {}, desc)]
    return el("svg", attrs, head + body)


def _regions(screen: Props) -> str:
    names = [str(as_dict(screen["regions"])[k]) for k in _used(dict(screen))]
    return f"{count_noun(len(names), 'region', 'regions')}: {', '.join(names)}"


def _item_parts(data: Props) -> list[tuple[Props, str, str, str]]:
    """(screen, lane suffix, region summary, next text) in reading order."""
    plan, screens = _plan(data, "LR")
    by_id = {str(s["id"]): s for s in screens}
    of, lanes = _lanes(data, screens)
    titles = {i: str(s["title"]) for i, s in by_id.items()}
    steps = _steps(data, set(by_id))
    out = []
    for tile in plan.tiles:
        screen = by_id[tile.id]
        lane = f" ({lanes[of[tile.id]]} lane)" if data.get("lanes") else ""
        follow = _next_pairs(steps, titles, tile.id)
        out.append(
            (
                screen,
                lane,
                _regions(screen),
                "next: " + ", ".join(follow) if follow else "end of flow",
            )
        )
    return out


def _note_items(screen: Props) -> list[dict[str, object]]:
    regions = as_dict(screen["regions"])
    return [
        {"n": n, "name": str(regions[r]), "text": text}
        for n, r, text in _notes(dict(screen))
    ]


def _item(parts: tuple[Props, str, str, str]) -> dict[str, object]:
    screen, lane, regions, follow = parts
    return {
        "id": str(screen["id"]),
        "title": str(screen["title"]),
        "lane": lane,
        "regions": regions,
        "next": follow,
        "notes": _note_items(screen),
    }


def alternative_lines(data: Props) -> list[str]:
    """`Title: 3 regions: a, b; next: Other (label)`, one per screen, in order."""
    return [f"{s['title']}{lane}: {r}; {f}" for s, lane, r, f in _item_parts(data)]


def _summary(data: Props) -> str:
    screens = _screens(data)
    steps = _steps(data, {str(s["id"]) for s in screens})
    parts = [
        count_noun(len(screens), "screen", "screens"),
        count_noun(len(steps), "step", "steps"),
    ]
    lanes = as_list(data.get("lanes"))
    if lanes:
        parts.append(count_noun(len(lanes), "lane", "lanes"))
    return ", ".join(parts)


def copy_text(data: Props) -> str:
    """Plain text for the Copy entry: the title, then the numbered screens."""
    head = f"{data.get('title', 'Screen flow')} (screen flow, {_summary(data)})"
    lines = [f"{n}. {line}" for n, line in enumerate(alternative_lines(data), 1)]
    return "\n".join([head, *lines])


def screen_flow_props(data: dict[str, object]) -> dict[str, object]:
    title, desc = str(data.get("title", "")), str(data.get("desc", "Screen flow"))
    name = title or "Screen flow"
    return {
        "title": title,
        "name": name,
        "summary": f"{desc} ({_summary(data)})",
        "views": [
            {
                "way": way,
                "svg": _drawing(data, direction, name, f"{desc}, {way}", tag),
            }
            for direction, way, tag in _DIRECTIONS
        ],
        "items": [_item(p) for p in _item_parts(data)],
        "copy": copy_text(data),
    }
