"""Comment widget design: stylesheet rules.

The markup is checked in `components/inputs_markup.test.js`.

The widget matrix (`widget_matrix -k comment`) covers layout, contrast and focus
in Chromium.
"""

from __future__ import annotations

from ui_paths import UI_ROOT

UI = UI_ROOT
CSS = (UI / "static/css/22-comment.css").read_text()


def test_stylesheet_keeps_the_global_button_ring() -> None:
    assert "button:focus-visible" not in CSS
