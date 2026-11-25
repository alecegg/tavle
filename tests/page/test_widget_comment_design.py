"""Comment widget design: counter, sending states and stylesheet rules.

The markup is checked in `components/inputs_markup.test.js`.

The widget matrix (`widget_matrix -k comment`) covers layout, contrast and focus
in Chromium.
"""

from __future__ import annotations

from ui_paths import UI_ROOT

UI = UI_ROOT
CSS = (UI / "static/css/22-comment.css").read_text()
JS = "\n".join(
    (UI / "static" / name).read_text()
    for name in ("inputs_fields.js", "inputs_widgets.js", "inputs_runtime.js")
)


def test_stylesheet_is_stacked_full_width_and_readable() -> None:
    assert "inline-size: 100%" in CSS and "flex-direction: column" in CSS
    assert "max(1rem, 16px)" in CSS and "field-sizing: content" in CSS
    assert "overflow-wrap: anywhere" in CSS and "forced-colors" in CSS
    assert ":disabled" in CSS and "focus-visible" in CSS
    assert "button:focus-visible" not in CSS


def test_script_announces_only_at_thresholds_and_shows_sending() -> None:
    assert "level === state.level" in JS
    assert "'Sending...'" in JS
    comment_js = JS.split("register('comment'")[1][:900]
    assert "textContent" in JS and "innerHTML" not in comment_js
