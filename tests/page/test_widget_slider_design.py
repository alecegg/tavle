"""Slider redesign: stylesheet rules, and fill and readout in a browser."""

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


def test_hit_area_is_44px_and_thumb_is_larger_than_the_track() -> None:
    assert "min-block-size: var(--vd-control-height)" in CSS
    assert "--slider-thumb: 1.75rem" in CSS and "--slider-track: 0.625rem" in CSS


def test_focus_ring_is_the_shared_field_ring_and_nothing_hides_overflow() -> None:
    assert "button:focus" not in CSS
    assert ".slider-input:focus-visible { outline: none; }" in CSS
    assert (
        ".slider-input:focus-visible::-webkit-slider-thumb { outline: 2px solid" in CSS
    )
    assert ".slider-input:focus-visible::-moz-range-thumb { outline: 2px solid" in CSS
    assert "overflow:" not in CSS.replace("overflow-wrap", "")
    assert PHYSICAL.findall(CSS) == []


def test_track_fill_rtl_and_forced_colors_are_styled() -> None:
    for needle in (
        "var(--vd-fill",
        ":dir(rtl)",
        "::-moz-range-progress",
        "forced-colors: active",
        "CanvasText",
        "tabular-nums",
    ):
        assert needle in CSS, needle
