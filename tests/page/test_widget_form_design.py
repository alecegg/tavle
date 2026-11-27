"""Form widget design: stylesheet rules a browser check cannot see.

The markup is checked in `components/inputs_markup.test.js`; the widget matrix
(`widget_matrix -k form`) covers layout, contrast and focus in Chromium.
"""

from __future__ import annotations

from ui_paths import UI_ROOT

UI = UI_ROOT
CSS = (UI / "static/css/21-form.css").read_text()


def test_grid_responds_to_its_container_not_the_viewport() -> None:
    assert "@media (min-width" not in CSS


def test_stylesheet_keeps_the_global_button_ring() -> None:
    assert "button:focus-visible" not in CSS
