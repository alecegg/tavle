"""Render recipe examples without errors or executable markup."""

import re
from pathlib import Path

import pytest

from tavle import blocks
from tavle.blocks_render.common import as_list
from tavle.blocks_render.inputs import choice_answer_schema, choice_props
from tavle.page.render import render_page

RECIPES = Path(__file__).parent / "fixtures" / "recipes"


@pytest.mark.parametrize("name", ("recap", "plan"))
def test_example_pages_render(name: str) -> None:
    doc = (RECIPES / f"{name}.md").read_text()
    body = render_page(doc, f"{name}.md").body
    props = re.compile(r'<script type="application/json">.*?</script>', re.DOTALL)
    body = props.sub("", body)  # client-side block props are data, not code
    assert "vb-error" not in body and "<script" not in body and "style=" not in body


def options(*flags: bool) -> list[object]:
    return [{"label": f"O{i}", "recommended": f} for i, f in enumerate(flags)]


def test_recommended_on_two_options_is_a_fault() -> None:
    props = {"question": "Which?", "options": options(True, True)}
    assert blocks.check_props("choice", props, 1)
    assert not blocks.check_props(
        "choice", {**props, "options": options(True, False)}, 1
    )
    assert blocks.check_props(
        "choice", {**props, "options": [{"label": "A", "recommended": "yes"}]}, 1
    )


def test_recommended_reaches_the_browser_as_a_flag_on_one_option() -> None:
    shown = choice_props({"question": "Which?", "options": options(False, True)})
    flags = [o["recommended"] for o in as_list(shown["options"])]
    assert flags == [False, True]


def test_answer_schema_ignores_recommended() -> None:
    plain = {"question": "Which?", "options": ["O0", "O1"]}
    marked = {"question": "Which?", "options": options(True, False)}
    assert choice_answer_schema(marked) == choice_answer_schema(plain)
