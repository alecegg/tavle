"""Block type for a decision matrix: matrix (options as columns, criteria as rows)."""

from ..blocks.rules import (
    Fault,
    duplicates,
    tables,
)
from ..blocks.spec import BlockSpec, PropertySpec

SCALES = {
    "verdict": {"yes": 2, "partial": 1, "no": 0},
    "level": {"high": 2, "medium": 1, "low": 0},
}
MAX_OPTIONS = 12
MAX_CRITERIA = 200
FIRST_COLUMN = "Criterion"


def rating_scale(cell: object) -> str | None:
    """The scale a cell's rating belongs to, or None when the cell is plain text."""
    word = cell.strip().lower() if isinstance(cell, str) else ""
    return next((name for name, words in SCALES.items() if word in words), None)


def _unique_faults(data: dict[str, object], key: str, field: str) -> list[Fault]:
    names = [str(e.get(field)) for e in tables(data, key) if field in e]
    return [
        Fault("duplicate", f"matrix.{key}: {field} '{name}' is repeated")
        for name in duplicates(names)
    ]


def _option_faults(data: dict[str, object]) -> list[Fault]:
    faults: list[Fault] = []
    options = tables(data, "options")
    if len(options) > MAX_OPTIONS:
        faults.append(Fault("limit", f"matrix: at most {MAX_OPTIONS} options"))
    if any(o.get("label") == FIRST_COLUMN for o in options):
        faults.append(
            Fault("duplicate", f"matrix.options: label '{FIRST_COLUMN}' is reserved")
        )
    return (
        faults
        + _unique_faults(data, "options", "id")
        + _unique_faults(data, "options", "label")
    )


def _weight_faults(data: dict[str, object]) -> list[Fault]:
    faults: list[Fault] = []
    for n, entry in enumerate(tables(data, "criteria"), 1):
        weight = entry.get("weight")
        if "weight" in entry and (
            not isinstance(weight, int)
            or isinstance(weight, bool)
            or not 1 <= weight <= 5
        ):
            faults.append(
                Fault(
                    "type",
                    f"matrix.criteria[{n}].weight must be a whole number from 1 to 5",
                )
            )
    return faults


def _criteria_faults(data: dict[str, object]) -> list[Fault]:
    faults = _weight_faults(data)
    if len(tables(data, "criteria")) > MAX_CRITERIA:
        faults.append(Fault("limit", f"matrix: at most {MAX_CRITERIA} criteria"))
    return faults + _unique_faults(data, "criteria", "id")


def _row_faults(
    n: int, row: list, criteria: list[dict[str, object]], width: int
) -> list[Fault]:
    name = criteria[n - 1].get("label") if n <= len(criteria) else None
    where = f"matrix.cells[{n}]" + (f" ('{name}')" if isinstance(name, str) else "")
    faults: list[Fault] = []
    if len(row) != width:
        faults.append(
            Fault(
                "cells-width",
                f"{where} has {len(row)} cells, expected {width} (one per option)",
            )
        )
    if not all(isinstance(c, str) for c in row):
        faults.append(Fault("type", f"{where}: each cell must be a string"))
    return faults


def _grid_faults(data: dict[str, object]) -> list[Fault]:
    cells = data["cells"]
    options = tables(data, "options")
    criteria = tables(data, "criteria")
    if not isinstance(cells, list) or not all(isinstance(r, list) for r in cells):
        return [
            Fault("type", "matrix: 'cells' must be a list of rows, one per criterion")
        ]
    faults: list[Fault] = []
    if len(cells) != len(criteria):
        faults.append(
            Fault(
                "cells-rows",
                f"matrix.cells has {len(cells)} rows, "
                f"expected {len(criteria)} (one per criterion)",
            )
        )
    for n, row in enumerate(cells, 1):
        faults += _row_faults(n, row, criteria, len(options))
    scales = {rating_scale(c) for row in cells for c in row} - {None}
    if len(scales) > 1:
        faults.append(
            Fault(
                "scale",
                "matrix.cells mix the yes/partial/no and high/medium/low scales",
            )
        )
    return faults


def _recommended_faults(data: dict[str, object]) -> list[Fault]:
    if "recommended" not in data:
        return []
    value = data["recommended"]
    if not isinstance(value, str) or not value.strip():
        return []  # the properties report a wrong type or a blank value
    ids = [o.get("id") for o in tables(data, "options")]
    if value in ids:
        return []
    return [Fault("recommended", f"matrix.recommended: no option with id '{value}'")]


def _entries_shaped(data: dict[str, object], key: str) -> bool:
    """True when every entry is a table whose id and label are non-blank strings."""
    entries = data.get(key)
    if not isinstance(entries, list) or not entries:
        return False
    return all(
        isinstance(e, dict)
        and all(isinstance(e.get(f), str) and e[f].strip() for f in ("id", "label"))
        for e in entries
    )


def validate_matrix(data: dict[str, object]) -> list[Fault]:
    faults = _option_faults(data) + _criteria_faults(data)
    # The grid is checked against well-formed options and criteria only, so a
    # malformed entry gives its own property fault and no grid faults besides.
    shaped = _entries_shaped(data, "options") and _entries_shaped(data, "criteria")
    if shaped and "cells" in data and not faults:
        faults += _grid_faults(data)
    return faults + _recommended_faults(data)


MATRIX = BlockSpec(
    "matrix",
    "A decision matrix: options as columns, criteria as rows, ratings in cells",
    (
        "title: heading.",
        "options: 1 to 12; label is the column name.",
        "criteria: up to 200; weight is 1 to 5.",
        "cells: one row per criterion, one cell per option. A cell is yes, partial",
        "  or no, or high, medium or low (one scale per matrix), or plain text;",
        "  empty reads 'Not rated'.",
        "recommended: an option id; its column gets a Recommended badge.",
        "Any weight adds a 'Weighted total' row (unweighted criteria count 1; yes",
        "or high scores 2, partial or medium 1, no or low 0; text scores 0).",
        "Rows stack on phones; sort and filter come from the table block.",
    ),
    r"""matrix = matrix(
  title: "Queue options",
  options: [
    {"id": "db", "label": "SQLite", "note": "One writer is enough."},
    {"id": "mq", "label": "Broker"},
  ],
  criteria: [
    {"id": "ops", "label": "Easy to run", "weight": 3},
    {"id": "scale", "label": "Scales out", "weight": 1},
  ],
  cells: [["yes", "no"], ["no", "yes"]],
  recommended: "db",
)
""",
    validate_matrix,
    properties=(
        PropertySpec("title", "string", nonempty=True),
        PropertySpec(
            "options",
            "list",
            required=True,
            items="object",
            nonempty=True,
            fields=(
                PropertySpec("id", "string", required=True, nonempty=True),
                PropertySpec("label", "string", required=True, nonempty=True),
                PropertySpec("note", "string", nonempty=True),
            ),
        ),
        PropertySpec(
            "criteria",
            "list",
            required=True,
            items="object",
            nonempty=True,
            fields=(
                PropertySpec("id", "string", required=True, nonempty=True),
                PropertySpec("label", "string", required=True, nonempty=True),
                PropertySpec("weight", "any"),
            ),
        ),
        PropertySpec("cells", "any", required=True),
        PropertySpec("recommended", "string", nonempty=True),
    ),
)
