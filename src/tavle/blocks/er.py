"""Checks for the data-model `layout` prop: `list` (default) or `graph`."""

from ..blocks.rules import Fault, tables

LAYOUTS = ("list", "graph")
MAX_GRAPH_ENTITIES = 30

LAYOUT_NOTE = (
    "layout: list (default) or graph; graph draws the relations as lines",
    f"  between entity boxes, up to {MAX_GRAPH_ENTITIES} entities.",
)


def layout_faults(data: dict[str, object]) -> list[Fault]:
    # The properties check that layout is one of LAYOUTS.
    count = len(tables(data, "entity"))
    if data.get("layout") == "graph" and count > MAX_GRAPH_ENTITIES:
        return [
            Fault(
                "graph-size",
                f"data-model: layout graph draws at most {MAX_GRAPH_ENTITIES} "
                f"entities, this has {count}; use layout list",
            )
        ]
    return []
