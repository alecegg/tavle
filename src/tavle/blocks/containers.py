"""Block types that hold other blocks by id: tabs and columns.

Each prop list names panels `{label, blocks: [id, ...]}`; an id names another
statement of the same document. The per-statement validators check shape; the
document-level `container_errors` checks the ids against the whole page.
"""

from collections.abc import Iterator, Sequence

from varde.ui.blocks.rules import Fault
from varde.ui.blocks.spec import BlockSpec, PropertySpec

MAX_PANELS = {"tabs": 12, "columns": 4}
MAX_HELD = 200
HOLD_KEYS = {"tabs": "tab", "columns": "col"}
CONTAINERS = frozenset(HOLD_KEYS)


def _validate(data: dict[str, object], kind: str) -> list[Fault]:
    """The panel and held-id limits; the properties own every shape rule."""
    panels = data.get(HOLD_KEYS[kind])
    if not isinstance(panels, list):
        return []
    faults: list[Fault] = []
    if len(panels) > MAX_PANELS[kind]:
        faults.append(Fault("limit", f"{kind}: at most {MAX_PANELS[kind]} entries"))
    if len(held_ids(kind, data)) > MAX_HELD:
        faults.append(Fault("limit", f"{kind}: at most {MAX_HELD} held blocks"))
    return faults


def validate_tabs(data: dict[str, object]) -> list[Fault]:
    return _validate(data, "tabs")


def validate_columns(data: dict[str, object]) -> list[Fault]:
    return _validate(data, "columns")


def _panel_properties(kind: str, label_needed: bool) -> tuple[PropertySpec, ...]:
    panel = (
        PropertySpec("label", "string", required=label_needed, nonempty=True),
        PropertySpec("blocks", "list", required=True, nonempty=True, items="id"),
    )
    return (
        PropertySpec(
            HOLD_KEYS[kind],
            "list",
            required=True,
            nonempty=True,
            items="object",
            fields=panel,
        ),
    )


def held_ids(kind: str, props: dict[str, object]) -> list[str]:
    """Every held id of one container's props, in panel order (valid shapes only)."""
    panels = props.get(HOLD_KEYS[kind])
    if not isinstance(panels, list):
        return []
    out: list[str] = []
    for panel in panels:
        held = panel.get("blocks") if isinstance(panel, dict) else None
        out += [h for h in held if isinstance(h, str)] if isinstance(held, list) else []
    return out


# (line, component, id, props) of each statement, in document order.
Statements = Sequence[tuple[int, str, str, dict[str, object]]]


def _chain_back(start: str, target: str, holds: dict[str, list[str]]) -> bool:
    """Whether `start` holds `target`, directly or through held containers."""
    seen: set[str] = set()
    todo = [start]
    while todo:
        node = todo.pop()
        if node == target:
            return True
        if node not in seen:
            seen.add(node)
            todo += holds.get(node, [])
    return False


def _held_fault(
    kind: str, own: str, held: str, component: str | None, inputs: frozenset[str]
) -> Fault | None:
    if component is None:
        return Fault(
            "container-unknown",
            f"{kind} '{own}' holds '{held}', which names no statement of this page",
        )
    if component == "include":
        return Fault(
            "container-include",
            f"{kind} '{own}' cannot hold include '{held}'",
        )
    if kind == "tabs" and component in inputs:
        return Fault(
            "container-input",
            f"tabs '{own}' cannot hold input '{held}'; "
            "tabs hide panels but inputs must stay visible (use columns)",
        )
    return None


def _nest_fault(kind: str, own: str, held: str, holds: dict[str, list[str]]) -> Fault:
    rule = "container-cycle" if _chain_back(held, own, holds) else "container-nested"
    message = f"{kind} '{own}' cannot hold container '{held}'; containers do not nest"
    return Fault(rule, message)


def held_faults(
    statements: Statements, inputs: frozenset[str]
) -> Iterator[tuple[int, str, str, Fault]]:
    """`(line, container id, held id, fault)` for each held id the page rules refuse.

    `inputs` names the components a tab may not hold.
    """
    components = {ident: component for _, component, ident, _ in statements}
    holds = {i: held_ids(c, p) for _, c, i, p in statements if c in CONTAINERS}
    taken: dict[str, str] = {}
    for line, kind, own, _ in statements:
        for held in holds.get(own, []):
            found = components.get(held)
            fault = _held_fault(kind, own, held, found, inputs)
            if found in CONTAINERS:
                fault = _nest_fault(kind, own, held, holds)
            elif held in taken:
                fault = Fault(
                    "container-double", f"'{held}' is already held by '{taken[held]}'"
                )
            taken.setdefault(held, own)
            if fault:
                yield line, own, held, fault


def container_errors(
    statements: Statements, inputs: frozenset[str]
) -> list[tuple[int, str, str]]:
    """`(line, rule, message)` for the ids containers hold across the whole page."""
    return [
        (line, fault.rule, fault.message)
        for line, _, _, fault in held_faults(statements, inputs)
    ]


TABS = BlockSpec(
    "tabs",
    "Tabs that show other blocks of the page, one panel at a time",
    (
        "tab: 1 to 12; label is the tab text, blocks the ids of other statements to",
        "  show in that panel (up to 200 ids in all).",
        "A held block is shown once, in its panel, with its own menu. A block is",
        "held by one container only, and containers do not nest. Input blocks",
        "(choice, form, comment, ranking, slider, decision) cannot be held in tabs.",
        "Without script and in print every panel shows, stacked under its label.",
    ),
    r"""tabs = tabs(
  tab: [
    {"label": "Code", "blocks": ["code"]},
    {"label": "Checks", "blocks": ["checklist"]},
  ],
)
""",
    validate_tabs,
    properties=_panel_properties("tabs", label_needed=True),
)

COLUMNS = BlockSpec(
    "columns",
    "Side-by-side columns that show other blocks of the page",
    (
        "col: 1 to 4; label is text above a column, blocks the ids of other",
        "  statements to show there.",
        "Columns stack below 44rem. A held block is shown once, with its own menu;",
        "a block is held by one container only and containers do not nest.",
    ),
    r"""columns = columns(
  col: [
    {"label": "Before", "blocks": ["callout"]},
    {"label": "After", "blocks": ["code"]},
  ],
)
""",
    validate_columns,
    properties=_panel_properties("columns", label_needed=False),
)
