"""Standalone exports embed themes and preserve unthemed output."""

import re
from pathlib import Path

from test_export_standalone import every_block_page

from varde.pages.assemble import assemble_static
from varde.pages.template import page_css
from varde.ui.components import export_page


def test_every_block_export_with_and_without_theme(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VARDE_CONFIG_DIR", str(tmp_path / "config"))
    body = every_block_page(tmp_path)
    doc = tmp_path / "all.md"
    unthemed = assemble_static(doc)
    assert "data-vd-theme" not in unthemed
    assert unthemed == export_page(
        doc.name, f'<main data-role="page">{body}</main>', page_css()
    )

    doc.write_text(
        "---\ntheme: harbor\n---\n" + doc.read_text(encoding="utf-8"), encoding="utf-8"
    )
    themed = assemble_static(doc)
    assert '<main data-role="page"><style data-vd-theme>' in themed
    markup = re.sub(r"<script[^>]*>.*?</script>", "", themed, flags=re.DOTALL)
    for remote in ("src=", "http://", "https://", "@import", "url(", "<link"):
        assert remote not in markup
