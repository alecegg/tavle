"""Graph and tree diagrams: props the browser draws, one layout per collapse state.

`diagram_states` lays out every subset of collapsed groups (at most 3 groups,
so at most 8 layouts); the page script only shows one and toggles `hidden`.
The first state (nothing collapsed) is what a static export shows.
`static/components/diagram.js` builds the DOM from the shapes drawn here.
"""

import math
from collections.abc import Mapping

from ..blocks_render.common import as_dict, as_list
from ..blocks_render.diagram_layout import (
    FRAME_HEAD,
    MIN_H,
    Box,
    EdgeSpec,
    Layout,
    NodeSpec,
    PlacedEdge,
    PlacedFrame,
    PlacedNode,
    layout_graph,
)
from ..blocks_render.svg import Shape, el, f1, view_box

HEAD_LEN, HEAD_HALF = 10.0, 5.0
GROUP_CLASSES = 3


def _edge_label(label: str, emphasis: str) -> str:
    if (
        emphasis == "warning"
        and label != "Warning"
        and not label.startswith("Warning:")
    ):
        return f"Warning: {label}" if label else "Warning"
    return label


def _graph(props: dict[str, object]):
    groups = [
        (str(g["id"]), str(g["label"]))
        for g in map(as_dict, as_list(props.get("groups")))
    ]
    nodes = [
        NodeSpec(
            str(n["id"]),
            str(n["label"]),
            str(n.get("shape", "box")),
            str(n.get("group", "")),
            str(n.get("emphasis", "")),
        )
        for n in map(as_dict, as_list(props["nodes"]))
    ]
    edges = [
        EdgeSpec(
            str(e["from"]),
            str(e["to"]),
            _edge_label(str(e.get("label", "")), str(e.get("emphasis", ""))),
            str(e.get("style", "solid")),
            str(e.get("emphasis", "")),
        )
        for e in map(as_dict, as_list(props.get("edges")))
    ]
    return groups, nodes, edges


def direction_of(props: dict[str, object]) -> str:
    return str(props.get("direction") or ("TB" if props["kind"] == "tree" else "LR"))


def _emphasis(values: list[str]) -> str:
    return max(
        values, key=lambda value: {"": 0, "focus": 1, "warning": 2}[value], default=""
    )


def _super_node(
    node: NodeSpec,
    nodes: list[NodeSpec],
    edges: list[EdgeSpec],
    name: str,
    labels: dict[str, str],
) -> NodeSpec:
    """The one node that stands for the shut group `node` belongs to."""
    group_ids = {n.id for n in nodes if n.lane == node.lane}
    label = f"{labels[node.lane]} ({len(group_ids)})"
    emphasis = _emphasis(
        [n.emphasis for n in nodes if n.id in group_ids]
        + [e.emphasis for e in edges if e.source in group_ids and e.target in group_ids]
    )
    return NodeSpec(name, label, "super", node.lane, emphasis)


def _merge_edges(edges: list[EdgeSpec], where: dict[str, str]) -> list[EdgeSpec]:
    """Edges between the collapsed nodes; parallel edges merge into one."""
    seen: dict[tuple[str, str], EdgeSpec] = {}
    for edge in edges:
        source, target = (
            where.get(edge.source, edge.source),
            where.get(edge.target, edge.target),
        )
        internal = source == target and edge.source != edge.target
        if internal:
            continue
        previous = seen.get((source, target))
        if not previous:
            seen[(source, target)] = EdgeSpec(
                source, target, edge.label, edge.style, edge.emphasis
            )
            continue
        emphasis = _emphasis([previous.emphasis, edge.emphasis])
        seen[(source, target)] = EdgeSpec(
            source,
            target,
            _edge_label(previous.label, emphasis),
            previous.style,
            emphasis,
        )
    return list(seen.values())


def collapse(
    nodes: list[NodeSpec], edges: list[EdgeSpec], labels: dict[str, str], shut: set[str]
) -> tuple[list[NodeSpec], list[EdgeSpec]]:
    """The graph with each group in `shut` replaced by one node `group:<id>`."""
    taken = {n.id for n in nodes}
    name = {g: _free(f"group:{g}", taken) for g in shut}
    out: list[NodeSpec] = []
    for node in nodes:
        if node.lane not in shut:
            out.append(node)
        elif not any(o.id == name[node.lane] for o in out):
            out.append(_super_node(node, nodes, edges, name[node.lane], labels))
    where = {n.id: name[n.lane] for n in nodes if n.lane in shut}
    return out, _merge_edges(edges, where)


def _free(name: str, taken: set[str]) -> str:
    while name in taken:
        name += "#"
    return name


def diagram_states(props: dict[str, object]) -> list[tuple[int, Layout]]:
    """(collapsed-group bit mask, layout) for every subset; mask 0 comes first."""
    groups, nodes, edges = _graph(props)
    labels = dict(groups)
    direction = direction_of(props)
    states = []
    for mask in range(2 ** len(groups)):
        shut = {g for bit, (g, _) in enumerate(groups) if mask >> bit & 1}
        shown_nodes, shown_edges = (
            collapse(nodes, edges, labels, shut) if shut else (nodes, edges)
        )
        frames = {g: label for g, label in groups if g not in shut}
        states.append((mask, layout_graph(shown_nodes, shown_edges, direction, frames)))
    return states


