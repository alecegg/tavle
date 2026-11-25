"""Choice widget design: group semantics, option cards, selected cue, focus and errors.

Stylesheet and script checks run without a browser (the markup is checked in
`components/inputs_markup.test.js`); the widget matrix
(`widget_matrix -k choice`) covers layout, contrast and focus in Chromium.
"""

from __future__ import annotations

import re

from ui_paths import UI_ROOT

UI = UI_ROOT
CSS = (UI / "static/css/20-choice.css").read_text()
JS = "\n".join(
    (UI / "static" / name).read_text()
    for name in ("inputs_fields.js", "inputs_widgets.js", "inputs_runtime.js")
)


def _choice_js() -> str:
    start = JS.index("function clearChoiceError")
    return JS[start : JS.index("register('comment'", start)]


def test_grid_is_a_container_query_with_three_two_one_columns() -> None:
    assert "container-type: inline-size" in CSS
    assert "@container (min-width: 44rem)" in CSS and "repeat(3," in CSS
    assert "@container (min-width: 30rem)" in CSS and "repeat(2," in CSS
    assert "@media (min-width" not in CSS


def test_selected_state_has_a_border_and_glyph_not_colour_alone() -> None:
    selected = re.search(r"\.choice-option:has\(input:checked\) \{([^}]*)\}", CSS)
    assert selected and "border-width: 2px" in selected.group(1)
    assert re.search(r"\.choice-option:has\(input:checked\)::after \{[^}]*content", CSS)
    assert "forced-colors: active" in CSS


def test_hover_only_under_hover_media_and_no_inline_colour() -> None:
    outside = re.sub(r"@media \(hover: hover\) \{.*?\n\}", "", CSS, flags=re.DOTALL)
    assert ":hover" not in outside
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(", CSS)
    assert "outline: none" not in CSS


def test_choice_script_moves_focus_to_first_option_and_clears_on_edit() -> None:
    js = _choice_js()
    assert "options[0]" in js and "aria-invalid" in js
    assert "'change'" in js and "clearChoiceError(root)" in js
    assert "innerHTML" not in js


def test_send_button_keeps_the_shared_button_ring_and_fill() -> None:
    send_rules = [ln for ln in CSS.splitlines() if ln.startswith(".choice-send")]
    assert send_rules
    assert not any("background" in ln or "outline" in ln for ln in send_rules)


def test_textarea_and_options_have_scroll_margin_for_the_focus_ring() -> None:
    assert re.search(r"textarea\.choice-text \{ scroll-margin-block", CSS)
    assert re.search(r"\.choice-option input \{ scroll-margin-block", CSS)
