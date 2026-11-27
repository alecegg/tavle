"""Page chrome stylesheet parts: token use only, logical properties, states."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

import pytest
from ui_paths import UI_STATIC_DIR

CSS_DIR = Path(str(files("tavle.page").joinpath("static", "css")))
UI_CSS_DIR = UI_STATIC_DIR / "css"
CSS_FILES = sorted(
    [*CSS_DIR.glob("*.css"), *UI_CSS_DIR.glob("*.css")], key=lambda p: p.name
)
OWNED = ("10-chrome.css", "50-blocks.css")
DECLARATION = re.compile(r"([a-z-]+)\s*:\s*([^;{}]+);")
LENGTH = re.compile(r"-?\d*\.?\d+(?:px|rem|em|vw|vh|ch)\b")
SPACING = re.compile(r"^(margin|padding|gap|row-gap|column-gap)(-|$)")
PHYSICAL = re.compile(
    r"\b(?:margin|padding|border)-(?:left|right|top|bottom)\b"
    r"|(?<![\w-])(?:left|right|top|bottom|width|height|min-width|min-height|max-width|max-height)\s*:"
    r"|text-align\s*:\s*(?:left|right)"
)


def _text(name: str) -> str:
    return re.sub(
        r"/\*.*?\*/",
        "",
        (next(p for p in CSS_FILES if p.name == name)).read_text(),
        flags=re.DOTALL,
    )


def _declarations(name: str) -> list[tuple[str, str]]:
    return [(p, v.strip()) for p, v in DECLARATION.findall(_text(name))]


@pytest.mark.parametrize("name", OWNED)
def test_font_sizes_come_from_tokens(name: str) -> None:
    bad = [
        v
        for p, v in _declarations(name)
        if p == "font-size" and not re.fullmatch(r"var\(--vd-[\w-]+\)|inherit", v)
    ]
    assert bad == []


@pytest.mark.parametrize("name", OWNED)
def test_spacing_comes_from_tokens(name: str) -> None:
    bad = []
    for prop, value in _declarations(name):
        if not SPACING.match(prop):
            continue
        stripped = re.sub(r"var\(--vd-[\w-]+\)|\d+vw", "", value)  # fluid vw step
        if LENGTH.search(stripped):
            bad.append(f"{prop}: {value}")
    assert bad == []


@pytest.mark.parametrize("name", OWNED)
def test_control_sizes_come_from_tokens(name: str) -> None:
    bad = [
        f"{p}: {v}"
        for p, v in _declarations(name)
        if p in ("min-block-size", "min-inline-size") and "px" in v
    ]
    assert bad == []


@pytest.mark.parametrize("name", OWNED)
def test_logical_properties_only(name: str) -> None:
    assert PHYSICAL.findall(_text(name)) == []


@pytest.mark.parametrize("name", (*OWNED, "20-choice.css", "21-form.css"))
def test_focus_is_never_removed(name: str) -> None:
    assert not re.search(r"outline\s*:\s*(?:none|0)\b", _text(name))


def test_flow_tokens_own_the_gaps_the_action_menu_once_reserved() -> None:
    base, menu = _text("01-base.css"), _text("30-menu.css")
    # the menu button is the last child, so the last content child is found before it
    assert ":has(+ .menu-btn:last-child)" in base
    assert ".block.has-menu { padding-block-start: var(--vd-space-1); }" in menu
    assert "padding-block-start: var(--vd-control-height)" not in menu
    assert "min-block-size: var(--vd-control-height)" not in menu
