# Static scan (task 4.1)

Scope: `tests/**/*.py` (139 files, 1149 `def test_` at any depth) and `tests/components/*.test.js` (30 files, 268 `it(`/`test(` blocks).

## Commands

- `rg -c "^\s*(async )?def test_" tests --type py` and `rg -c "^\s*(it|test)\(" tests/components --glob '*.test.js'` to count tests.
- `sg run --lang python --pattern 'assert True' tests`: 0 matches; `rg -n '^\s*assert True\b' tests`: 0 matches. `sg run --lang python --pattern 'assert $X == $X' tests`: 6 sites, the same six the scanner reports as `assert x == x`.
- `rg -n 'read_text|readFileSync' tests` to find files that read source text.
- `python3 -I scan.py` (scratch, `$TMPDIR/audit-scan/scan.py`): `ast` walk for C4 (no `assert`, `pytest.raises`, or `check_*`/`assert_*` call; `assert True`; `assert x == x`), C3 (reads `src/tavle` text and asserts `in` or a regex), C5 (parametrize rows repeated by AST equality; test bodies identical after renaming names and constants). JS: block split on `it(`/`test(` titles, no `expect(`/`assert`, `expect(true).toBe(true)`, source read with containment or match, body shape equal after renaming.

Known limit: the scan reads syntax, not meaning. Some C4 no-check hits call a local helper whose name is not `check_*`/`assert_*` (for example `expectView`, `expectNoFit`, `validate_answer`, `refuse`, `validate_theme`); they are listed as scanned, and the area audit decides them. C2 is not scanned (needs the fixture reading in tasks 5.x).

## Hit count per criterion

| Language | Criterion | Hits |
|---|---|---|
| Python | C2 | not scanned |
| Python | C3 | 2 |
| Python | C4 | 21 |
| Python | C5 | 57 |
| JavaScript | C2 | not scanned |
| JavaScript | C3 | 0 |
| JavaScript | C4 | 16 |
| JavaScript | C5 | 0 |

Note on the `x == x` rows: the brief files `assert x == x` under C4. D6 names the same form `assert f(x) == f(x)` under C3, so a later decision may cite either.

Per-subcriterion counts: js C4 no check = 16; py C3 src-text = 2; py C4 no check = 15; py C4 trivial = 6; py C5 identical body = 57.

## Hits by test file

