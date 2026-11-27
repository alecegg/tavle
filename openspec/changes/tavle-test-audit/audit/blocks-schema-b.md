# Audit: blocks-schema-b (task 5.5, base `96d078e`)

- Source (`--only` globs): `tavle.blocks.backend.*`, `tavle.blocks.dag.*`, `tavle.blocks.decision.*`, `tavle.blocks.deps.*`, `tavle.blocks.diagrams.*`, `tavle.blocks.er.*`, `tavle.blocks.flow.*`, `tavle.blocks.sequence.*`, `tavle.blocks.state.*`, `tavle.blocks_render.decision.*`
- Test files: `tests/page/test_blocks_decision.py`, `tests/page/test_extract_blocks_schema.py`, `tests/page/test_pages_block_types.py`, `tests/page/test_row_kind_rules.py`, `tests/page/test_pages_decision.py`, `tests/page/test_extract_custom_removed.py`
- Collected tests (file order as above): 182 before (10, 34, 59, 62, 16, 1), 197 after (12, 48, 59, 62, 15, 1). Test functions: 38 before, 34 after.
- Mutation score before: 81% (968 mutants: 792 killed, 175 survived, 1 timeout; the `blocks` and `blocks_render` baselines, whose package scores are in `audit/py-blocks.md`)
- Mutation score after: 95% (968 mutants: 925 killed, 43 survived, 0 timeout; run wall time 298s)

The globs are the `tavle.blocks.*` modules this task's tests judge and no other 5.x task names, plus the decision renderer. The other `tavle.blocks.*` modules belong to tasks 5.4 and 5.6 to 5.13.

## C1 (leave-one-out)

Each run used a copy of a baseline's `mutants/` under a `blocks-schema-b-*` tag. Wall time of the table's runs was about 28 minutes in total.

| `--without` | mutants judged (baseline) | lost kills |
|---|---|---|
| the six files together | the area's `tavle.blocks.*` modules (`blocks`) | 10, all `decision.x_validate_decision` |
| the six files together | `tavle.blocks_render.decision` (`blocks_render`) | none |
| each of the six, on those 10 | `blocks` | none (each of the 10 has more than one killer among the six) |
| `test_extract_blocks_schema.py::test_find_fences_matches_the_reference_scanner` | `tavle.page.fences.*` (`page`) | 9 |
| `test_row_kind_rules.py` | `tavle.comments.store.*` (`comments-serve`) | 3 |
| `test_pages_decision.py` | `tavle.comments.store.*` (`comments-serve`) | 2 |
| `test_extract_custom_removed.py` | `tavle.serve.assemble_served.*` (`comments-serve`) | none |
| `test_extract_custom_removed.py` | `tavle.page.render.x__custom_removed` (`page`) | 2 (`_1`, `_6`) |
| `test_pages_block_types.py` | `tavle.page.actions.*` (`page`) | none |
| `test_pages_block_types.py` | `tavle.page.render.x__custom_removed`, `x__parse_table` (`page`) | none |
| `test_blocks_decision.py` | `tavle.page.page_check.*` (`page`) | none |

Mode was per file, plus the one single-test run. No test was removed on C1 evidence.
The 16 lost kills outside the area (9, 3, 2, 2) were each confirmed killed with only the six files.

## Decisions

