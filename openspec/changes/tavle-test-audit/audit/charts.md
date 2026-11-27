# Audit: charts (task 5.8, base `4dfadfc`) — incomplete

- Source (`--only` globs): `tavle.blocks.charts.*`, `tavle.blocks_render.chart*`
- Test files: `tests/page/test_blocks_charts_diagrams.py`, `tests/page/test_rich_chart.py`, `tests/page/test_rich_chart_events.py`, `tests/page/test_blocks_code_diff.py`
- Mutation score before: 91% (3,754 mutants: 3,419 killed, 333 survived, 1 timeout, 1 segfault), selected from the `blocks` and `blocks_render` baseline copies; package scores in `audit/py-blocks.md` are 80% and 92%.
- Mutation score after: not yet measured.

## Progress

Added `test_compact_scale_boundaries` in `test_rich_chart.py` for the positive and negative compact-format thresholds. Its mutant kills have not been verified. The C1 run, survivor dispositions, remaining file audits, and final mutation run remain outstanding. No tests were removed.

## Verified survivor kills

| mutant | result | evidence |
|---|---|---|
| `tavle.blocks_render.chart_scale.x_compact__mutmut_4` | killed | `test_rich_chart.py::test_compact_scale_boundaries[1000000-1M]`, direct run with this mutant and the owned test file |
| `tavle.blocks_render.chart_scale.x_compact__mutmut_7` | killed | `test_rich_chart.py::test_compact_scale_boundaries[10000-10k]` and `[-10000--10k]`, direct run with this mutant and the owned test file |

| `tavle.blocks_render.chart_scale.x_compact__mutmut_23` | equivalent | Omitting `fmt`'s second argument uses its default `None`, identical to the original explicit argument. |
| `tavle.blocks_render.chart_scale.x_fmt__mutmut_8` | equivalent | Numeric fixed-point formatting cannot contain `X`, so adding `X` to the characters stripped changes nothing. |
| `tavle.blocks_render.chart_scale.x_fmt__mutmut_9` | equivalent | Numeric fixed-point formatting cannot contain `X`, so adding `X` to the characters stripped changes nothing. |
| `tavle.blocks_render.chart_scale.x_fmt__mutmut_15` | equivalent | Fixed-point formatting contains a digit even after trailing zeroes and the decimal point are stripped, so `text` cannot be empty. |

## Static scan decisions

| test id | decision | criterion | evidence |
|---|---|---|---|
| `test_blocks_charts_diagrams.py::test_block_is_client_side_and_bundled` | keep | C5 | Same body as the code/diff test but parametrized over different component names. |
| `test_blocks_charts_diagrams.py::test_family_shape_mistake_gets_one_fault_naming_the_field` | keep | C5 | Same body as inputs test but exercises diagram, flow, state and sequence fault cases. |
| `test_blocks_charts_diagrams.py::test_blank_text_and_empty_lists_fault_once` | keep | C5 | Same body as other files but checks different components and property paths. |
| `test_blocks_code_diff.py::test_block_is_client_side_and_bundled` | keep | C5 | Its parameters cover code and diff components, unlike the chart/diagram cases. |
| `test_blocks_code_diff.py::test_blank_text_and_empty_lists_fault_once` | keep | C5 | Its parameter rows check code/diff component paths distinct from chart/diagram rows. |

## Stop at the area budget

The 20-minute stop rule in `tasks.md` line 14 applies. The grouped C1 run on `tavle.blocks.charts.*` finished in 243.394s and lost 94 kills; the exact names are in `/var/tmp/tmp-alec/t5-charts-c1.log`. The render half had 3,193 affected baseline kills and was stopped after 529.532s at the budget; it has no completed result. Neither per-file C1 nor the final mutation run was started. The remaining 329 baseline survivors still need a disposition, and the two CSS source-inspection tests in `test_rich_chart.py` still need a C3 decision. Do not interpret the grouped C1 loss as a unique kill by any one file.

Scratch retained for the lead: `/var/tmp/tmp-alec/mutate-tavle-t5-charts-blocks`, `mutate-tavle-t5-charts-blocks-without`, `mutate-tavle-t5-charts-render`, `mutate-tavle-t5-charts-render-without`, `mutate-tavle-t5-charts-verify`, and `/var/tmp/tmp-alec/t5-charts*.log`.