| test id | line | criterion | evidence |
|---|---|---|---|
| **tests/components/enhance_viewport.test.js** | | | |
| `zooms about the centre from the bar buttons and resets from Reset view` | 80 | C4 no check | no expect()/assert |
| `keeps the centre fixed when no point is given` | 94 | C4 no check | no expect()/assert |
| `pan moves the view by the given amount in view units` | 125 | C4 no check | no expect()/assert |
| `reset restores the viewBox it started with` | 130 | C4 no check | no expect()/assert |
| `does nothing for a move under 4px` | 180 | C4 no check | no expect()/assert |
| `pans by the drag in view units` | 187 | C4 no check | no expect()/assert |
| `scales the drag by the zoom level` | 196 | C4 no check | no expect()/assert |
| `pans only with the primary button held` | 204 | C4 no check | no expect()/assert |
| `ends on pointercancel` | 235 | C4 no check | no expect()/assert |
| `pinch-zooms about the midpoint of two pointers` | 244 | C4 no check | no expect()/assert |
| `continues the drag with the remaining pointer after one lifts, without a jump` | 252 | C4 no check | no expect()/assert |
| **tests/components/enhance_wireframe.test.js** | | | |
| `does not fit two taps more than 350ms apart` | 223 | C4 no check | no expect()/assert |
| `does not fit two taps more than 30px apart` | 230 | C4 no check | no expect()/assert |
| `does not count a tap that moved more than 30px` | 237 | C4 no check | no expect()/assert |
| `does not count multi-touch taps` | 245 | C4 no check | no expect()/assert |
| `does not count mouse taps` | 256 | C4 no check | no expect()/assert |
| **tests/page/test_actions.py** | | | |
| `test_component_block_type` | 97 | C5 identical body | same body as tests/page/test_page_header.py:test_reading_time_boundaries, tests/page/test_rich_diff.py:test_validation, tests/test_contrast.py:test_parse_rgba |
| **tests/page/test_answers.py** | | | |
| `test_validate_answer_accepts_what_the_component_offers` | 52 | C4 no check | no assert/raises/check_ helper |
| `test_validate_answer_accepts_what_the_component_offers` | 52 | C5 identical body | same body as tests/page/test_extract_inputs.py:test_choice_form_comment_answer_accepts |
| `test_validate_answer_allows_newlines_and_tabs_in_text` | 250 | C4 no check | no assert/raises/check_ helper |
| **tests/page/test_blocks_charts_diagrams.py** | | | |
| `test_block_is_client_side_and_bundled` | 63 | C5 identical body | same body as tests/page/test_blocks_code_diff.py:test_block_is_client_side_and_bundled |
| `test_family_shape_mistake_gets_one_fault_naming_the_field` | 274 | C5 identical body | same body as tests/page/test_blocks_inputs.py:test_a_property_mistake_gets_one_fault_naming_the_field |
| `test_blank_text_and_empty_lists_fault_once` | 326 | C5 identical body | same body as tests/page/test_blocks_code_diff.py:test_blank_text_and_empty_lists_fault_once, tests/page/test_blocks_text.py:test_blank_text_faults_once, tests/test_block_tables.py:test_blank_text_and_empty_lists_fault_once |
| **tests/page/test_blocks_code_diff.py** | | | |
| `test_block_is_client_side_and_bundled` | 79 | C5 identical body | same body as tests/page/test_blocks_charts_diagrams.py:test_block_is_client_side_and_bundled |
| `test_blank_text_and_empty_lists_fault_once` | 537 | C5 identical body | same body as tests/page/test_blocks_charts_diagrams.py:test_blank_text_and_empty_lists_fault_once, tests/page/test_blocks_text.py:test_blank_text_faults_once, tests/test_block_tables.py:test_blank_text_and_empty_lists_fault_once |
| **tests/page/test_blocks_decision.py** | | | |
| `test_unknown_option` | 29 | C5 identical body | same body as tests/page/test_blocks_decision.py:test_duplicate_option, tests/page/test_blocks_decision.py:test_unknown_key |
| `test_duplicate_option` | 33 | C5 identical body | same body as tests/page/test_blocks_decision.py:test_unknown_option, tests/page/test_blocks_decision.py:test_unknown_key |
| `test_unknown_key` | 53 | C5 identical body | same body as tests/page/test_blocks_decision.py:test_unknown_option, tests/page/test_blocks_decision.py:test_duplicate_option |
| **tests/page/test_blocks_inputs.py** | | | |
| `test_a_property_mistake_gets_one_fault_naming_the_field` | 328 | C5 identical body | same body as tests/page/test_blocks_charts_diagrams.py:test_family_shape_mistake_gets_one_fault_naming_the_field |
| **tests/page/test_blocks_render.py** | | | |
| `test_parse_error_renders_one_error_card` | 106 | C5 identical body | same body as tests/page/test_blocks_render.py:test_old_typed_fence_renders_a_removed_card, tests/page/test_pages_ui.py:test_a_syntax_error_is_one_error_card_with_the_document_line |
| `test_old_typed_fence_renders_a_removed_card` | 111 | C5 identical body | same body as tests/page/test_blocks_render.py:test_parse_error_renders_one_error_card, tests/page/test_pages_ui.py:test_a_syntax_error_is_one_error_card_with_the_document_line |
| `test_chart_rejects_non_finite` | 116 | C5 identical body | same body as tests/page/test_page_header.py:test_h1_inside_a_code_fence_does_not_count_as_a_title, tests/page/test_pages_ui.py:test_unclosed_fence_with_complete_statements_renders_them |
| **tests/page/test_blocks_text.py** | | | |
| `test_blank_text_faults_once` | 163 | C5 identical body | same body as tests/page/test_blocks_charts_diagrams.py:test_blank_text_and_empty_lists_fault_once, tests/page/test_blocks_code_diff.py:test_blank_text_and_empty_lists_fault_once, tests/test_block_tables.py:test_blank_text_and_empty_lists_fault_once |
| **tests/page/test_extract_include.py** | | | |
| `test_select_nth_block_under_a_heading` | 91 | C5 identical body | same body as tests/page/test_extract_include.py:test_select_repeated_heading_takes_the_suffixed_anchor, tests/page/test_extract_include.py:test_select_frontmatter |
| `test_select_repeated_heading_takes_the_suffixed_anchor` | 95 | C5 identical body | same body as tests/page/test_extract_include.py:test_select_nth_block_under_a_heading, tests/page/test_extract_include.py:test_select_frontmatter |
| `test_select_frontmatter` | 110 | C5 identical body | same body as tests/page/test_extract_include.py:test_select_nth_block_under_a_heading, tests/page/test_extract_include.py:test_select_repeated_heading_takes_the_suffixed_anchor |
| **tests/page/test_extract_inputs.py** | | | |
| `test_ordered_answer_accepts` | 73 | C4 no check | no assert/raises/check_ helper |
| `test_choice_form_comment_answer_accepts` | 155 | C4 no check | no assert/raises/check_ helper |
| `test_choice_form_comment_answer_accepts` | 155 | C5 identical body | same body as tests/page/test_answers.py:test_validate_answer_accepts_what_the_component_offers |
| **tests/page/test_include_comments.py** | | | |
| `test_kind_with_part_is_rejected` | 195 | C4 no check | no assert/raises/check_ helper |
| `test_kind_unknown_value_is_rejected` | 200 | C4 no check | no assert/raises/check_ helper |
| `test_part_must_be_a_string` | 204 | C4 no check | no assert/raises/check_ helper |
| `test_allowlist_unknown_part_is_rejected` | 208 | C4 no check | no assert/raises/check_ helper |
| `test_allowlist_part_cannot_be_a_path` | 212 | C4 no check | no assert/raises/check_ helper |
| `test_allowlist_anchor_outside_the_region_is_rejected` | 217 | C4 no check | no assert/raises/check_ helper |
| `test_allowlist_bad_anchor_syntax_is_rejected` | 222 | C4 no check | no assert/raises/check_ helper |
| `test_allowlist_dotfile_and_non_md_sources_are_never_writable` | 227 | C4 no check | no assert/raises/check_ helper |
| `test_part_comment_needs_text` | 313 | C4 no check | no assert/raises/check_ helper |
| **tests/page/test_inputs_basic.py** | | | |
| `test_props_faults` | 96 | C5 identical body | same body as tests/page/test_inputs_ordered.py:test_props_faults |
| `test_invalid_props_are_not_answerable` | 115 | C5 identical body | same body as tests/page/test_inputs_ordered.py:test_invalid_props_are_not_answerable |
| **tests/page/test_inputs_ordered.py** | | | |
| `test_props_faults` | 67 | C5 identical body | same body as tests/page/test_inputs_basic.py:test_props_faults |
| `test_invalid_props_are_not_answerable` | 85 | C5 identical body | same body as tests/page/test_inputs_basic.py:test_invalid_props_are_not_answerable |
| **tests/page/test_page_header.py** | | | |
| `test_reading_time_boundaries` | 107 | C5 identical body | same body as tests/page/test_actions.py:test_component_block_type, tests/page/test_rich_diff.py:test_validation, tests/test_contrast.py:test_parse_rgba |
| `test_h1_inside_a_code_fence_does_not_count_as_a_title` | 148 | C5 identical body | same body as tests/page/test_blocks_render.py:test_chart_rejects_non_finite, tests/page/test_pages_ui.py:test_unclosed_fence_with_complete_statements_renders_them |
| **tests/page/test_pages_comments.py** | | | |
| `test_bad_intervals_error` | 71 | C5 identical body | same body as tests/test_theme_tokens.py:test_colour_rejects_css |
| **tests/page/test_pages_render.py** | | | |
| `test_nul_in_table_row_does_not_crash_or_hang` | 179 | C5 identical body | same body as tests/page/test_pages_render.py:test_comment_marker_in_code_span_keeps_later_content |
| `test_comment_marker_in_code_span_keeps_later_content` | 226 | C5 identical body | same body as tests/page/test_pages_render.py:test_nul_in_table_row_does_not_crash_or_hang |
| **tests/page/test_pages_toc.py** | | | |
| `test_phone_contents_bar_names_the_current_section` | 241 | C4 no check | no assert/raises/check_ helper |
| **tests/page/test_pages_ui.py** | | | |
| `test_a_syntax_error_is_one_error_card_with_the_document_line` | 61 | C5 identical body | same body as tests/page/test_blocks_render.py:test_parse_error_renders_one_error_card, tests/page/test_blocks_render.py:test_old_typed_fence_renders_a_removed_card |
| `test_unclosed_fence_with_complete_statements_renders_them` | 73 | C5 identical body | same body as tests/page/test_blocks_render.py:test_chart_rejects_non_finite, tests/page/test_page_header.py:test_h1_inside_a_code_fence_does_not_count_as_a_title |
| **tests/page/test_rich_callout.py** | | | |
| `test_registered_and_renders_through_the_page` | 27 | C5 identical body | same body as tests/page/test_rich_timeline.py:test_registered_and_renders_through_the_page |
| `test_stress_fixture_validates_and_stays_escaped` | 36 | C5 identical body | same body as tests/page/test_rich_stats.py:test_stress_fixture_validates_and_stays_escaped |
| **tests/page/test_rich_checklist.py** | | | |
| `test_registered_and_fixtures_render` | 43 | C5 identical body | same body as tests/page/test_rich_matrix.py:test_registered_help_and_fixtures |
| `test_fixture_family_exists` | 55 | C5 identical body | same body as tests/page/test_rich_containers.py:test_fixture_family_exists, tests/page/test_rich_matrix.py:test_fixture_family_exists |
| `test_status_has_no_inline_start_border` | 59 | C5 identical body | same body as tests/page/test_rich_screen_flow.py:test_status_has_no_inline_start_border, tests/page/test_rich_timeline.py:test_status_has_no_inline_start_border |
| **tests/page/test_rich_containers.py** | | | |
| `test_fixture_family_exists` | 259 | C5 identical body | same body as tests/page/test_rich_checklist.py:test_fixture_family_exists, tests/page/test_rich_matrix.py:test_fixture_family_exists |
| **tests/page/test_rich_diagram.py** | | | |
| `test_layout_is_deterministic` | 147 | C4 trivial | assert x == x |
| **tests/page/test_rich_diff.py** | | | |
| `test_rows_follow_difflib_and_carry_both_line_numbers` | 38 | C4 trivial | assert x == x |
| `test_validation` | 88 | C5 identical body | same body as tests/page/test_actions.py:test_component_block_type, tests/page/test_page_header.py:test_reading_time_boundaries, tests/test_contrast.py:test_parse_rgba |
| **tests/page/test_rich_er.py** | | | |
| `test_placement_is_deterministic_and_grid_shaped` | 57 | C4 trivial | assert x == x |
| `test_props_are_deterministic` | 220 | C4 trivial | assert x == x |
| **tests/page/test_rich_matrix.py** | | | |
| `test_registered_help_and_fixtures` | 61 | C5 identical body | same body as tests/page/test_rich_checklist.py:test_registered_and_fixtures_render |
| `test_fixture_family_exists` | 78 | C5 identical body | same body as tests/page/test_rich_checklist.py:test_fixture_family_exists, tests/page/test_rich_containers.py:test_fixture_family_exists |
| **tests/page/test_rich_risk.py** | | | |
| `test_registered_and_renders_through_the_page` | 57 | C5 identical body | same body as tests/page/test_rich_stats.py:test_registered_and_renders_through_the_page |
| **tests/page/test_rich_screen_flow.py** | | | |
| `test_spec_faults` | 211 | C5 identical body | same body as tests/page/test_rich_sequence.py:test_spec_faults, tests/page/test_rich_state.py:test_spec_faults |
| `test_status_has_no_inline_start_border` | 613 | C5 identical body | same body as tests/page/test_rich_checklist.py:test_status_has_no_inline_start_border, tests/page/test_rich_timeline.py:test_status_has_no_inline_start_border |
| **tests/page/test_rich_sequence.py** | | | |
| `test_layout_is_deterministic_and_byte_identical` | 80 | C4 trivial | assert x == x |
| `test_spec_faults` | 233 | C5 identical body | same body as tests/page/test_rich_screen_flow.py:test_spec_faults, tests/page/test_rich_state.py:test_spec_faults |
| **tests/page/test_rich_state.py** | | | |
| `test_render_is_deterministic_and_finite` | 150 | C4 trivial | assert x == x |
| `test_spec_faults` | 249 | C5 identical body | same body as tests/page/test_rich_screen_flow.py:test_spec_faults, tests/page/test_rich_sequence.py:test_spec_faults |
| **tests/page/test_rich_stats.py** | | | |
| `test_registered_and_renders_through_the_page` | 47 | C5 identical body | same body as tests/page/test_rich_risk.py:test_registered_and_renders_through_the_page |
| `test_stress_fixture_validates_and_stays_escaped` | 56 | C5 identical body | same body as tests/page/test_rich_callout.py:test_stress_fixture_validates_and_stays_escaped |
| **tests/page/test_rich_timeline.py** | | | |
| `test_registered_and_renders_through_the_page` | 40 | C5 identical body | same body as tests/page/test_rich_callout.py:test_registered_and_renders_through_the_page |
| `test_status_has_no_inline_start_border` | 58 | C5 identical body | same body as tests/page/test_rich_checklist.py:test_status_has_no_inline_start_border, tests/page/test_rich_screen_flow.py:test_status_has_no_inline_start_border |
| **tests/page/test_rich_wireframe.py** | | | |
| `test_one_mistake_gives_one_fault_naming_the_field` | 248 | C5 identical body | same body as tests/page/test_rich_wireframe.py:test_ui_states_one_mistake_gives_one_fault |
| `test_wireframe_is_registered` | 262 | C5 identical body | same body as tests/test_widget_decision_design.py:test_diff_scrolls_and_is_keyboard_reachable |
| `test_ui_states_one_mistake_gives_one_fault` | 307 | C5 identical body | same body as tests/page/test_rich_wireframe.py:test_one_mistake_gives_one_fault_naming_the_field |
| **tests/page/test_wheel_standalone.py** | | | |
| `test_wheel_exports_standalone_page` | 24 | C3 src-text | reads src/tavle text, asserts in/regex |
| **tests/test_block_tables.py** | | | |
| `test_blank_text_and_empty_lists_fault_once` | 103 | C5 identical body | same body as tests/page/test_blocks_charts_diagrams.py:test_blank_text_and_empty_lists_fault_once, tests/page/test_blocks_code_diff.py:test_blank_text_and_empty_lists_fault_once, tests/page/test_blocks_text.py:test_blank_text_faults_once |
| **tests/test_contrast.py** | | | |
| `test_parse_rgba` | 46 | C5 identical body | same body as tests/page/test_actions.py:test_component_block_type, tests/page/test_page_header.py:test_reading_time_boundaries, tests/page/test_rich_diff.py:test_validation |
| **tests/test_lines_parse.py** | | | |
| `test_non_finite_number_rejected` | 180 | C5 identical body | same body as tests/test_lines_parse.py:test_lone_surrogate_rejected |
| `test_lone_surrogate_rejected` | 184 | C5 identical body | same body as tests/test_lines_parse.py:test_non_finite_number_rejected |
| **tests/test_theme_derive_shape.py** | | | |
| `test_shared_defaults_and_coverage` | 9 | C3 src-text | reads src/tavle text, asserts in/regex |
| **tests/test_theme_tokens.py** | | | |
| `test_colour_rejects_css` | 38 | C5 identical body | same body as tests/page/test_pages_comments.py:test_bad_intervals_error |
| **tests/test_theme_validate.py** | | | |
| `test_preset_and_derived_dark_pass` | 13 | C4 no check | no assert/raises/check_ helper |
| **tests/test_widget_decision_design.py** | | | |
| `test_diff_scrolls_and_is_keyboard_reachable` | 15 | C5 identical body | same body as tests/page/test_rich_wireframe.py:test_wireframe_is_registered |
