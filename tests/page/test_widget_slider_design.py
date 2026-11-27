"""Slider design: stylesheet rules a browser check cannot see."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

UI = Path(str(files("tavle")))
CSS = re.sub(
    r"/\*.*?\*/",
    "",
    (UI / "static" / "css" / "25-slider.css").read_text(),
    flags=re.DOTALL,
)
PHYSICAL = re.compile(
    r"\b(?:margin|padding|border)-(?:left|right|top|bottom)\b"
    r"|(?<![\w-])(?:left|right|top|bottom|width|height|min-width|min-height)\s*:"
)


def test_no_button_ring_override_hidden_overflow_or_physical_properties() -> None:
    assert "button:focus" not in CSS
    assert "overflow:" not in CSS.replace("overflow-wrap", "")
    assert PHYSICAL.findall(CSS) == []