def _lane_class(lane: str, groups: list[str]) -> str:
    if lane not in groups:
        return ""
    return f" vd-g{groups.index(lane) % GROUP_CLASSES + 1}"


def _shape(shape: str, box: Box) -> list[Shape]:
    w, h = box.w, box.h
    if shape == "diamond":
        pts = f"{w / 2:.1f},0 {w:.1f},{h / 2:.1f} {w / 2:.1f},{h:.1f} 0,{h / 2:.1f}"
        return [el("polygon", {"class": "vd-shape", "points": pts})]
    if shape == "cylinder":
        ry = 7.0
        body = (
            f"M0 {ry} V{h - ry:.1f} A{w / 2:.1f} {ry} 0 0 0 {w:.1f} {h - ry:.1f} "
            f"V{ry} A{w / 2:.1f} {ry} 0 0 1 0 {ry}Z"
        )
        top = el(
            "ellipse",
            {
                "class": "vd-shape vd-cap",
                "cx": f1(w / 2),
                "cy": str(ry),
                "rx": f1(w / 2),
                "ry": str(ry),
            },
        )
        return [el("path", {"class": "vd-shape", "d": body}), top]
    radius = min(h / 2, 18) if shape == "rounded" else 3
    attrs = {"class": "vd-shape", "width": f1(w), "height": f1(h), "rx": f1(radius)}
    return [el("rect", attrs)]


def _text(lines: tuple[str, ...], cls: str, x: float, y: float, line_h: float) -> Shape:
    top = y - (len(lines) - 1) * line_h / 2
    spans = [
        el("tspan", {"x": f1(x), "y": f1(top + n * line_h)}, line)
        for n, line in enumerate(lines)
    ]
    attrs = {"class": cls, "text-anchor": "middle", "dominant-baseline": "central"}
    return el("text", attrs, spans)


def _node(node: PlacedNode, groups: list[str], bits: dict[str, int]) -> Shape:
    spec, box = node.spec, node.box
    emphasis = f" vd-emphasis-{spec.emphasis}" if spec.emphasis else ""
    cls = f"vd-node vd-{spec.shape}{_lane_class(spec.lane, groups)}{emphasis}"
    attrs = {"class": cls, "data-id": spec.id}
    if spec.shape == "super":
        attrs["data-bit"] = str(bits[spec.lane])
    attrs["transform"] = f"translate({f1(box.x)} {f1(box.y)})"
    label = _text(node.lines, "vd-label", box.w / 2, box.h / 2, 16.0)
    return el(
        "g", attrs, [el("title", {}, spec.label), *_shape(spec.shape, box), label]
    )


def _head(points: tuple[tuple[float, float], ...], cls: str = "vd-head") -> Shape:
    (x1, y1), (x2, y2) = points[-2], points[-1]
    length = math.hypot(x2 - x1, y2 - y1) or 1.0
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    bx, by = x2 - ux * HEAD_LEN, y2 - uy * HEAD_LEN
    left = (bx - uy * HEAD_HALF, by + ux * HEAD_HALF)
    right = (bx + uy * HEAD_HALF, by - ux * HEAD_HALF)
    pts = f"{x2:.1f},{y2:.1f} {left[0]:.1f},{left[1]:.1f} {right[0]:.1f},{right[1]:.1f}"
    return el("polygon", {"class": cls, "points": pts})


def _edge(edge: PlacedEdge, names: dict[str, str]) -> Shape:
    spec = edge.spec
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in edge.points)
    label: list[Shape] = []
    if edge.label_box is not None:
        b = edge.label_box
        background = {
            "class": "vd-elabel-bg",
            "x": f1(b.x),
            "y": f1(b.y),
            "width": f1(b.w),
            "height": f1(b.h),
            "rx": "3",
        }
        label = [
            el("rect", background),
            _text(edge.label_lines, "vd-elabel", b.x + b.w / 2, b.y + b.h / 2, 14.0),
        ]
    source = names.get(spec.source, spec.source)
    said = f"{source} to {names.get(spec.target, spec.target)}"
    said += f": {spec.label}" if spec.label else ""
    emphasis = f" vd-emphasis-{spec.emphasis}" if spec.emphasis else ""
    attrs = {
        "class": f"vd-edge vd-{spec.style}{emphasis}",
        "data-from": spec.source,
        "data-to": spec.target,
    }
    return el(
        "g",
        attrs,
        [
            el("title", {}, said),
            el("path", {"class": "vd-line", "d": d}),
            _head(edge.points),
            *label,
        ],
    )


