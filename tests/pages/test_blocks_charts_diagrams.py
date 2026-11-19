"""Chart, diagram and image blocks render client-side: registration, props, hosts, copy.

The component DOM is checked in `pages/tests/components/charts_diagrams.test.js` against
`components/fixtures/<block>.json`, the HTML the former Python renderers produced.
These tests keep the Python side of that contract: the fixture inputs still produce
the recorded props, the blocks render as hosts with their source as the no-script
fallback, every host carries its copy text, and a container copies a held client block.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
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
