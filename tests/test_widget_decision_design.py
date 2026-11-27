"""Decision widget design: stylesheet rules.

The markup is checked in `components/blocks_text.test.js`; the widget matrix
(`widget_matrix -k decision`) covers layout, contrast and focus in Chromium.
"""

from __future__ import annotations

from pathlib import Path

UI = Path(__file__).resolve().parents[1] / "src/tavle"
CSS = (UI / "static/css/23-decision.css").read_text()


def test_stylesheet_keeps_the_global_button_ring() -> None:
    assert "button:focus-visible" not in CSS
