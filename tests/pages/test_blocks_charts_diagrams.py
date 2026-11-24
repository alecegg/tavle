"""Chart, diagram and image blocks render client-side: registration, props, hosts, copy.

The component DOM is checked in `tests/pages/components/charts_diagrams.test.js` against
`components/fixtures/<block>.json`, the HTML the former Python renderers produced.
These tests keep the Python side of that contract: the fixture inputs still produce
the recorded props, the blocks render as hosts with their source as the no-script
fallback, every host carries its copy text, and a container copies a held client block.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

from varde.base.ui_lines.parse import parse_lines
from varde.pages.blocks import COMPONENT_SPECS, check_props
from varde.pages.blocks_render.charts import chart_props
from varde.pages.blocks_render.diagrams import diagram_props
from varde.pages.blocks_render.flow import flow_props
from varde.pages.blocks_render.image import image_props
from varde.pages.blocks_render.registry import COMPONENTS
from varde.pages.blocks_render.screen_flow import screen_flow_props
from varde.pages.blocks_render.screens import ui_states_props, wireframe_props
from varde.pages.blocks_render.sequence import sequence_props
from varde.pages.blocks_render.state import state_props
from varde.pages.components import component_bundle, mount_block
from varde.pages.media import Media
from varde.pages.render import render_page

FIXTURES = Path(__file__).parent / "components" / "fixtures"
PROPS = {
    "chart": chart_props,
    "diagram": diagram_props,
    "flow": flow_props,
    "state": state_props,
    "sequence": sequence_props,
    "wireframe": wireframe_props,
    "ui-states": ui_states_props,
    "screen-flow": screen_flow_props,
}
BLOCKS = (*PROPS, "image")


def _fixture(name: str) -> list[dict[str, Any]]:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def _props_of(block: str, case: dict[str, Any]) -> dict[str, object]:
    if block != "image":
        return PROPS[block](case["input"])
    media = None if case["media"] is None else Media(**case["media"])
    return image_props(case["input"], media, export=case["export"])


@pytest.mark.parametrize("block", BLOCKS)
def test_block_is_client_side_and_bundled(block: str) -> None:
    assert COMPONENTS[block].props is not None
    assert f'components["{block}"]' in component_bundle()


@pytest.mark.parametrize("block", BLOCKS)
def test_fixture_inputs_still_produce_the_recorded_props(block: str) -> None:
    cases = _fixture(block)
    assert len(cases) >= 5 or block == "image"
    for case in cases:
        assert _props_of(block, case) == case["props"], case["name"]
        assert isinstance(case["html"], str) and case["html"]


def _doc() -> str:
    return (
        "```ui\n"
        'c = chart(kind: "bar", title: "T <b>", unit: "ms", labels: ["a"],'
        ' series: [{"name": "s", "values": [1]}])\n'
        'd = diagram(kind: "graph",'
        ' nodes: [{"id": "a", "label": "A"}, {"id": "b", "label": "B"}],'
        ' edges: [{"from": "a", "to": "b"}])\n'
        'f = flow(step: [{"id": "a", "text": "A"}])\n'
        'e = state(desc: "d", states: [{"id": "a", "label": "A", "kind": "initial"}])\n'
        's = sequence(desc: "d", actors: [{"id": "a", "label": "A"}],'
        ' steps: [{"from": "a", "to": "a", "text": "t"}])\n'
        'w = wireframe(title: "W", grid: ["AB"], regions: {"A": "a", "B": "b"})\n'
        'u = ui-states(screen: "S", empty: {"shows": "x"}, loading: {"na": "y"},'
        ' error: {"na": "z"})\n'
        'g = screen-flow(desc: "d", screens: [{"id": "a", "title": "A",'
        ' "grid": ["A"], "regions": {"A": "a"}}, {"id": "b", "title": "B",'
        ' "grid": ["A"], "regions": {"A": "a"}}], steps: [{"from": "a", "to": "b"}])\n'
        'i = image(src: "a.png", alt: "A")\n'
        "```\n"
    )


def test_statements_render_hosts_with_their_source_as_fallback() -> None:
    body = render_page(_doc(), "t.md").body
    for block in BLOCKS:
        assert f'data-mithril="{block}"' in body, block
    assert "vb-error" not in body and body.count("<noscript><pre") == len(BLOCKS)
    assert "T &lt;b&gt;" in body and "<b>" not in body


def test_every_host_carries_its_copy_text() -> None:
    body = render_page(_doc(), "t.md").body
    hosts = [part for part in body.split("<div ") if 'data-mithril="' in part]
    assert len(hosts) == len(BLOCKS)
    assert all(' data-copy="' in host.split(">", 1)[0] for host in hosts)


def test_a_host_without_copy_text_copies_its_source() -> None:
    host = mount_block("chart", {}, "c = chart(<x>)", "c")
    assert 'data-copy="c = chart(&lt;x&gt;)"' in host


def test_a_container_copies_a_held_client_block_from_its_host() -> None:
    doc = (
        "```ui id=c\n"
        'c = chart(kind: "bar", title: "T", labels: ["a"],'
        ' series: [{"name": "s", "values": [1]}])\n'
        "```\n\n"
        '```ui id=t\nt = tabs(tab: [{"label": "One", "blocks": ["c"]}])\n```\n'
    )
    body = render_page(doc, "t.md").body
    assert "vb-error" not in body
    assert 'data-copy="One\n\nlabel,s\na,1"' in body  # the tab, then the chart's copy


_CHART = {
    "kind": "bar",
    "labels": ["a", "b"],
    "series": [{"name": "s", "values": [1, 2]}],
}
_CHART_NOTE = {"x": "a", "label": "n"}


def test_chart_example_passes_and_a_shape_mistake_gets_one_fault() -> None:
    assert check_props("chart", _CHART, 1) == []
    cases: list[tuple[dict[str, object], str]] = [
        ({**_CHART, "unexpected": 1}, "unexpected"),
        ({"kind": "bar", "labels": ["a"]}, "series"),
        ({**_CHART, "decimals": "2"}, "decimals"),
        ({**_CHART, "decimals": 9}, "decimals"),
        ({**_CHART, "kind": "pie"}, "kind"),
        ({**_CHART, "series": [{"name": "s", "values": [1, "x"]}]}, "values[1]"),
        ({**_CHART, "series": [{"values": [1, 2]}]}, "series[0].name"),
        (
            {
                **_CHART,
                "kind": "combo",
                "series": [{"name": "s", "values": [1, 2], "axis": "up"}],
            },
            "axis",
        ),
    ]
    for props, field in cases:
        errors = check_props("chart", props, 1)
        assert len(errors) == 1, props
        assert field in errors[0].message


def test_chart_note_metadata_and_rules_check_a_note_once() -> None:
    assert check_props("chart", {**_CHART, "notes": [_CHART_NOTE]}, 1) == []
    cases: list[tuple[list[object], str]] = [
        ([{**_CHART_NOTE, "unexpected": 1}], "notes[0].unexpected"),
        ([{"x": "a"}], "notes[0].label"),
        ([{**_CHART_NOTE, "label": 3}], "notes[0].label"),
        ([{**_CHART_NOTE, "tone": "loud"}], "notes[0].tone"),
        ([{"label": "n", "from": "a"}], "notes[1]: missing required key 'to'"),
        ([{**_CHART_NOTE, "x": "nope"}], "notes[1].x"),
        ([], "'notes' must not be empty"),
        (["x"], "notes[0]"),
    ]
    for notes, field in cases:
        errors = check_props("chart", {**_CHART, "notes": notes}, 1)
        assert len(errors) == 1, notes
        assert field in errors[0].message


_DIAGRAM = {"kind": "graph", "nodes": [{"id": "a", "label": "A"}]}
_FLOW = {"step": [{"id": "a", "text": "A", "next": ["a"]}]}
_STATE = {"desc": "d", "states": [{"id": "a", "label": "A", "kind": "initial"}]}
_SEQUENCE = {
    "desc": "d",
    "actors": [{"id": "a", "label": "A"}],
    "steps": [{"from": "a", "to": "a", "text": "t"}],
}
_FAMILY: dict[str, Mapping[str, object]] = {
    "diagram": _DIAGRAM,
    "flow": _FLOW,
    "state": _STATE,
    "sequence": _SEQUENCE,
}


@pytest.mark.parametrize("block", _FAMILY)
def test_family_example_passes(block: str) -> None:
    result = parse_lines(COMPONENT_SPECS[block].example)
    assert result.errors == []
    assert check_props(block, result.statements[0].props, 1) == []
    assert check_props(block, dict(_FAMILY[block]), 1) == []


_FAMILY_FAULTS: list[tuple[str, dict[str, object], str]] = [
    ("diagram", {**_DIAGRAM, "mermaid": "x"}, "unknown key 'mermaid'"),
    ("diagram", {"kind": "graph"}, "missing required key 'nodes'"),
    ("diagram", {**_DIAGRAM, "direction": 3}, "'direction' must be string"),
    ("diagram", {**_DIAGRAM, "kind": "ring"}, "'kind' must be one of"),
    (
        "diagram",
        {**_DIAGRAM, "nodes": [{"id": "a", "label": "A", "size": 1}]},
        "unknown key 'nodes[0].size'",
    ),
    (
        "diagram",
        {**_DIAGRAM, "edges": [{"from": "a"}]},
        "missing required key 'edges[0].to'",
    ),
    (
        "diagram",
        {**_DIAGRAM, "edges": [{"from": "a", "to": 2}]},
        "'edges[0].to' must be string",
    ),
    ("diagram", {**_DIAGRAM, "nodes": []}, "'nodes' must not be empty"),
    ("flow", {**_FLOW, "extra": 1}, "unknown key 'extra'"),
    ("flow", {"title": "t"}, "missing required key 'step'"),
    ("flow", {"step": "a"}, "'step' must be list"),
    ("flow", {"step": [{"id": "a"}]}, "missing required key 'step[0].text'"),
    ("flow", {"step": [{"id": "a", "text": "A", "next": "b"}]}, "'step[0].next'"),
    ("flow", {"step": []}, "'step' must not be empty"),
    ("state", {**_STATE, "extra": 1}, "unknown key 'extra'"),
    ("state", {"states": _STATE["states"]}, "missing required key 'desc'"),
    ("state", {**_STATE, "title": 1}, "'title' must be string"),
    (
        "state",
        {
            **_STATE,
            "states": [*_STATE["states"], {"id": "b", "label": "B", "kind": "loud"}],
        },
        "'states[1].kind' must be one of",
    ),
    (
        "state",
        {**_STATE, "transitions": [{"from": "a"}]},
        "missing required key 'transitions[0].to'",
    ),
    ("state", {**_STATE, "states": []}, "'states' must not be empty"),
    ("sequence", {**_SEQUENCE, "extra": 1}, "unknown key 'extra'"),
    ("sequence", {**_SEQUENCE, "desc": None}, "'desc' must be string"),
    (
        "sequence",
        {"desc": "d", "actors": _SEQUENCE["actors"]},
        "missing required key 'steps'",
    ),
    (
        "sequence",
        {**_SEQUENCE, "steps": [{"from": "a", "to": "a", "text": "t", "kind": "x"}]},
        "'steps[0].kind' must be one of",
    ),
    (
        "sequence",
        {**_SEQUENCE, "steps": [{"from": "a", "to": "a", "text": 1}]},
        "'steps[0].text' must be string",
    ),
    ("sequence", {**_SEQUENCE, "steps": []}, "'steps' must not be empty"),
]


@pytest.mark.parametrize(("block", "props", "message"), _FAMILY_FAULTS)
def test_family_shape_mistake_gets_one_fault_naming_the_field(
    block: str, props: dict[str, object], message: str
) -> None:
    errors = check_props(block, props, 1)
    assert len(errors) == 1, errors
    assert message in errors[0].message
