# Audit: charts (task 5.8, base `4dfadfc`)

- Source (`--only` globs): `tavle.blocks.charts.*`, `tavle.blocks_render.chart*`
- Test files: `tests/page/test_blocks_charts_diagrams.py`, `tests/page/test_rich_chart.py`, `tests/page/test_rich_chart_events.py`, `tests/page/test_blocks_code_diff.py`
- Collected tests: 203 before (77, 41, 21, 64), 288 after (77, 114, 33, 64); 14 of the 288 are `slow`. Test functions: 91 before (11, 28, 20, 32), 123 after (11, 56, 24, 32).
- Mutation score before: 91% (3,754 mutants: 3,419 killed, 333 survived, 1 timeout, 1 segfault), selected from the `blocks` and `blocks_render` baseline copies; package scores in `audit/py-blocks.md` are 80% and 92%.
- Mutation score after: 98% (3,750 mutants: 3,687 killed, 63 survived, 0 timeout, 0 segfault). The run (`/var/tmp/tmp-alec/t5-charts-final.log`, 1,005 s) reported 3,686 killed and 1 segfault: `xǁAxisǁat__mutmut_8` made `test_scatter_event_ends_are_formatted_numbers` run away until the memory cap killed it. That test now carries the signal timeout, and a mutmut rerun of that one mutant in the same copy reports it killed. The 63 survivors are exactly the equivalent and source-defect rows below; the 3,750 total is 4 lower than the baseline because `eb39701` removed lines from `_series_faults`.

## C1 (leave-one-out, baselines `t5-charts-blocks` and `t5-charts-render`)

Grouped first, then per file on the grouped losses only. Each run used `just mutate --without ... --baseline <tag> --only <names>`; logs are `/var/tmp/tmp-alec/t5-charts-c1.log` (blocks grouped), `t5-charts-c1-render.log` (render grouped) and `t5-charts-c1-perfile.log`.

| run | `tavle.blocks.charts.*` lost kills | `tavle.blocks_render.chart*` lost kills |
|---|---|---|
| all four files removed (grouped) | 94 | 815 |
| without `test_blocks_charts_diagrams.py` | 4 | 291 |
| without `test_rich_chart.py` | 86 | 18 |
| without `test_rich_chart_events.py` | 4 | 30 |
| without `test_blocks_code_diff.py` | 0 | 0 |

- The three chart files each hold unique kills, so none is a C1 candidate.
- `test_blocks_code_diff.py` covers no chart mutant: it tests the `code` and `diff` blocks, whose sources are outside this area's globs. It stays; its only static hits are the C5 rows below.
- The per-file runs used the current test files, so the new tests count toward the kills that remain. No base test was removed, so no new kill can have lost its only killer.
- One test added during this task, `test_category_labels_are_cut_thinned_and_clamped_inside`, was dropped while the final run was in progress (the run still included it): it killed 7 baseline survivors, and other tests kill all 7 (in-process check with it excluded), while the base tests still cover every baseline kill. It never existed at `4dfadfc`.

## Decisions

| test id | decision | criterion | evidence |
|---|---|---|---|
| `test_blocks_charts_diagrams.py::test_block_is_client_side_and_bundled` | keep | C5 | `audit/static-scan.md` identical body; parametrized over chart and diagram component names, not code and diff |
| `test_blocks_charts_diagrams.py::test_family_shape_mistake_gets_one_fault_naming_the_field` | keep | C5 | `audit/static-scan.md` identical body; its rows are diagram, flow, state and sequence faults |
| `test_blocks_charts_diagrams.py::test_blank_text_and_empty_lists_fault_once` | keep | C5 | `audit/static-scan.md` identical body; different components and property paths |
| `test_blocks_code_diff.py::test_block_is_client_side_and_bundled` | keep | C5 | `audit/static-scan.md` identical body; its rows are the code and diff components |
| `test_blocks_code_diff.py::test_blank_text_and_empty_lists_fault_once` | keep | C5 | `audit/static-scan.md` identical body; code and diff property paths |
| `test_rich_chart.py::test_label_text_is_small_and_scaled_to_a_fixed_rendered_size` | keep | C3 | reads `static/css` text, but checks a contract between two files: the CSS `--vb-w` must equal `chart_draw.W` and each label class must use the shared font size |
| `test_rich_chart.py::test_the_plot_has_no_width_cap` | keep | C3 | guards a CSS rule no Python test can see (no `max-inline-size` on `.vb-plot`) |
| `test_rich_chart.py::test_validation_names_each_fault` | changed | survivors | now a table of exact `(rule, message)` pairs, one row per fault site; first killer of 55 survivors |
| `test_rich_chart_events.py::test_hatch_lines_are_eight_apart`, `test_rich_chart.py::test_scatter_event_ends_are_formatted_numbers`: `pytest.mark.timeout(2, method="signal")` | added | survivors | under some `_steps` and `Axis.at` mutants these tests run away; the marker turns that into a failure instead of a mutmut timeout or memory kill |
| `test_rich_chart.py::test_nice_ticks_step_follows_the_target` | added | survivors | first killer of 3 survivors (rows below) |
| `test_rich_chart.py::test_tick_decimals_follow_the_step` | added | survivors | first killer of 5 survivors (rows below) |
| `test_rich_chart.py::test_thin_step_keeps_labels_eight_units_apart` | added | survivors | first killer of 8 survivors (rows below) |
| `test_rich_chart.py::test_csv_numbers_keep_a_lower_case_exponent` | added | survivors | first killer of 1 survivor (rows below) |
| `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` | added | survivors | first killer of 14 survivors (rows below) |
| `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` | added | survivors | first killer of 20 survivors (rows below) |
| `test_rich_chart.py::test_scatter_event_ends_are_formatted_numbers` | added | survivors | first killer of 5 survivors (rows below) |
| `test_rich_chart.py::test_copy_quotes_only_cells_with_csv_specials` | added | survivors | first killer of 1 survivor (rows below) |
| `test_rich_chart.py::test_other_faults_name_their_rule` | added | survivors | split from the old validation test: the faults not in the exact table, each with its rule |
| `test_rich_chart.py::test_value_axes_reach_zero_for_bars_and_areas_and_keep_decimals` | added | survivors | first killer of 1 survivor (rows below) |
| `test_rich_chart.py::test_a_chart_with_only_a_right_axis_starts_at_the_left_edge` | added | survivors | first killer of 3 survivors (rows below) |
| `test_rich_chart.py::test_stacks_put_zero_and_small_values_on_the_positive_run` | added | survivors | first killer of 3 survivors (rows below) |
| `test_rich_chart.py::test_bars_keep_a_one_unit_minimum_and_a_minimum_width` | added | survivors | first killer of 2 survivors (rows below) |
| `test_rich_chart.py::test_negative_areas_fill_up_to_zero` | added | survivors | first killer of 2 survivors (rows below) |
| `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` | added | survivors | first killer of 17 survivors (rows below) |
| `test_rich_chart.py::test_end_labels_stack_apart_and_drop_out_when_they_cannot_fit` | added | survivors | first killer of 9 survivors (rows below) |
| `test_rich_chart.py::test_end_labels_need_150_units_of_plot_and_cut_long_names` | added | survivors | first killer of 11 survivors (rows below) |
| `test_rich_chart.py::test_note_labels_keep_six_units_apart_or_are_left_to_the_list` | added | survivors | first killer of 10 survivors (rows below) |
| `test_rich_chart.py::test_end_labels_that_would_run_below_the_plot_are_all_dropped` | added | survivors | first killer of 3 survivors (rows below) |
| `test_rich_chart.py::test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour` | added | survivors | first killer of 12 survivors (rows below) |
| `test_rich_chart.py::test_more_than_24_points_is_dense` | added | survivors | first killer of 2 survivors (rows below) |
| `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` | added | survivors | first killer of 20 survivors (rows below) |
| `test_rich_chart.py::test_horizontal_axis_rows_and_labels` | added | survivors | first killer of 6 survivors (rows below) |
| `test_rich_chart.py::test_scatter_notes_inside_the_x_ticks_draw_a_rule` | added | survivors | first killer of 9 survivors (rows below) |
| `test_rich_chart.py::test_scatter_x_axis_does_not_reach_zero` | added | survivors | first killer of 1 survivor (rows below) |
| `test_rich_chart.py::test_sparkline_spreads_points_or_centres_one` | added | survivors | first killer of 6 survivors (rows below) |
| `test_rich_chart.py::test_donut_arcs_skip_empty_slices_and_flag_large_ones` | added | survivors | first killer of 7 survivors (rows below) |
| `test_rich_chart.py::test_compact_scale_boundaries` | added | survivors | first killer of 4 survivors (rows below) |
| `test_rich_chart_events.py::test_hatch_lines_are_eight_apart` | added | survivors | first killer of 4 survivors (rows below) |
| `test_rich_chart_events.py::test_event_rows_grow_one_per_four_events_up_to_three` | added | survivors | first killer of 6 survivors (rows below) |
| `test_rich_chart_events.py::test_pin_placement` | added | survivors | first killer of 16 survivors (rows below) |
| `test_rich_chart_events.py::test_pins_sit_one_row_apart_and_a_zero_width_band_keeps_one_unit` | added | survivors | first killer of 3 survivors (rows below) |

