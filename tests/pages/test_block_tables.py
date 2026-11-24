"""Every spec but a page statement has a component file; no block has a renderer."""

from pathlib import Path

from varde.pages.blocks import COMPONENT_SPECS, check_props
from varde.pages.blocks_render.registry import COMPONENTS, PAGE_STATEMENTS
from varde.pages.components import component_bundle

COMPONENT_FILES = Path(__file__).parents[2] / "src/varde/pages/static/components"


def test_component_registry_matches_the_specs() -> None:
    assert set(COMPONENTS) == set(COMPONENT_SPECS)


def test_each_block_has_a_component_file_and_only_page_statements_do_not() -> None:
    files = {path.stem for path in COMPONENT_FILES.glob("*.js")} - {"mount", "shared"}
    assert files == set(COMPONENT_SPECS) - PAGE_STATEMENTS
    assert 'components["tabs"]' in component_bundle()


def test_the_registry_has_no_html_renderer() -> None:
    assert not any(hasattr(entry, "render") for entry in COMPONENTS.values())


_TABLE: dict[str, object] = {"columns": ["a", "b"], "rows": [["1", "2"]]}
_FIRST = {"label": "a", "value": 1}
_SECOND = {"label": "b", "value": 2}
_STATS: dict[str, object] = {"item": [_FIRST, _SECOND]}


def _one_fault(component: str, props: dict[str, object], field: str) -> None:
    errors = check_props(component, props, 1)
    assert len(errors) == 1, props
    assert field in errors[0].message


def test_table_declares_its_shape_and_each_mistake_gets_one_fault() -> None:
    assert check_props("table", _TABLE, 1) == []
    cases: list[tuple[dict[str, object], str]] = [
        ({**_TABLE, "unexpected": 1}, "unexpected"),
        ({"columns": ["a"]}, "rows"),
        ({**_TABLE, "columns": "a"}, "columns"),
        ({**_TABLE, "columns": ["a", 2]}, "columns[1]"),
        ({**_TABLE, "rows": ["x"]}, "'rows[0]' must be list"),
        ({**_TABLE, "stack": 1}, "stack"),
        ({**_TABLE, "types": "x"}, "types"),
        ({**_TABLE, "groups": [{"label": "g"}]}, "groups[0].rows"),
        ({**_TABLE, "groups": [{"label": "g", "rows": "1"}]}, "groups[0].rows"),
        ({**_TABLE, "groups": [{"label": "g", "rows": 2}]}, "groups cover 2 rows"),
    ]
    for props, field in cases:
        _one_fault("table", props, field)


def test_stats_declares_its_shape_and_each_mistake_gets_one_fault() -> None:
    assert check_props("stats", _STATS, 1) == []
    first, second = _FIRST, _SECOND
    cases: list[tuple[dict[str, object], str]] = [
        ({**_STATS, "unexpected": 1}, "unexpected"),
        ({}, "item"),
        ({"item": "x"}, "item"),
        ({"item": [{"value": 1}, second]}, "item[0].label"),
        ({"item": [{"label": "a"}, second]}, "item[0].value"),
        ({"item": [{**first, "tone": "loud"}, second]}, "tone"),
        ({"item": [{**first, "decimals": "2"}, second]}, "decimals"),
        ({"item": [{**first, "decimals": 9}, second]}, "decimals"),
        ({"item": [{**first, "value": True}, second]}, "value"),
        ({"item": [{**first, "delta": "12%"}, second]}, "delta"),
        ({"item": [first]}, "2 to 6 items"),
    ]
    for props, field in cases:
        _one_fault("stats", props, field)


def test_table_rows_are_checked_once_each_as_lists() -> None:
    """Mixed cell types pass; only a row that is not a list faults, once."""
    mixed = {"columns": ["a", "b"], "rows": [["x", 1], ["y", 2.5]]}
    assert check_props("table", mixed, 1) == []
    errors = check_props("table", {**_TABLE, "rows": [["1", "2"], "x"]}, 1)
    assert [e.message for e in errors] == ["'rows[1]' must be list"]
