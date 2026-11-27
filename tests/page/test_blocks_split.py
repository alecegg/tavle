"""Facts the split of the block code by kind relies on."""

from tavle import props_errors
from tavle.page.include_statement import INCLUDE


def test_block_scripts_are_es_modules_imported_by_blocks_js() -> None:
    from tavle.page.template import page_scripts, static_scripts

    parts = {"dom.js", "table.js", "tabs.js", "flow.js", "chart.js", "viewport.js"}
    assert parts <= set(static_scripts())
    assert parts.isdisjoint(page_scripts())
    assert page_scripts() == (
        "components.js",
        "app.js",
        "blocks.js",
        "inputs_fields.js",
        "inputs_widgets.js",
        "inputs_runtime.js",
        "recap.js",
        "inputs_ordered.js",
    )


def test_include_property_faults_are_single_and_name_the_field() -> None:
    ok: dict[str, object] = {"source": "plan.md", "select": "acceptance"}
    cases: list[tuple[dict[str, object], str]] = [
        ({**ok, "extra": 1}, "extra"),
        ({"select": "acceptance"}, "source"),
        ({**ok, "source": 3}, "source"),
        ({**ok, "select": " "}, "select"),
        ({**ok, "title": ""}, "title"),
        ({**ok, "select": "nope"}, "selector"),
    ]
    assert props_errors(INCLUDE, {**ok, "title": "T"}, 1) == []
    for data, field in cases:
        faults = props_errors(INCLUDE, data, 1)
        assert len(faults) == 1, (data, faults)
        assert field in faults[0].message


def test_static_script_names_are_unique():
    from tavle import UI_STATIC
    from tavle.page.template import _HOST_STATIC

    host = {p.name for p in _HOST_STATIC.iterdir() if p.name.endswith(".js")}
    ui = {p.name for p in UI_STATIC.iterdir() if p.name.endswith(".js")}
    assert host.isdisjoint(ui)
