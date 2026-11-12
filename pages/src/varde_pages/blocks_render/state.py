"""Props for the state block, drawn on the flow layout.

`state_graph` adapts the states and transitions to `layout_graph`; this module draws
the result: start dot, double border for final, cross mark for error, dashed border
for unreachable, self-loops with their label beside the node.
`static/components/state.js` builds the DOM: the drawing sits at 1:1 scale in a
scroll region. Below it the states and an ordered list of transitions are the text
alternative, the print form and the copy text. Colours come only from `--vd-*`
tokens in `60-state.css`.
"""

from dataclasses import replace

from varde_pages.blocks_render.common import count_noun
from varde_pages.blocks_render.diagram_layout import (
    Box,
    Layout,
    PlacedEdge,
    PlacedNode,
    layout_graph,
)
from varde_pages.blocks_render.diagrams import _head, _text
from varde_pages.blocks_render.state_graph import (
    KIND_WORDS,
    Props,
    free_id,
    kind_of,
    loop_labels,
    states_of,
    transition_text,
    transitions_of,
    unreachable_ids,
)
from varde_pages.blocks_render.state_graph import (
    graph_specs as specs,
)
from varde_pages.blocks_render.svg import Shape, el, f1, view_box

DOT_R = 8.0
RING = 4.0
LINE = 16.0


Names = dict[str, tuple[str, str]]


def _dot(box: Box) -> Shape:
    circle = el(
        "circle",
        {
            "class": "vd-state-dot",
            "cx": f1(box.w / 2),
            "cy": f1(box.h / 2),
            "r": f"{DOT_R:g}",
        },
    )
    title = el("title", {}, "initial state marker")
    attrs = {
        "class": "vd-state-start",
        "transform": f"translate({f1(box.x)} {f1(box.y)})",
    }
    return el("g", attrs, [title, circle])


def _node(node: PlacedNode, names: Names, dim: set[str], start: str) -> Shape:
    spec, box = node.spec, node.box
    if spec.id == start:
        return _dot(box)
    kind, unreachable = names[spec.id][1], spec.id in dim
    cls = f"vd-state-node vd-state-{kind}" + (
        " vd-state-unreachable" if unreachable else ""
    )
    shape = [
        el(
            "rect",
            {
                "class": "vd-state-shape",
                "width": f1(box.w),
                "height": f1(box.h),
                "rx": "10",
            },
        )
    ]
    if kind == "final":
        ring = {
            "class": "vd-state-ring",
            "x": f"{RING:g}",
            "y": f"{RING:g}",
            "width": f1(box.w - 2 * RING),
            "height": f1(box.h - 2 * RING),
            "rx": "7",
        }
        shape.append(el("rect", ring))
    said = f"{names[spec.id][0]}, {KIND_WORDS[kind]}" + (
        ", unreachable" if unreachable else ""
    )
    text = _text(node.lines, "vd-state-label", box.w / 2, box.h / 2, LINE)
    attrs = {"class": cls, "transform": f"translate({f1(box.x)} {f1(box.y)})"}
    return el("g", attrs, [el("title", {}, said), *shape, text])


def _label(box: Box, lines: tuple[str, ...]) -> list[Shape]:
    background = {
        "class": "vd-state-label-bg",
        "x": f1(box.x),
        "y": f1(box.y),
        "width": f1(box.w),
        "height": f1(box.h),
        "rx": "3",
    }
    text = _text(
        lines, "vd-state-edge-label", box.x + box.w / 2, box.y + box.h / 2, 14.0
    )
    return [el("rect", background), text]


def _edge(edge: PlacedEdge, said: str) -> Shape:
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in edge.points)
    box, lines = edge.label_box, edge.label_lines
    label = _label(box, lines) if box is not None and lines else []
    return el(
        "g",
        {"class": "vd-state-edge"},
        [
            el("title", {}, said),
            el("path", {"class": "vd-state-line", "d": d}),
            _head(edge.points, "vd-state-head"),
            *label,
        ],
    )


