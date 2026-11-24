"""Checks for the data-model `layout` prop: `list` (default) or `graph`."""

from varde.pages.blocks.rules import Fault, tables

LAYOUTS = ("list", "graph")
MAX_GRAPH_ENTITIES = 30

LAYOUT_NOTE = (
    "layout  optional: list (default) or graph; graph draws the relations as",
    f"        lines between entity boxes, up to {MAX_GRAPH_ENTITIES} entities",
)


def layout_faults(data: dict[str, object]) -> list[Fault]:
    # The properties check that layout is one of LAYOUTS.
    count = len(tables(data, "entity", "data-model"))
    if data.get("layout") == "graph" and count > MAX_GRAPH_ENTITIES:
        return [
            Fault(
                "graph-size",
                f"data-model: layout graph draws at most {MAX_GRAPH_ENTITIES} "
                f"entities, this has {count}; use layout list",
            )
        ]
    return []
