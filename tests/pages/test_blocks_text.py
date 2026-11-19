"""Text and reference blocks render client-side: registration, hosts, fixtures.

The component DOM is checked in `pages/tests/components/blocks_text.test.js`
against `components/fixtures/<block>.json`, the HTML the former Python renderers
produced. These tests keep the Python side of that contract: the fixtures hold
valid props, the blocks render as hosts, and the facts the components copy from
Python still match their owners.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from varde.pages.blocks import check_props
from varde.pages.blocks.decision import OPTIONS
from varde.pages.blocks.option_matrix import FIRST_COLUMN, SCALES
from varde.pages.blocks_render.decision import LABELS, VERDICT_OF
from varde.pages.blocks_render.registry import COMPONENTS
from varde.pages.components import component_bundle
from varde.pages.render import classify_url, render_page

TESTS = Path(__file__).parent
FIXTURES = TESTS / "components" / "fixtures"
STATIC = TESTS.parent / "src" / "varde.pages" / "static" / "components"
TEXT_BLOCKS = (
    "checklist",
    "decision",
    "matrix",
    "recap",
    "risks",
    "stats",
    "table",
    "timeline",
)


def _fixture(name: str) -> list[dict[str, object]]:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", TEXT_BLOCKS)
def test_block_is_client_side_and_bundled(name: str) -> None:
    assert name in COMPONENTS
    assert f'components["{name}"]' in component_bundle()


@pytest.mark.parametrize("name", TEXT_BLOCKS)
def test_fixture_props_are_valid_and_the_html_is_recorded(name: str) -> None:
    cases = _fixture(name)
    assert len(cases) >= 5
    for case in cases:
        props = case["props"]
        assert isinstance(props, dict)
        assert check_props(name, props, 1) == [], case["name"]
        assert isinstance(case["html"], str) and case["html"].startswith("<")


@pytest.mark.parametrize("name", TEXT_BLOCKS)
def test_statement_renders_a_host_with_its_source_as_fallback(name: str) -> None:
    props = _fixture(name)[0]["props"]
    assert isinstance(props, dict)
    args = ", ".join(f"{key}: {json.dumps(value)}" for key, value in props.items())
    statement = f"b1 = {name}({args})"
    body = render_page(f"```ui\n{statement}\n```\n", "t.md").body
    assert f'data-mithril="{name}"' in body
    assert "<noscript><pre" in body and "vb-error" not in body


def test_classify_url_fixture_matches_the_python_classifier() -> None:
    for case in _fixture("classify-url"):
        assert classify_url(str(case["url"])) == case["kind"], case["url"]


def _js_constant(file: str, name: str) -> object:
    """The value of `const NAME = <object or array literal>;` in a component file."""
    source = (STATIC / file).read_text(encoding="utf-8")
    found = re.search(rf"const {name} = (.*?);\n", source, re.DOTALL)
    assert found, name
    as_json = re.sub(r"(\w+):", r'"\1":', found[1]).replace("'", '"')
    return json.loads(as_json)


def test_decision_component_verdicts_match_the_python_owner() -> None:
    assert _js_constant("decision.js", "OPTIONS") == list(OPTIONS)
    assert _js_constant("decision.js", "VERDICT_OF") == VERDICT_OF
    assert _js_constant("decision.js", "LABELS") == LABELS


def test_matrix_component_scales_match_the_spec() -> None:
    assert _js_constant("matrix.js", "SCALES") == SCALES
    source = (STATIC / "matrix.js").read_text(encoding="utf-8")
    assert f"const FIRST_COLUMN = '{FIRST_COLUMN}';" in source
