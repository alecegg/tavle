# Audit: inputs-a (task 5.6, base `d585610`)

- Source (`--only` globs): `tavle.blocks.inputs*`
- Test files: `tests/page/test_blocks_inputs.py`, `tests/page/test_extract_inputs.py`, `tests/page/test_blocks_interactive.py`
- Collected tests (file order as above): 176 before (86, 80, 10), 206 after (111, 87, 8). Test functions: 33 before (12, 11, 10), 36 after (13, 15, 8).
- Mutation score before: 78% (773 mutants: 610 killed, 163 survived, 0 timeout; `audit/py-blocks.md`)
- Mutation score after: 99% (773 mutants: 770 killed, 3 survived, 0 timeout)

## C1 (leave-one-out, baseline `inputs-a-base`, a copy of `blocks`)

The test edits were made first, so each single-file run judges against the edited versions of the other files.

| `--without` | lost kills |
|---|---|
| the three files together | 112 |
| `test_blocks_inputs.py`, on those 112 | 47, so not a candidate |
| `test_extract_inputs.py`, on those 112 | 62, so not a candidate |
| `test_blocks_interactive.py`, on those 112 | none |

Three mutants are lost only by the joint run (`x__field_json_bound__mutmut_32`, `x__maxlength_faults__mutmut_7`, `x__items_faults__mutmut_46`): both inputs files kill them.
`test_blocks_interactive.py` kills no `tavle.blocks.inputs*` mutant that another file does not. It tests the served page and the widgets, so its remaining tests have keep rows below.
Mode was per file; no test was removed on C1 evidence.

## Decisions

| test id | decision | criterion | evidence |
|---|---|---|---|
| `test_blocks_inputs.py::test_block_is_client_side_and_bundled` | delete | C5 | bundled: `test_components_contract.py::test_every_block_but_page_statements_is_a_bundled_component`; `props`: `test_fixture_inputs_still_produce_the_recorded_props`; `answer_schema`: the `validate_answer` calls of `test_extract_inputs.py` need it for all five blocks |
| `test_blocks_inputs.py::test_each_example_is_valid` | delete | C5 | `test_extract_blocks_schema.py::test_every_component_example_is_one_valid_statement_that_renders` makes the same `check` of every example |
| `test_blocks_interactive.py::test_blocks_script_served_with_parent_csp` | delete | C5 | `test_pages_server.py::test_static_assets_and_headers` requests `blocks.js` and asserts status, a JavaScript type, a body and the exact security headers (CSP and `nosniff`) |
| `test_blocks_interactive.py::test_flow_pans_zooms_and_highlights` | delete | C5 | `test_rich_flow.py::test_interact_select_highlights_dependencies_and_reads_them_out` and `::test_interact_pan_zoom_and_fit` assert the same selection, highlight, release, zoom and fit facts |
| `test_extract_inputs.py::test_choice_form_comment_answer_accepts`, row `("ship", "approved", "")` | delete row | C5 | same call as a row of `test_answers.py::test_validate_answer_accepts_what_the_component_offers` |
| `test_extract_inputs.py::test_ordered_answer_rejects`, rows `("conf", 11)`, `("conf", 3)`, `("conf", nan)` | delete rows | C5 | same calls in `test_slider_rejections_name_the_range_or_the_step`, which also checks the message |
| `test_extract_inputs.py::test_choice_form_comment_answer_rejects`, the `setup` rows | merge into `test_form_answer_rejection_says_why` | C5 | same calls; the new test asserts the whole message |
| `test_extract_inputs.py::test_ordered_answer_accepts`, `::test_choice_form_comment_answer_accepts` | changed | C4 | assert the `None` result |
| `test_extract_inputs.py::test_choice_form_comment_answer_accepts` | changed | survivors | adds the number field's two limits |
| `test_extract_inputs.py::test_form_answer_rejection_says_why` | added | survivors | exact `ValueError` text per form mistake |
| `test_extract_inputs.py::test_a_free_answer_is_bounded_text` | added | survivors | `allowed_value` length and list limits |
| `test_extract_inputs.py::test_a_value_within_float_tolerance_of_a_step_is_on_it`, `::test_slider_value_check_refuses_a_non_finite_number` | added | survivors | `check_slider_value` tolerance and message |
| `test_blocks_inputs.py::test_a_property_mistake_gets_one_fault_naming_the_field`, rows only the widget sees | moved to `test_a_widget_fault_names_the_rule_and_the_place` | survivors | same props; the new test asserts every rule and message |
| `test_blocks_inputs.py::test_a_property_mistake_gets_one_fault_naming_the_field` | changed | survivors | three wrong-type values are now ones a widget check could walk (`"aa"`, `5`) |
| `test_blocks_inputs.py::test_props_exactly_at_a_limit_are_valid` | added | survivors | each limit's accepting side |
| `test_blocks_inputs.py::test_an_option_list_is_a_required_non_empty_list_of_anything` | added | survivors | calls `option_list` at test time (specs call it at import, which mutation testing does not judge) |
| `test_blocks_inputs.py::test_a_property_mistake_gets_one_fault_naming_the_field` | keep | C5 | static identical-body hit with a test that checks other blocks |
| `test_blocks_interactive.py::test_shell_has_script_tag_and_no_inline_script` | keep | C1 | guards the no-inline-script contract of the page |
| `test_blocks_interactive.py::test_script_uses_no_eval_network_or_html_injection` | keep | C1 | security contract of the served script |
| `test_blocks_interactive.py::test_rendered_html_carries_widget_hooks` | keep | C1 | published `data-mithril` hooks the scripts mount on |
| `test_blocks_interactive.py`, the five `slow` tests left | keep | C2-C5 | Chromium behaviour (table sort and filter, state tabs, chart readout, 390px width, live update); no matrix check asserts the same fact in the same mode |

