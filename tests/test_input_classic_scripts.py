"""Input parts are loaded as classic scripts by the page host."""

import re

from tavle.shell import UI_STATIC


def test_input_parts_have_no_module_statements() -> None:
    for name in (
        "inputs_fields.js",
        "inputs_widgets.js",
        "inputs_runtime.js",
        "inputs_ordered.js",
    ):
        source = UI_STATIC.joinpath(name).read_text(encoding="utf-8")
        assert not re.search(r"^\s*(?:import\s|export\s)", source, re.MULTILINE), name
