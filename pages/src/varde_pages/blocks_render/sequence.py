"""Props for the sequence block.

The drawing is server-laid-out (`sequence_layout`) at 1:1 scale inside a scroll region,
so its text stays readable on a phone. `static/components/sequence.js` builds it.
Below it an ordered list states every step as text: that list is also the no-script,
print and copy form, and `static/sequence.js` links its items to the drawing's rows
through `data-step`. Colours come only from `--vd-*` tokens in `57-sequence.css`.
"""

from collections.abc import Mapping

from varde_pages.blocks_render.common import as_list, count_noun
from varde_pages.blocks_render.sequence_layout import (
    CHAR_W,
    HEAD_H,
    LINE_H,
    LOOP_W,
    PAD,
    Actor,
    Frame,
    Geometry,
    Row,
    clip_lines,
    layout,
)
from varde_pages.blocks_render.svg import Shape, el

Props = Mapping[str, object]
KIND_WORDS = {"call": "", "return": " (return)", "async": " (async)"}
HEAD_LEN = 9
HEAD_HALF = 5


def step_text(step: Props, labels: Mapping[str, str]) -> str:
    """`A to B: text`, `A to B (return): text`, `Note over A to B: text`."""
    source, target = labels[str(step["from"])], labels[str(step["to"])]
    kind, text = str(step.get("kind", "call")), str(step["text"])
    group = f" (group: {step['group']})" if "group" in step else ""
    if kind == "note":
        span = source if source == target else f"{source} to {target}"
        return f"Note over {span}: {text}{group}"
    return f"{source} to {target}{KIND_WORDS[kind]}: {text}{group}"


def _text(x: int, y: int, cls: str, body: str, anchor: str = "start") -> Shape:
    attrs = {"class": cls, "x": str(x), "y": str(y), "text-anchor": anchor}
    return el("text", attrs, body)


def _lines(row: Row, top: int) -> list[Shape]:
    return [
        _text(row.text_x, top + n * LINE_H, "vd-sequence-text", line, row.anchor)
        for n, line in enumerate(row.lines)
    ]


def _head(x: int, y: int, direction: int, filled: bool) -> Shape:
    back = x - direction * HEAD_LEN
    if filled:
        points = f"{x},{y} {back},{y - HEAD_HALF} {back},{y + HEAD_HALF}"
        return el("polygon", {"class": "vd-sequence-head", "points": points})
    path = f"M{back} {y - HEAD_HALF} L{x} {y} L{back} {y + HEAD_HALF}"
    return el("path", {"class": "vd-sequence-head-open", "d": path})


def _arrow(row: Row) -> list[Shape]:
    cls = "vd-sequence-line" + (" vd-sequence-dashed" if row.kind == "return" else "")
    filled = row.kind == "call"
    if row.self_call:
        y, x = row.arrow_y, row.x1
        path = f"M{x} {y} H{x + LOOP_W} V{y + 14} H{x}"
        return [el("path", {"class": cls, "d": path}), _head(x, y + 14, -1, filled)]
    direction = 1 if row.x2 > row.x1 else -1
    line = el("path", {"class": cls, "d": f"M{row.x1} {row.arrow_y} H{row.x2}"})
    return [line, _head(row.x2, row.arrow_y, direction, filled)]


def _row_body(row: Row) -> list[Shape]:
    if row.kind == "note":
        box = el(
            "rect",
            {
                "class": "vd-sequence-note-box",
                "x": str(row.x1),
                "y": str(row.y + 4),
                "width": str(row.x2 - row.x1),
                "height": str(row.h - 8),
                "rx": "4",
            },
        )
        top = row.y + 4 + (row.h - 8 - LINE_H * len(row.lines)) // 2 + 12
        return [box, *_lines(row, top)]
    return [*_lines(row, row.y + 14), *_arrow(row)]


def _row(row: Row, width: int) -> Shape:
    hit = el(
        "rect",
        {
            "class": "vd-sequence-hit",
            "x": "1",
            "y": str(row.y + 1),
            "width": str(width - 2),
            "height": str(row.h - 2),
        },
    )
    attrs = {
        "class": f"vd-sequence-row vd-sequence-{row.kind}",
        "data-step": str(row.index),
    }
    return el("g", attrs, [hit, *_row_body(row)])


def _actor(actor: Actor, bottom: int) -> Shape:
    title = [el("title", {}, actor.label)] if actor.truncated else []
    texts = [
        _text(actor.x, 18 + n * LINE_H, "vd-sequence-name", line, "middle")
        for n, line in enumerate(actor.lines)
    ]
    life = el(
        "path", {"class": "vd-sequence-life", "d": f"M{actor.x} {HEAD_H} V{bottom}"}
    )
    box = el(
        "rect",
        {
            "class": "vd-sequence-actor-box",
            "x": str(actor.box_x),
            "y": "1",
            "width": str(actor.box_w),
            "height": str(HEAD_H - 2),
            "rx": "4",
        },
    )
    return el("g", {"class": "vd-sequence-actor"}, [*title, life, box, *texts])


def _frame(frame: Frame, width: int) -> Shape:
    chars = max((width - PAD - 16) // CHAR_W, 4)
    label = clip_lines(frame.label, chars, 1)[0]
    cut = [el("title", {}, frame.label)] if label != frame.label else []
    box = el(
        "rect",
        {
            "class": "vd-sequence-frame-box",
            "x": str(PAD // 2),
            "y": str(frame.y),
            "width": str(width - PAD),
            "height": str(frame.h),
            "rx": "4",
        },
    )
    text = _text(PAD // 2 + 8, frame.y + 17, "vd-sequence-frame-label", label)
    return el("g", {"class": "vd-sequence-frame"}, [*cut, box, text])


def _drawing(geo: Geometry) -> dict[str, object]:
    shapes = [
        *(_frame(f, geo.width) for f in geo.frames),
        *(_actor(a, geo.height - PAD // 2) for a in geo.actors),
        *(_row(r, geo.width) for r in geo.rows),
    ]
    return {"width": geo.width, "height": geo.height, "shapes": shapes}


def sequence_props(data: dict[str, object]) -> dict[str, object]:
    actors = [a for a in as_list(data["actors"]) if isinstance(a, dict)]
    steps = [s for s in as_list(data["steps"]) if isinstance(s, dict)]
    labels = {str(a["id"]): str(a["label"]) for a in actors}
    texts = [step_text(s, labels) for s in steps]
    title, desc = str(data.get("title", "")), str(data["desc"])
    counts = f"{count_noun(len(steps), 'step', 'steps')}, " + count_noun(
        len(actors), "actor", "actors"
    )
    return {
        "title": title,
        "name": title or "Sequence diagram",
        "desc": desc,
        "counts": counts,
        "drawing": _drawing(layout(actors, steps)),
        "steps": texts,
        "copy": "\n".join(f"{n}. {t}" for n, t in enumerate(texts, 1)),
    }
