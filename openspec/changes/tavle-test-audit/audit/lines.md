# Audit: lines (task 5.1, base `31829b1`)

- Source (`--only` globs): `tavle.lines.*`
- Test files: `tests/test_lines_parse.py`, `tests/test_lines_stream.py`, `tests/test_block_tables.py`
- Collected tests: 87 before (61, 12, 14), 98 after (77, 7, 14). Test functions: 36 before (22, 7, 7), 26 after (18, 1, 7).
- Mutation score before: 73% (634 mutants: 469 killed, 154 survived, 11 timeout; `audit/py-blocks.md`)
- Mutation score after: 94% (634 mutants: 598 killed, 36 survived, 0 timeout)

## C1 (leave-one-out, baseline `lines`)

- `--without tests/test_lines_parse.py`: 123 lost kills (swallowed-statement, error-path and cursor mutants), so the file is not a candidate.
- `--without tests/test_lines_stream.py`: 3 lost kills (`x__array__mutmut_22`, `x__array__mutmut_23`, `x_parse_lines__mutmut_51`). All three make the parser loop and are also lost without `test_lines_parse.py`, so neither file is their only killer. The final run kills all three. The stream file stays.
- `tests/test_block_tables.py`: covers 0 of the 469 killed `lines` mutants, and `audit/inventory.md` classes it `asset-browser`, so design A2 audits it by C2 to C5 only. No change: its one static hit (`test_blank_text_and_empty_lists_fault_once`, C5 identical body) checks different blocks and paths from the other files.

Mode was per file; no single test was removed on C1 evidence.

## Decisions

| test id | decision | criterion | evidence |
|---|---|---|---|
| `test_lines_parse.py::test_non_finite_number_rejected` | merge into `test_error_classes_have_lines` | C5 | `audit/static-scan.md` identical body; same `parse_lines` call, exact error now asserted |
| `test_lines_parse.py::test_lone_surrogate_rejected` | merge into `test_error_classes_have_lines` | C5 | `audit/static-scan.md` identical body |
| `test_lines_parse.py::test_raw_tab_in_string_has_clear_message` | merge into `test_error_classes_have_lines` | C5 | same call; the exact message row covers both substring checks |
| `test_lines_parse.py::test_huge_integer_is_an_error_not_a_crash` | merge into `test_error_classes_have_lines` | C5 | same call and rule, line, message facts (`huge-integer` row) |
| `test_lines_parse.py::test_literal_words_are_not_valid_ids` | merge into `test_error_classes_have_lines` | C5 | same call; rows `true`, `false`, `null`; the shared assert keeps "no statement from the failing line" |
| `test_lines_parse.py::test_deep_nesting_within_limit` | delete | C5 | `test_nesting_stops_after_32_levels` asserts no errors at 32 levels (was 20) and the depth error at 33 (was the 40-level table row) |
| `test_lines_parse.py::test_missing_close_paren_after_comma_and_value_forms` | merge into `test_missing_close_paren_does_not_swallow_next_statement` | C5 | same call and asserted fact |
| `test_lines_parse.py::test_partial_complete_text_has_no_pending` | keep, absorbs the stream copy | C5 | now also asserts the ids |
| `test_lines_stream.py::test_complete_text_has_no_pending` | delete | C5 | same input `"a = flow()\n"` and facts as `test_partial_complete_text_has_no_pending` |
| `test_lines_stream.py::test_pending_holds_cut_tail_and_renders_nothing` | merge into `test_partial_tail_is_pending_not_error` | C5 | its input is the second param |
| `test_lines_stream.py::test_strict_mode_still_errors_on_cut_tail` | merge into `test_partial_tail_is_pending_not_error` | C5 | strict half of that test asserts the same ids, rule and empty `pending` |
| `test_lines_stream.py::test_cut_reference_is_pending_not_error` | delete | C5 | `test_partial_mid_token_cutoff_is_pending` param `b` is a cut reference with the same facts |
| `test_lines_stream.py::test_real_errors_still_reported_while_streaming` | merge into `test_partial_still_reports_real_errors` | C5 | its input is the second param |
| `test_lines_stream.py::test_example_cut_at_every_offset` | merge into `test_every_offset_is_prefix_stable_and_never_raises` | C5 | same fact; examples now also get the never-shrinks and final-equality asserts |
| `test_lines_stream.py::test_every_offset_is_prefix_stable_and_never_raises` | keep | C1 | guards the published streaming contract (`partial=True` prefix stability) |
| `test_lines_parse.py::test_error_classes_have_lines` | changed | survivors | asserts the whole `ParseError`; rows added per error site; `junk` row is now one character so a short slice is caught |
| `test_lines_parse.py::test_values_of_every_type` | changed | survivors | adds `1E2` |
| `test_lines_parse.py::test_empty_and_comment_only` | changed | survivors | parametrized; adds a comment with no final newline |
| `test_lines_parse.py::test_partial_mid_token_cutoff_is_pending` | changed | survivors | adds the `1e999` tail |
| `test_lines_parse.py::test_refs_resolve_at_any_nesting` | added | survivors | see rows below |
| `test_lines_parse.py::test_commas_need_no_space` | added | survivors | see rows below |
| `test_lines_parse.py::test_nesting_stops_after_32_levels` | added | survivors | see rows below |
| both lines files, `pytestmark = pytest.mark.timeout(2, method="signal")` | added | survivors | a parser that stops advancing fails the test instead of ending as a mutmut timeout |

