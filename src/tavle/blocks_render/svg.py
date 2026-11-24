"""SVG helpers shared by the chart, diagram, flow and wireframe props builders.

Styling is by class only (colours come from `--vd-*` tokens in `static/css`):
no `style=` attribute, no fixed width, every text from props escaped.
"""

from typing import Any

from ..blocks_render.common import esc

# A drawn element the browser builds: [tag, attributes, text or child shapes].
Shape = list[Any]

_MARKER_SHAPES = ("circle", "square", "triangle", "diamond", "cross", "plus")
_DASHES = ("", "6 3", "2 3", "8 3 2 3", "1 4", "10 4")


def el(
    tag: str, attrs: dict[str, str], content: str | list[Shape] | None = None
) -> Shape:
    """One SVG element for `static/components/shared.js` `scene` to build."""
    return [tag, attrs, content]


def f1(value: float) -> str:
    """A coordinate to one decimal."""
    return f"{value:.1f}"


def view_box(box: tuple[float, float, float, float]) -> str:
    return " ".join(f"{v:g}" for v in box)


def marker_shape(index: int) -> str:
    """Series differentiator besides colour: a point-marker shape name."""
    return _MARKER_SHAPES[index % len(_MARKER_SHAPES)]


def dash(index: int) -> str:
    """Series differentiator besides colour: a `stroke-dasharray` ('' is solid)."""
    return _DASHES[index % len(_DASHES)]


def wrap_text(text: str, width: int) -> list[str]:
    """Break text into lines of at most `width` characters; long words are split."""
    width = max(width, 1)
    lines: list[str] = []
    current = ""
    for word in text.split():
        rest = word
        while len(rest) > width:
            if current:
                lines.append(current)
                current = ""
            lines.append(rest[:width])
            rest = rest[width:]
        joined = f"{current} {rest}" if current else rest
        if len(joined) <= width:
            current = joined
            continue
        lines.append(current)
        current = rest
    if current:
        lines.append(current)
    return lines


def ellipsize(text: str, limit: int) -> str:
    """The text cut to `limit` characters, a cut marked with an ellipsis."""
    return text if len(text) <= limit else text[: max(limit - 1, 1)] + "…"


def clip_lines(text: str, chars: int, limit: int) -> tuple[str, ...]:
    """Wrap to `chars`, keep `limit` lines, mark a cut with an ellipsis."""
    lines = wrap_text(text, chars)
    if len(lines) <= limit:
        return tuple(lines)
    kept = lines[:limit]
    kept[-1] = kept[-1][: max(chars - 1, 1)] + "…"
    return tuple(kept)


def copy_attr(text: str) -> str:
    """The `data-copy` attribute the action menu's Copy entry reads."""
    return f' data-copy="{esc(text)}"'
