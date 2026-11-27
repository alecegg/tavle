# Audit: blocks-schema-a (task 5.4, base `a7ab891`)

- Source (`--only` globs): `tavle.blocks.check.*`, `tavle.blocks.spec.*`, `tavle.blocks.rules.*`, `tavle.blocks.reference.*`, `tavle.blocks_render.registry.*`
- Test files: `tests/page/test_blocks_render.py`, `tests/page/test_blocks_schema.py`, `tests/page/test_blocks_split.py`, `tests/page/test_blocks_text.py`, `tests/page/test_blocks_help_parity.py`
- Collected tests (file order as above): 147 before (17, 54, 6, 35, 35), 154 after (21, 57, 3, 35, 38). Test functions: 59 before, 58 after.
- Mutation score before: 78% (482 mutants: 376 killed, 69 survived, 37 no tests; read from the `blocks` baseline of `audit/py-blocks.md`, whose `tavle.blocks.*` figure is 80%)
- Mutation score after: 93% (482 mutants: 450 killed, 3 survived, 29 no tests, 0 timeout, 0 skipped; `--min-score 80`, 375 s)

The task names `tavle.blocks.*` (schema, rules, reference).
The full glob has 1121 non-killed mutants, mostly in modules that tasks 5.5 to 5.13 name, so this area is the schema check, spec, rules and reference modules.
`tavle.blocks_render.registry` is module-level code only and has no mutants.
No 5.x task names these `tavle.blocks` modules with non-killed mutants: `backend`, `dag`, `deps`, `diagrams`, `er`, `flow`, `sequence`, `state`.

## C1 (leave-one-out)

Each run used the edited tests and a copy of the `blocks` baseline's `mutants/` under a `blocks-schema-a-base` tag, judged on the four module globs.

| `--without` | mutants judged (baseline) | lost kills |
|---|---|---|
| the five files together | `check`, `spec`, `rules`, `reference` | 61 (14 `check`, 17 `spec`, 30 `reference`) |
| `test_blocks_schema.py` | the 61 | 31, all in `check` and `spec`, so not a candidate |
| `test_blocks_help_parity.py` | the 61 | 30, all in `reference`, so not a candidate |
| `test_blocks_render.py` | the 61 | none |
| `test_blocks_split.py` | the 61 | none |
| `test_blocks_text.py` | the 61 | none |

The three flagged files assert facts whose sources are outside these globs, so they are kept.
Mode was per file; no test was removed on C1 evidence.
The baseline does not include mutants that only the new tests kill, which does not matter here for the same reason.

## Decisions

| test id | decision | criterion | evidence |
|---|---|---|---|
| `test_blocks_render.py::test_markers` | merge into `test_example_props_reach_the_page` | C5 | the `data-mithril` facts repeat `test_every_example_renders_classed_html`; the prop facts are now rows |
| `test_blocks_render.py::test_wireframe_ui_states_flow_table_chart_shapes` | merge into `test_every_example_renders_classed_html` and `test_example_props_reach_the_page` | C5 | same calls on the same examples |
| `test_blocks_render.py::test_invalid_block_renders_error_card_with_errors` | merge into `test_faulty_source_renders_an_error_card` | C5 | same call and error-card fact; row `invalid-block` |
| `test_blocks_render.py::test_parse_error_renders_one_error_card` | merge into `test_faulty_source_renders_an_error_card` | C5 | static identical body (`audit/static-scan.md`); row `parse-error` |
| `test_blocks_render.py::test_old_typed_fence_renders_a_removed_card` | merge into `test_faulty_source_renders_an_error_card` | C5 | static identical body; row `old-typed-fence` |
| `test_blocks_render.py::test_chart_rejects_non_finite` | merge into `test_faulty_source_renders_an_error_card` | C5 | same call and error-card fact; row `non-number-chart-value` |
| `test_blocks_split.py::test_table_and_flow_render_as_before` | merge into `test_blocks_render.py::test_example_props_reach_the_page` | C3 | restated the registry row `"flow": flow_props`. With flow `props` set to `None` only `test_blocks_charts_diagrams.py::test_block_is_client_side_and_bundled[flow]` failed; with a wrong hook (`props=dict`) nothing did. The new flow row fails under the wrong hook |
| `test_blocks_split.py::test_specs_moved_with_their_validators` | delete | C3 | identity copies of the registry; `test_each_example_is_valid` covers validity |
| `test_blocks_split.py::test_diagram_modules_wait_for_rb_diagram` | delete | C3 | asserted the module attribute layout |
| `test_blocks_schema.py::test_property_metadata_construction_and_defaults` | delete | C2 | asserted dataclass defaults and the values it had just set; the string-list enum behaviour is now `test_enum_applies_to_each_item_of_a_string_list` |
| `test_blocks_text.py::test_blank_text_faults_once` | keep | C5 | static identical-body hit with tests that check other components |
| `test_blocks_render.py` | keep | C1 | only page-seam tests of hostile-input escaping and the error card in this area |
| `test_blocks_text.py` | keep | C1 | guards the Python to JS fixture contract, `classify_url` and decision and matrix constant parity |
| `test_blocks_split.py` | keep | C1 | guards the ES-module load contract of the page scripts and include prop faults |
| `test_blocks_render.py::test_every_example_renders_classed_html` | changed | C2 | asserts the example's own `data-mithril` name instead of any `class="vb` |
| `test_blocks_schema.py::test_unknown_key_is_reported`, `test_covers_is_reserved_and_validated`, `test_property_metadata_rejects_impossible_combinations`, `test_nonempty_rejects_a_blank_string_and_an_empty_list_once` | changed | survivors | assert whole errors, messages and paths |