## Survivors

All 165 non-killed mutants of the baseline (154 survived, 11 timeout): 129 killed by a fast test, 36 equivalent, 0 slow-only.
"Killed" evidence is the first test that failed with the mutant active (`pytest -x` over the two lines files in a copy of the baseline's `mutants/`).

| mutant | result | evidence |
|---|---|---|
| tavle.lines.parse.x__array__mutmut_1 | killed | `test_lines_parse.py::test_pinned_examples_parse`, first param `'intro = recap(title: "Done", items: ["a", "b"])'` |
| tavle.lines.parse.x__array__mutmut_14 | killed | `test_lines_parse.py::test_refs_resolve_at_any_nesting` |
| tavle.lines.parse.x__array__mutmut_24 | killed | `test_lines_parse.py::test_commas_need_no_space` |
| tavle.lines.parse.x__array__mutmut_28 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: [1 2])'` |
| tavle.lines.parse.x__array__mutmut_33 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: [1 2])'` |
| tavle.lines.parse.x__array__mutmut_34 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: [1 2])'` |
| tavle.lines.parse.x__decode_string__mutmut_10 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "bad \\q")'` |
| tavle.lines.parse.x__decode_string__mutmut_13 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "q\\\n")'` |
| tavle.lines.parse.x__decode_string__mutmut_16 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "q\\\n")'` |
| tavle.lines.parse.x__decode_string__mutmut_22 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "\\udfff")'` |
| tavle.lines.parse.x__decode_string__mutmut_25 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "\\ud800")'` |
| tavle.lines.parse.x__decode_string__mutmut_26 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: a string that decodes holds no raw newline. |
| tavle.lines.parse.x__decode_string__mutmut_28 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "\\ud800")'` |
| tavle.lines.parse.x__decode_string__mutmut_29 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: a string that decodes holds no raw newline. |
| tavle.lines.parse.x__decode_string__mutmut_3 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "a\tb")'` |
| tavle.lines.parse.x__decode_string__mutmut_32 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "\\ud800")'` |
| tavle.lines.parse.x__decode_string__mutmut_33 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "\\ud800")'` |
| tavle.lines.parse.x__decode_string__mutmut_4 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "a\tb")'` |
| tavle.lines.parse.x__decode_string__mutmut_5 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "bad \\q")'` |
| tavle.lines.parse.x__decode_string__mutmut_6 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "a\tb")'` |
| tavle.lines.parse.x__decode_string__mutmut_8 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "a\tb")'` |
| tavle.lines.parse.x__int__mutmut_10 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: 999999999999999999999999999...` |
| tavle.lines.parse.x__int__mutmut_4 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: an integer token holds no newline. |
| tavle.lines.parse.x__int__mutmut_7 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: an integer token holds no newline. |
| tavle.lines.parse.x__key__mutmut_10 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {1: 2})'` |
| tavle.lines.parse.x__key__mutmut_11 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {1: 2})'` |
| tavle.lines.parse.x__key__mutmut_12 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {1: 2})'` |
| tavle.lines.parse.x__key__mutmut_13 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {1: 2})'` |
| tavle.lines.parse.x__key__mutmut_14 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {1: 2})'` |
| tavle.lines.parse.x__key__mutmut_7 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {1: 2})'` |
| tavle.lines.parse.x__key__mutmut_8 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {1: 2})'` |
| tavle.lines.parse.x__key__mutmut_9 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {1: 2})'` |
| tavle.lines.parse.x__number__mutmut_11 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: -)'` |
| tavle.lines.parse.x__number__mutmut_12 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: the number match failed, so the cursor is still at `start`. |
| tavle.lines.parse.x__number__mutmut_15 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: -)'` |
| tavle.lines.parse.x__number__mutmut_16 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: -)'` |
| tavle.lines.parse.x__number__mutmut_18 | killed | `test_lines_parse.py::test_partial_mid_token_cutoff_is_pending`, first param `'1e999'` |
| tavle.lines.parse.x__number__mutmut_30 | killed | `test_lines_parse.py::test_values_of_every_type` |
| tavle.lines.parse.x__number__mutmut_31 | killed | `test_lines_parse.py::test_values_of_every_type` |
| tavle.lines.parse.x__number__mutmut_35 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: a number token holds no newline. |
| tavle.lines.parse.x__number__mutmut_44 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: 1e999)'` |
| tavle.lines.parse.x__number__mutmut_45 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: a number token holds no newline. |
| tavle.lines.parse.x__number__mutmut_47 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: 1e999)'` |
| tavle.lines.parse.x__number__mutmut_48 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: a number token holds no newline. |
| tavle.lines.parse.x__number__mutmut_51 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: 1e999)'` |
| tavle.lines.parse.x__number__mutmut_52 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: 1e999)'` |
| tavle.lines.parse.x__number__mutmut_8 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: -)'` |
| tavle.lines.parse.x__number__mutmut_9 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: the number match failed, so the cursor is still at `start`. |
| tavle.lines.parse.x__object__mutmut_11 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: a key that parsed holds no newline and the cursor is just after it. |
| tavle.lines.parse.x__object__mutmut_16 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(o: {"k": 1, "k": 2})'` |
| tavle.lines.parse.x__object__mutmut_17 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: a key that parsed holds no newline and the cursor is just after it. |
| tavle.lines.parse.x__object__mutmut_19 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(o: {"k": 1, "k": 2})'` |
| tavle.lines.parse.x__object__mutmut_20 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: a key that parsed holds no newline and the cursor is just after it. |
| tavle.lines.parse.x__object__mutmut_24 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {k 1})'` |
| tavle.lines.parse.x__object__mutmut_28 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {k 1})'` |
| tavle.lines.parse.x__object__mutmut_29 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {k 1})'` |
| tavle.lines.parse.x__object__mutmut_33 | killed | `test_lines_parse.py::test_refs_resolve_at_any_nesting` |
| tavle.lines.parse.x__object__mutmut_37 | killed | `test_lines_parse.py::test_nesting_stops_after_32_levels`, first param `'{}'` |
| tavle.lines.parse.x__object__mutmut_38 | killed | `test_lines_parse.py::test_nesting_stops_after_32_levels`, first param `'{}'` |
| tavle.lines.parse.x__object__mutmut_43 | killed | `test_lines_parse.py::test_commas_need_no_space` |
| tavle.lines.parse.x__object__mutmut_46 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {k: 1 j: 2})'` |
| tavle.lines.parse.x__object__mutmut_47 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {k: 1 j: 2})'` |
| tavle.lines.parse.x__object__mutmut_48 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {k: 1 j: 2})'` |
| tavle.lines.parse.x__object__mutmut_49 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {k: 1 j: 2})'` |
| tavle.lines.parse.x__object__mutmut_50 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {k: 1 j: 2})'` |
| tavle.lines.parse.x__object__mutmut_51 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {k: 1 j: 2})'` |
| tavle.lines.parse.x__object__mutmut_52 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {k: 1 j: 2})'` |
| tavle.lines.parse.x__object__mutmut_53 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: {k: 1 j: 2})'` |
| tavle.lines.parse.x__props__mutmut_12 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(1: 2)'` |
| tavle.lines.parse.x__props__mutmut_13 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(1: 2)'` |
| tavle.lines.parse.x__props__mutmut_16 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(1: 2)'` |
| tavle.lines.parse.x__props__mutmut_17 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(1: 2)'` |
| tavle.lines.parse.x__props__mutmut_20 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'\n\na = flow(x: 1, x: 2)'` |
| tavle.lines.parse.x__props__mutmut_21 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: a prop name match holds no newline. |
| tavle.lines.parse.x__props__mutmut_23 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'\n\na = flow(x: 1, x: 2)'` |
| tavle.lines.parse.x__props__mutmut_24 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: a prop name match holds no newline. |
| tavle.lines.parse.x__props__mutmut_28 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x 1)'` |
| tavle.lines.parse.x__props__mutmut_32 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x 1)'` |
| tavle.lines.parse.x__props__mutmut_33 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x 1)'` |
| tavle.lines.parse.x__props__mutmut_41 | killed | `test_lines_parse.py::test_nesting_stops_after_32_levels`, first param `'[]'` |
| tavle.lines.parse.x__props__mutmut_46 | killed | `test_lines_parse.py::test_commas_need_no_space` |
| tavle.lines.parse.x__props__mutmut_50 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(\n  x: 1\n  y: 2\n)'` |
| tavle.lines.parse.x__props__mutmut_55 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(\n  x: 1\n  y: 2\n)'` |
| tavle.lines.parse.x__props__mutmut_56 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(\n  x: 1\n  y: 2\n)'` |
| tavle.lines.parse.x__props__mutmut_8 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: a prop name match holds no newline. |
| tavle.lines.parse.x__recover__mutmut_15 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(\n  x: 1\n  y: 2\n)'` (loops; the 2 s test timeout fails it) |
| tavle.lines.parse.x__recover__mutmut_16 | equivalent | Searching from `end - 1` adds only positions on the failing line or its newline; none can start a line holding `id =` before the next newline. |
| tavle.lines.parse.x__recover__mutmut_3 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow()\nb = flow()\na = flow()'` (loops; the 2 s test timeout fails it) |
| tavle.lines.parse.x__recover__mutmut_5 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow()\nb = flow()\na = flow()'` (loops; the 2 s test timeout fails it) |
| tavle.lines.parse.x__recover__mutmut_8 | equivalent | `end == 0` cannot happen: `error_pos` is at or after the statement's first non-blank character, so no newline at index 0 follows it. |
| tavle.lines.parse.x__recover__mutmut_9 | equivalent | `end == 0` cannot happen: `error_pos` is at or after the statement's first non-blank character, so no newline at index 0 follows it. |
| tavle.lines.parse.x__rest_of_line_blank__mutmut_10 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow() x'` |
| tavle.lines.parse.x__rest_of_line_blank__mutmut_12 | equivalent | `find` starts after a `)`, so it never returns 0. |
| tavle.lines.parse.x__rest_of_line_blank__mutmut_13 | equivalent | `find` starts after a `)`, so it never returns 0. |
| tavle.lines.parse.x__rest_of_line_blank__mutmut_20 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow() x'` |
| tavle.lines.parse.x__rest_of_line_blank__mutmut_25 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow() x'` |
| tavle.lines.parse.x__rest_of_line_blank__mutmut_26 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow() x'` |
| tavle.lines.parse.x__rest_of_line_blank__mutmut_4 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow()\nb = flow() x'` |
| tavle.lines.parse.x__rest_of_line_blank__mutmut_6 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow()\nb = flow() x'` |
| tavle.lines.parse.x__statement__mutmut_10 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'(x)'` |
| tavle.lines.parse.x__statement__mutmut_13 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'true = flow()'` |
| tavle.lines.parse.x__statement__mutmut_14 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: an id match holds no newline. |
| tavle.lines.parse.x__statement__mutmut_16 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'true = flow()'` |
| tavle.lines.parse.x__statement__mutmut_17 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: an id match holds no newline. |
| tavle.lines.parse.x__statement__mutmut_23 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'A = flow()'` |
| tavle.lines.parse.x__statement__mutmut_24 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: an id match holds no newline. |
| tavle.lines.parse.x__statement__mutmut_26 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'A = flow()'` |
| tavle.lines.parse.x__statement__mutmut_27 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: an id match holds no newline. |
| tavle.lines.parse.x__statement__mutmut_31 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow()\nb = flow()\na = flow()'` |
| tavle.lines.parse.x__statement__mutmut_33 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow()\nb = flow()\na = flow()'` |
| tavle.lines.parse.x__statement__mutmut_34 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: an id match holds no newline. |
| tavle.lines.parse.x__statement__mutmut_36 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow()\nb = flow()\na = flow()'` |
| tavle.lines.parse.x__statement__mutmut_37 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: an id match holds no newline. |
| tavle.lines.parse.x__statement__mutmut_41 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a flow()'` |
| tavle.lines.parse.x__statement__mutmut_45 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a flow()'` |
| tavle.lines.parse.x__statement__mutmut_46 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a flow()'` |
| tavle.lines.parse.x__statement__mutmut_49 | equivalent | At `pos == len(text)` the following `expect('(')` raises the same `_Cutoff`; a failed match cannot be at the end because `peek()` ran first. |
| tavle.lines.parse.x__statement__mutmut_5 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'(x)'` |
| tavle.lines.parse.x__statement__mutmut_52 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = (x: 1)'` |
| tavle.lines.parse.x__statement__mutmut_57 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = (x: 1)'` |
| tavle.lines.parse.x__statement__mutmut_58 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = (x: 1)'` |
| tavle.lines.parse.x__statement__mutmut_6 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'(x)'` |
| tavle.lines.parse.x__statement__mutmut_60 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow x'` |
| tavle.lines.parse.x__statement__mutmut_64 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow x'` |
| tavle.lines.parse.x__statement__mutmut_65 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow x'` |
| tavle.lines.parse.x__statement__mutmut_9 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'(x)'` |
| tavle.lines.parse.x__string__mutmut_12 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(\n  x: "open\n)'` |
| tavle.lines.parse.x__string__mutmut_13 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: the cursor is still at `start` when this is raised. |
| tavle.lines.parse.x__string__mutmut_15 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(\n  x: "open\n)'` |
| tavle.lines.parse.x__string__mutmut_16 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: the cursor is still at `start` when this is raised. |
| tavle.lines.parse.x__string__mutmut_19 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(\n  x: "open\n)'` |
| tavle.lines.parse.x__string__mutmut_20 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(\n  x: "open\n)'` |
| tavle.lines.parse.x__string__mutmut_21 | killed | `test_lines_parse.py::test_pinned_examples_parse`, first param `'model = data-model(name: "User")\nstate...` (loops; the 2 s test timeout fails it) |
| tavle.lines.parse.x__swallowed_next_statement__mutmut_3 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = (x: 1)'` (loops; the 2 s test timeout fails it) |
| tavle.lines.parse.x__swallowed_next_statement__mutmut_7 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = (x: 1)'` (loops; the 2 s test timeout fails it) |
| tavle.lines.parse.x__swallowed_next_statement__mutmut_9 | killed | `test_lines_parse.py::test_nesting_stops_after_32_levels`, first param `'[]'` (loops; the 2 s test timeout fails it) |
| tavle.lines.parse.x__value__mutmut_1 | killed | `test_lines_parse.py::test_nesting_stops_after_32_levels`, first param `'[]'` |
| tavle.lines.parse.x__value__mutmut_16 | killed | `test_lines_parse.py::test_refs_resolve_at_any_nesting` |
| tavle.lines.parse.x__value__mutmut_24 | killed | `test_lines_parse.py::test_refs_resolve_at_any_nesting` |
| tavle.lines.parse.x__value__mutmut_3 | killed | `test_lines_parse.py::test_nesting_stops_after_32_levels`, first param `'[]'` |
| tavle.lines.parse.x__word__mutmut_11 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: @)'` |
| tavle.lines.parse.x__word__mutmut_12 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: the word match either failed (cursor unmoved) or holds no newline. |
| tavle.lines.parse.x__word__mutmut_14 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: @)'` |
| tavle.lines.parse.x__word__mutmut_15 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: the word match either failed (cursor unmoved) or holds no newline. |
| tavle.lines.parse.x__word__mutmut_20 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: b)'` |
| tavle.lines.parse.x__word__mutmut_21 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: the word match either failed (cursor unmoved) or holds no newline. |
| tavle.lines.parse.x__word__mutmut_23 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: b)'` |
| tavle.lines.parse.x__word__mutmut_24 | equivalent | `pos` only picks the reported line and the recovery newline, and here both positions are on one line: the word match either failed (cursor unmoved) or holds no newline. |
| tavle.lines.parse.x_parse_lines__mutmut_15 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: 1'` |
| tavle.lines.parse.x_parse_lines__mutmut_16 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: 1'` |
| tavle.lines.parse.x_parse_lines__mutmut_17 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: 1'` |
| tavle.lines.parse.x_parse_lines__mutmut_21 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: 1'` |
| tavle.lines.parse.x_parse_lines__mutmut_34 | killed | `test_lines_parse.py::test_missing_close_paren_does_not_swallow_next_statement`, first param `'a = flow(x: 1\nb = flow()\nc = flow()'` |
| tavle.lines.parse.x_parse_lines__mutmut_35 | killed | `test_lines_parse.py::test_missing_close_paren_does_not_swallow_next_statement`, first param `'a = flow(x: 1\nb = flow()\nc = flow()'` |
| tavle.lines.parse.x_parse_lines__mutmut_36 | killed | `test_lines_parse.py::test_missing_close_paren_does_not_swallow_next_statement`, first param `'a = flow(x: 1\nb = flow()\nc = flow()'` |
| tavle.lines.parse.x_parse_lines__mutmut_42 | killed | `test_lines_parse.py::test_missing_close_paren_does_not_swallow_next_statement`, first param `'a = flow(x: 1\nb = flow()\nc = flow()'` |
| tavle.lines.parse.x_parse_lines__mutmut_62 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow()\nb = flow()\na = flow()'` (loops; the 2 s test timeout fails it) |
| tavle.lines.parse.x_parse_lines__mutmut_66 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow()\nb = flow()\na = flow()'` |
| tavle.lines.parse.xǁ_Cursorǁexpect__mutmut_3 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a flow()'` |
| tavle.lines.parse.xǁ_Cursorǁfail__mutmut_8 | killed | `test_lines_parse.py::test_error_classes_have_lines`, first param `'a = flow(x: "q\\\n")'` |
| tavle.lines.parse.xǁ_Cursorǁskip__mutmut_14 | killed | `test_lines_parse.py::test_empty_and_comment_only`, first param `'# no newline at the end'` |
| tavle.lines.parse.xǁ_Cursorǁskip__mutmut_16 | equivalent | `find` starts at the `#`, so it returns -1 or an index above 0, or the `#` itself at 0 which is not a newline. |
| tavle.lines.parse.xǁ_Cursorǁskip__mutmut_17 | equivalent | `find` starts at the `#`, so it returns -1 or an index above 0, or the `#` itself at 0 which is not a newline. |
| tavle.lines.parse.xǁ_Cursorǁskip__mutmut_18 | killed | `test_lines_parse.py::test_pinned_examples_parse`, first param `'model = data-model(name: "User")\nstate...` (loops; the 2 s test timeout fails it) |
| tavle.lines.parse.xǁ_Failǁ__init____mutmut_1 | equivalent | Only `Exception.args` changes; `parse_lines` reads `pos`, `rule` and `message` and never lets `_Fail` escape. |