def _start_edge(edge: PlacedEdge, marker: Box) -> PlacedEdge:
    """The arrow leaves the dot, not the empty layout box around it."""
    x = edge.points[0][0]
    leaving = (x, marker.y + marker.h / 2 + DOT_R)
    return replace(edge, points=(leaving, *edge.points[1:]))


def _edge_texts(
    moves: list[Props], labels: dict[str, str], first: str | None
) -> list[str]:
    """Spoken text per layout edge, in the order `graph_specs` emits them."""
    plain = [m for m in moves if m["from"] != m["to"]]
    texts = [] if first is None else [f"initial state marker to {labels[first]}"]
    texts += [transition_text(m, labels) for m in plain]
    for state in loop_labels(moves):
        own = [m for m in moves if m["from"] == m["to"] == state]
        texts.append(" / ".join(transition_text(m, labels) for m in own))
    return texts


def _edge_shapes(layout: Layout, said: list[str], start: str) -> list[Shape]:
    """Edges in layout order; those leaving the initial marker start at its dot."""
    marker = next((n.box for n in layout.nodes if n.spec.id == start), None)
    body: list[Shape] = []
    for index, placed in enumerate(layout.edges):
        from_marker = marker is not None and placed.spec.source == start
        edge = _start_edge(placed, marker) if from_marker and marker else placed
        body.append(_edge(edge, said[index]))
    return body


def _drawing(data: Props) -> dict[str, object]:
    """The state graph as shapes with its size."""
    states = states_of(data)
    ids = {str(s["id"]) for s in states}
    moves = transitions_of(data, ids)
    start = free_id(ids)
    nodes, edges = specs(states, moves, start)
    layout = layout_graph(nodes, edges, "TB")
    names = {str(s["id"]): (str(s["label"]), kind_of(s)) for s in states}
    initial = next((str(s["id"]) for s in states if kind_of(s) == "initial"), None)
    said = _edge_texts(moves, {i: v[0] for i, v in names.items()}, initial)
    body = _edge_shapes(layout, said, start)
    dim = unreachable_ids(states, moves)
    body += [_node(n, names, dim, start) for n in layout.nodes]
    return {
        "box": view_box((0.0, 0.0, layout.width, layout.height)),
        "width": f"{layout.width:g}",
        "height": f"{layout.height:g}",
        "shapes": body,
    }


def _state_item(state: Props, dim: set[str]) -> str:
    words = KIND_WORDS[kind_of(state)] + (
        ", unreachable from the initial state" if str(state["id"]) in dim else ""
    )
    note = f": {state['note']}" if "note" in state else ""
    return f"{state['label']} ({words}){note}"


def _summary(states: list[Props], moves: list[Props]) -> str:
    return f"{count_noun(len(states), 'state', 'states')}, " + count_noun(
        len(moves), "transition", "transitions"
    )


def copy_text(
    title: str, states: list[Props], moves: list[Props], texts: list[str]
) -> str:
    lines = [f"{title} ({_summary(states, moves)})", "States:"]
    lines += [f"- {s['label']} ({KIND_WORDS[kind_of(s)]})" for s in states]
    if texts:
        lines.append("Transitions:")
        lines += [f"{n}. {t}" for n, t in enumerate(texts, 1)]
    return "\n".join(lines)


def state_props(data: dict[str, object]) -> dict[str, object]:
    states = states_of(data)
    moves = transitions_of(data, {str(s["id"]) for s in states})
    labels = {str(s["id"]): str(s["label"]) for s in states}
    texts = [transition_text(m, labels) for m in moves]
    dim = unreachable_ids(states, moves)
    title, desc = str(data.get("title", "")), str(data["desc"])
    name = title or "State machine"
    return {
        "title": title,
        "name": name,
        "desc": desc,
        "counts": _summary(states, moves),
        "drawing": _drawing(data),
        "states": [_state_item(s, dim) for s in states],
        "moves": texts,
        "copy": copy_text(name, states, moves, texts),
    }
