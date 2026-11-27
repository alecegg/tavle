# Audit: asset-text (task 5.20, base `b7fdf75`)

- Source (`--only` globs): none (design D3 class 3 and A2; judged by C2 to C5, no mutation run)
- Test files: `tests/test_tokens_shared.py`, `tests/test_input_classic_scripts.py`, `tests/test_shell_assets.py`, `tests/test_vendor_mithril.py`, `tests/test_svg_kit.py`, `tests/test_widget_decision_design.py`, `tests/page/test_design_tokens.py`, `tests/page/test_ds_tokens.py`, `tests/page/test_chrome_design.py`, `tests/page/test_widget_choice_design.py`, `tests/page/test_widget_comment_design.py`, `tests/page/test_widget_form_design.py`, `tests/page/test_widget_ranking_design.py`, `tests/page/test_widget_slider_design.py`, `tests/page/test_no_status_edge_border.py`, `tests/page/test_no_typed_icons.py`, `tests/page/test_static_js_syntax.py`
- Collected tests (file order as above): 228 before (116, 1, 7, 3, 3, 2, 14, 13, 15, 6, 2, 3, 7, 3, 2, 1, 30), 98 after (12, 1, 7, 2, 3, 1, 10, 8, 13, 2, 1, 2, 2, 1, 2, 1, 30). Test functions: 82 before, 52 after.
- Mutation score before and after: not mutation-judged.

All 17 files are done.

## Rule for C3 in stylesheet tests

A check fails C3 when it only finds a declaration, selector or value copied from one source file in that same file.
It is kept when adding code can break it (a ban or a lint over all declarations), when it computes a property (contrast, ratio, ordering, completeness over a set), when it compares two separately maintained sources, or when it guards a published contract or a recorded change.

Matrix checks named below are in `tests/page/widget_matrix/checks.py`. They are supporting facts; each deletion stands on its criterion.

## Decisions

CSS paths are under `src/tavle/static/css/`, except `10-chrome.css`, which is under `src/tavle/page/static/css/`.

