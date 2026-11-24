"""No rendered icon is a typed symbol: that glyph needs a font the machine may lack."""

from __future__ import annotations

import re
from pathlib import Path

PAGES = Path(__file__).parents[2] / "src/varde/pages"
TYPED_ICONS = re.compile("[✓✕●○▲▼◆◐✎▬]")
# Server SVG text and a code-line mark outside the icon set; reported separately.
OUT_OF_SCOPE = {"blocks_render/state_graph.py"}


def test_icons_are_drawn_not_typed() -> None:
    found = [
        f"{path.relative_to(PAGES)}:{number}"
        for path in sorted(PAGES.rglob("*"))
        if path.suffix in {".py", ".js", ".css"}
        and "vendor" not in path.parts
        and path.relative_to(PAGES).as_posix() not in OUT_OF_SCOPE
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if TYPED_ICONS.search(line)
    ]
    assert found == []