## Survivors

Every mutant that `audit/py-blocks.md` records as not killed for this area.
Each `killed` row names the first test of the three owned files that fails with that mutant active.
The five `x_option_list` mutants break import, so they were switched on after test collection, as in a mutmut run.
No mutant is `slow-only`.

| mutant | outcome | evidence |
|---|---|---|
| tavle.blocks.inputs.x_option_list__mutmut_1 | killed | `test_blocks_inputs.py::test_statements_render_hosts_with_their_source_as_fallback` |
| tavle.blocks.inputs.x_option_list__mutmut_2 | killed | `test_blocks_inputs.py::test_an_option_list_is_a_required_non_empty_list_of_anything` |
| tavle.blocks.inputs.x_option_list__mutmut_3 | killed | `test_blocks_inputs.py::test_a_property_mistake_gets_one_fault_naming_the_field[choice-props7-options]` |
| tavle.blocks.inputs.x_option_list__mutmut_4 | killed | `test_blocks_inputs.py::test_an_option_list_is_a_required_non_empty_list_of_anything` |
| tavle.blocks.inputs.x_option_list__mutmut_5 | killed | `test_blocks_inputs.py::test_a_property_mistake_gets_one_fault_naming_the_field[choice-props36-options]` |
| tavle.blocks.inputs.x_option_list__mutmut_6 | killed | `test_blocks_inputs.py::test_an_option_list_is_a_required_non_empty_list_of_anything` |
| tavle.blocks.inputs.x_option_list__mutmut_7 | killed | `test_blocks_inputs.py::test_an_option_list_is_a_required_non_empty_list_of_anything` |
| tavle.blocks.inputs.x_option_list__mutmut_8 | killed | `test_blocks_inputs.py::test_a_property_mistake_gets_one_fault_naming_the_field[choice-props7-options]` |
| tavle.blocks.inputs.x_option_list__mutmut_9 | killed | `test_blocks_inputs.py::test_an_option_list_is_a_required_non_empty_list_of_anything` |
| tavle.blocks.inputs.x_option_list__mutmut_10 | killed | `test_blocks_inputs.py::test_a_property_mistake_gets_one_fault_naming_the_field[choice-props36-options]` |
| tavle.blocks.inputs.x_option_list__mutmut_11 | killed | `test_blocks_inputs.py::test_an_option_list_is_a_required_non_empty_list_of_anything` |
| tavle.blocks.inputs.x_option_list__mutmut_12 | killed | `test_blocks_inputs.py::test_an_option_list_is_a_required_non_empty_list_of_anything` |
| tavle.blocks.inputs.x_option_list__mutmut_13 | killed | `test_blocks_inputs.py::test_a_property_mistake_gets_one_fault_naming_the_field[choice-props7-options]` |
| tavle.blocks.inputs.x_option_list__mutmut_14 | killed | `test_blocks_inputs.py::test_statements_render_hosts_with_their_source_as_fallback` |
| tavle.blocks.inputs.x_option_list__mutmut_15 | killed | `test_blocks_inputs.py::test_statements_render_hosts_with_their_source_as_fallback` |
| tavle.blocks.inputs.x_option_list__mutmut_16 | killed | `test_blocks_inputs.py::test_a_property_mistake_gets_one_fault_naming_the_field[choice-props36-options]` |
| tavle.blocks.inputs.x__members_ok__mutmut_3 | killed | `test_extract_inputs.py::test_a_free_answer_is_bounded_text[list-value3-True]` |
| tavle.blocks.inputs.x_allowed_value__mutmut_15 | killed | `test_extract_inputs.py::test_a_free_answer_is_bounded_text[string-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-False]` |
| tavle.blocks.inputs.x_allowed_value__mutmut_16 | killed | `test_extract_inputs.py::test_a_free_answer_is_bounded_text[string-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-True]` |
| tavle.blocks.inputs.x_finite__mutmut_5 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value10-field` |
| tavle.blocks.inputs.x_text_fault__mutmut_11 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props2-expected2]` |
| tavle.blocks.inputs.x_option_label_value__mutmut_4 | equivalent | The label default is read only for a table without a label; every caller passes options that passed `option_faults`, which requires one. |
| tavle.blocks.inputs.x_option_label_value__mutmut_6 | equivalent | The label default is read only for a table without a label; every caller passes options that passed `option_faults`, which requires one. |
| tavle.blocks.inputs.x_option_label_value__mutmut_9 | equivalent | The label default is read only for a table without a label; every caller passes options that passed `option_faults`, which requires one. |
| tavle.blocks.inputs.x_option_faults__mutmut_2 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props2-expected2]` |
| tavle.blocks.inputs.x_option_faults__mutmut_8 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props0-expected0]` |
| tavle.blocks.inputs.x_option_faults__mutmut_9 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props0-expected0]` |
| tavle.blocks.inputs.x_option_faults__mutmut_10 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props0-expected0]` |
| tavle.blocks.inputs.x_option_faults__mutmut_11 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props0-expected0]` |
| tavle.blocks.inputs.x_option_faults__mutmut_12 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props0-expected0]` |
| tavle.blocks.inputs.x_option_faults__mutmut_13 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props0-expected0]` |
| tavle.blocks.inputs.x_option_faults__mutmut_18 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props3-expected3]` |
| tavle.blocks.inputs.x_option_faults__mutmut_34 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props4-expected4]` |
| tavle.blocks.inputs.x_option_faults__mutmut_48 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props5-expected5]` |
| tavle.blocks.inputs.x_option_faults__mutmut_49 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props5-expected5]` |
| tavle.blocks.inputs.x_option_faults__mutmut_52 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props5-expected5]` |
| tavle.blocks.inputs.x_option_faults__mutmut_53 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props5-expected5]` |
| tavle.blocks.inputs.x_option_faults__mutmut_54 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props6-expected6]` |
| tavle.blocks.inputs.x_option_faults__mutmut_55 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props6-expected6]` |
| tavle.blocks.inputs.x_option_faults__mutmut_56 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props7-expected7]` |
| tavle.blocks.inputs.x_option_faults__mutmut_57 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props7-expected7]` |
| tavle.blocks.inputs.x_option_faults__mutmut_62 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props6-expected6]` |
| tavle.blocks.inputs.x__options_faults__mutmut_5 | killed | `test_blocks_inputs.py::test_a_property_mistake_gets_one_fault_naming_the_field[choice-props17-options]` |
| tavle.blocks.inputs.x__options_faults__mutmut_8 | killed | `test_blocks_inputs.py::test_props_exactly_at_a_limit_are_valid[choice-props0]` |
| tavle.blocks.inputs.x__options_faults__mutmut_9 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props8-expected8]` |
| tavle.blocks.inputs.x__options_faults__mutmut_10 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props8-expected8]` |
| tavle.blocks.inputs.x__options_faults__mutmut_11 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props8-expected8]` |
| tavle.blocks.inputs.x__options_faults__mutmut_12 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props8-expected8]` |
| tavle.blocks.inputs.x__options_faults__mutmut_13 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props8-expected8]` |
| tavle.blocks.inputs.x__options_faults__mutmut_14 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props8-expected8]` |
| tavle.blocks.inputs.x__options_faults__mutmut_19 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props0-expected0]` |
| tavle.blocks.inputs.x__options_faults__mutmut_20 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props0-expected0]` |
| tavle.blocks.inputs.x__options_faults__mutmut_21 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props1-expected1]` |
| tavle.blocks.inputs.x__options_faults__mutmut_24 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props0-expected0]` |
| tavle.blocks.inputs.x__option_set_faults__mutmut_20 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props10-expected10]` |
| tavle.blocks.inputs.x__option_set_faults__mutmut_21 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props10-expected10]` |
| tavle.blocks.inputs.x__option_set_faults__mutmut_24 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props10-expected10]` |
| tavle.blocks.inputs.x__option_set_faults__mutmut_25 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props10-expected10]` |
| tavle.blocks.inputs.x__option_set_faults__mutmut_26 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props10-expected10]` |
| tavle.blocks.inputs.x__option_set_faults__mutmut_27 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[choice-props10-expected10]` |
| tavle.blocks.inputs.x__maxlength_faults__mutmut_5 | killed | `test_blocks_inputs.py::test_props_exactly_at_a_limit_are_valid[form-props2]` |
| tavle.blocks.inputs.x__maxlength_faults__mutmut_6 | killed | `test_blocks_inputs.py::test_props_exactly_at_a_limit_are_valid[form-props2]` |
| tavle.blocks.inputs.x__maxlength_faults__mutmut_8 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props15-expected15]` |
| tavle.blocks.inputs.x__maxlength_faults__mutmut_12 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props15-expected15]` |
| tavle.blocks.inputs.x__maxlength_faults__mutmut_13 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props15-expected15]` |
| tavle.blocks.inputs.x__bound_faults__mutmut_9 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props17-expected17]` |
| tavle.blocks.inputs.x__bound_faults__mutmut_13 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props17-expected17]` |
| tavle.blocks.inputs.x__bound_faults__mutmut_14 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props17-expected17]` |
| tavle.blocks.inputs.x__bound_faults__mutmut_21 | killed | `test_blocks_inputs.py::test_props_exactly_at_a_limit_are_valid[form-props3]` |
| tavle.blocks.inputs.x__select_faults__mutmut_13 | killed | `test_blocks_inputs.py::test_a_property_mistake_gets_one_fault_naming_the_field[form-props33-options]` |
| tavle.blocks.inputs.x__select_faults__mutmut_16 | killed | `test_blocks_inputs.py::test_props_exactly_at_a_limit_are_valid[form-props1]` |
| tavle.blocks.inputs.x__select_faults__mutmut_17 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props21-expected21]` |
| tavle.blocks.inputs.x__select_faults__mutmut_18 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props21-expected21]` |
| tavle.blocks.inputs.x__select_faults__mutmut_19 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props21-expected21]` |
| tavle.blocks.inputs.x__select_faults__mutmut_20 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props21-expected21]` |
| tavle.blocks.inputs.x__select_faults__mutmut_21 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props21-expected21]` |
| tavle.blocks.inputs.x__select_faults__mutmut_22 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props21-expected21]` |
| tavle.blocks.inputs.x__select_faults__mutmut_25 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props22-expected22]` |
| tavle.blocks.inputs.x__select_faults__mutmut_34 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props23-expected23]` |
| tavle.blocks.inputs.x__select_faults__mutmut_35 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props23-expected23]` |
| tavle.blocks.inputs.x__select_faults__mutmut_36 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props23-expected23]` |
| tavle.blocks.inputs.x__select_faults__mutmut_37 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props23-expected23]` |
| tavle.blocks.inputs.x__select_faults__mutmut_38 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props23-expected23]` |
| tavle.blocks.inputs.x__select_faults__mutmut_39 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props23-expected23]` |
| tavle.blocks.inputs.x__field_faults__mutmut_1 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props11-expected11]` |
| tavle.blocks.inputs.x__field_faults__mutmut_14 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props11-expected11]` |
| tavle.blocks.inputs.x__field_faults__mutmut_32 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props13-expected13]` |
| tavle.blocks.inputs.x__field_faults__mutmut_44 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props15-expected15]` |
| tavle.blocks.inputs.x__field_faults__mutmut_50 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props19-expected19]` |
| tavle.blocks.inputs.x__field_faults__mutmut_53 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props17-expected17]` |
| tavle.blocks.inputs.x__field_faults__mutmut_59 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props24-expected24]` |
| tavle.blocks.inputs.x__field_faults__mutmut_62 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props20-expected20]` |
| tavle.blocks.inputs.x__field_json_bound__mutmut_11 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__field_json_bound__mutmut_12 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__field_json_bound__mutmut_13 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__field_json_bound__mutmut_14 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__field_json_bound__mutmut_15 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__field_json_bound__mutmut_16 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__field_json_bound__mutmut_17 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__field_json_bound__mutmut_19 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__field_json_bound__mutmut_26 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__field_json_bound__mutmut_28 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__field_json_bound__mutmut_29 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__field_json_bound__mutmut_30 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__field_json_bound__mutmut_33 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__size_faults__mutmut_5 | killed | `test_blocks_inputs.py::test_props_exactly_at_a_limit_are_valid[form-props4]` |
| tavle.blocks.inputs.x__size_faults__mutmut_7 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props27-expected27]` |
| tavle.blocks.inputs.x__fields_faults__mutmut_1 | killed | `test_blocks_inputs.py::test_a_property_mistake_gets_one_fault_naming_the_field[form-props19-fields]` |
| tavle.blocks.inputs.x__fields_faults__mutmut_5 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props25-expected25]` |
| tavle.blocks.inputs.x__fields_faults__mutmut_6 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props25-expected25]` |
| tavle.blocks.inputs.x__fields_faults__mutmut_7 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props25-expected25]` |
| tavle.blocks.inputs.x__fields_faults__mutmut_8 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props25-expected25]` |
| tavle.blocks.inputs.x__fields_faults__mutmut_9 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props25-expected25]` |
| tavle.blocks.inputs.x__fields_faults__mutmut_10 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props25-expected25]` |
| tavle.blocks.inputs.x__fields_faults__mutmut_15 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props11-expected11]` |
| tavle.blocks.inputs.x__fields_faults__mutmut_16 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props11-expected11]` |
| tavle.blocks.inputs.x__fields_faults__mutmut_17 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props14-expected14]` |
| tavle.blocks.inputs.x__fields_faults__mutmut_20 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props11-expected11]` |
| tavle.blocks.inputs.x__fields_faults__mutmut_35 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[form-props26-expected26]` |
| tavle.blocks.inputs.x__text_value__mutmut_14 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value4-field` |
| tavle.blocks.inputs.x__text_value__mutmut_22 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value3-field` |
| tavle.blocks.inputs.x__number_value__mutmut_22 | killed | `test_extract_inputs.py::test_choice_form_comment_answer_accepts[setup-value8-]` |
| tavle.blocks.inputs.x__number_value__mutmut_23 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value6-field` |
| tavle.blocks.inputs.x__number_value__mutmut_26 | killed | `test_extract_inputs.py::test_choice_form_comment_answer_accepts[setup-value9-]` |
| tavle.blocks.inputs.x__number_value__mutmut_27 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value7-field` |
| tavle.blocks.inputs.x__select_value__mutmut_11 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value13-field` |
| tavle.blocks.inputs.x__checkbox_value__mutmut_6 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value14-field` |
| tavle.blocks.inputs.x__checkbox_value__mutmut_9 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value15-field` |
| tavle.blocks.inputs.x_check_form_value__mutmut_2 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value2-form` |
| tavle.blocks.inputs.x_check_form_value__mutmut_3 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value2-form` |
| tavle.blocks.inputs.x_check_form_value__mutmut_4 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value2-form` |
| tavle.blocks.inputs.x_check_form_value__mutmut_11 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value0-form` |
| tavle.blocks.inputs.x_check_form_value__mutmut_12 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value0-form` |
| tavle.blocks.inputs.x_check_form_value__mutmut_13 | killed | `test_extract_inputs.py::test_form_answer_rejection_says_why[value0-form` |
| tavle.blocks.inputs_ordered.x__items_faults__mutmut_22 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[ranking-props30-expected30]` |
| tavle.blocks.inputs_ordered.x__items_faults__mutmut_23 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[ranking-props30-expected30]` |
| tavle.blocks.inputs_ordered.x__items_faults__mutmut_24 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[ranking-props30-expected30]` |
| tavle.blocks.inputs_ordered.x__items_faults__mutmut_27 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[ranking-props30-expected30]` |
| tavle.blocks.inputs_ordered.x__items_faults__mutmut_35 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[ranking-props31-expected31]` |
| tavle.blocks.inputs_ordered.x__items_faults__mutmut_42 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[ranking-props32-expected32]` |
| tavle.blocks.inputs_ordered.x__items_faults__mutmut_44 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[ranking-props32-expected32]` |
| tavle.blocks.inputs_ordered.x__items_faults__mutmut_47 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[ranking-props32-expected32]` |
| tavle.blocks.inputs_ordered.x__items_faults__mutmut_48 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[ranking-props32-expected32]` |
| tavle.blocks.inputs_ordered.x__items_faults__mutmut_49 | killed | `test_blocks_inputs.py::test_props_exactly_at_a_limit_are_valid[ranking-props5]` |
| tavle.blocks.inputs_ordered.x__items_faults__mutmut_52 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[ranking-props32-expected32]` |
| tavle.blocks.inputs_ordered.x__bound_faults__mutmut_5 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[slider-props33-expected33]` |
| tavle.blocks.inputs_ordered.x__bound_faults__mutmut_9 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[slider-props33-expected33]` |
| tavle.blocks.inputs_ordered.x__bound_faults__mutmut_10 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[slider-props33-expected33]` |
| tavle.blocks.inputs_ordered.x__bound_faults__mutmut_24 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[slider-props36-expected36]` |
| tavle.blocks.inputs_ordered.x__bound_faults__mutmut_31 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[slider-props35-expected35]` |
| tavle.blocks.inputs_ordered.x__bound_faults__mutmut_36 | killed | `test_blocks_inputs.py::test_props_exactly_at_a_limit_are_valid[slider-props6]` |
| tavle.blocks.inputs_ordered.x__bound_faults__mutmut_39 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[slider-props37-expected37]` |
| tavle.blocks.inputs_ordered.x__bound_faults__mutmut_44 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[slider-props37-expected37]` |
| tavle.blocks.inputs_ordered.x__bound_faults__mutmut_45 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[slider-props37-expected37]` |
| tavle.blocks.inputs_ordered.x__bound_faults__mutmut_50 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[slider-props38-expected38]` |
| tavle.blocks.inputs_ordered.x__labels_faults__mutmut_14 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[slider-props39-expected39]` |
| tavle.blocks.inputs_ordered.x__labels_faults__mutmut_22 | killed | `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place[slider-props40-expected40]` |
| tavle.blocks.inputs_ordered.x_check_slider_value__mutmut_4 | killed | `test_extract_inputs.py::test_slider_value_check_refuses_a_non_finite_number` |
| tavle.blocks.inputs_ordered.x_check_slider_value__mutmut_5 | killed | `test_extract_inputs.py::test_slider_value_check_refuses_a_non_finite_number` |
| tavle.blocks.inputs_ordered.x_check_slider_value__mutmut_6 | killed | `test_extract_inputs.py::test_slider_value_check_refuses_a_non_finite_number` |
| tavle.blocks.inputs_ordered.x_check_slider_value__mutmut_13 | killed | `test_extract_inputs.py::test_a_value_within_float_tolerance_of_a_step_is_on_it[bounds0-4]` |
| tavle.blocks.inputs_ordered.x_check_slider_value__mutmut_19 | killed | `test_extract_inputs.py::test_a_value_within_float_tolerance_of_a_step_is_on_it[bounds1-1000.0000001]` |
| tavle.blocks.inputs_ordered.x_check_slider_value__mutmut_32 | killed | `test_extract_inputs.py::test_a_value_within_float_tolerance_of_a_step_is_on_it[bounds2-1.0000004768371582]` |
