"""Block type for a multi-screen wireframe flow: screens, steps and optional lanes."""

from varde.pages.blocks.rules import Fault, duplicates, tables
from varde.pages.blocks.screens import FRAME_PROPERTIES, SURFACE, frame_faults
from varde.pages.blocks.spec import BlockSpec, PropertySpec

MAX_SCREENS = 12
MAX_STEPS = 20
WHERE = "screen-flow"


def _ids(data: dict[str, object]) -> list[str] | None:
    """Screen ids; None unless screens is a list of tables that each name an id."""
    screens = data.get("screens")
    if not isinstance(screens, list) or not screens:
        return None
    ids = [s.get("id") for s in screens if isinstance(s, dict)]
    if len(ids) < len(screens) or not all(isinstance(i, str) for i in ids):
        return None
    return [i for i in ids if isinstance(i, str)]


def _screen_faults(data: dict[str, object]) -> list[Fault]:
    entries = tables(data, "screens", WHERE)
    ids = [i for s in entries if isinstance(i := s.get("id"), str)]
    faults = [
        Fault("screen-duplicate", f"{WHERE}: screen id '{name}' is used twice")
        for name in duplicates(ids)
    ]
    if len(entries) > MAX_SCREENS:
        faults.append(Fault("too-many", f"{WHERE}: at most {MAX_SCREENS} screens"))
    for n, screen in enumerate(entries, 1):
        faults += frame_faults(screen, f"screens[{n}]")
    return faults


def _end_fault(step: dict[str, object], key: str, ids: list[str], where: str):
    end = step.get(key)
    if isinstance(end, str) and end not in ids:
        return [Fault("step-screen", f"{where}: {key} '{end}' is not a screen id")]
    return []


def _step_faults(data: dict[str, object], ids: list[str]) -> list[Fault]:
    steps = tables(data, "steps", WHERE)
    faults: list[Fault] = []
    if len(steps) > MAX_STEPS:
        faults.append(Fault("too-many", f"{WHERE}: at most {MAX_STEPS} steps"))
    for n, step in enumerate(steps, 1):
        where = f"steps[{n}]"
        faults += _end_fault(step, "from", ids, where)
        faults += _end_fault(step, "to", ids, where)
    return faults


def _members(lane: object) -> list[str] | None:
    """The screen ids a lane names; None unless it holds a non-empty list of strings."""
    members = lane.get("screens") if isinstance(lane, dict) else None
    if (
        isinstance(members, list)
        and members
        and all(isinstance(m, str) for m in members)
    ):
        return members
    return None


def _lane_faults(data: dict[str, object], ids: list[str]) -> list[Fault]:
    lanes = tables(data, "lanes", WHERE)
    named = [_members(lane) for lane in lanes]
    faults = [
        Fault("lane-screen", f"lanes[{n}]: '{name}' is not a screen id")
        for n, names in enumerate(named, 1)
        for name in names or []
        if name not in ids
    ]
    if not lanes or None in named:
        return faults
    placed = [name for names in named for name in names or []]
    faults += [
        Fault("lane-duplicate", f"{WHERE}: screen '{name}' is in more than one lane")
        for name in duplicates(placed)
    ]
    return faults + [
        Fault("lane-missing", f"{WHERE}: screen '{name}' is in no lane")
        for name in ids
        if name not in placed
    ]


def _links_well_formed(data: dict[str, object]) -> bool:
    """Every step names two ids and every lane lists ids, so a layout exists."""
    steps, lanes = data.get("steps", []), data.get("lanes", [])
    if not isinstance(steps, list) or not isinstance(lanes, list):
        return False
    steps_named = all(
        isinstance(s, dict)
        and isinstance(s.get("from"), str)
        and isinstance(s.get("to"), str)
        for s in steps
    )
    return steps_named and all(_members(lane) is not None for lane in lanes)


def _lane_of(data: dict[str, object]) -> dict[str, int]:
    """Lane index per screen id; empty when no lanes are declared."""
    out: dict[str, int] = {}
    for k, lane in enumerate(tables(data, "lanes", WHERE)):
        members = lane.get("screens")
        for name in members if isinstance(members, list) else []:
            if isinstance(name, str):
                out[name] = k
    return out


def _pairs(data: dict[str, object], ids: list[str]) -> list[tuple[str, str]]:
    steps = tables(data, "steps", WHERE)
    return [
        (a, b)
        for s in steps
        if isinstance(a := s.get("from"), str) and isinstance(b := s.get("to"), str)
        if a in ids and b in ids
    ]


def _flow_faults(data: dict[str, object], ids: list[str]) -> list[Fault]:
    """Cycles, then lanes and ranks: a step joins neighbouring ranks of one lane."""
    # Imported here: the renderer package imports this one at load time.
    from varde.pages.blocks_render.diagram_layout import (
        assign_layers,
        back_edges,
    )

    pairs = _pairs(data, ids)
    faults = [
        Fault("step-duplicate", f"{WHERE}: step '{a}' to '{b}' is given twice")
        for a, b in sorted({p for p in pairs if pairs.count(p) > 1})
    ]
    pairs = list(dict.fromkeys(pairs))
    loops = sorted(back_edges(ids, pairs))
    if loops:
        return faults + [
            Fault(
                "cycle",
                f"{WHERE}: step '{pairs[i][0]}' to '{pairs[i][1]}' closes a cycle; "
                "a flow runs one way",
            )
            for i in loops
        ]
    rank, lane = assign_layers(ids, pairs), _lane_of(data)
    faults += _placement_faults(pairs, rank, lane)
    return faults + _cell_faults(ids, rank, lane)


