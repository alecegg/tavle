"""Block type for structure: diagram (a graph or tree of nodes and edges)."""

from varde.pages.blocks.rules import Fault, duplicates, tables
from varde.pages.blocks.spec import BlockSpec, PropertySpec

KINDS = ("graph", "tree")
SHAPES = ("box", "rounded", "cylinder", "diamond")
EMPHASIS = ("focus", "warning")
EDGE_STYLES = ("solid", "dashed", "dotted")
DIRECTIONS = ("LR", "TB")
MAX_NODES = 200
MAX_EDGES = 400
MAX_GROUPS = 3  # one pre-computed layout per subset of collapsed groups


def empty_list_faults(
    data: dict[str, object], keys: tuple[str, ...], where: str
) -> list[Fault]:
    """An empty list passes the properties; these blocks need at least one item."""
    return [
        Fault("type", f"{where}: '{key}' must not be empty")
        for key in keys
        if data.get(key) == []
    ]


def _group_faults(data: dict[str, object]) -> tuple[list[Fault], list[str]]:
    faults: list[Fault] = []
    entries = tables(data, "groups", "diagram")
    names = [n for g in entries if isinstance(n := g.get("id"), str)]
    faults += [
        Fault("group-duplicate", f"diagram: group id '{name}' is used more than once")
        for name in duplicates(names)
    ]
    if len(entries) > MAX_GROUPS:
        faults.append(Fault("too-many", f"diagram: at most {MAX_GROUPS} groups"))
    return faults, names


def _node_faults(
    data: dict[str, object], groups: list[str]
) -> tuple[list[Fault], list[str]]:
    faults: list[Fault] = []
    entries = tables(data, "nodes", "diagram")
    names = [n for e in entries if isinstance(n := e.get("id"), str)]
    faults += [
        Fault("node-duplicate", f"diagram: node id '{name}' is used more than once")
        for name in duplicates(names)
    ]
    if len(entries) > MAX_NODES:
        faults.append(Fault("too-many", f"diagram: at most {MAX_NODES} nodes"))
    for n, node in enumerate(entries, 1):
        where = f"nodes[{n}]"
        group = node.get("group")
        if isinstance(group, str) and group not in groups:
            faults.append(
                Fault("node-group", f"{where}: group '{group}' is not a group id")
            )
    return faults, names


def _edge_faults(data: dict[str, object], nodes: list[str]) -> list[Fault]:
    faults: list[Fault] = []
    entries = tables(data, "edges", "diagram")
    if len(entries) > MAX_EDGES:
        faults.append(Fault("too-many", f"diagram: at most {MAX_EDGES} edges"))
    for n, edge in enumerate(entries, 1):
        where = f"edges[{n}]"
        for key in ("from", "to"):
            end = edge.get(key)
            if isinstance(end, str) and end not in nodes:
                faults.append(
                    Fault("edge-target", f"{where}: {key} '{end}' is not a node id")
                )
    return faults


def _tree_parents(data: dict[str, object]) -> tuple[dict[str, str], list[Fault]]:
    parent: dict[str, str] = {}
    faults: list[Fault] = []
    for edge in tables(data, "edges", "diagram"):
        source, target = edge.get("from"), edge.get("to")
        if not (isinstance(source, str) and isinstance(target, str)):
            continue
        if target in parent:
            faults.append(
                Fault("tree-parent", f"diagram: tree node '{target}' has two parents")
            )
        parent[target] = source
    return parent, faults


def _has_cycle_from(parent: dict[str, str], start: str) -> bool:
    seen, here = {start}, parent.get(start)
    while here is not None and here not in seen:
        seen.add(here)
        here = parent.get(here)
    return here is not None


def _tree_faults(data: dict[str, object]) -> list[Fault]:
    """A tree has one parent per node and no cycle."""
    parent, faults = _tree_parents(data)
    for start in parent:
        if _has_cycle_from(parent, start):
            faults.append(
                Fault("tree-cycle", f"diagram: tree has a cycle through '{start}'")
            )
            break
    return faults


def validate_diagram(data: dict[str, object]) -> list[Fault]:
    faults = empty_list_faults(data, ("nodes", "edges", "groups"), "diagram")
    group_faults, groups = _group_faults(data)
    node_faults, nodes = _node_faults(data, groups)
    faults += group_faults + node_faults + _edge_faults(data, nodes)
    used = {
        g
        for n in tables(data, "nodes", "diagram")
        if isinstance(g := n.get("group"), str)
    }
    faults += [
        Fault("group-empty", f"diagram: group '{g}' has no nodes")
        for g in groups
        if g not in used
    ]
    if data.get("kind") == "tree":
        faults += _tree_faults(data)
    return faults


DIAGRAM = BlockSpec(
    "diagram",
    "A graph or tree of nodes and edges, laid out and drawn as SVG",
    (
        "kind        graph or tree",
        "nodes: list of {id, label, group, shape, detail, emphasis}",
        "  id      unique node name",
        "  label   text on the node",
        "  group   optional group id; the group can be collapsed",
        "  shape   optional: box (default), rounded, cylinder or diamond",
        "  detail  optional longer text shown when the node is selected",
        "  emphasis  optional focus or warning; also shown as text",
        "edges: optional list of {from, to, label, style, emphasis}",
        "  from, to  node ids",
        "  label     optional text on the edge",
        "  style     optional: solid (default), dashed or dotted",
        "  emphasis  optional focus or warning; also shown as text",
        "groups: optional list of {id, label}, at most 3",
        "direction   optional LR (graph default) or TB (tree default)",
        "title, desc optional text",
        f"limits: {MAX_NODES} nodes, {MAX_EDGES} edges; a tree has one parent per node",
    ),
    r"""diagram = diagram(
  kind: "graph",
  title: "Request path",
  direction: "LR",
  groups: [{"id": "edge", "label": "Edge"}, {"id": "core", "label": "Core"}],
  nodes: [
    {"id": "user", "label": "User", "shape": "rounded"},
    {"id": "gw", "label": "Gateway", "group": "edge", "detail": "Terminates TLS"},
    {"id": "api", "label": "API", "group": "core"},
    {"id": "db", "label": "Database", "group": "core", "shape": "cylinder"},
  ],
  edges: [
    {"from": "user", "to": "gw", "label": "https"},
    {"from": "gw", "to": "api"},
    {"from": "api", "to": "db", "label": "sql", "style": "dashed"},
  ],
)
""",
    validate_diagram,
    properties=(
        PropertySpec("kind", "string", required=True, enum=KINDS),
        PropertySpec(
            "nodes",
            "list",
            required=True,
            items="object",
            fields=(
                PropertySpec("id", "string", required=True),
                PropertySpec("label", "string", required=True),
                PropertySpec("group", "string"),
                PropertySpec("shape", "string", enum=SHAPES),
                PropertySpec("detail", "string"),
                PropertySpec("emphasis", "string", enum=EMPHASIS),
            ),
        ),
        PropertySpec(
            "edges",
            "list",
            items="object",
            fields=(
                PropertySpec("from", "string", required=True),
                PropertySpec("to", "string", required=True),
                PropertySpec("label", "string"),
                PropertySpec("style", "string", enum=EDGE_STYLES),
                PropertySpec("emphasis", "string", enum=EMPHASIS),
            ),
        ),
        PropertySpec("direction", "string", enum=DIRECTIONS),
        PropertySpec(
            "groups",
            "list",
            items="object",
            fields=(
                PropertySpec("id", "string", required=True),
                PropertySpec("label", "string", required=True),
            ),
        ),
        PropertySpec("title", "string"),
        PropertySpec("desc", "string"),
    ),
)
