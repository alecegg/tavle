"""Fragment rendering shares the static export's page body."""

import re
from pathlib import Path

from tavle.page.assemble import assemble_static, render_fragment


def test_fragment_is_the_exported_read_only_page(tmp_path: Path) -> None:
    doc = tmp_path / "page.md"
    doc.write_text("# Hello\n\nA page.\n", encoding="utf-8")
    fragment = render_fragment(doc)
    assert fragment.startswith('<main data-role="page">')
    assert fragment.endswith("</main>")
    assert not re.search(r"<(?:html|style|script)\b", fragment, re.IGNORECASE)
    assert "Hello" in fragment
    assert fragment in assemble_static(doc)


def test_fragment_includes_theme(tmp_path: Path) -> None:
    doc = tmp_path / "page.md"
    doc.write_text("---\ntheme: harbor\n---\n# Hello\n", encoding="utf-8")
    fragment = render_fragment(doc)
    assert "<style data-vd-theme>" in fragment
    without_theme = re.sub(
        r"<style data-vd-theme>.*?</style>", "", fragment, flags=re.DOTALL
    )
    assert not re.search(r"<(?:html|style|script)\b", without_theme, re.IGNORECASE)
    assert fragment in assemble_static(doc)