def _placement_faults(
    pairs: list[tuple[str, str]], rank: dict[str, int], lane: dict[str, int]
) -> list[Fault]:
    faults: list[Fault] = []
    for a, b in pairs:
        if lane.get(a, 0) != lane.get(b, 0):
            faults.append(
                Fault(
                    "step-lane",
                    f"{WHERE}: step '{a}' to '{b}' crosses lanes; "
                    "put both screens in one lane",
                )
            )
        elif rank[b] != rank[a] + 1:
            faults.append(
                Fault(
                    "step-rank",
                    f"{WHERE}: step '{a}' to '{b}' skips a rank; "
                    "add an intermediate screen between them",
                )
            )
    return faults


def _cell_faults(
    ids: list[str], rank: dict[str, int], lane: dict[str, int]
) -> list[Fault]:
    cells: dict[tuple[int, int], list[str]] = {}
    for name in ids:
        cells.setdefault((rank[name], lane.get(name, 0)), []).append(name)
    return [
        Fault(
            "cell-taken",
            f"{WHERE}: screens {', '.join(repr(m) for m in members)} share a lane "
            "and a rank; give one its own lane or chain them with a step",
        )
        for members in cells.values()
        if len(members) > 1
    ]


def validate_screen_flow(data: dict[str, object]) -> list[Fault]:
    faults = _screen_faults(data)
    ids = _ids(data)
    if ids is None:
        return faults
    faults += _step_faults(data, ids) + _lane_faults(data, ids)
    if faults or not _links_well_formed(data):
        return faults
    return _flow_faults(data, ids)


SCREEN_FLOW = BlockSpec(
    "screen-flow",
    "A flow of wireframe screens in lanes, joined by labelled arrows",
    (
        "screens: list of {id, title, grid, regions, surface, kinds, notes}, 1 to 12",
        "  id, title  unique screen name and its caption",
        "  grid, regions, surface, kinds, notes  as in wireframe (drawn at half size)",
        "steps: optional list of {from, to, label}, up to 20",
        "  from, to  screen ids; a step joins neighbouring ranks of one lane",
        "  label     optional text on the arrow",
        "  A step across lanes or over a rank is a fault: add an intermediate screen.",
        "  A cycle is a fault; one screen per lane and rank.",
        "lanes: optional list of {title, screens: [id]}; every screen in one lane",
        "title, desc  optional text; desc is a one-sentence summary",
        "  Screens read left to right (top to bottom on phones); select one to hear",
        "  its notes. The screens are always also listed as text, in step order.",
    ),
    r"""screen-flow = screen-flow(
  title: "Checkout",
  desc: "The buyer picks a cart, pays, and sees a receipt.",
  screens: [
    {"id": "cart", "title": "Cart", "surface": "phone",
     "grid": ["HH", "LL", "BB"], "regions": {"H": "header", "L": "lines", "B": "pay"},
     "kinds": {"L": "list", "B": "action"},
     "notes": [{"region": "B", "text": "Disabled while the cart is empty"}]},
    {"id": "pay", "title": "Payment", "surface": "phone",
     "grid": ["HH", "FF", "BB"], "regions": {"H": "header", "F": "card", "B": "pay"},
     "kinds": {"F": "input", "B": "action"}},
    {"id": "done", "title": "Receipt", "surface": "phone",
     "grid": ["HH", "RR"], "regions": {"H": "header", "R": "receipt"}},
  ],
  steps: [
    {"from": "cart", "to": "pay", "label": "Pay"},
    {"from": "pay", "to": "done", "label": "Card accepted"},
  ],
)
""",
    validate_screen_flow,
    properties=(
        PropertySpec("title", "string", nonempty=True),
        PropertySpec("desc", "string", nonempty=True),
        PropertySpec(
            "screens",
            "list",
            required=True,
            items="object",
            nonempty=True,
            fields=(
                PropertySpec("id", "string", required=True, nonempty=True),
                PropertySpec("title", "string", required=True, nonempty=True),
                SURFACE,
                *FRAME_PROPERTIES,
            ),
        ),
        PropertySpec(
            "steps",
            "list",
            items="object",
            nonempty=True,
            fields=(
                PropertySpec("from", "string", required=True),
                PropertySpec("to", "string", required=True),
                PropertySpec("label", "string", nonempty=True),
            ),
        ),
        PropertySpec(
            "lanes",
            "list",
            items="object",
            nonempty=True,
            fields=(
                PropertySpec("title", "string", required=True, nonempty=True),
                PropertySpec(
                    "screens", "list", required=True, items="string", nonempty=True
                ),
            ),
        ),
    ),
)
