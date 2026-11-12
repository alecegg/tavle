"""Block type for tabular data: table."""

from varde_pages.blocks.rules import (
    Fault,
    check_keys,
    duplicates,
    is_number,
    list_of,
    str_field,
    str_map,
    tables,
    tables_fault,
    type_name,
)
from varde_pages.blocks.spec import BlockSpec

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


def _bool_faults(data: dict[str, object]) -> list[Fault]:
    return [
        Fault("type", f"table.{key} must be a boolean, got {type_name(data[key])}")
        for key in ("sticky_column", "stack")
        if key in data and not isinstance(data[key], bool)
    ]


def _type_faults(data: dict[str, object], columns: list[object]) -> list[Fault]:
    if "types" not in data:
        return []
    faults = str_map(data["types"], "table.types")
    kinds = data["types"]
    if not isinstance(kinds, dict):
        return faults
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


def _group_entry_faults(group: dict[str, object], n: int) -> tuple[list[Fault], bool]:
    """Faults of one row group, and whether its row count is unusable."""
    where = f"table.groups[{n}]"
    faults = check_keys(group, {"label", "rows"}, set(), where)
    faults += str_field(group, "label", where)
    count = group.get("rows")
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        faults.append(Fault("type", f"{where}.rows must be a positive integer"))
        return faults, True
    return faults, False


def _group_faults(data: dict[str, object], row_count: int) -> list[Fault]:
    if "groups" not in data:
        return []
    faults = tables_fault(data, "groups", "table")
    groups = tables(data, "groups", "table")
    for n, group in enumerate(groups, 1):
        found, unusable = _group_entry_faults(group, n)
        faults += found
        if unusable:
            return faults
    if groups and not faults:
        total = sum(g["rows"] for g in groups if isinstance(g["rows"], int))
        if total != row_count:
            faults.append(
                Fault(
                    "group-rows",
                    f"table.groups cover {total} rows, the table has {row_count}",
                )
            )
    return faults


def _column_faults(data: dict[str, object], columns: object) -> list[Fault]:
    faults = list_of(columns, "table.columns") if "columns" in data else []
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
    optional = {"caption", "footnote", "types", "sticky_column", "stack", "groups"}
    faults = check_keys(data, {"columns", "rows"}, optional, "table")
    faults += str_field(data, "caption", "table")
    faults += str_field(data, "footnote", "table")
    faults += _bool_faults(data)
    columns = data.get("columns")
    faults += _column_faults(data, columns)
    rows = data.get("rows")
    if "rows" in data:
        faults += list_of(rows, "table.rows", list)
    if isinstance(rows, list) and isinstance(columns, list):
        faults += _body_faults(data, columns, rows)
    return faults


TABLE = BlockSpec(
    "table",
    "A data table: sticky header, sort, filter, typed columns, row groups",
    (
        "caption        optional text",
        "columns        list of unique column names",
        "rows           list of rows; each row has one cell per column",
        "types          optional table: column name to text, number, status, bar, link",
        "                number and bar cells are numbers; a link cell is a URL",
        "                or a [label, url] pair",
        "footnote       optional text under the table",
        "sticky_column  optional boolean: keep the first column in view",
        "stack          optional boolean: on phones show each row as labelled pairs",
        "groups         optional list of {label, rows}: row groups with a header",
    ),
    r"""table = table(
  caption: "Plan options",
  columns: ["option", "cost", "risk"],
  rows: [["queue", "low", "slow"], ["cache", "medium", "stale"]],
)
""",
    validate_table,
)
