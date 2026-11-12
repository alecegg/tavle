"""The token file serves the dashboard too: explicit and OS dark values must agree."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

TOKENS = files("varde_pages").joinpath("static", "css", "00-tokens.css")
CSS = Path(str(TOKENS)).read_text()


def _body(selector_start: str) -> str:
    """Body of the first block whose header starts with `selector_start`."""
    start = CSS.index(selector_start)
    open_at = CSS.index("{", start)
    depth = 0
    for i in range(open_at, len(CSS)):
        depth += CSS[i] == "{"
        depth -= CSS[i] == "}"
        if depth == 0:
            return CSS[open_at + 1 : i]
    raise AssertionError("unclosed block")


def _declarations(body: str) -> dict[str, str]:
    return dict(re.findall(r"(--vd-[\w-]+)\s*:\s*([^;]+);", body))


def test_explicit_dark_theme_matches_the_os_dark_theme() -> None:
    os_dark = _declarations(_body("@media (prefers-color-scheme: dark)"))
    explicit = _declarations(_body(':root[data-theme="dark"]'))
    assert os_dark and os_dark == explicit


def test_os_dark_theme_skips_a_page_forced_light() -> None:
    media = _body("@media (prefers-color-scheme: dark)")
    assert ':root:not([data-theme="light"])' in media
    assert "color-scheme: light" in _body(':root[data-theme="light"]')
