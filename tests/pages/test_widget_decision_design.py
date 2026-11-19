"""Decision widget design: stylesheet rules.

The markup is checked in `components/blocks_text.test.js`; the widget matrix
(`widget_matrix -k decision`) covers layout, contrast and focus in Chromium.
"""

from __future__ import annotations

from pathlib import Path

PAGES = Path(__file__).resolve().parents[2] / "src/varde/pages"
CSS = (PAGES / "static/css/23-decision.css").read_text()


def test_diff_scrolls_and_is_keyboard_reachable() -> None:
    assert "overflow: auto" in CSS and "focus-visible" in CSS


def test_stylesheet_wraps_and_keeps_the_global_button_ring() -> None:
    assert "flex-wrap: wrap" in CSS and "overflow-wrap: anywhere" in CSS
    assert "forced-colors" in CSS and "max(1rem, 16px)" in CSS
    assert "button:focus-visible" not in CSS
