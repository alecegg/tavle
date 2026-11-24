"""Task dependency graph: `deps` edges to fixed server-side inline SVG. Stdlib only."""

from collections.abc import Mapping

_NODE_W, _NODE_H = 112, 30
_GAP_X, _GAP_Y, _PAD = 16, 40, 10
_MAX_LABEL = 16
_MAX_NODES = 200  # defined and unknown nodes together
_MAX_EDGES = 400


def parse_deps(edges: Mapping[str, object]) -> dict[str, list[str]]:
    """Map task id to its distinct dependency ids, from the `edges` prop."""
    graph: dict[str, list[str]] = {}
    for task, needs in edges.items():
        deps = graph.setdefault(task, [])
        for dep in needs if isinstance(needs, list) else []:
            if isinstance(dep, str) and dep and dep not in deps:
                deps.append(dep)
    return graph


def _keep_deps(
    deps: list[str], nodes: set[str], edges: int
) -> tuple[list[str], int, bool]:
    """The deps that fit under the caps, the new edge count, and whether any dropped."""
    kept: list[str] = []
    truncated = False
    for dep in deps:
        full = dep not in nodes and len(nodes) >= _MAX_NODES
        if full or edges >= _MAX_EDGES:
            truncated = True
            continue
        nodes.add(dep)
        kept.append(dep)
        edges += 1
    return kept, edges, truncated


def limit_graph(graph: dict[str, list[str]]) -> tuple[dict[str, list[str]], bool]:
    """Cap nodes and edges; also report whether anything was dropped."""
    kept: dict[str, list[str]] = {}
    nodes: set[str] = set()
    edges = 0
    truncated = False
    for task, deps in graph.items():
        if len(nodes) >= _MAX_NODES and task not in nodes:
            truncated = True
            continue
        nodes.add(task)
        kept[task], edges, cut = _keep_deps(deps, nodes, edges)
        truncated = truncated or cut
    return kept, truncated


def _layer_from(root: str, graph: dict[str, list[str]], layers: dict[str, int]) -> None:
    """Iterative depth-first walk from `root`, filling `layers` for what it reaches."""
    stack = [(root, iter(graph.get(root, [])))]
    active = {root}
    best = {root: 0}
    while stack:
        node, pending = stack[-1]
        nxt = next(pending, None)
        if nxt is None:
            layers[node] = best[node]
            active.discard(node)
            stack.pop()
            if stack:
                parent = stack[-1][0]
                best[parent] = max(best[parent], layers[node] + 1)
        elif nxt in layers:
            best[node] = max(best[node], layers[nxt] + 1)
        elif nxt not in active:
            active.add(nxt)
            best[nxt] = 0
            stack.append((nxt, iter(graph.get(nxt, []))))


def assign_layers(graph: dict[str, list[str]]) -> dict[str, int]:
    """Layer = longest dependency chain below a node; back edges of cycles are ignored.

    Unknown dependencies are layered too, as nodes with no dependencies.
    """
    layers: dict[str, int] = {}
    for root in [*graph, *(d for deps in graph.values() for d in deps)]:
        if root not in layers:
            _layer_from(root, graph, layers)
    return layers


def _label(name: str) -> str:
    return name if len(name) <= _MAX_LABEL else name[: _MAX_LABEL - 1] + "…"


def deps_layout(
    edges: Mapping[str, object], status: Mapping[str, object] | None = None
) -> dict[str, object]:
    """What the `deps` component draws: canvas size, arrow paths, positioned nodes."""
    graph, truncated = limit_graph(parse_deps(edges))
    if not graph:
        return {"empty": True}
    layers = assign_layers(graph)
    rows: dict[int, list[str]] = {}
    for name, layer in layers.items():
        rows.setdefault(layer, []).append(name)
    widest = max(len(r) for r in rows.values())
    width = _PAD * 2 + widest * _NODE_W + (widest - 1) * _GAP_X
    height = _PAD * 2 + len(rows) * _NODE_H + (len(rows) - 1) * _GAP_Y
    pos: dict[str, tuple[float, float]] = {}
    for layer, names in rows.items():
        row_w = len(names) * _NODE_W + (len(names) - 1) * _GAP_X
        left = (width - row_w) / 2
        top = _PAD + layer * (_NODE_H + _GAP_Y)
        for n, name in enumerate(names):
            pos[name] = (left + n * (_NODE_W + _GAP_X), top)
    return {
        "empty": False,
        "width": width,
        "height": height,
        "truncated": truncated,
        "edges": [
            _edge_path(pos[dep], pos[task], layers[dep] < layers[task])
            for task, deps in graph.items()
            for dep in deps
            if dep != task
        ],
        "nodes": [
            _node_props(name, pos[name], name in graph, (status or {}).get(name))
            for name in layers
        ],
    }


def _edge_path(
    dep: tuple[float, float], task: tuple[float, float], forward: bool
) -> dict[str, object]:
    x1, y1 = dep[0] + _NODE_W / 2, dep[1] + _NODE_H
    x2, y2 = task[0] + _NODE_W / 2, task[1]
    if not forward:
        y1 = dep[1] + _NODE_H / 2
        y2 = task[1] + _NODE_H / 2
    mid = (y1 + y2) / 2
    path = f"M{x1:.0f} {y1:.0f}C{x1:.0f} {mid:.0f} {x2:.0f} {mid:.0f} {x2:.0f} {y2:.0f}"
    return {"d": path, "back": not forward}


def _node_props(
    name: str, at: tuple[float, float], known: bool, status: object
) -> dict[str, object]:
    result = {
        "known": known,
        "title": name + ("" if known else " (not defined)"),
        "label": _label(name),
        "x": f"{at[0]:.0f}",
        "y": f"{at[1]:.0f}",
        "tx": f"{at[0] + _NODE_W / 2:.0f}",
        "ty": f"{at[1] + _NODE_H / 2 + 4:.0f}",
        "w": _NODE_W,
        "h": _NODE_H,
    }
    if isinstance(status, str):
        result["status"] = status
        result["title"] += f": {status}"
    return result