| test id | decision | criterion | evidence |
|---|---|---|---|
| `test_tokens_shared.py::test_text_tokens_meet_aa_on_every_surface` | merge into `test_design_tokens.py::test_token_pairs_meet_contrast` | C5 | `PAIRS` already held 36 of the 42 pairs at 4.5; `--vd-accent-2` joined `HUES` for the other 6 |
| `test_tokens_shared.py::test_interactive_borders_and_on_accent_text_meet_ui_contrast` | delete | C5 | `PAIRS` holds `--vd-border-interactive` on all three surfaces at 3.0 and `--vd-on-accent` on `--vd-accent` at 4.5 |
| `test_tokens_shared.py::test_tone_text_meets_aa_on_its_tint_over_every_surface` | merge (30 cases to 2) | C6 | stacked `parametrize` (design D12); surface and tone are loops with collected failures, same threshold |
| `test_tokens_shared.py::test_tone_edge_meets_ui_contrast_on_every_surface` | merge (30 cases to 2) | C6 | same |
| `test_design_tokens.py::test_heading_tokens_keep_default_values_and_drive_chrome` | merge into `test_tokens_shared.py::test_heading_tokens_are_shared_across_schemes_and_drive_chrome` (renamed from `test_heading_tokens_are_shared_across_schemes`) | C3, C5 | the value dict copied `00-tokens.css:29` onward; the name list was a second copy; the `var(--vd-…)` use in `10-chrome.css` moved |
| `test_design_tokens.py::test_token_table_covers_the_design_language` | delete | C3 | list of token names and media queries copied from `00-tokens.css` (e.g. lines 19 and 334) |
| `test_design_tokens.py::test_base_applies_the_flow_tokens_to_the_page_blocks` | delete | C3 | declarations and selectors copied from `01-base.css:24-27` |
| `test_design_tokens.py::test_part_files_exist_and_load_in_order` | delete | C3, C5 | `PART_NAMES` copied the directory listing; load order is `page_css()` against the name-sorted parts in `test_served_css_equals_the_concatenation` |
| `test_design_tokens.py::test_served_css_equals_the_concatenation`, `::test_export_inlines_the_same_css`, `::test_served_route_returns_the_concatenation` | keep | C2 | they mirror `page_css` and `static_body`, but guard the delivery contract: every part is served and inlined, and the CSS loads no `url()` |
| `test_ds_tokens.py::test_neutral_ramp_is_ten_forty_five_ninety_ninety_five` | delete | C3 | four values copied from `00-tokens.css:24` onward |
| `test_ds_tokens.py::test_every_pre_existing_class_still_has_a_rule` | delete | C3 | hand copy of about 250 class names from the stylesheets (a one-off restyle guard) |
| `test_ds_tokens.py::test_page_is_a_container_with_a_60rem_column_and_1_75_body` | delete | C3 | `01-base.css:8`, `00-tokens.css:167` and `:170` |
| `test_ds_tokens.py::test_toc_is_a_collapsed_block_by_default_and_a_rail_from_64rem` | delete | C3 | `01-base.css:12` onward; `test_pages_toc.py::test_phone_contents_bar_stays_in_view_and_closes_on_follow` checks the visible collapsed bar in Chromium |
| `test_ds_tokens.py::test_headings_use_their_font_token_and_are_bolder_than_body` | delete | C3 | `10-chrome.css:9` and `:14`, `00-tokens.css:29` |
| `test_ds_tokens.py::test_mono_stack_is_monospace_and_used_for_code`, `::test_prose_blocks_are_limited_to_the_reading_measure` | keep | C3 | each also checks a property that can break (generic fallback last; measure in 70 to 80ch) |
| `test_chrome_design.py::test_button_family_has_every_state` | delete | C3, C5 | selectors copied from `10-chrome.css:45-46`; hover placement is `test_design_tokens.py::test_hover_rules_sit_inside_the_hover_media_query` |
| `test_chrome_design.py::test_thread_state_uses_a_full_border_not_an_edge_bar` | delete | C3, C5 | `10-chrome.css:68-69`; the edge-bar ban is `test_no_status_edge_border.py::test_no_status_edge_border` |
| `test_chrome_design.py::test_flash_and_forced_colors_are_covered` | delete | C3 | `10-chrome.css:41` and `:59` |
| `test_chrome_design.py::test_button_targets_use_the_control_height_token` | delete | C3 | `10-chrome.css:44`; `check_target_sizes` (line 192) measures the 44px minimum |
| `test_chrome_design.py::test_flow_tokens_own_the_gaps_the_action_menu_once_reserved` | keep | C3 | records a past change: its bans stop the menu from reserving padding again |
| `test_chrome_design.py::test_focus_is_never_removed` | changed | C5 | gains `20-choice.css` and `21-form.css` rows, which replace the `outline: none` lines of the choice and form tests |
| `test_widget_choice_design.py::test_grid_is_a_container_query_with_three_two_one_columns` | changed, now `test_grid_responds_to_its_container_not_the_viewport` | C3 | dropped `20-choice.css:7` and `:10` copies; kept the viewport media query ban |
| `test_widget_choice_design.py::test_selected_state_has_a_border_and_glyph_not_colour_alone` | delete | C3 | `20-choice.css:29` and `:43`; `check_selection` (line 283) fails a selection marked by fill alone |
| `test_widget_choice_design.py::test_hover_only_under_hover_media_and_no_inline_colour` | delete | C5 | `test_design_tokens.py::test_hover_rules_sit_inside_the_hover_media_query` and `::test_no_colour_literal_outside_the_tokens_file` cover every part; the outline line moved to `test_focus_is_never_removed` |
| `test_widget_choice_design.py::test_choice_script_moves_focus_to_first_option_and_clears_on_edit` | delete | C3, C5 | identifiers copied from `inputs_widgets.js:10-27`; behaviour is in `enhance_inputs_widgets.test.js` (`validates choices and sends…`); the `innerHTML` ban is `test_runtime_injection.py::test_static_scripts_have_no_dynamic_code_paths` |
| `test_widget_choice_design.py::test_textarea_and_options_have_scroll_margin_for_the_focus_ring` | delete | C3 | `20-choice.css:22` and `:50`; `check_focus` (line 307) judges clipped and obscured rings |
| `test_widget_comment_design.py::test_stylesheet_is_stacked_full_width_and_readable` | changed, now `test_stylesheet_keeps_the_global_button_ring` | C3 | dropped copies of `22-comment.css:7-11`; kept the `button:focus-visible` ban |
| `test_widget_comment_design.py::test_script_announces_only_at_thresholds_and_shows_sending` | delete | C3, C5 | `inputs_widgets.js:53` and `:67`; `enhance_inputs_widgets.test.js` asserts the threshold announcements and `Sending...`; `innerHTML` as above |
| `test_widget_form_design.py::test_css_uses_container_grid_44px_controls_and_16px_font` | changed, now `test_grid_responds_to_its_container_not_the_viewport` | C3 | dropped copies of `21-form.css:6-32`; `check_target_sizes` covers 44px; the outline lines moved to `test_focus_is_never_removed` |
| `test_widget_form_design.py::test_invalid_state_is_a_thicker_border_and_the_shared_error_text` | changed, now `test_stylesheet_keeps_the_global_button_ring` | C3 | dropped `21-form.css:23` copies; kept the ban |
| `test_widget_form_design.py::test_form_script_tracks_required_fields_and_invalid_controls` | delete | C3, C5 | `inputs_widgets.js:75-84`; `enhance_inputs_widgets.test.js` (`tracks required fields, marks errors…`); `innerHTML` as above |
| `test_widget_decision_design.py::test_diff_scrolls_and_is_keyboard_reachable` | delete | C3 | `23-decision.css:11-12`; `check_focus` (line 307) |
| `test_widget_decision_design.py::test_stylesheet_wraps_and_keeps_the_global_button_ring` | changed, now `test_stylesheet_keeps_the_global_button_ring` | C3 | dropped `23-decision.css:7` and `:49` copies; kept the ban |
| `test_widget_ranking_design.py::test_li_is_not_flex_and_numbers_are_a_counter_badge` | delete | C3 | `24-ranking.css:6-8` |
| `test_widget_ranking_design.py::test_drag_is_pointer_fine_only_and_touch_scroll_survives` | delete | C3, C5 | `24-ranking.css:6` and `:18`; the script's `(pointer: fine)` query is asserted in `enhance_inputs_ordered.test.js` |
| `test_widget_ranking_design.py::test_elevation_drop_line_and_forced_colors_are_styled` | delete | C3 | `24-ranking.css:24-30` |
| `test_widget_ranking_design.py::test_row_wraps_and_label_keeps_min_content_room` | delete | C3 | `24-ranking.css:7-10`; `check_overflow` (line 167) on the long labels in `fixtures/widgets/stress.md:33` |
| `test_widget_ranking_design.py::test_card_does_not_clip_focus_rings_and_print_resets_clipping` | delete | C3 | `24-ranking.css:14` and `:36-37`; `check_focus` (line 307, `focus-clipped`) and `check_print` (line 374, `print-clipped`) |
| `test_widget_slider_design.py::test_hit_area_is_44px_and_thumb_is_larger_than_the_track` | delete | C3 | `25-slider.css:11` and `:15`; `check_target_sizes` (line 192) |
| `test_widget_slider_design.py::test_focus_ring_is_the_shared_field_ring_and_nothing_hides_overflow` | changed, now `test_no_button_ring_override_hidden_overflow_or_physical_properties` | C3 | dropped `25-slider.css:19-20` copies; `check_focus` reads the thumb ring; kept the three bans |
| `test_widget_slider_design.py::test_track_fill_rtl_and_forced_colors_are_styled` | delete | C3 | `25-slider.css:13`, `:31`, `:73` |
| `test_vendor_mithril.py::test_header_names_the_recorded_version_and_licence` | merge into `::test_vendored_mithril_hash_matches_recorded_row` | C3 | the header is now compared with the version and licence read from the licence doc, not with a copied literal |

No other test in the 17 files is a C2 to C5 candidate. The one static-scan hit (`audit/static-scan.md`, C5 identical body, `test_widget_decision_design.py::test_diff_scrolls_and_is_keyboard_reachable`) is deleted above.

## Facts no test checks now

The deleted string checks were the only checks of these; none ran the behaviour:

- the `max(1rem, 16px)` input font size (no iOS focus zoom) in the comment, form and decision stylesheets;
- `touch-action: pan-y` on ranking rows;
- the presence of the `forced-colors` and reduced-motion blocks (the matrix `forced-colors` mode checks selection, control borders and names only).
