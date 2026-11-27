# Audit: inputs-b (task 5.7, base `4e932e6`)

- Source (`--only` globs): `tavle.blocks.inputs*`, `tavle.page.actions.*`
- Test files: `tests/page/test_inputs_basic.py`, `tests/page/test_inputs_ordered.py`, `tests/page/test_actions.py`
- Collected tests (file order as above): 139 before (22, 26, 91), 79 after (15, 16, 48). Test functions: 25 before (7, 10, 8), 21 after (6, 8, 7).
- Mutation score before: 79% (812 mutants: 649 killed, 163 survived; `tavle.blocks.inputs*` 773 and 610 killed in `audit/py-blocks.md`, `tavle.page.actions` 39 and all killed in the `page` baseline copy)
- Mutation score after: 99% (812 mutants: 809 killed, 3 survived, 0 timeout)

## C1 (leave-one-out, baselines `inputs-b-base` and `inputs-b-page-base`, copies of the `blocks` and `page` results)

The test edits were made first, so each run judges the edited files.

| `--without` | lost kills in `tavle.blocks.inputs*` | lost kills in `tavle.page.actions.*` |
|---|---|---|
| the three files together | 5 | 17 |
| `test_inputs_basic.py`, on those | 4 | none |
| `test_inputs_ordered.py`, on those | 1 | none |
| `test_actions.py`, on those | none | 17 |

Each file has unique kills, so none is a candidate. Mode was per file; no test was removed on C1 evidence.
Each of the 22 mutants also fails when only the three owned files run with it active (not slow):

| mutants | failing test in the owned files |
|---|---|
| `x__number_value__mutmut_7`, `_8`, `_9` | `test_inputs_basic.py::test_form_value_check_reports_the_field` |
| `x_option_faults__mutmut_59` | `test_inputs_basic.py::test_props_faults`, the option with only a `detail` |
| `x__bound_faults__mutmut_34` | `test_inputs_ordered.py::test_props_faults`, the `step: 0` row |
| `x_kind_allowed__mutmut_3`, `_5` | `test_actions.py::test_answer_only_on_widget_and_decision` |
| `x_menu_entries__mutmut_4` to `_6`, `_9` to `_15`, `_17` to `_21` | `test_actions.py::test_entries_write_only_accepted_kinds` |

## Decisions

"Widget cases" is `test_blocks_inputs.py::test_a_widget_fault_names_the_rule_and_the_place`, which calls `check_props` (the validator `check` runs) and asserts every rule and message.

| test id | decision | criterion | evidence |
|---|---|---|---|
| `test_inputs_basic.py::test_props_faults`, rows `options: ["a", "a"]`, field name `"A b"`, select without `options`, number `min: 5, max: 1`, text field `min: 1`, two fields named `a` | delete rows | C5 | the same props are widget cases `_choice("a", "a")`, `_in_field(name="A b")`, `_in_field(type="select")`, `_number(min=5, max=1)`, `_in_field(min=1)` and `_fields({}, {})`, with the same rule |
| `test_inputs_basic.py::test_check_refuses_a_form_whose_answer_could_not_fit` | delete | C5 | widget case `_sized_form(254)` asserts the `size` fault and its message at the limit |
| `test_inputs_ordered.py::test_props_faults`, rows `items: ["a"]`, `items: ["a", "a"]`, `step: 9`, `max: 1000000, step: 1` | delete rows | C5 | widget cases `ranking` `["a"]`, `ranking` `["a", "a"]`, slider `step: 9` and slider `max: 20000` (the same step-count rule) |
| `test_inputs_ordered.py::test_props_faults`, rows `min: 5, max: 1`, `min: 1, max: 1` | delete rows | C5 | widget cases `{**_SLIDER, "min": 9}` and `{**_SLIDER, "min": 5}` (min above and equal to max) |
| `test_inputs_ordered.py::test_props_faults`, rows `labels: ["x"]`, `labels: ["x", ""]` | delete rows | C5 | widget cases slider `labels: ["a"]` and `labels: ["a", " "]` |
| `test_inputs_ordered.py::test_check_refuses_a_ranking_whose_answer_could_not_fit` | delete | C5 | widget case `_ranked(260)` asserts the `size` fault and its message at the limit |
| `test_inputs_ordered.py::test_browser_slider_valuetext_starts_unchosen` | delete | C5 | "Not chosen yet" and the dropped `aria-valuetext` after a key: `test_browser_fill_readout_valuetext_and_csp`; the mid-scale thumb, and `Home` plus three steps giving 6: `test_browser_slider_needs_a_move_then_posts_and_read_only_stays_inert` |
| `test_actions.py::test_text_types_allow_suggestion`, `::test_other_types_refuse_suggestion` | merge into `test_only_text_types_allow_suggestion` | C5 | their menu assertion repeats `test_entries_write_only_accepted_kinds` (`suggest` present exactly when the kind is allowed, outside a part); the kind sets are one set equality |
| `test_actions.py::test_entries_write_only_accepted_kinds` | merge flag cases into a loop (44 cases to 11) | D12 | two stacked `parametrize` decorators |
| `test_inputs_basic.py::test_props_faults`, `test_inputs_ordered.py::test_props_faults` | keep | C5 | static identical-body hit; the rows left are different components and props, and they assert the rule id where the property cases of `test_blocks_inputs.py` assert only the field |
| `test_inputs_basic.py::test_invalid_props_are_not_answerable`, `test_inputs_ordered.py::test_invalid_props_are_not_answerable` | keep | C5 | static identical-body hit; different components and faults |
| `test_actions.py::test_component_block_type` | keep | C5 | static identical-body hit with tests of other functions; each row pins one component's published `data-block-type`, which is module-level spec data that mutation does not judge |

## Survivors

The 163 `tavle.blocks.inputs*` mutants that `audit/py-blocks.md` records as not killed have their rows in `audit/inputs-a.md` (task 5.6, same source globs); they are not repeated here.
`audit/py-page.md` records none for `tavle.page.actions`.
The final run leaves three mutants not killed, none of them `slow-only`:

| mutant | outcome | evidence |
|---|---|---|
| tavle.blocks.inputs.x_option_label_value__mutmut_4 | equivalent | The label default is read only for a table without a label; every caller passes options that passed `option_faults`, which requires one. |
| tavle.blocks.inputs.x_option_label_value__mutmut_6 | equivalent | The label default is read only for a table without a label; every caller passes options that passed `option_faults`, which requires one. |
| tavle.blocks.inputs.x_option_label_value__mutmut_9 | equivalent | The label default is read only for a table without a label; every caller passes options that passed `option_faults`, which requires one. |