def _frame(frame: PlacedFrame, groups: list[str], bits: dict[str, int]) -> Shape:
    b = frame.box
    mid = b.y + FRAME_HEAD / 2
    hit = {
        "class": "vd-head-hit",
        "x": f1(b.x),
        "y": f1(b.y),
        "width": f1(b.w),
        "height": f"{FRAME_HEAD:g}",
        "rx": "8",
    }
    chevron = {
        "class": "vd-chev",
        "x": f1(b.x + 12),
        "y": f1(mid),
        "dominant-baseline": "central",
    }
    name = {
        "class": "vd-group-label",
        "x": f1(b.x + 30),
        "y": f1(mid),
        "dominant-baseline": "central",
    }
    head = el(
        "g",
        {
            "class": "vd-group-head",
            "data-bit": str(bits[frame.lane]),
            "data-group": frame.lane,
        },
        [el("rect", hit), el("text", chevron, "\u25be"), el("text", name, frame.label)],
    )
    outline = {
        "class": "vd-frame",
        "x": f1(b.x),
        "y": f1(b.y),
        "width": f1(b.w),
        "height": f1(b.h),
        "rx": "8",
    }
    cls = f"vd-group{_lane_class(frame.lane, groups)}"
    return el("g", {"class": cls}, [el("rect", outline), head])


def state_view(
    mask: int,
    layout: Layout,
    groups: list[str],
    bits: dict[str, int],
) -> dict[str, object]:
    """One collapse state as the drawing the component builds (shapes and size)."""
    names = {n.spec.id: n.spec.label for n in layout.nodes}
    shapes = [
        *(_frame(f, groups, bits) for f in layout.frames),
        *(_edge(e, names) for e in layout.edges),
        *(_node(n, groups, bits) for n in layout.nodes),
    ]
    return {
        "mask": mask,
        "box": view_box((0.0, 0.0, layout.width, layout.height)),
        "width": f"{layout.width:g}",
        "height": f"{layout.height:g}",
        "shapes": shapes,
    }


def text_summary(props: dict[str, object]) -> str:
    n, e = len(as_list(props["nodes"])), len(as_list(props.get("edges")))
    return f"{props['kind']} with {n} nodes and {e} edges"


def copy_text(props: dict[str, object]) -> str:
    """Plain text for the Copy entry: title, nodes, then edges, by label."""
    _, nodes, edges = _graph(props)
    label = {n.id: n.label for n in nodes}
    lines = [f"{props.get('title', 'Diagram')} ({text_summary(props)})", "Nodes:"]
    lines += [
        f"- {n.label} [{n.shape}]"
        + (f" (emphasis: {n.emphasis})" if n.emphasis else "")
        for n in nodes
    ]
    lines.append("Edges:")
    for e in edges:
        said = f"- {label[e.source]} -> {label[e.target]}"
        said += f": {e.label}" if e.label else ""
        lines.append(said + (f" (emphasis: {e.emphasis})" if e.emphasis else ""))
    return "\n".join(lines)


def _alt_node(
    n: NodeSpec, group_name: dict[str, str], details: Mapping[str, object]
) -> dict[str, object]:
    tags = [n.shape] + ([f"group {group_name[n.lane]}"] if n.lane else [])
    if n.emphasis:
        tags.append(f"emphasis: {n.emphasis}")
    note = details.get(n.id)
    return {
        "id": n.id,
        "label": n.label,
        "tags": ", ".join(tags),
        "detail": str(note) if note else "",
    }


def _alt_edge(e: EdgeSpec, label: dict[str, str]) -> dict[str, object]:
    return {
        "from": e.source,
        "to": e.target,
        "text": f"{label[e.source]} to {label[e.target]}"
        + (f": {e.label}" if e.label else "")
        + (f" ({e.style})" if e.style != "solid" else "")
        + (f" (emphasis: {e.emphasis})" if e.emphasis else ""),
    }


def _alternative(props: dict[str, object]) -> dict[str, object]:
    """The text alternative: each node with its tags and detail, each edge as a line."""
    groups, nodes, edges = _graph(props)
    group_name = dict(groups)
    details = {
        str(n["id"]): n.get("detail") for n in map(as_dict, as_list(props["nodes"]))
    }
    label = {n.id: n.label for n in nodes}
    items = [_alt_node(n, group_name, details) for n in nodes]
    links = [_alt_edge(e, label) for e in edges]
    return {"summary": text_summary(props), "nodes": items, "edges": links}


def diagram_props(props: dict[str, object]) -> dict[str, object]:
    groups, _, _ = _graph(props)
    ids = [g for g, _ in groups]
    bits = {g: 1 << n for n, g in enumerate(ids)}
    title = str(props.get("title", "Diagram"))
    return {
        "heading": str(props["title"]) if "title" in props else "",
        "title": title,
        "desc": str(props.get("desc", "")) or text_summary(props),
        "unit": f"{min(MIN_H, FRAME_HEAD):g}",
        "views": [state_view(m, lay, ids, bits) for m, lay in diagram_states(props)],
        "alt": _alternative(props),
        "copy": copy_text(props),
    }
