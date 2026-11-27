"""Ranking design: stylesheet rules a browser check cannot see."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

UI = Path(str(files("tavle")))
CSS = re.sub(
    r"/\*.*?\*/",
    "",
    (UI / "static" / "css" / "24-ranking.css").read_text(),
    flags=re.DOTALL,
)
DECLARATION = re.compile(r"([a-z-]+)\s*:\s*([^;{}]+);")
LENGTH = re.compile(r"-?\d*\.?\d+(?:px|rem|em|vw|vh|ch)\b")
PHYSICAL = re.compile(
    r"\b(?:margin|padding|border)-(?:left|right|top|bottom)\b"
    r"|(?<![\w-])(?:left|right|top|bottom|width|height|min-width|min-height)\s*:"
)


def test_spacing_sizes_and_logical_properties_come_from_tokens() -> None:
    for prop, value in DECLARATION.findall(CSS):
        if re.match(r"^(margin|padding|gap)(-|$)", prop) or prop in (
            "min-block-size",
            "min-inline-size",
        ):
            bare = re.sub(r"var\(--vd-[\w-]+\)", "", value)
            assert not LENGTH.search(bare), (prop, value)
    assert PHYSICAL.findall(CSS) == []


def test_focus_ring_is_not_overridden_and_nothing_hides_overflow() -> None:
    assert not re.search(r"outline|:focus", CSS)
    assert not re.search(r"overflow(-[xy])?:\s*(hidden|auto|scroll|clip)", CSS)
