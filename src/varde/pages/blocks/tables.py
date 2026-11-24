"""Block type for tabular data: table."""

from varde.pages.blocks.rules import Fault, duplicates, is_number, str_map, tables
from varde.pages.blocks.spec import BlockSpec, PropertySpec

COLUMN_TYPES = ("text", "number", "status", "bar", "link")
NUMERIC_TYPES = ("number", "bar")


def numeric(cell: object) -> bool:
    if is_number(cell):
        return True
    if not isinstance(cell, str):
        return False
    try:
        float(cell)
    except ValueError:
        return False
    return True


def _type_faults(data: dict[str, object], columns: list[object]) -> list[Fault]:
    kinds = data.get("types")
    if not isinstance(kinds, dict):
        return []  # absent, or a type fault the properties already report
    faults = str_map(kinds, "table.types")
    for name, kind in kinds.items():
        if name not in columns:
            faults.append(Fault("types-column", f"table.types: no column '{name}'"))
        if isinstance(kind, str) and kind not in COLUMN_TYPES:
            options = ", ".join(COLUMN_TYPES)
            faults.append(
                Fault("types-kind", f"table.types.{name} must be one of {options}")
            )
    return faults


def _typed_cell_faults(kind: object, cell: object, where: str) -> list[Fault]:
    faults: list[Fault] = []
    if kind in NUMERIC_TYPES and not numeric(cell):
        faults.append(Fault("cell-number", f"{where} must be a number"))
    if kind == "link" and not _link_cell(cell):
        text = "must be a URL or a [label, url] pair of strings"
        faults.append(Fault("cell-link", f"{where} {text}"))
    return faults


def _cell_faults(
    columns: list[object], kinds: dict[str, object], rows: list[object]
) -> list[Fault]:
    faults: list[Fault] = []
    for n, row in enumerate(rows, 1):
        if not isinstance(row, list) or len(row) != len(columns):
            continue
        for name, cell in zip(columns, row, strict=True):
            kind = kinds.get(name) if isinstance(name, str) else None
            faults += _typed_cell_faults(kind, cell, f"table.rows[{n}] '{name}'")
    return faults


def _link_cell(cell: object) -> bool:
    if isinstance(cell, str):
        return True
    return (
        isinstance(cell, list)
        and len(cell) == 2
        and all(isinstance(part, str) for part in cell)
    )


def _row_count(group: dict[str, object]) -> int | None:
    count = group.get("rows")
    return count if isinstance(count, int) and not isinstance(count, bool) else None


def _group_faults(data: dict[str, object], row_count: int) -> list[Fault]:
    counts = [_row_count(g) for g in tables(data, "groups", "table")]
    faults = [
        Fault("type", f"table.groups[{n}].rows must be a positive integer")
        for n, count in enumerate(counts, 1)
        if count is not None and count < 1
    ]
    whole = [count for count in counts if count is not None]
    if faults or not counts or len(whole) < len(counts) or sum(whole) == row_count:
        return faults
    message = f"table.groups cover {sum(whole)} rows, the table has {row_count}"
    return [Fault("group-rows", message)]


def _column_faults(data: dict[str, object], columns: object) -> list[Fault]:
    faults: list[Fault] = []
    if isinstance(columns, list):
        faults += [
            Fault("column-duplicate", f"table: column '{c}' is repeated")
            for c in duplicates([c for c in columns if isinstance(c, str)])
        ]
        faults += _type_faults(data, columns)
    return faults


def _body_faults(data: dict[str, object], columns: list, rows: list) -> list[Fault]:
    faults = [
        Fault(
            "row-width",
            f"table.rows[{n}] has {len(r)} cells, expected {len(columns)}",
        )
        for n, r in enumerate(rows, 1)
        if isinstance(r, list) and len(r) != len(columns)
    ]
    types = data.get("types")
    kinds: dict[str, object] = types if isinstance(types, dict) else {}
    faults += _cell_faults(columns, kinds, rows)
    return faults + _group_faults(data, len(rows))


def validate_table(data: dict[str, object]) -> list[Fault]:
    columns = data.get("columns")
    faults = _column_faults(data, columns)
    rows = data.get("rows")
    if not isinstance(rows, list) or not isinstance(columns, list) or not columns:
        return faults
    if all(isinstance(row, list) for row in rows):
        faults += _body_faults(data, columns, rows)
    return faults


TABLE = BlockSpec(
    "table",
    "A data table: sticky header, sort, filter, typed columns, row groups",
    (
        "caption, footnote: text above and under the table.",
        "columns: unique column names.",
        "rows: each row has one cell per column.",
        "types: maps a column name to text, number, status, bar or link; number and",
        "  bar cells are numbers; a link cell is a URL or a [label, url] pair.",
        "sticky_column: keeps the first column in view.",
        "stack: on phones shows each row as labelled pairs.",
        "groups: row groups, each with a label and its rows.",
    ),
    r"""table = table(
  caption: "Plan options",
  columns: ["option", "cost", "risk"],
  rows: [["queue", "low", "slow"], ["cache", "medium", "stale"]],
)
""",
    validate_table,
    properties=(
        PropertySpec("caption", "string", nonempty=True),
        PropertySpec("columns", "list", required=True, nonempty=True, items="string"),
        # Each row is a list; `items="list"` would check the cells as lists too.
        PropertySpec("rows", "list", required=True, nonempty=True, items="list"),
        PropertySpec("types", "object"),  # column names are the keys
        PropertySpec("footnote", "string", nonempty=True),
        PropertySpec("sticky_column", "boolean"),
        PropertySpec("stack", "boolean"),
        PropertySpec(
            "groups",
            "list",
            nonempty=True,
            items="object",
            fields=(
                PropertySpec("label", "string", required=True, nonempty=True),
                PropertySpec("rows", "integer", required=True),
            ),
        ),
    ),
)
