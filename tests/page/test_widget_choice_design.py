"""Choice widget design: stylesheet rules a browser check cannot see.

The markup is checked in `components/inputs_markup.test.js`; the widget matrix
(`widget_matrix -k choice`) covers layout, contrast and focus in Chromium.
"""

from __future__ import annotations

from ui_paths import UI_ROOT

UI = UI_ROOT
CSS = (UI / "static/css/20-choice.css").read_text()


def test_grid_responds_to_its_container_not_the_viewport() -> None:
    assert "@media (min-width" not in CSS


def test_send_button_keeps_the_shared_button_ring_and_fill() -> None:
    send_rules = [ln for ln in CSS.splitlines() if ln.startswith(".choice-send")]
    assert send_rules
    assert not any("background" in ln or "outline" in ln for ln in send_rules)
