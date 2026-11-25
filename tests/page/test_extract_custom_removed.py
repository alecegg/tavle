from pathlib import Path

import pytest

from tavle.serve.assemble_served import assemble_page

DOC = "# Plan\n\nIntro.\n\n```custom id=widget\n<p>hi</p>\n```\n"


@pytest.fixture
def doc(tmp_path: Path) -> Path:
    path = tmp_path / "plan.md"
    path.write_text(DOC, encoding="utf-8")
    return path


def test_rendered_page_shows_the_error_card_and_no_frame(doc: Path) -> None:
    page = assemble_page(doc, token="t")  # noqa: S106
    assert "vb-card vb-error" in page and "custom block removed" in page
    assert (
        "<iframe" not in page and "&lt;p&gt;hi" not in page and "<p>hi</p>" not in page
    )