| test id | decision | criterion | evidence |
|---|---|---|---|
| `test_blocks_decision.py::test_example_is_valid` | delete | C5 | same call and fact as `test_extract_blocks_schema.py::test_every_component_example_is_one_valid_statement_that_renders[decision]` |
| `test_blocks_decision.py::test_unknown_option` | merge into `test_a_bad_decision_reports_one_rule[unknown-option]` | C5 | static identical-body hit (`audit/static-scan.md`) |
| `test_blocks_decision.py::test_duplicate_option` | merge into `test_a_bad_decision_reports_one_rule[duplicate-option]` | C5 | static identical-body hit |
| `test_blocks_decision.py::test_unknown_key` | merge into `test_a_bad_decision_reports_one_rule[unknown-key]` | C5 | static identical-body hit |
| `test_blocks_decision.py::test_missing_question` | merge into `test_a_bad_decision_reports_one_rule[missing-question]` | C5 | same call, one input differs |
| `test_blocks_decision.py::test_evidence_row_needs_label_and_text` | merge into `test_a_bad_decision_reports_one_rule[evidence-row-without-text]` | C5 | same call, one input differs |
| `test_blocks_decision.py::test_wrong_type_and_blank_question` | merge into `test_a_bad_decision_reports_one_rule[question-not-text]` and `[blank-question]` | C5 | same call, one input differs |
| `test_pages_decision.py::test_pages_decision_buttons_disabled_while_posting` | merge into `test_pages_decision_one_click` | C3 | string search over `recap.js`; the slow test now records at each POST that every button of the item is disabled, and that none is afterwards |
| `test_pages_block_types.py::test_ui_statements_use_the_component_type` | changed | C2 | expected values came from `component_block_type`, the code under test; now literals |
| `test_extract_blocks_schema.py::test_find_fences_matches_the_reference_scanner` | keep | C1 | carries a copy of the old scanner, but alone kills 9 `tavle.page.fences` mutants |
| `test_extract_blocks_schema.py` (file) | keep | C1 | alone kills those 9; its new validator rows kill most of the area's former survivors |
| `test_blocks_decision.py` (file) | keep | C1 | its two `decision_as_choice` tests kill mutants of `blocks_render.decision` that the pre-audit suite left alive |
| `test_row_kind_rules.py` (file) | keep | C1 | alone kills 3 `tavle.comments.store` mutants |
| `test_row_kind_rules.py::test_every_type_and_kind_cell` | keep | C2 | expected value comes from `kind_allowed`, but the test checks that the server store enforces that table (slow) |
| `test_row_kind_rules.py::test_forged_suggestion_on_code_is_refused` | keep | C5 | repeats the slow `code`/`suggestion` cell, and is the fast guard for it |
| `test_pages_decision.py` (file) | keep | C1 | alone kills 2 `tavle.comments.store` mutants |
| `test_extract_custom_removed.py` (file) | keep | C1 | alone kills `tavle.page.render.x__custom_removed__mutmut_1` and `_6`; guards that a removed `custom` block never renders author HTML |
| `test_pages_block_types.py` (file) | keep | C1 | no unique kill in the runs above; it asserts the published `data-block-type` wrapper contract, whose source (`tavle.page`) is outside these globs |

## Survivors

All 176 non-killed mutants of the baselines (175 survived, 1 timeout): 133 killed by a fast test, 43 equivalent, 0 slow-only.
"Killed" evidence is the first test that failed with the mutant active (`pytest -x -m "not slow and not matrix_full"` over only the six files, in the copy of the final run). The full run left exactly the 43 equivalent mutants alive.