## Survivors

All 335 non-killed mutants of the baseline (333 survived, 1 timeout, 1 segfault): 269 killed by a fast test, 62 equivalent, 0 slow-only, 3 removed from the source by commit `eb39701`, and 1 that cannot be killed without a source fix (`x_nice_ticks__mutmut_33`, reported to the lead).
"Killed" evidence is the first owned test that failed with the mutant active. These were run in process over `test_rich_chart.py`, `test_rich_chart_events.py` and `test_blocks_charts_diagrams.py` only, against the baseline copies' `mutants/src`, with a 2 s alarm per test. "Case N" is the zero-based parametrize row.
Equivalence notes: several bar and area mutants survive because the axis zero flag is redundant (`_extent` already widens bar and area spans to 0). Seven boundary mutants need an exact float equality that targeted searches never produced; their rows name the search.

| mutant | result | evidence |
|---|---|---|
| `tavle.blocks.charts.x__bool_faults__mutmut_14` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 1) |
| `tavle.blocks.charts.x__bool_faults__mutmut_15` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 1) |
| `tavle.blocks.charts.x__bool_faults__mutmut_18` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 0) |
| `tavle.blocks.charts.x__bool_faults__mutmut_23` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 0) |
| `tavle.blocks.charts.x__bool_faults__mutmut_24` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 0) |
| `tavle.blocks.charts.x__bool_faults__mutmut_39` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 2) |
| `tavle.blocks.charts.x__bool_faults__mutmut_44` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 2) |
| `tavle.blocks.charts.x__bool_faults__mutmut_45` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 2) |
| `tavle.blocks.charts.x__decimals_faults__mutmut_7` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 3) |
| `tavle.blocks.charts.x__decimals_faults__mutmut_8` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 3) |
| `tavle.blocks.charts.x__decimals_faults__mutmut_9` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 4) |
| `tavle.blocks.charts.x__decimals_faults__mutmut_16` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 5) |
| `tavle.blocks.charts.x__labels_faults__mutmut_12` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 7) |
| `tavle.blocks.charts.x__labels_faults__mutmut_17` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 7) |
| `tavle.blocks.charts.x__labels_faults__mutmut_18` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 7) |
| `tavle.blocks.charts.x__values_faults__mutmut_10` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 8) |
| `tavle.blocks.charts.x__values_faults__mutmut_11` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 8) |
| `tavle.blocks.charts.x__values_faults__mutmut_12` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 8) |
| `tavle.blocks.charts.x__values_faults__mutmut_13` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 8) |
| `tavle.blocks.charts.x__values_faults__mutmut_14` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 8) |
| `tavle.blocks.charts.x__values_faults__mutmut_15` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 8) |
| `tavle.blocks.charts.x__values_faults__mutmut_16` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 9) |
| `tavle.blocks.charts.x__values_faults__mutmut_17` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 10) |
| `tavle.blocks.charts.x__values_faults__mutmut_18` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 10) |
| `tavle.blocks.charts.x__values_faults__mutmut_19` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 10) |
| `tavle.blocks.charts.x__values_faults__mutmut_20` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 10) |
| `tavle.blocks.charts.x__values_faults__mutmut_21` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 10) |
| `tavle.blocks.charts.x__values_faults__mutmut_22` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 10) |
| `tavle.blocks.charts.x__values_faults__mutmut_31` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 11) |
| `tavle.blocks.charts.x__values_faults__mutmut_39` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 13) |
| `tavle.blocks.charts.x__values_faults__mutmut_40` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 13) |
| `tavle.blocks.charts.x__values_faults__mutmut_42` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 12) |
| `tavle.blocks.charts.x__values_faults__mutmut_44` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 12) |
| `tavle.blocks.charts.x__scatter_faults__mutmut_5` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 14) |
| `tavle.blocks.charts.x__scatter_faults__mutmut_21` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 15) |
| `tavle.blocks.charts.x__scatter_faults__mutmut_22` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 15) |
| `tavle.blocks.charts.x__scatter_faults__mutmut_23` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 15) |
| `tavle.blocks.charts.x__scatter_faults__mutmut_24` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 15) |
| `tavle.blocks.charts.x__scatter_faults__mutmut_25` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 15) |
| `tavle.blocks.charts.x__scatter_faults__mutmut_26` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 15) |
| `tavle.blocks.charts.x__scatter_faults__mutmut_29` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 16) |
| `tavle.blocks.charts.x__scatter_faults__mutmut_31` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 16) |
| `tavle.blocks.charts.x__combo_faults__mutmut_5` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 18) |
| `tavle.blocks.charts.x__combo_faults__mutmut_12` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 18) |
| `tavle.blocks.charts.x__combo_faults__mutmut_13` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 18) |
| `tavle.blocks.charts.x__one_series_faults__mutmut_5` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 8) |
| `tavle.blocks.charts.x__one_series_faults__mutmut_13` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 17) |
| `tavle.blocks.charts.x__one_series_faults__mutmut_16` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 14) |
| `tavle.blocks.charts.x__one_series_faults__mutmut_24` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 19) |
| `tavle.blocks.charts.x__one_series_faults__mutmut_32` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 18) |
| `tavle.blocks.charts.x__series_faults__mutmut_13` | removed | line removed by commit `eb39701`; the mutant no longer exists |
| `tavle.blocks.charts.x__series_faults__mutmut_19` | removed | line removed by commit `eb39701`; the mutant no longer exists |
| `tavle.blocks.charts.x__series_faults__mutmut_20` | removed | line removed by commit `eb39701`; the mutant no longer exists |
| `tavle.blocks.charts.x__series_faults__mutmut_25` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 20) |
| `tavle.blocks.charts.x__series_faults__mutmut_40` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 21) |
| `tavle.blocks.charts.x__series_faults__mutmut_48` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 8) |
| `tavle.blocks.charts.x__series_faults__mutmut_49` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 8) |
| `tavle.blocks.charts.x__series_faults__mutmut_55` | killed | `test_rich_chart.py::test_validation_names_each_fault` (case 8) |
| `tavle.blocks_render.chart_draw.x_make_axis__mutmut_6` | equivalent | the zero flag is redundant: every caller that passes True already spans 0 (bar and area values are extended to 0 in `_extent`) |
| `tavle.blocks_render.chart_draw.x_make_axis__mutmut_11` | killed | `test_rich_chart.py::test_value_axes_reach_zero_for_bars_and_areas_and_keep_decimals` |
| `tavle.blocks_render.chart_draw.x_make_axis__mutmut_31` | killed | `test_rich_chart.py::test_end_labels_need_150_units_of_plot_and_cut_long_names` |
| `tavle.blocks_render.chart_draw.x__spans__mutmut_21` | killed | `test_rich_chart.py::test_stacks_put_zero_and_small_values_on_the_positive_run` |
| `tavle.blocks_render.chart_draw.x__spans__mutmut_22` | killed | `test_rich_chart.py::test_stacks_put_zero_and_small_values_on_the_positive_run` |
| `tavle.blocks_render.chart_draw.x__extent__mutmut_5` | equivalent | bar and area spans already include 0, so adding 0 again cannot move the extent |
| `tavle.blocks_render.chart_draw.x__extent__mutmut_6` | equivalent | bar and area spans already include 0, so adding 0 again cannot move the extent |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_2` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_3` | killed | `test_rich_chart.py::test_note_labels_keep_six_units_apart_or_are_left_to_the_list` (case 0) |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_4` | killed | `test_rich_chart.py::test_note_labels_keep_six_units_apart_or_are_left_to_the_list` (case 3) |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_5` | killed | `test_rich_chart.py::test_note_labels_keep_six_units_apart_or_are_left_to_the_list` (case 0) |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_12` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_14` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_16` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_18` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_19` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_20` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_21` | equivalent | needs `x - frame.x0 == width / 2 + 4` exactly; an exhaustive search of 18,018 one-note line charts (2 to 40 points, labels 1 to 22 chars) never hit it |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_22` | killed | `test_rich_chart.py::test_note_labels_keep_six_units_apart_or_are_left_to_the_list` (case 1) |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_24` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_25` | killed | `test_rich_chart.py::test_note_labels_keep_six_units_apart_or_are_left_to_the_list` (case 0) |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_29` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_30` | killed | `test_rich_chart.py::test_note_labels_keep_six_units_apart_or_are_left_to_the_list` (case 0) |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_31` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_32` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_33` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_34` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_36` | killed | `test_rich_chart.py::test_note_labels_keep_six_units_apart_or_are_left_to_the_list` (case 0) |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_39` | killed | `test_rich_chart.py::test_note_labels_keep_six_units_apart_or_are_left_to_the_list` (case 4) |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_40` | killed | `test_rich_chart.py::test_note_labels_keep_six_units_apart_or_are_left_to_the_list` (case 0) |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_41` | killed | `test_rich_chart.py::test_note_labels_keep_six_units_apart_or_are_left_to_the_list` (case 5) |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_43` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_45` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__note_texts__mutmut_48` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x__end_labels__mutmut_3` | killed | `test_rich_chart.py::test_end_labels_stack_apart_and_drop_out_when_they_cannot_fit` |
| `tavle.blocks_render.chart_draw.x__end_labels__mutmut_5` | killed | `test_rich_chart.py::test_end_labels_stack_apart_and_drop_out_when_they_cannot_fit` |
| `tavle.blocks_render.chart_draw.x__end_labels__mutmut_10` | killed | `test_rich_chart.py::test_end_labels_stack_apart_and_drop_out_when_they_cannot_fit` |
| `tavle.blocks_render.chart_draw.x__end_labels__mutmut_12` | killed | `test_rich_chart.py::test_end_labels_stack_apart_and_drop_out_when_they_cannot_fit` |
| `tavle.blocks_render.chart_draw.x__end_labels__mutmut_16` | killed | `test_rich_chart.py::test_end_labels_stack_apart_and_drop_out_when_they_cannot_fit` |
| `tavle.blocks_render.chart_draw.x__end_labels__mutmut_23` | killed | `test_rich_chart.py::test_end_labels_that_would_run_below_the_plot_are_all_dropped` (case 0) |
| `tavle.blocks_render.chart_draw.x__end_labels__mutmut_24` | killed | `test_rich_chart.py::test_end_labels_that_would_run_below_the_plot_are_all_dropped` (case 0) |
| `tavle.blocks_render.chart_draw.x__end_labels__mutmut_26` | equivalent | needs the last label at exactly `frame.y1 + 6`; a search of 5,043 two-series charts never hit it |
| `tavle.blocks_render.chart_draw.x__end_labels__mutmut_27` | killed | `test_rich_chart.py::test_end_labels_stack_apart_and_drop_out_when_they_cannot_fit` |
| `tavle.blocks_render.chart_draw.x__end_labels__mutmut_28` | killed | `test_rich_chart.py::test_end_labels_that_would_run_below_the_plot_are_all_dropped` (case 1) |
| `tavle.blocks_render.chart_draw.x__end_labels__mutmut_32` | killed | `test_rich_chart.py::test_end_labels_need_150_units_of_plot_and_cut_long_names` |
| `tavle.blocks_render.chart_draw.x__end_labels__mutmut_33` | killed | `test_rich_chart.py::test_end_labels_need_150_units_of_plot_and_cut_long_names` |
| `tavle.blocks_render.chart_draw.x__end_labels__mutmut_34` | equivalent | `room` is `n * CHAR + 14`, so `(room - 6) / CHAR` and `(room - 7) / CHAR` both floor to `n` |
| `tavle.blocks_render.chart_draw.x__note_xs__mutmut_8` | equivalent | `known` is empty whenever `count` is 0, so both branches return `[]` |
| `tavle.blocks_render.chart_draw.x__category_axes__mutmut_9` | killed | `test_rich_chart.py::test_a_chart_with_only_a_right_axis_starts_at_the_left_edge` |
| `tavle.blocks_render.chart_draw.x__category_axes__mutmut_15` | equivalent | the zero flag only matters when the extent excludes 0; bar and area extents never do |
| `tavle.blocks_render.chart_draw.x__category_axes__mutmut_18` | equivalent | the zero flag only matters when the extent excludes 0; bar and area extents never do |
| `tavle.blocks_render.chart_draw.x__category_axes__mutmut_19` | equivalent | the zero flag only matters when the extent excludes 0; bar and area extents never do |
| `tavle.blocks_render.chart_draw.x__category_axes__mutmut_20` | equivalent | the zero flag only matters when the extent excludes 0; bar and area extents never do |
| `tavle.blocks_render.chart_draw.x__category_axes__mutmut_21` | equivalent | the zero flag only matters when the extent excludes 0; bar and area extents never do |
| `tavle.blocks_render.chart_draw.x__category_axes__mutmut_27` | equivalent | the zero flag only matters when the extent excludes 0; bar and area extents never do |
| `tavle.blocks_render.chart_draw.x__category_axes__mutmut_28` | killed | `test_rich_chart.py::test_end_labels_need_150_units_of_plot_and_cut_long_names` |
| `tavle.blocks_render.chart_draw.x__wants_end_labels__mutmut_7` | killed | `test_rich_chart.py::test_end_labels_stack_apart_and_drop_out_when_they_cannot_fit` |
| `tavle.blocks_render.chart_draw.x__wants_end_labels__mutmut_8` | killed | `test_rich_chart.py::test_end_labels_stack_apart_and_drop_out_when_they_cannot_fit` |
| `tavle.blocks_render.chart_draw.x__wants_end_labels__mutmut_11` | killed | `test_rich_chart.py::test_end_labels_stack_apart_and_drop_out_when_they_cannot_fit` |
| `tavle.blocks_render.chart_draw.x__wants_end_labels__mutmut_12` | equivalent | a right axis exists only on combo charts, which an earlier clause already excludes |
| `tavle.blocks_render.chart_draw.x__wants_end_labels__mutmut_13` | equivalent | a right axis exists only on combo charts, which an earlier clause already excludes |
| `tavle.blocks_render.chart_draw.x__wants_end_labels__mutmut_15` | killed | `test_rich_chart.py::test_end_labels_need_150_units_of_plot_and_cut_long_names` |
| `tavle.blocks_render.chart_draw.x__wants_end_labels__mutmut_16` | killed | `test_rich_chart.py::test_end_labels_need_150_units_of_plot_and_cut_long_names` |
| `tavle.blocks_render.chart_draw.x__wants_end_labels__mutmut_17` | killed | `test_rich_chart.py::test_end_labels_need_150_units_of_plot_and_cut_long_names` |
| `tavle.blocks_render.chart_draw.x__wants_end_labels__mutmut_18` | killed | `test_rich_chart.py::test_end_labels_need_150_units_of_plot_and_cut_long_names` |
| `tavle.blocks_render.chart_draw.x__wants_end_labels__mutmut_19` | killed | `test_rich_chart.py::test_end_labels_need_150_units_of_plot_and_cut_long_names` |
| `tavle.blocks_render.chart_draw.x__wants_end_labels__mutmut_20` | killed | `test_rich_chart.py::test_end_labels_need_150_units_of_plot_and_cut_long_names` |
| `tavle.blocks_render.chart_draw.x__line_marks__mutmut_22` | killed | `test_rich_chart.py::test_negative_areas_fill_up_to_zero` |
| `tavle.blocks_render.chart_draw.x__line_marks__mutmut_23` | killed | `test_rich_chart.py::test_negative_areas_fill_up_to_zero` |
| `tavle.blocks_render.chart_draw.x__series_marks__mutmut_22` | killed | `test_rich_chart.py::test_bars_keep_a_one_unit_minimum_and_a_minimum_width` |
| `tavle.blocks_render.chart_draw.x_categorical__mutmut_17` | killed | `test_rich_chart.py::test_note_labels_take_two_rows_and_shift_the_plot_down` |
| `tavle.blocks_render.chart_draw.x_categorical__mutmut_29` | killed | `test_rich_chart.py::test_a_chart_with_only_a_right_axis_starts_at_the_left_edge` |
| `tavle.blocks_render.chart_draw.x_categorical__mutmut_37` | killed | `test_rich_chart.py::test_a_chart_with_only_a_right_axis_starts_at_the_left_edge` |
| `tavle.blocks_render.chart_draw.x_categorical__mutmut_57` | killed | `test_rich_chart.py::test_end_labels_need_150_units_of_plot_and_cut_long_names` |
| `tavle.blocks_render.chart_draw.x_categorical__mutmut_89` | killed | `test_rich_chart.py::test_stacks_put_zero_and_small_values_on_the_positive_run` |
| `tavle.blocks_render.chart_draw.x_categorical__mutmut_156` | killed | `test_rich_chart.py::test_more_than_24_points_is_dense` |
| `tavle.blocks_render.chart_draw.x__category_events__mutmut_26` | equivalent | `x1` of a marker (no `end`) is never read: markers draw at `x0` |
| `tavle.blocks_render.chart_draw.x__category_events__mutmut_28` | equivalent | `x1` of a marker (no `end`) is never read: markers draw at `x0` |
| `tavle.blocks_render.chart_draw.x__category_events__mutmut_33` | equivalent | `draw_events` returns `[]` for empty spans |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_6` | killed | `test_rich_chart.py::test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour` (case 0) |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_8` | killed | `test_rich_chart.py::test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour` (case 0) |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_19` | equivalent | the first label skips the overlap check (`out` is empty), and later checks use the updated reach |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_25` | killed | `test_rich_chart.py::test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour` (case 0) |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_29` | killed | `test_rich_chart.py::test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour` (case 0) |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_30` | killed | `test_rich_chart.py::test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour` (case 0) |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_32` | killed | `test_rich_chart.py::test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour` (case 0) |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_46` | killed | `test_rich_chart.py::test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour` (case 0) |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_48` | killed | `test_rich_chart.py::test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour` (case 1) |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_49` | equivalent | needs `x - half == reach + 4` exactly; a search of 20,000 random bar charts never hit it |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_50` | killed | `test_rich_chart.py::test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour` (case 1) |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_51` | killed | `test_rich_chart.py::test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour` (case 2) |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_52` | killed | `test_rich_chart.py::test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour` (case 1) |
| `tavle.blocks_render.chart_draw.x__category_labels__mutmut_54` | killed | `test_rich_chart.py::test_thinned_labels_skip_any_that_clamping_pushes_onto_a_neighbour` (case 1) |
| `tavle.blocks_render.chart_draw.x__bars__mutmut_23` | equivalent | needs a bar exactly 1.0 unit tall; a search of tick-aligned values at 1 to 8 decimals never hit it |
| `tavle.blocks_render.chart_draw.x__bars__mutmut_24` | killed | `test_rich_chart.py::test_bars_keep_a_one_unit_minimum_and_a_minimum_width` |
| `tavle.blocks_render.chart_draw.x__hbar_rows__mutmut_10` | killed | `test_rich_chart.py::test_horizontal_axis_rows_and_labels` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_2` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_3` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_4` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_10` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_13` | killed | `test_rich_chart.py::test_horizontal_axis_rows_and_labels` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_26` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_29` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_35` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_36` | equivalent | needs a bar exactly 1.0 unit wide; a search of tick-aligned values at 1 to 8 decimals never hit it |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_37` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_38` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_39` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_41` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_42` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_43` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_45` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x__hbar_marks__mutmut_52` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x_horizontal_bars__mutmut_2` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x_horizontal_bars__mutmut_3` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x_horizontal_bars__mutmut_4` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x_horizontal_bars__mutmut_11` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x_horizontal_bars__mutmut_12` | killed | `test_rich_chart.py::test_horizontal_bars_stack_or_group_per_row` |
| `tavle.blocks_render.chart_draw.x_horizontal_bars__mutmut_21` | killed | `test_rich_chart.py::test_horizontal_axis_rows_and_labels` |
| `tavle.blocks_render.chart_draw.x_horizontal_bars__mutmut_34` | killed | `test_rich_chart.py::test_horizontal_axis_rows_and_labels` |
| `tavle.blocks_render.chart_draw.x_horizontal_bars__mutmut_59` | equivalent | horizontal bar spans already include 0, so the zero flag changes nothing |
| `tavle.blocks_render.chart_draw.x_horizontal_bars__mutmut_60` | killed | `test_rich_chart.py::test_horizontal_axis_rows_and_labels` |
| `tavle.blocks_render.chart_draw.x_horizontal_bars__mutmut_67` | equivalent | horizontal bar spans already include 0, so the zero flag changes nothing |
| `tavle.blocks_render.chart_draw.x_horizontal_bars__mutmut_75` | killed | `test_rich_chart.py::test_horizontal_axis_rows_and_labels` |
| `tavle.blocks_render.chart_draw.x_horizontal_bars__mutmut_108` | killed | `test_rich_chart.py::test_more_than_24_points_is_dense` |
| `tavle.blocks_render.chart_draw.x__scatter_dots__mutmut_5` | equivalent | validation makes `xs` and `values` the same length, so `strict` never fires |
| `tavle.blocks_render.chart_draw.x__scatter_dots__mutmut_8` | equivalent | validation makes `xs` and `values` the same length, so `strict` never fires |
| `tavle.blocks_render.chart_draw.x__scatter_dots__mutmut_9` | equivalent | validation makes `xs` and `values` the same length, so `strict` never fires |
| `tavle.blocks_render.chart_draw.x__scatter_notes__mutmut_3` | killed | `test_rich_chart.py::test_scatter_notes_inside_the_x_ticks_draw_a_rule` |
| `tavle.blocks_render.chart_draw.x__scatter_notes__mutmut_4` | killed | `test_rich_chart.py::test_scatter_notes_inside_the_x_ticks_draw_a_rule` |
| `tavle.blocks_render.chart_draw.x__scatter_notes__mutmut_5` | killed | `test_rich_chart.py::test_scatter_notes_inside_the_x_ticks_draw_a_rule` |
| `tavle.blocks_render.chart_draw.x__scatter_notes__mutmut_6` | killed | `test_rich_chart.py::test_scatter_notes_inside_the_x_ticks_draw_a_rule` |
| `tavle.blocks_render.chart_draw.x__scatter_notes__mutmut_7` | killed | `test_rich_chart.py::test_scatter_notes_inside_the_x_ticks_draw_a_rule` |
| `tavle.blocks_render.chart_draw.x__scatter_notes__mutmut_19` | killed | `test_rich_chart.py::test_scatter_notes_inside_the_x_ticks_draw_a_rule` |
| `tavle.blocks_render.chart_draw.x_scatter__mutmut_8` | killed | `test_rich_chart.py::test_scatter_notes_inside_the_x_ticks_draw_a_rule` |
| `tavle.blocks_render.chart_draw.x_scatter__mutmut_15` | killed | `test_rich_chart.py::test_scatter_notes_inside_the_x_ticks_draw_a_rule` |
| `tavle.blocks_render.chart_draw.x_scatter__mutmut_21` | equivalent | `None` is falsy like `False` in `make_axis` |
| `tavle.blocks_render.chart_draw.x_scatter__mutmut_22` | killed | `test_rich_chart.py::test_scatter_notes_inside_the_x_ticks_draw_a_rule` |
| `tavle.blocks_render.chart_draw.x_scatter__mutmut_41` | equivalent | `None` is falsy like `False` in `make_axis` |
| `tavle.blocks_render.chart_draw.x_scatter__mutmut_52` | killed | `test_rich_chart.py::test_scatter_x_axis_does_not_reach_zero` |
| `tavle.blocks_render.chart_draw.x_scatter__mutmut_56` | equivalent | scatter never reads `frame.y0`; it uses `top` directly |
| `tavle.blocks_render.chart_draw.x__value_events__mutmut_13` | equivalent | `draw_events` returns `[]` for empty spans |
| `tavle.blocks_render.chart_draw.x_sparkline__mutmut_37` | killed | `test_rich_chart.py::test_sparkline_spreads_points_or_centres_one` |
| `tavle.blocks_render.chart_draw.x_sparkline__mutmut_40` | killed | `test_rich_chart.py::test_sparkline_spreads_points_or_centres_one` |
| `tavle.blocks_render.chart_draw.x_sparkline__mutmut_43` | killed | `test_rich_chart.py::test_sparkline_spreads_points_or_centres_one` |
| `tavle.blocks_render.chart_draw.x_sparkline__mutmut_44` | killed | `test_rich_chart.py::test_sparkline_spreads_points_or_centres_one` |
| `tavle.blocks_render.chart_draw.x_sparkline__mutmut_45` | killed | `test_rich_chart.py::test_sparkline_spreads_points_or_centres_one` |
| `tavle.blocks_render.chart_draw.x_sparkline__mutmut_46` | killed | `test_rich_chart.py::test_sparkline_spreads_points_or_centres_one` |
| `tavle.blocks_render.chart_draw.x_donut__mutmut_18` | killed | `test_rich_chart.py::test_donut_arcs_skip_empty_slices_and_flag_large_ones` |
| `tavle.blocks_render.chart_draw.x_donut__mutmut_21` | killed | `test_rich_chart.py::test_donut_arcs_skip_empty_slices_and_flag_large_ones` |
| `tavle.blocks_render.chart_draw.x_donut__mutmut_24` | killed | `test_rich_chart.py::test_donut_arcs_skip_empty_slices_and_flag_large_ones` |
| `tavle.blocks_render.chart_draw.x_donut__mutmut_32` | equivalent | share is at most 1; for a single full slice the arc end moves by under 0.0001 units, below the one-decimal output |
| `tavle.blocks_render.chart_draw.x_donut__mutmut_38` | killed | `test_rich_chart.py::test_donut_arcs_skip_empty_slices_and_flag_large_ones` |
| `tavle.blocks_render.chart_draw.x_donut__mutmut_40` | killed | `test_rich_chart.py::test_donut_arcs_skip_empty_slices_and_flag_large_ones` |
| `tavle.blocks_render.chart_draw.x_donut__mutmut_41` | killed | `test_rich_chart.py::test_donut_arcs_skip_empty_slices_and_flag_large_ones` |
| `tavle.blocks_render.chart_draw.x_donut__mutmut_92` | killed | `test_rich_chart.py::test_donut_arcs_skip_empty_slices_and_flag_large_ones` |
| `tavle.blocks_render.chart_draw.x_donut__mutmut_153` | equivalent | needs `cos(mid) == 0.2` exactly; no slice pair up to 149:149 produces it |
| `tavle.blocks_render.chart_draw.x_donut__mutmut_160` | equivalent | needs `cos(mid) == -0.2` exactly; no slice pair up to 149:149 produces it |
| `tavle.blocks_render.chart_draw.x_donut__mutmut_206` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.charts.x__heading__mutmut_4` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_scale.x_fmt__mutmut_8` | equivalent | fixed-point numbers never contain `X`, so stripping it changes nothing |
| `tavle.blocks_render.chart_scale.x_fmt__mutmut_9` | equivalent | fixed-point numbers never contain `X`, so stripping it changes nothing |
| `tavle.blocks_render.chart_scale.x_fmt__mutmut_15` | equivalent | fixed-point text keeps a digit after stripping, so the empty fallback is unreachable |
| `tavle.blocks_render.chart_scale.x_raw__mutmut_6` | killed | `test_rich_chart.py::test_csv_numbers_keep_a_lower_case_exponent` |
| `tavle.blocks_render.chart_scale.x_compact__mutmut_4` | killed | `test_rich_chart.py::test_compact_scale_boundaries` (case 5) |
| `tavle.blocks_render.chart_scale.x_compact__mutmut_7` | killed | `test_rich_chart.py::test_compact_scale_boundaries` (case 1) |
| `tavle.blocks_render.chart_scale.x_compact__mutmut_19` | killed | `test_rich_chart.py::test_compact_scale_boundaries` (case 3) |
| `tavle.blocks_render.chart_scale.x_compact__mutmut_23` | equivalent | drops `fmt`'s second argument, whose default is the same `None` |
| `tavle.blocks_render.chart_scale.x_compact__mutmut_28` | killed | `test_rich_chart.py::test_compact_scale_boundaries` (case 2) |
| `tavle.blocks_render.chart_scale.x__step_for__mutmut_7` | killed | `test_rich_chart.py::test_nice_ticks_step_follows_the_target` (case 0) |
| `tavle.blocks_render.chart_scale.x__step_for__mutmut_13` | killed | `test_rich_chart.py::test_nice_ticks_step_follows_the_target` (case 0) |
| `tavle.blocks_render.chart_scale.x__step_for__mutmut_20` | equivalent | unreachable: `magnitude` is `10 ** floor(log10(raw_step))`, so the loop returns by factor 10 |
| `tavle.blocks_render.chart_scale.x__step_for__mutmut_21` | equivalent | unreachable: `magnitude` is `10 ** floor(log10(raw_step))`, so the loop returns by factor 10 |
| `tavle.blocks_render.chart_scale.x_nice_ticks__mutmut_8` | killed | `test_rich_chart.py::test_nice_ticks_step_follows_the_target` (case 2) |
| `tavle.blocks_render.chart_scale.x_nice_ticks__mutmut_33` | survived | not killable without a source fix: the input that reaches it (values `[0, 1e-12]`) raises `ValueError` in `tick_decimals` (`log10(0)`); reported to the lead |
| `tavle.blocks_render.chart_scale.x_tick_decimals__mutmut_1` | killed | `test_rich_chart.py::test_tick_decimals_follow_the_step` (case 1) |
| `tavle.blocks_render.chart_scale.x_tick_decimals__mutmut_2` | killed | `test_rich_chart.py::test_tick_decimals_follow_the_step` (case 1) |
| `tavle.blocks_render.chart_scale.x_tick_decimals__mutmut_3` | killed | `test_rich_chart.py::test_tick_decimals_follow_the_step` (case 0) |
| `tavle.blocks_render.chart_scale.x_tick_decimals__mutmut_18` | killed | `test_rich_chart.py::test_tick_decimals_follow_the_step` (case 3) |
| `tavle.blocks_render.chart_scale.x_tick_decimals__mutmut_21` | killed | `test_rich_chart.py::test_tick_decimals_follow_the_step` (case 2) |
| `tavle.blocks_render.chart_scale.x_thin_step__mutmut_1` | killed | `test_rich_chart.py::test_thin_step_keeps_labels_eight_units_apart` (case 0) |
| `tavle.blocks_render.chart_scale.x_thin_step__mutmut_2` | killed | `test_rich_chart.py::test_thin_step_keeps_labels_eight_units_apart` (case 0) |
| `tavle.blocks_render.chart_scale.x_thin_step__mutmut_3` | killed | `test_rich_chart.py::test_thin_step_keeps_labels_eight_units_apart` (case 1) |
| `tavle.blocks_render.chart_scale.x_thin_step__mutmut_4` | killed | `test_rich_chart.py::test_thin_step_keeps_labels_eight_units_apart` (case 2) |
| `tavle.blocks_render.chart_scale.x_thin_step__mutmut_5` | killed | `test_rich_chart.py::test_thin_step_keeps_labels_eight_units_apart` (case 3) |
| `tavle.blocks_render.chart_scale.x_thin_step__mutmut_6` | killed | `test_rich_chart.py::test_thin_step_keeps_labels_eight_units_apart` (case 0) |
| `tavle.blocks_render.chart_scale.x_thin_step__mutmut_14` | killed | `test_rich_chart.py::test_thin_step_keeps_labels_eight_units_apart` (case 1) |
| `tavle.blocks_render.chart_scale.x_thin_step__mutmut_15` | killed | `test_rich_chart.py::test_thin_step_keeps_labels_eight_units_apart` (case 3) |
| `tavle.blocks_render.chart_model.x__kind_of__mutmut_5` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x__kind_of__mutmut_9` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x__kind_of__mutmut_10` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x__kind_of__mutmut_15` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x__kind_of__mutmut_16` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x__kind_of__mutmut_17` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x__kind_of__mutmut_21` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x__kind_of__mutmut_22` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x__kind_of__mutmut_23` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x__kind_of__mutmut_24` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x__series_of__mutmut_55` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x__series_of__mutmut_56` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x__series_of__mutmut_64` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x__series_of__mutmut_65` | killed | `test_rich_chart.py::test_series_kinds_follow_the_chart_kind` |
| `tavle.blocks_render.chart_model.x_build_model__mutmut_34` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_build_model__mutmut_35` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_build_model__mutmut_36` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_build_model__mutmut_37` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_build_model__mutmut_43` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_build_model__mutmut_64` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_build_model__mutmut_66` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_build_model__mutmut_69` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_build_model__mutmut_70` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_build_model__mutmut_95` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_build_model__mutmut_96` | equivalent | validation rejects non-integer `decimals`, so the `isinstance` test is always true |
| `tavle.blocks_render.chart_model.x_show__mutmut_2` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_show__mutmut_4` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_point_label__mutmut_6` | equivalent | validation makes each series as long as the labels, so `i < len(model.labels)` always holds |
| `tavle.blocks_render.chart_model.x_point_label__mutmut_7` | equivalent | validation makes each series as long as the labels, so `i < len(model.labels)` always holds |
| `tavle.blocks_render.chart_model.x_point_label__mutmut_8` | equivalent | validation makes each series as long as the labels, so `i < len(model.labels)` always holds |
| `tavle.blocks_render.chart_model.x_point_label__mutmut_9` | equivalent | validation makes each series as long as the labels, so `i < len(model.labels)` always holds |
| `tavle.blocks_render.chart_model.x_point_label__mutmut_10` | equivalent | validation makes each series as long as the labels, so `i < len(model.labels)` always holds |
| `tavle.blocks_render.chart_model.x_position__mutmut_1` | equivalent | on non-scatter charts event ends are label strings, so `or` and `and` take the same branch |
| `tavle.blocks_render.chart_model.x_position__mutmut_2` | killed | `test_rich_chart.py::test_scatter_event_ends_are_formatted_numbers` |
| `tavle.blocks_render.chart_model.x_position__mutmut_3` | killed | `test_rich_chart.py::test_scatter_event_ends_are_formatted_numbers` |
| `tavle.blocks_render.chart_model.x_position__mutmut_4` | killed | `test_rich_chart.py::test_scatter_event_ends_are_formatted_numbers` |
| `tavle.blocks_render.chart_model.x_summary__mutmut_4` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_summary__mutmut_6` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_summary__mutmut_9` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_summary__mutmut_11` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_summary__mutmut_40` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x_summary__mutmut_43` | killed | `test_rich_chart.py::test_decimals_title_and_heading_reach_the_text_forms` |
| `tavle.blocks_render.chart_model.x__csv_cell__mutmut_3` | killed | `test_rich_chart.py::test_copy_quotes_only_cells_with_csv_specials` |
| `tavle.blocks_render.chart_model.x_csv_rows__mutmut_17` | equivalent | validation makes `xs` and `values` the same length, so `strict` never fires |
| `tavle.blocks_render.chart_model.x_csv_rows__mutmut_20` | equivalent | validation makes `xs` and `values` the same length, so `strict` never fires |
| `tavle.blocks_render.chart_model.x_csv_rows__mutmut_21` | equivalent | validation makes `xs` and `values` the same length, so `strict` never fires |
| `tavle.blocks_render.chart_events.x_rows_for__mutmut_1` | equivalent | for count 0 the else branch gives `min(3, 1 + (-1) // 4) == 0`, the same as the guard |
| `tavle.blocks_render.chart_events.x_rows_for__mutmut_5` | killed | `test_rich_chart_events.py::test_event_rows_grow_one_per_four_events_up_to_three` |
| `tavle.blocks_render.chart_events.x_rows_for__mutmut_10` | killed | `test_rich_chart_events.py::test_event_rows_grow_one_per_four_events_up_to_three` |
| `tavle.blocks_render.chart_events.x_rows_for__mutmut_13` | killed | `test_rich_chart_events.py::test_event_rows_grow_one_per_four_events_up_to_three` |
| `tavle.blocks_render.chart_events.x_rows_for__mutmut_14` | killed | `test_rich_chart_events.py::test_event_rows_grow_one_per_four_events_up_to_three` |
| `tavle.blocks_render.chart_events.x_rows_for__mutmut_15` | killed | `test_rich_chart_events.py::test_event_rows_grow_one_per_four_events_up_to_three` |
| `tavle.blocks_render.chart_events.x_events_top__mutmut_7` | killed | `test_rich_chart_events.py::test_event_rows_grow_one_per_four_events_up_to_three` |
| `tavle.blocks_render.chart_events.x__diagonal_runs__mutmut_4` | equivalent | the extra run at `c == w` has `ta >= tb` and draws nothing |
| `tavle.blocks_render.chart_events.x__diagonal_runs__mutmut_10` | killed | `test_rich_chart_events.py::test_hatch_lines_are_eight_apart` (case 0) |
| `tavle.blocks_render.chart_events.x__diagonal_runs__mutmut_17` | killed | `test_rich_chart_events.py::test_hatch_lines_are_eight_apart` (case 0) |
| `tavle.blocks_render.chart_events.x__diagonal_runs__mutmut_19` | killed | `test_rich_chart.py::test_scatter_event_ends_are_formatted_numbers` |
| `tavle.blocks_render.chart_events.x__diagonal_runs__mutmut_20` | killed | `test_rich_chart.py::test_scatter_event_ends_are_formatted_numbers` |
| `tavle.blocks_render.chart_events.x_hatch_path__mutmut_14` | equivalent | styles come from `HATCH`, all single characters other than `X`, so the padded string matches the same styles |
| `tavle.blocks_render.chart_events.x_hatch_path__mutmut_16` | equivalent | `d` is still empty when this block runs, so `=` and `+=` agree |
| `tavle.blocks_render.chart_events.x_hatch_path__mutmut_25` | equivalent | styles come from `HATCH`, all single characters other than `X`, so the padded string matches the same styles |
| `tavle.blocks_render.chart_events.x_hatch_path__mutmut_36` | equivalent | `d` is empty for every style that reaches this block, so `=` and `+=` agree |
| `tavle.blocks_render.chart_events.x_hatch_path__mutmut_49` | equivalent | `d` is empty for every style that reaches this block, so `=` and `+=` agree |
| `tavle.blocks_render.chart_events.x_hatch_path__mutmut_58` | killed | `test_rich_chart_events.py::test_hatch_lines_are_eight_apart` (case 4) |
| `tavle.blocks_render.chart_events.x_hatch_path__mutmut_59` | killed | `test_rich_chart_events.py::test_hatch_lines_are_eight_apart` (case 4) |
| `tavle.blocks_render.chart_events.x__steps__mutmut_8` | equivalent | with non-negative coordinates the count only grows, and the `< stop` filter drops the extra steps |
| `tavle.blocks_render.chart_events.x__steps__mutmut_9` | equivalent | with non-negative coordinates the count only grows, and the `< stop` filter drops the extra steps |
| `tavle.blocks_render.chart_events.x__steps__mutmut_10` | equivalent | with non-negative coordinates the count only grows, and the `< stop` filter drops the extra steps |
| `tavle.blocks_render.chart_events.x__steps__mutmut_11` | equivalent | with non-negative coordinates the count only grows, and the `< stop` filter drops the extra steps |
| `tavle.blocks_render.chart_events.x_place_pins__mutmut_7` | equivalent | a pin x is at least `left + half`, so an untouched row passes `x - half >= end + 4` with either start |
| `tavle.blocks_render.chart_events.x_place_pins__mutmut_28` | killed | `test_rich_chart_events.py::test_pin_placement` (case 0) |
| `tavle.blocks_render.chart_events.x_place_pins__mutmut_29` | killed | `test_rich_chart_events.py::test_pin_placement` (case 3) |
| `tavle.blocks_render.chart_events.x_place_pins__mutmut_37` | killed | `test_rich_chart_events.py::test_pin_placement` (case 0) |
| `tavle.blocks_render.chart_events.x__fit__mutmut_5` | killed | `test_rich_chart_events.py::test_pin_placement` (case 3) |
| `tavle.blocks_render.chart_events.x__fit__mutmut_8` | killed | `test_rich_chart_events.py::test_pin_placement` (case 3) |
| `tavle.blocks_render.chart_events.x__fit__mutmut_9` | killed | `test_rich_chart_events.py::test_pin_placement` (case 3) |
| `tavle.blocks_render.chart_events.x__fit__mutmut_12` | killed | `test_rich_chart_events.py::test_pin_placement` (case 2) |
| `tavle.blocks_render.chart_events.x__fit__mutmut_13` | killed | `test_rich_chart_events.py::test_pin_placement` (case 2) |
| `tavle.blocks_render.chart_events.x__fit__mutmut_14` | killed | `test_rich_chart_events.py::test_pin_placement` (case 2) |
| `tavle.blocks_render.chart_events.x__fit__mutmut_15` | killed | `test_rich_chart_events.py::test_pin_placement` (case 2) |
| `tavle.blocks_render.chart_events.x__fit__mutmut_18` | killed | `test_rich_chart_events.py::test_pin_placement` (case 0) |
| `tavle.blocks_render.chart_events.x__fit__mutmut_35` | killed | `test_rich_chart_events.py::test_pin_placement` (case 4) |
| `tavle.blocks_render.chart_events.x__fit__mutmut_37` | killed | `test_rich_chart_events.py::test_pin_placement` (case 4) |
| `tavle.blocks_render.chart_events.x__fit__mutmut_50` | killed | `test_rich_chart_events.py::test_pin_placement` (case 4) |
| `tavle.blocks_render.chart_events.x__fit__mutmut_57` | killed | `test_rich_chart_events.py::test_pin_placement` (case 4) |
| `tavle.blocks_render.chart_events.x__fit__mutmut_61` | killed | `test_rich_chart_events.py::test_pin_placement` (case 4) |
| `tavle.blocks_render.chart_events.x__band__mutmut_6` | killed | `test_rich_chart_events.py::test_pins_sit_one_row_apart_and_a_zero_width_band_keeps_one_unit` |
| `tavle.blocks_render.chart_events.x__band__mutmut_7` | killed | `test_rich_chart_events.py::test_pins_sit_one_row_apart_and_a_zero_width_band_keeps_one_unit` |
| `tavle.blocks_render.chart_events.x__pin__mutmut_3` | killed | `test_rich_chart_events.py::test_pins_sit_one_row_apart_and_a_zero_width_band_keeps_one_unit` |
