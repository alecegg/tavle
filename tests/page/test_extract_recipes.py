"""Render recipe examples without errors or executable markup."""

import re
from pathlib import Path

import pytest

from tavle.page.render import render_page

RECIPES = Path(__file__).parent / "fixtures" / "recipes"


@pytest.mark.parametrize("name", ("recap", "plan"))
def test_example_pages_render(name: str) -> None:
    doc = (RECIPES / f"{name}.md").read_text()
    body = render_page(doc, f"{name}.md").body
    props = re.compile(r'<script type="application/json">.*?</script>', re.DOTALL)
    body = props.sub("", body)  # client-side block props are data, not code
    assert "vb-error" not in body and "<script" not in body and "style=" not in body
