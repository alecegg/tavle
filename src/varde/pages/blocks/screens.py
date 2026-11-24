"""Block types for screens: wireframe, ui-states."""

from varde.pages.blocks.rules import Fault, str_map
from varde.pages.blocks.spec import BlockSpec, PropertySpec

_REQUIRED_STATES = ("empty", "loading", "error")
_BLANK = " ."
SURFACES = ("browser", "phone", "tablet")
KINDS = ("nav", "text", "media", "input", "action", "list")
LAYOUTS = ("tabs", "grid")

SURFACE = PropertySpec("surface", "string", enum=SURFACES)
# The frame fields wireframe, its compare frame and each screen-flow screen share.
FRAME_PROPERTIES = (
    PropertySpec("grid", "list", required=True, items="string", nonempty=True),
    PropertySpec("regions", "object", required=True),
    PropertySpec("kinds", "object"),
    PropertySpec(
        "notes",
        "list",
        items="object",
        nonempty=True,
        fields=(
            PropertySpec("region", "string", required=True),
            PropertySpec("text", "string", required=True, nonempty=True),
        ),
    ),
)


def _usable_rows(data: dict[str, object]) -> list[str] | None:
    grid = data.get("grid")
    if isinstance(grid, list) and grid and all(isinstance(r, str) for r in grid):
        return grid
    return None


def _usable_regions(data: dict[str, object]) -> dict[str, object] | None:
    regions = data.get("regions")
    return regions if isinstance(regions, dict) and regions else None


def _region_faults(regions: dict, rows: list[str], where: str) -> list[Fault]:
    used = {c for r in rows for c in r if c not in _BLANK}
    faults = [
        Fault("region-undeclared", f"{where}.grid uses '{c}' with no entry in regions")
        for c in sorted(used - regions.keys())
    ]
    return faults + [
        Fault("region-unused", f"{where}.regions '{k}' does not appear in the grid")
        for k in sorted(regions.keys() - used)
        if len(k) == 1
    ]


def _grid_faults(data: dict[str, object], where: str) -> list[Fault]:
    rows = _usable_rows(data)
    regions = data.get("regions")
    faults = str_map(regions, f"{where}.regions") if isinstance(regions, dict) else []
    if rows is not None and len({len(r) for r in rows}) > 1:
        faults.append(Fault("grid-width", f"{where}.grid rows must have equal width"))
    declared = _usable_regions(data)
    if declared is None:
        return faults
    faults += [
        Fault("type", f"{where}.regions key '{k}' must be one character")
        for k in sorted(declared)
        if len(k) != 1 or k in _BLANK
    ]
    return faults + (_region_faults(declared, rows, where) if rows else [])


def _kind_faults(data: dict[str, object], where: str) -> list[Fault]:
    kinds = data.get("kinds")
    if not isinstance(kinds, dict):
        return []
    if not kinds:
        return [Fault("type", f"{where}.kinds must be a non-empty table of kinds")]
    declared = _usable_regions(data)
    faults = [
        Fault("kind-unknown", f"{where}.kinds '{k}' is not one of {', '.join(KINDS)}")
        for k, v in sorted(kinds.items())
        if v not in KINDS
    ]
    if declared is None:
        return faults
    return faults + [
        Fault("kind-region", f"{where}.kinds '{k}' is not a declared region")
        for k in sorted(kinds)
        if k not in declared
    ]


def _note_faults(data: dict[str, object], where: str) -> list[Fault]:
    notes = data.get("notes")
    declared = _usable_regions(data)
    if not isinstance(notes, list) or declared is None:
        return []
    return [
        Fault(
            "note-region",
            f"{where}.notes[{n}]: region '{note['region']}' is not declared",
        )
        for n, note in enumerate(notes, 1)
        if isinstance(note, dict)
        and isinstance(note.get("region"), str)
        and note["region"] not in declared
    ]


def frame_faults(data: dict[str, object], where: str) -> list[Fault]:
    """Value rules of one frame (grid, regions, kinds, notes) the properties lack."""
    return (
        _grid_faults(data, where)
        + _kind_faults(data, where)
        + _note_faults(data, where)
    )


def validate_wireframe(data: dict[str, object]) -> list[Fault]:
    faults = frame_faults(data, "wireframe")
    after = data.get("compare")
    if not isinstance(after, dict):
        return faults
    return faults + frame_faults(after, "wireframe.compare")


def _state_faults(name: str, state: dict[str, object]) -> list[Fault]:
    if ("shows" in state) == ("na" in state):
        return [
            Fault("state-form", f"ui-states.{name}: give exactly one of shows or na")
        ]
    return []


def _missing_state_faults(data: dict[str, object]) -> list[Fault]:
    return [
        Fault(
            "ui-state-missing",
            f"ui-states: state '{name}' is missing; "
            "describe it or mark it na with a reason",
        )
        for name in _REQUIRED_STATES
        if name not in data
    ]


def validate_ui_states(data: dict[str, object]) -> list[Fault]:
    faults = _missing_state_faults(data)
    for name, state in data.items():
        if name not in ("screen", "layout") and isinstance(state, dict):
            faults += _state_faults(name, state)
    return faults


WIREFRAME = BlockSpec(
    "wireframe",
    "Screen regions laid out on a text grid",
    (
        "title: text.",
        "grid: equal-width strings; a letter is a region, space or . is empty.",
        "regions: one-letter key = region label; every letter in grid must be",
        "  declared.",
        "surface: a device frame: browser, phone or tablet.",
        "kinds: one-letter key = nav, text, media, input, action or list; each kind",
        "  has its own hatch pattern and a [kind] label.",
        "notes: a list of {region, text}; numbered pins and a notes list.",
        "compare: a second frame {grid, regions, kinds, notes}; the main frame is",
        "  Before and compare is After (side by side on wide screens).",
    ),
    r"""wireframe = wireframe(
  title: "Orders list",
  surface: "browser",
  grid: ["HHHHHH", "SSLLLL", "SSLLLL", "FFFFFF"],
  regions: {"H": "header", "S": "filters", "L": "order list", "F": "footer"},
  kinds: {"H": "nav", "S": "input", "L": "list"},
  notes: [{"region": "S", "text": "Filters stay in the URL"}],
)
""",
    validate_wireframe,
    properties=(
        PropertySpec("title", "string", nonempty=True),
        SURFACE,
        *FRAME_PROPERTIES,
        PropertySpec("compare", "object", fields=FRAME_PROPERTIES),
    ),
)

UI_STATES = BlockSpec(
    "ui-states",
    "What a screen shows when empty, loading and failing",
    (
        "screen: the screen name.",
        "layout: tabs (one state at a time, default) or grid.",
        "empty, loading and error are required; every state, including any extra",
        "  one, takes shows (text) or na (the reason it cannot occur).",
    ),
    r"""ui-states = ui-states(
  screen: "Orders list",
  empty: {"shows": "No orders yet, with a Create order button"},
  loading: {"shows": "Skeleton rows"},
  error: {"shows": "Message and a Retry button"},
)
""",
    validate_ui_states,
    properties=(
        PropertySpec("screen", "string", nonempty=True),
        PropertySpec("layout", "string", enum=LAYOUTS),
    ),
    extra_keys=PropertySpec(
        "state",
        "object",
        fields=(
            PropertySpec("shows", "string", nonempty=True),
            PropertySpec("na", "string", nonempty=True),
        ),
    ),
)