New tests for survivors: see the killer ids below.

## Dead code

`type_name`, `list_of` and `tables_fault` in `src/tavle/blocks/rules.py` have no callers in `src/`, `tests/` or `scripts/`, are not exported from `tavle`, and varde does not import them.
Their 29 mutants have no test and fit none of the three survivor outcomes.
No test was written for them; the source file is outside this task, so removing them is left to the lead.

## Survivors

All 106 mutants of these globs that the baseline did not kill.
74 are killed by a fast test, 3 are equivalent, 29 are dead code.
No mutant is `slow-only`.
Killer ids are the first failing test among the five owned files, with the mutant activated after collection as mutmut does.

| mutant | outcome | evidence |
|---|---|---|
| tavle.blocks.check.x__covers_faults__mutmut_9 | killed | `test_blocks_schema.py::test_covers_is_reserved_and_validated` |
| tavle.blocks.check.x__covers_faults__mutmut_12 | killed | `test_blocks_schema.py::test_covers_is_reserved_and_validated` |
| tavle.blocks.check.x__covers_faults__mutmut_13 | killed | `test_blocks_schema.py::test_covers_is_reserved_and_validated` |
| tavle.blocks.check.x__covers_faults__mutmut_15 | killed | `test_blocks_schema.py::test_covers_is_reserved_and_validated` |
| tavle.blocks.check.x__covers_faults__mutmut_16 | killed | `test_blocks_schema.py::test_covers_is_reserved_and_validated` |
| tavle.blocks.check.x__covers_faults__mutmut_19 | killed | `test_blocks_schema.py::test_covers_is_reserved_and_validated` |
| tavle.blocks.check.x__covers_faults__mutmut_20 | killed | `test_blocks_schema.py::test_covers_is_reserved_and_validated` |
| tavle.blocks.check.x__covers_faults__mutmut_21 | killed | `test_blocks_schema.py::test_covers_is_reserved_and_validated` |
| tavle.blocks.check.x__covers_faults__mutmut_22 | killed | `test_blocks_schema.py::test_covers_is_reserved_and_validated` |
| tavle.blocks.check.x__property_faults__mutmut_17 | killed | `test_blocks_schema.py::test_unknown_key_is_reported` |
| tavle.blocks.check.x__value_faults__mutmut_48 | killed | `test_blocks_schema.py::test_nonempty_rejects_a_blank_string_and_an_empty_list_once` |
| tavle.blocks.check.x__value_faults__mutmut_51 | killed | `test_blocks_schema.py::test_nonempty_rejects_a_blank_string_and_an_empty_list_once` |
| tavle.blocks.check.x__value_faults__mutmut_77 | equivalent | `=` for `+=`: for kind `object` nothing has been added to `faults` before this line, so it is still empty. |
| tavle.blocks.check.x__value_faults__mutmut_91 | equivalent | The element spec's `name` becomes `None`: neither `_value_faults` nor `PropertySpec.__post_init__` reads it. |
| tavle.blocks.check.x_check_props__mutmut_1 | killed | `test_blocks_schema.py::test_unknown_component_lists_the_known_names` |
| tavle.blocks.check.x_check_props__mutmut_5 | killed | `test_blocks_schema.py::test_unknown_component_lists_the_known_names` |
| tavle.blocks.check.x_check_props__mutmut_7 | killed | `test_blocks_schema.py::test_unknown_component_lists_the_known_names` |
| tavle.blocks.check.x_check_props__mutmut_9 | killed | `test_blocks_schema.py::test_unknown_component_lists_the_known_names` |
| tavle.blocks.check.x_check_props__mutmut_12 | killed | `test_blocks_schema.py::test_unknown_component_lists_the_known_names` |
| tavle.blocks.check.x_check_props__mutmut_13 | killed | `test_blocks_schema.py::test_unknown_component_lists_the_known_names` |
| tavle.blocks.check.x_check_props__mutmut_16 | killed | `test_blocks_schema.py::test_unknown_component_lists_the_known_names` |
| tavle.blocks.check.x_check_props__mutmut_17 | killed | `test_blocks_schema.py::test_unknown_component_lists_the_known_names` |
| tavle.blocks.check.x_props_errors__mutmut_1 | killed | `test_blocks_schema.py::test_errors_have_no_statement_id_unless_one_is_given` |
| tavle.blocks.reference.x__field_lines__mutmut_5 | equivalent | `if rows or True`: the only caller, `type_text`, calls it only when the spec has properties or extra keys, so `rows` is never empty. |
| tavle.blocks.reference.x__indented__mutmut_8 | killed | `test_blocks_help_parity.py::test_type_text_lays_out_fields_details_and_syntax` |
| tavle.blocks.reference.x__indented__mutmut_9 | killed | `test_blocks_help_parity.py::test_type_text_lays_out_fields_details_and_syntax` |
| tavle.blocks.reference.x__indented__mutmut_10 | killed | `test_blocks_help_parity.py::test_type_text_lays_out_fields_details_and_syntax` |
| tavle.blocks.reference.x_catalog__mutmut_1 | killed | `test_blocks_help_parity.py::test_catalog_holds_every_named_component_as_plain_data` |
| tavle.blocks.reference.x_catalog__mutmut_2 | killed | `test_blocks_help_parity.py::test_catalog_holds_every_named_component_as_plain_data` |
| tavle.blocks.reference.x_catalog__mutmut_3 | killed | `test_blocks_help_parity.py::test_catalog_holds_every_named_component_as_plain_data` |
| tavle.blocks.reference.x_catalog__mutmut_4 | killed | `test_blocks_help_parity.py::test_catalog_holds_every_named_component_as_plain_data` |
| tavle.blocks.reference.x_catalog__mutmut_5 | killed | `test_blocks_help_parity.py::test_catalog_holds_every_named_component_as_plain_data` |
| tavle.blocks.reference.x_catalog__mutmut_6 | killed | `test_blocks_help_parity.py::test_catalog_holds_every_named_component_as_plain_data` |
| tavle.blocks.reference.x_catalog__mutmut_10 | killed | `test_blocks_help_parity.py::test_catalog_holds_every_named_component_as_plain_data` |
| tavle.blocks.reference.x_catalog__mutmut_11 | killed | `test_blocks_help_parity.py::test_catalog_holds_every_named_component_as_plain_data` |
| tavle.blocks.reference.x_catalog__mutmut_12 | killed | `test_blocks_help_parity.py::test_catalog_holds_every_named_component_as_plain_data` |
| tavle.blocks.reference.x_catalog__mutmut_15 | killed | `test_blocks_help_parity.py::test_catalog_holds_every_named_component_as_plain_data` |
| tavle.blocks.reference.x_index_text__mutmut_1 | killed | `test_blocks_help_parity.py::test_index_text_lists_each_component_by_name` |
| tavle.blocks.reference.x_index_text__mutmut_2 | killed | `test_blocks_help_parity.py::test_index_text_lists_each_component_by_name` |
| tavle.blocks.reference.x_index_text__mutmut_3 | killed | `test_blocks_help_parity.py::test_index_text_lists_each_component_by_name` |
| tavle.blocks.reference.x_index_text__mutmut_4 | killed | `test_blocks_help_parity.py::test_index_text_lists_each_component_by_name` |
| tavle.blocks.reference.x_index_text__mutmut_5 | killed | `test_blocks_help_parity.py::test_index_text_lists_each_component_by_name` |
| tavle.blocks.reference.x_index_text__mutmut_6 | killed | `test_blocks_help_parity.py::test_index_text_lists_each_component_by_name` |
| tavle.blocks.reference.x_index_text__mutmut_7 | killed | `test_blocks_help_parity.py::test_index_text_lists_each_component_by_name` |
| tavle.blocks.reference.x_index_text__mutmut_8 | killed | `test_blocks_help_parity.py::test_index_text_lists_each_component_by_name` |
| tavle.blocks.reference.x_type_text__mutmut_18 | killed | `test_blocks_help_parity.py::test_type_text_lays_out_fields_details_and_syntax` |
| tavle.blocks.reference.x_type_text__mutmut_19 | killed | `test_blocks_help_parity.py::test_type_text_lays_out_fields_details_and_syntax` |
| tavle.blocks.reference.x_type_text__mutmut_20 | killed | `test_blocks_help_parity.py::test_type_text_lays_out_fields_details_and_syntax` |
| tavle.blocks.reference.x_type_text__mutmut_23 | killed | `test_blocks_help_parity.py::test_type_text_lays_out_fields_details_and_syntax` |
| tavle.blocks.reference.x_type_text__mutmut_29 | killed | `test_blocks_help_parity.py::test_type_text_lays_out_fields_details_and_syntax` |
| tavle.blocks.rules.x_check_keys__mutmut_12 | killed | `test_blocks_schema.py::test_field_helpers_name_the_fault_and_the_place` |
| tavle.blocks.rules.x_check_keys__mutmut_16 | killed | `test_blocks_schema.py::test_field_helpers_name_the_fault_and_the_place` |
| tavle.blocks.rules.x_check_keys__mutmut_17 | killed | `test_blocks_schema.py::test_field_helpers_name_the_fault_and_the_place` |
| tavle.blocks.rules.x_duplicates__mutmut_6 | killed | `test_blocks_schema.py::test_field_helpers_name_the_fault_and_the_place` |
| tavle.blocks.rules.x_list_of__mutmut_1 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_2 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_3 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_4 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_5 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_6 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_7 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_8 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_9 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_10 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_11 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_12 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_13 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_14 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_15 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_list_of__mutmut_16 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_str_field__mutmut_4 | killed | `test_blocks_schema.py::test_field_helpers_name_the_fault_and_the_place` |
| tavle.blocks.rules.x_str_field__mutmut_8 | killed | `test_blocks_schema.py::test_field_helpers_name_the_fault_and_the_place` |
| tavle.blocks.rules.x_str_field__mutmut_9 | killed | `test_blocks_schema.py::test_field_helpers_name_the_fault_and_the_place` |
| tavle.blocks.rules.x_str_map__mutmut_4 | killed | `test_blocks_schema.py::test_field_helpers_name_the_fault_and_the_place` |
| tavle.blocks.rules.x_str_map__mutmut_8 | killed | `test_blocks_schema.py::test_field_helpers_name_the_fault_and_the_place` |
| tavle.blocks.rules.x_str_map__mutmut_9 | killed | `test_blocks_schema.py::test_field_helpers_name_the_fault_and_the_place` |
| tavle.blocks.rules.x_tables_fault__mutmut_1 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_tables_fault__mutmut_2 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_tables_fault__mutmut_3 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_tables_fault__mutmut_4 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_tables_fault__mutmut_5 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_tables_fault__mutmut_6 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_tables_fault__mutmut_7 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_tables_fault__mutmut_8 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_tables_fault__mutmut_9 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_tables_fault__mutmut_10 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_tables_fault__mutmut_11 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_tables_fault__mutmut_12 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.rules.x_type_name__mutmut_1 | no test, dead code | No caller in `src/`, `tests/` or `scripts/`; see Dead code. |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_7 | killed | `test_blocks_schema.py::test_property_metadata_rejects_impossible_combinations[kwargs7-nonempty requires a string or a list]` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_8 | killed | `test_blocks_schema.py::test_property_metadata_rejects_impossible_combinations[kwargs7-nonempty requires a string or a list]` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_9 | killed | `test_blocks_schema.py::test_property_metadata_rejects_impossible_combinations[kwargs7-nonempty requires a string or a list]` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_15 | killed | `test_blocks_schema.py::test_property_metadata_rejects_impossible_combinations[kwargs0-items requires a list]` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_16 | killed | `test_blocks_schema.py::test_property_metadata_rejects_impossible_combinations[kwargs0-items requires a list]` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_17 | killed | `test_blocks_schema.py::test_property_metadata_rejects_impossible_combinations[kwargs0-items requires a list]` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_31 | killed | `test_blocks_schema.py::test_property_metadata_rejects_impossible_combinations[kwargs5-fields requires an object or list of objects]` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_32 | killed | `test_blocks_schema.py::test_property_metadata_rejects_impossible_combinations[kwargs5-fields requires an object or list of objects]` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_33 | killed | `test_blocks_schema.py::test_property_metadata_rejects_impossible_combinations[kwargs5-fields requires an object or list of objects]` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_41 | killed | `test_blocks_schema.py::test_enum_applies_to_each_item_of_a_string_list` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_42 | killed | `test_blocks_schema.py::test_enum_applies_to_each_item_of_a_string_list` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_43 | killed | `test_blocks_schema.py::test_enum_applies_to_each_item_of_a_string_list` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_45 | killed | `test_blocks_schema.py::test_enum_applies_to_each_item_of_a_string_list` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_46 | killed | `test_blocks_schema.py::test_enum_applies_to_each_item_of_a_string_list` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_47 | killed | `test_blocks_schema.py::test_property_metadata_rejects_impossible_combinations[kwargs1-enum requires a string or list of strings]` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_48 | killed | `test_blocks_schema.py::test_property_metadata_rejects_impossible_combinations[kwargs1-enum requires a string or list of strings]` |
| tavle.blocks.spec.xǁPropertySpecǁ__post_init____mutmut_49 | killed | `test_blocks_schema.py::test_property_metadata_rejects_impossible_combinations[kwargs1-enum requires a string or list of strings]` |