| mutant | result | evidence |
|---|---|---|
| tavle.blocks.backend.x__entity_faults__mutmut_3 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__entity_faults__mutmut_12 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__entity_faults__mutmut_28 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__entity_faults__mutmut_36 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__entity_faults__mutmut_39 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.backend.x__entity_faults__mutmut_45 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__entity_faults__mutmut_46 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__entity_faults__mutmut_50 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__out_of_range__mutmut_5 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[endpoint]` |
| tavle.blocks.backend.x__out_of_range__mutmut_6 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[endpoint]` |
| tavle.blocks.backend.x__out_of_range__mutmut_7 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[endpoint]` |
| tavle.blocks.backend.x__out_of_range__mutmut_8 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[endpoint]` |
| tavle.blocks.backend.x__response_faults__mutmut_3 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[endpoint]` |
| tavle.blocks.backend.x__route_faults__mutmut_16 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[endpoint]` |
| tavle.blocks.backend.x__typed_item_faults__mutmut_34 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__typed_item_faults__mutmut_38 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__typed_item_faults__mutmut_39 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__typed_item_faults__mutmut_41 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__typed_item_faults__mutmut_46 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__typed_item_faults__mutmut_53 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__typed_map_faults__mutmut_3 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__typed_map_faults__mutmut_7 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__typed_map_faults__mutmut_8 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__typed_map_faults__mutmut_13 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__typed_map_faults__mutmut_17 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__typed_map_faults__mutmut_18 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__typed_map_faults__mutmut_19 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x__typed_map_faults__mutmut_20 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x_validate_data_model__mutmut_6 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.backend.x_validate_data_model__mutmut_12 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.backend.x_validate_data_model__mutmut_13 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.backend.x_validate_data_model__mutmut_18 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x_validate_data_model__mutmut_27 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x_validate_data_model__mutmut_28 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x_validate_data_model__mutmut_33 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model]` |
| tavle.blocks.backend.x_validate_endpoint__mutmut_5 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[endpoint]` |
| tavle.blocks.backend.x_validate_endpoint__mutmut_8 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[endpoint]` |
| tavle.blocks.backend.x_validate_endpoint__mutmut_9 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[endpoint]` |
| tavle.blocks.backend.x_validate_endpoint__mutmut_27 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.backend.x_validate_endpoint__mutmut_33 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.backend.x_validate_endpoint__mutmut_34 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.dag.x__dfs_from__mutmut_13 | equivalent | The finished state is only compared with 1 and tested for presence, so any other value acts as 2. |
| tavle.blocks.dag.x__dfs_from__mutmut_14 | equivalent | The finished state is only compared with 1 and tested for presence, so any other value acts as 2. |
| tavle.blocks.decision.x_validate_decision__mutmut_7 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[decision]` |
| tavle.blocks.decision.x_validate_decision__mutmut_10 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[decision]` |
| tavle.blocks.deps.x__name_fault__mutmut_6 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x__name_fault__mutmut_7 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x__name_fault__mutmut_10 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x__name_fault__mutmut_11 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x__named_tasks__mutmut_2 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x__status_faults__mutmut_5 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x__status_faults__mutmut_6 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x__status_faults__mutmut_9 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x__status_faults__mutmut_10 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x__status_faults__mutmut_14 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x__status_faults__mutmut_15 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x__status_faults__mutmut_18 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x__status_faults__mutmut_19 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x_validate_deps__mutmut_7 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x_validate_deps__mutmut_10 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x_validate_deps__mutmut_13 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x_validate_deps__mutmut_14 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x_validate_deps__mutmut_17 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x_validate_deps__mutmut_18 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x_validate_deps__mutmut_21 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x_validate_deps__mutmut_22 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x_validate_deps__mutmut_23 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x_validate_deps__mutmut_24 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.deps.x_validate_deps__mutmut_27 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[deps]` |
| tavle.blocks.diagrams.x__edge_faults__mutmut_5 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x__edge_faults__mutmut_11 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x__edge_faults__mutmut_12 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x__edge_faults__mutmut_13 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram-at-limits]` |
| tavle.blocks.diagrams.x__edge_faults__mutmut_16 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram-over-limits]` |
| tavle.blocks.diagrams.x__edge_faults__mutmut_24 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__edge_faults__mutmut_25 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__edge_faults__mutmut_26 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__edge_faults__mutmut_27 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__edge_faults__mutmut_28 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__edge_faults__mutmut_37 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__group_faults__mutmut_5 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x__group_faults__mutmut_11 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x__group_faults__mutmut_12 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x__group_faults__mutmut_14 | equivalent | `faults` is still empty here, so `=` and `+=` give the same list. |
| tavle.blocks.diagrams.x__group_faults__mutmut_16 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__group_faults__mutmut_17 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__group_faults__mutmut_18 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__group_faults__mutmut_19 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__group_faults__mutmut_20 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__group_faults__mutmut_21 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__group_faults__mutmut_23 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__group_faults__mutmut_26 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram-over-limits]` |
| tavle.blocks.diagrams.x__has_cycle_from__mutmut_3 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram-tree-cycle]` |
| tavle.blocks.diagrams.x__has_cycle_from__mutmut_6 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram-tree-cycle]` |
| tavle.blocks.diagrams.x__node_faults__mutmut_5 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x__node_faults__mutmut_11 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x__node_faults__mutmut_12 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x__node_faults__mutmut_14 | equivalent | `faults` is still empty here, so `=` and `+=` give the same list. |
| tavle.blocks.diagrams.x__node_faults__mutmut_17 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__node_faults__mutmut_23 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram-at-limits]` |
| tavle.blocks.diagrams.x__node_faults__mutmut_26 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram-over-limits]` |
| tavle.blocks.diagrams.x__node_faults__mutmut_34 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__node_faults__mutmut_35 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__node_faults__mutmut_36 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__node_faults__mutmut_45 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x__tree_faults__mutmut_9 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram-tree-cycle]` |
| tavle.blocks.diagrams.x__tree_parents__mutmut_5 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x__tree_parents__mutmut_11 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x__tree_parents__mutmut_12 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x__tree_parents__mutmut_21 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram-tree]` |
| tavle.blocks.diagrams.x__tree_parents__mutmut_22 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram-tree]` |
| tavle.blocks.diagrams.x__tree_parents__mutmut_26 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram-tree]` |
| tavle.blocks.diagrams.x_validate_diagram__mutmut_18 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x_validate_diagram__mutmut_24 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x_validate_diagram__mutmut_25 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.diagrams.x_validate_diagram__mutmut_29 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram]` |
| tavle.blocks.diagrams.x_validate_diagram__mutmut_41 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[diagram-tree]` |
| tavle.blocks.er.x_layout_faults__mutmut_11 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[data-model-graph-size]` |
| tavle.blocks.flow.x_validate_flow__mutmut_4 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.flow.x_validate_flow__mutmut_10 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.flow.x_validate_flow__mutmut_11 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.flow.x_validate_flow__mutmut_15 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[flow]` |
| tavle.blocks.flow.x_validate_flow__mutmut_24 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[flow]` |
| tavle.blocks.flow.x_validate_flow__mutmut_25 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[flow]` |
| tavle.blocks.flow.x_validate_flow__mutmut_26 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[flow]` |
| tavle.blocks.flow.x_validate_flow__mutmut_32 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[flow]` |
| tavle.blocks.flow.x_validate_flow__mutmut_36 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[flow]` |
| tavle.blocks.sequence.x__actor_faults__mutmut_5 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.sequence.x__actor_faults__mutmut_11 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.sequence.x__actor_faults__mutmut_12 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.sequence.x__actor_faults__mutmut_14 | equivalent | `faults` is still empty here, so `=` and `+=` give the same list. |
| tavle.blocks.sequence.x__actor_faults__mutmut_17 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[sequence]` |
| tavle.blocks.sequence.x__actor_faults__mutmut_26 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[sequence]` |
| tavle.blocks.sequence.x__end_fault__mutmut_6 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[sequence]` |
| tavle.blocks.sequence.x__step_faults__mutmut_6 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[sequence]` |
| tavle.blocks.sequence.x__step_faults__mutmut_16 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[sequence]` |
| tavle.blocks.sequence.x__steps_faults__mutmut_5 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.sequence.x__steps_faults__mutmut_11 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.sequence.x__steps_faults__mutmut_12 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.sequence.x__steps_faults__mutmut_16 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[sequence]` |
| tavle.blocks.sequence.x__steps_faults__mutmut_24 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[sequence]` |
| tavle.blocks.sequence.x__steps_faults__mutmut_25 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[sequence]` |
| tavle.blocks.sequence.x__steps_faults__mutmut_30 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[sequence]` |
| tavle.blocks.state.x__end_fault__mutmut_6 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state]` |
| tavle.blocks.state.x__initial_faults__mutmut_16 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state-no-initial]` |
| tavle.blocks.state.x__initial_faults__mutmut_21 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state-no-initial]` |
| tavle.blocks.state.x__initial_faults__mutmut_22 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state-no-initial]` |
| tavle.blocks.state.x__initial_faults__mutmut_27 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state]` |
| tavle.blocks.state.x__initial_faults__mutmut_32 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state]` |
| tavle.blocks.state.x__initial_faults__mutmut_33 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state]` |
| tavle.blocks.state.x__move_faults__mutmut_5 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state]` |
| tavle.blocks.state.x__move_faults__mutmut_8 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.state.x__move_faults__mutmut_14 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.state.x__move_faults__mutmut_15 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.state.x__move_faults__mutmut_16 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state]` |
| tavle.blocks.state.x__move_faults__mutmut_17 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state]` |
| tavle.blocks.state.x__move_faults__mutmut_18 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state]` |
| tavle.blocks.state.x__move_faults__mutmut_23 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state]` |
| tavle.blocks.state.x__move_faults__mutmut_35 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state]` |
| tavle.blocks.state.x__state_faults__mutmut_5 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.state.x__state_faults__mutmut_11 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.state.x__state_faults__mutmut_12 | equivalent | `blocks.rules.tables` never reads its `where` argument, the only thing changed. |
| tavle.blocks.state.x__state_faults__mutmut_14 | equivalent | `faults` is still empty here, so `=` and `+=` give the same list. |
| tavle.blocks.state.x__state_faults__mutmut_17 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state]` |
| tavle.blocks.state.x__state_faults__mutmut_26 | killed | `test_extract_blocks_schema.py::test_validator_reports_each_fault[state]` |
| tavle.blocks_render.decision.x_decision_as_choice__mutmut_4 | killed | `test_blocks_decision.py::test_decision_without_options_offers_all_three_verdicts` |
| tavle.blocks_render.decision.x_decision_as_choice__mutmut_6 | killed | `test_blocks_decision.py::test_decision_without_options_offers_all_three_verdicts` |
| tavle.blocks_render.decision.x_decision_as_choice__mutmut_11 | killed | `test_blocks_decision.py::test_decision_without_options_offers_all_three_verdicts` |
| tavle.blocks_render.decision.x_decision_as_choice__mutmut_12 | killed | `test_blocks_decision.py::test_decision_without_options_offers_all_three_verdicts` |
| tavle.blocks_render.decision.x_decision_as_choice__mutmut_13 | killed | `test_blocks_decision.py::test_decision_with_one_option_keeps_the_question_and_takes_no_comment` |
| tavle.blocks_render.decision.x_decision_as_choice__mutmut_14 | killed | `test_blocks_decision.py::test_decision_without_options_offers_all_three_verdicts` |
| tavle.blocks_render.decision.x_decision_as_choice__mutmut_15 | killed | `test_blocks_decision.py::test_decision_without_options_offers_all_three_verdicts` |
| tavle.blocks_render.decision.x_decision_as_choice__mutmut_16 | killed | `test_blocks_decision.py::test_decision_without_options_offers_all_three_verdicts` |
| tavle.blocks_render.decision.x_decision_as_choice__mutmut_17 | killed | `test_blocks_decision.py::test_decision_with_one_option_keeps_the_question_and_takes_no_comment` |
| tavle.blocks_render.decision.x_decision_as_choice__mutmut_18 | killed | `test_blocks_decision.py::test_decision_with_one_option_keeps_the_question_and_takes_no_comment` |
| tavle.blocks_render.decision.x_decision_as_choice__mutmut_19 | killed | `test_blocks_decision.py::test_decision_without_options_offers_all_three_verdicts` |
