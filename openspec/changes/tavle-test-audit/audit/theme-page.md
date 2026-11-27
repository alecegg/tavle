# Audit: theme-page (task 5.3, base `7420232`)

- Source (`--only` globs): `tavle.theme.*`, `tavle.contrast.*`
- Test files: `tests/test_contrast.py`, `tests/test_contrast_values.py`, `tests/page/test_page_theme_layers.py`, `tests/page/test_theme_page.py`, `tests/page/test_theme_show.py`, `tests/page/test_theme_export.py`, `tests/page/test_extract_theme_coverage.py`
- Collected tests (file order as above): 39 before (16, 9, 2, 3, 3, 1, 5), 36 after (16, 6, 2, 3, 3, 1, 5). Test functions: 25 before, 21 after.
- Mutation score before: 85% (1628 mutants: 1389 killed, 233 survived, 6 timeout; `audit/py-theme.md` 84% and `tavle.contrast.*` in `audit/py-top.md` 95%)
- Mutation score after: 95% (1628 mutants: 1559 killed, 67 survived, 2 timeout). The full run includes the 5.2 theme tests. A fresh rerun of `theme.show`, `theme.merge` and `contrast` on the final test files left the same 21 mutants alive.

## C1 (leave-one-out)

Each run used a copy of the baseline's `mutants/` under a `theme-page-*` tag, because `--without` writes to `<baseline>-without` and 5.2 reads `t26` too.

| `--without` | mutants judged (baseline) | lost kills |
|---|---|---|
| `test_contrast.py` | `tavle.contrast.*` (`top`) | 40, so not a candidate |
| `test_contrast_values.py` | `tavle.contrast.*` (`top`) | 8, so not a candidate |
| the five `tests/page/` files together | `tavle.contrast.*` (`top`) | none |
| the five `tests/page/` files together | `tavle.theme.*` (`t26`) | 29, all in `theme.merge` and `theme.show` |
| each of the five, on those 29 | `t26` | `test_theme_show.py` 27, so not a candidate; the other four none |

Neither contrast file covers a `tavle.theme.*` mutant in `t26`.
The two `merge` mutants lost only by the joint run (`x_resolve_layers__mutmut_113`, `_122`) have more than one killer among the five.

Three of the four flagged files test `tavle.page` modules, so they were also judged against the `page` baseline (`--only 'tavle.page.theme_page.*' --only 'tavle.page.assemble.*'`).
Each is the only killer of at least one mutant there. Mode was per file; no test was removed on C1 evidence.

## Decisions

| test id | decision | criterion | evidence |
|---|---|---|---|
| `test_contrast.py::test_black_on_white_is_21` | delete | C5 | same call and fact as the first row of `test_ratio_matches_reference_values` (black on white is 21.0) |
| `test_contrast.py::test_parse_rejects_other_colour_syntax` | merge into `test_contrast_values.py::test_unsupported_colour_error_quotes_the_text` | C5 | same call and raise path; the `#fff` row now also asserts the whole message |
| `test_contrast_values.py::test_alpha_is_clamped_to_the_unit_range` | merge into `test_contrast.py::test_parse_rgba` | C5 | the two clamp rows moved and assert the whole tuple; the `50%` row repeated the percent-alpha row |
| `test_contrast_values.py::test_a_ratio_exactly_at_the_margin_does_not_fail` | merge into `test_contrast.py::test_fail_margin_is_0_05` | C5 | same call and rule; `4.45` passes and `4.449` fails, which are tighter than the old `4.46` and `4.44` |
| `test_contrast.py::test_parse_rgba` | keep | C5 | static identical-body hit (`audit/static-scan.md`) with tests that call other code |
| `test_page_theme_layers.py` (both tests) | keep | C1 | alone kills `tavle.page.theme_page.x_page_theme__mutmut_7` |
| `test_theme_page.py` (all three) | keep | C1 | alone kills `x_page_theme__mutmut_20`, `_23` |
| `test_theme_export.py::test_every_block_export_with_and_without_theme` | keep | C1 | alone kills `tavle.page.assemble.x__section_script__mutmut_2`, `x_assemble_static__mutmut_8`; guards the self-contained export contract |
| `test_extract_theme_coverage.py` (both tests) | keep | C1 | `audit/inventory.md` classes it `asset-browser` (design A2); guards token parity between `00-tokens.css` and the theme code |
| `test_contrast_values.py::test_luminance_of_black_white_and_dark_channels` | changed | survivors | adds the sRGB cutoff value (see `x__channel__mutmut_8`) |

## Survivors

The `tavle.theme.*` mutants of `audit/py-theme.md` (227 survived, 6 timeout) are recorded once, in `audit/theme-core.md`.
This run's 64 non-killed theme mutants are the 62 marked equivalent there, plus `x_derive_colour__mutmut_135` and `_136`, which timed out here and were killed when 5.2 reran them alone.
No mutant is `slow-only`.

| mutant | outcome | evidence |
|---|---|---|
| tavle.contrast.x__channel__mutmut_8 | killed | `test_contrast_values.py::test_luminance_of_black_white_and_dark_channels` (`10.31475 / 255` equals `0.04045` exactly) |
| tavle.contrast.x_parse_rgba__mutmut_10 | equivalent | A missing alpha of 2.0 is clamped to 1.0. |
| tavle.contrast.x_composite__mutmut_25 | equivalent | Only the first three of the computed channels are returned. |
| tavle.contrast.x_contrast_ratio__mutmut_3 | equivalent | Compositing an opaque foreground returns its own channels, and alpha does not affect luminance. |
| tavle.contrast.x_contrast_ratio__mutmut_9 | equivalent | Same: it differs only for alpha 1, where compositing changes nothing. |
| tavle.contrast.x_contrast_ratio__mutmut_10 | equivalent | Same: alpha is at most 1, so only opaque foregrounds take the other branch. |
