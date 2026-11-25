"""Form widget design: stacked fields, hints, grid, error and checkbox styling.

Stylesheet and script checks run without a browser (the markup is checked in
`components/inputs_markup.test.js`); the widget matrix
(`widget_matrix -k form`) covers layout, contrast and focus in Chromium.
"""

from __future__ import annotations

import re

from ui_paths import UI_ROOT

UI = UI_ROOT
CSS = (UI / "static/css/21-form.css").read_text()
JS = "\n".join(
    (UI / "static" / name).read_text()
    for name in ("inputs_fields.js", "inputs_widgets.js", "inputs_runtime.js")
)


def test_css_uses_container_grid_44px_controls_and_16px_font() -> None:
    assert "container-type: inline-size" in CSS
    assert "@container (min-width: 40rem)" in CSS and "repeat(2," in CSS
    assert "@media (min-width" not in CSS
    assert "var(--vd-control-height)" in CSS and "max(1rem, 16px)" in CSS
    assert "accent-color: var(--vd-accent)" in CSS
    assert "outline: none" not in CSS and "outline:none" not in CSS


def test_invalid_state_is_a_thicker_border_and_the_shared_error_text() -> None:
    assert re.search(r'\[aria-invalid="true"\][^{]*\{[^}]*border-width: 2px', CSS)
    assert ".form-error" in CSS and "var(--vd-error)" in CSS
    assert "button:focus-visible" not in CSS


def test_form_script_tracks_required_fields_and_invalid_controls() -> None:
    start = JS.index("function unfilled")
    form_js = JS[start:]
    assert "required field" in form_js and ".form-remaining" in form_js
    assert "aria-invalid" in form_js and "innerHTML" not in form_js
