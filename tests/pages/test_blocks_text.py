"""Text and reference blocks render client-side: registration, hosts, fixtures.

The component DOM is checked in `tests/pages/components/blocks_text.test.js`
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

from varde.pages.blocks import COMPONENT_SPECS, check_props
from varde.pages.blocks.chart_notes import NOTE_PROPERTIES, note_rule_faults
from varde.pages.blocks.decision import OPTIONS
from varde.pages.blocks.option_matrix import FIRST_COLUMN, SCALES
from varde.pages.blocks.spec import BlockSpec, PropertySpec
from varde.pages.blocks_render.decision import LABELS, VERDICT_OF
from varde.pages.blocks_render.registry import COMPONENTS
from varde.pages.components import component_bundle
from varde.pages.render import classify_url, render_page

TESTS = Path(__file__).parent
FIXTURES = TESTS / "components" / "fixtures"
STATIC = TESTS.parents[1] / "src" / "varde" / "pages" / "static" / "components"
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


@pytest.mark.parametrize(
    "name,valid,required",
    [
        ("callout", {"tone": "info", "text": "hello"}, "text"),
        ("code", {"language": "py", "source": "x"}, "source"),
        (
            "annotated-code",
            {"filename": "f", "language": "py", "source": "x", "notes": []},
            "filename",
        ),
    ],
)
def test_metadata_rejects_shape_errors(
    name: str, valid: dict[str, object], required: str
) -> None:
    for props, field in [
        ({**valid, "unexpected": 1}, "unexpected"),
        ({k: v for k, v in valid.items() if k != required}, required),
        ({**valid, required: 42}, required),
    ]:
        errors = check_props(name, props, 1)
        assert len(errors) == 1
        assert field in errors[0].message


RECAP_ROW = {"file": "a.py", "status": "M", "hunk": "@@"}


def test_recap_metadata_rejects_shape_errors() -> None:
    valid: dict[str, object] = {"rows": [RECAP_ROW]}
    assert check_props("recap", valid, 1) == []
    for props, field in [
        ({**valid, "unexpected": 1}, "unexpected"),
        ({}, "rows"),
        ({"rows": 42}, "rows"),
        ({"rows": [{**RECAP_ROW, "unexpected": 1}]}, "rows[0].unexpected"),
        ({"rows": [{"file": "a.py", "status": "M"}]}, "rows[0].hunk"),
        ({"rows": [{**RECAP_ROW, "file": 3}]}, "rows[0].file"),
    ]:
        errors = check_props("recap", props, 1)
        assert len(errors) == 1
        assert field in errors[0].message


def test_change_summary_metadata_rejects_shape_errors() -> None:
    assert check_props("change-summary", {}, 1) == []
    assert check_props("change-summary", {"title": "T"}, 1) == []
    cases: list[tuple[dict[str, object], str]] = [
        ({"unexpected": 1}, "unexpected"),
        ({"title": 3}, "title"),
    ]
    for props, field in cases:
        errors = check_props("change-summary", props, 1)
        assert len(errors) == 1
        assert field in errors[0].message


def test_chart_note_metadata_and_rules_check_a_note_once(monkeypatch) -> None:
    spec = BlockSpec(
        "notes-test",
        "chart notes",
        (),
        "",
        note_rule_faults,
        properties=(
            PropertySpec("labels", "list", items="string"),
            PropertySpec(
                "notes", "list", items="object", fields=NOTE_PROPERTIES, required=True
            ),
        ),
    )
    monkeypatch.setitem(COMPONENT_SPECS, "notes-test", spec)
    base = {"labels": ["a", "b"]}
    note = {"x": "a", "label": "n"}
    assert check_props("notes-test", {**base, "notes": [note]}, 1) == []
    for notes, field in [
        ([{**note, "unexpected": 1}], "notes[0].unexpected"),
        ([{"x": "a"}], "notes[0].label"),
        ([{**note, "label": 3}], "notes[0].label"),
        ([{**note, "tone": "loud"}], "notes[0].tone"),
        ([{"label": "n", "from": "a"}], "notes[1]: missing required key 'to'"),
    ]:
        errors = check_props("notes-test", {**base, "notes": notes}, 1)
        assert len(errors) == 1
        assert field in errors[0].message
