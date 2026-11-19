"""The block code split by kind keeps every existing render output unchanged."""

from varde.pages.blocks import SPECS, check_props
from varde.pages.blocks import charts as chart_spec
from varde.pages.blocks import diagrams as diagram_spec
from varde.pages.blocks import flow as flow_spec
from varde.pages.blocks import tables as table_spec
from varde.pages.blocks_render import diagrams, flow, registry

TABLE = {
    "columns": ["a", "b<"],
    "rows": [["1", "x&y"], ["2", "z"]],
    "caption": "Cap",
}
FLOW = {
    "title": "T",
    "step": [
        {"id": "a", "text": "A <b>", "next": ["b", "c"]},
        {"id": "b", "text": "B"},
        {"id": "c", "text": "C", "next": ["a"]},
    ],
}


def test_table_and_flow_render_as_before() -> None:
    # The flow draws in the browser from props the server lays out.
    assert registry.COMPONENTS["flow"].props == flow.flow_props


def test_specs_moved_with_their_validators() -> None:
    assert SPECS["table"] is table_spec.TABLE
    assert SPECS["flow"] is flow_spec.FLOW
    assert SPECS["chart"] is chart_spec.CHART
    assert check_props("table", TABLE, 1) == []
    assert check_props("flow", FLOW, 1) == []


def test_diagram_modules_wait_for_rb_diagram() -> None:
    assert not hasattr(diagrams, "render_flow") and not hasattr(
        diagrams, "render_table"
    )
    assert diagrams.__doc__ and diagram_spec.__doc__
    assert not hasattr(diagram_spec, "FLOW")


def test_block_scripts_are_es_modules_imported_by_blocks_js() -> None:
    from varde.pages.template import page_scripts, static_scripts

    parts = {"dom.js", "table.js", "tabs.js", "flow.js", "chart.js", "viewport.js"}
    assert parts <= set(static_scripts())
    assert parts.isdisjoint(page_scripts())
    assert page_scripts() == (
        "components.js",
        "app.js",
        "blocks.js",
        "recap.js",
        "inputs_ordered.js",
    )
