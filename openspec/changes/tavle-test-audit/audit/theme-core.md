# Audit: theme-core (task 5.2, base `7420232`)

- Source (`--only` globs): `tavle.theme.*`
- Test files: `tests/test_theme_css.py`, `tests/test_theme_derive_colour.py`, `tests/test_theme_derive_shape.py`, `tests/test_theme_layers.py`, `tests/test_theme_presets_load.py`, `tests/test_theme_presets_valid.py`, `tests/test_theme_tokens.py`, `tests/test_theme_validate.py`
- Collected tests (file order as above): 32 before (2, 2, 1, 7, 3, 5, 9, 3), 74 after (6, 8, 2, 23, 2, 9, 14, 10). Test functions: 19 before, 34 after.
- Mutation score before: 84% (1505 mutants: 1272 killed, 227 survived, 6 timeout; `audit/py-theme.md`)
- Mutation score after: 95% (1505 mutants: 1443 killed, 62 survived, 0 timeout). The full run gave 1441 killed, 62 survived, 2 timeout; `x_derive_colour__mutmut_135` and `_136` were then rerun alone with `--only` after the grey-on-grey case moved into the first-run test, and both were killed.

## C1 (leave-one-out, baseline `t26`): NOT RUN

The 20-minute budget ran out after the final mutation run, so the procedure's stop rule applies and task 5.2 stays unticked. No test was deleted or merged on C1 evidence. Still to do, once per file, with `just mutate --without tests/test_theme_<name>.py --baseline t26 --only 'tavle.theme.*'`, then `just mutate --tag t26-without --clean`. Affected mutants per file: css 1146, derive_colour 487, derive_shape 179, layers 183, presets_load 126, presets_valid 704, tokens 43, validate 807 (3,675 in total; at the 1.3 to 1.7 s per mutant of `audit/leave-one-out.md` that is about 80 to 105 minutes, and `css` alone exceeds one job).

## Decisions (C2 to C5)

| test id | decision | criterion | evidence |
|---|---|---|---|
| `test_theme_presets_load.py::test_varde_complete` | delete | C5 | same `load_preset("varde")` call and the same two set assertions as `test_theme_presets_valid.py::test_preset_is_complete_and_valid[varde]` |
| `test_theme_derive_shape.py::test_shared_defaults_and_coverage` | keep | C3 | static hit reads `00-tokens.css`; it guards CSS and Python token parity, not a copy of `derive_shape` |
| `test_theme_tokens.py::test_colour_rejects_css` | keep | C5 | static identical body with `test_bad_intervals_error`, which calls different code |
| `test_theme_validate.py::test_preset_and_derived_dark_pass` | keep | C4 | `validate_theme` raises on failure; the derived-dark call has no other test |

The digest tests (`test_pinned_derivations`, `test_preset_css_is_pinned`) pin current output; an intended colour change updates the digest.

## Survivors

Every mutant listed in `audit/py-theme.md` (227 survived, 6 timeout). No mutant is `slow-only`. Killer ids are the first failing test among the eight owned files.

| mutant | outcome | evidence |
|---|---|---|
| tavle.theme.css.x__value__mutmut_1 | killed | `test_theme_css.py::test_error_messages`, param `light0-^Invalid theme colour$` |
| tavle.theme.css.x__value__mutmut_7 | killed | `test_theme_css.py::test_error_messages`, param `light0-^Invalid theme colour$` |
| tavle.theme.css.x__value__mutmut_8 | killed | `test_theme_css.py::test_error_messages`, param `light0-^Invalid theme colour$` |
| tavle.theme.css.x__value__mutmut_9 | killed | `test_theme_css.py::test_error_messages`, param `light0-^Invalid theme colour$` |
| tavle.theme.css.x__value__mutmut_10 | killed | `test_theme_css.py::test_error_messages`, param `light0-^Invalid theme colour$` |
| tavle.theme.css.x__value__mutmut_23 | equivalent | The formatted number holds no `X`, so the strip set removes the same characters. |
| tavle.theme.css.x__value__mutmut_24 | equivalent | The formatted number holds no `X`, so the strip set removes the same characters. |
| tavle.theme.css.x__value__mutmut_25 | equivalent | A `.6f` number keeps its integer digit, so the stripped text is never empty. |
| tavle.theme.css.x__value__mutmut_31 | killed | `test_theme_css.py::test_error_messages`, param `light1-^Invalid theme value: 'red'$` |
| tavle.theme.css.x__declarations__mutmut_4 | killed | `test_theme_css.py::test_error_messages`, param `light2-^Invalid theme name: 'a'$` |
| tavle.theme.css.x_theme_css__mutmut_3 | killed | `test_theme_css.py::test_exact_output` |
| tavle.theme.css.x_theme_css__mutmut_6 | killed | `test_theme_css.py::test_exact_output` |
| tavle.theme.css.x_style_element__mutmut_5 | killed | `test_theme_css.py::test_rejects_injection` |
| tavle.theme.css.x_style_element__mutmut_6 | killed | `test_theme_css.py::test_rejects_injection` |
| tavle.theme.css.x_style_element__mutmut_7 | killed | `test_theme_css.py::test_rejects_injection` |
| tavle.theme.css.x_style_element__mutmut_8 | killed | `test_theme_css.py::test_rejects_injection` |
| tavle.theme.derive_colour.x__rgba__mutmut_24 | equivalent | `value[5:8]` of a seven-character colour equals `value[5:7]`. |
| tavle.theme.derive_colour.x__hls__mutmut_10 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x__hls__mutmut_12 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x__over__mutmut_3 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x__over__mutmut_4 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x__over__mutmut_5 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x__over__mutmut_6 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x__over__mutmut_7 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x__over__mutmut_10 | equivalent | Both zipped slices have length 3, so `strict` has no effect. |
| tavle.theme.derive_colour.x__over__mutmut_13 | equivalent | Both zipped slices have length 3, so `strict` has no effect. |
| tavle.theme.derive_colour.x__over__mutmut_16 | equivalent | Both zipped slices have length 3, so `strict` has no effect. |
| tavle.theme.derive_colour.x__over__mutmut_17 | equivalent | The tint is only a contrast background, and the ratio ignores a background's alpha. |
| tavle.theme.derive_colour.x_derive_dark__mutmut_19 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x_derive_dark__mutmut_30 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x_derive_dark__mutmut_53 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x_derive_dark__mutmut_54 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-1e9840 6c189c 24279e 9851d5 814204 136` |
| tavle.theme.derive_colour.x_derive_dark__mutmut_55 | equivalent | Only the sunk surface changes (to black). It is darker than `surface` either way and every candidate is lighter, so `surface` is always the tighter ratio. |
| tavle.theme.derive_colour.x_derive_dark__mutmut_60 | equivalent | The value is overwritten by the first loop iteration, which always runs. |
| tavle.theme.derive_colour.x_derive_dark__mutmut_67 | equivalent | The value is overwritten by the first loop iteration, which always runs. |
| tavle.theme.derive_colour.x_derive_dark__mutmut_72 | equivalent | The value is overwritten by the first loop iteration, which always runs. |
| tavle.theme.derive_colour.x_derive_dark__mutmut_76 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x_derive_dark__mutmut_77 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x_derive_dark__mutmut_78 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x_derive_dark__mutmut_79 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x_derive_dark__mutmut_80 | equivalent | `range(70, 102, 2)` yields the same steps as `range(70, 101, 2)`. |
| tavle.theme.derive_colour.x_derive_dark__mutmut_81 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x_derive_dark__mutmut_90 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x_derive_dark__mutmut_95 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x_derive_dark__mutmut_105 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x_derive_dark__mutmut_111 | equivalent | Differs only when a float contrast ratio equals the threshold exactly; ratios are sums of `**2.4` channel terms and no input hits it. |
| tavle.theme.derive_colour.x_derive_dark__mutmut_112 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_dark-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_16 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_17 | equivalent | A sum of three integer channels is never 382.5. |
| tavle.theme.derive_colour.x_derive_colour__mutmut_18 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f8080 7670eb 940bd5 335f97 3daad8 6` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_53 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_86 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_87 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_88 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f8080 7670eb 940bd5 335f97 3daad8 6` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_89 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_99 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_102 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_109 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_112 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_115 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_118 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_121 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_134 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_135 | killed | `test_theme_derive_colour.py::test_series_override_and_interactive_border_step` (grey on grey; loops, the 2 s test timeout fails it) |
| tavle.theme.derive_colour.x_derive_colour__mutmut_136 | killed | `test_theme_derive_colour.py::test_series_override_and_interactive_border_step` (grey on grey; loops, the 2 s test timeout fails it) |
| tavle.theme.derive_colour.x_derive_colour__mutmut_143 | equivalent | Differs only when a float contrast ratio equals the threshold exactly; ratios are sums of `**2.4` channel terms and no input hits it. |
| tavle.theme.derive_colour.x_derive_colour__mutmut_144 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-151515 161616 d9d9d9 a745ad db6d88 3` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_153 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_155 | killed | `test_theme_css.py::test_scopes_and_declarations` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_156 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-151515 161616 d9d9d9 a745ad db6d88 3` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_157 | killed | `test_theme_css.py::test_scopes_and_declarations` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_158 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_159 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-151515 161616 d9d9d9 a745ad db6d88 3` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_160 | killed | `test_theme_derive_colour.py::test_series_override_and_interactive_border_step` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_218 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f8080 7670eb 940bd5 335f97 3daad8 6` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_219 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f8080 7670eb 940bd5 335f97 3daad8 6` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_220 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f8080 7670eb 940bd5 335f97 3daad8 6` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_221 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f8080 7670eb 940bd5 335f97 3daad8 6` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_223 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_224 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_225 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_226 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_274 | killed | `test_theme_derive_colour.py::test_series_override_and_interactive_border_step` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_319 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_333 | equivalent | The value is overwritten by the first loop iteration, which always runs. |
| tavle.theme.derive_colour.x_derive_colour__mutmut_335 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_340 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_342 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_343 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_344 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_349 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f8080 7670eb 940bd5 335f97 3daad8 6` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_363 | equivalent | Differs only when a float contrast ratio equals the threshold exactly; ratios are sums of `**2.4` channel terms and no input hits it. |
| tavle.theme.derive_colour.x_derive_colour__mutmut_364 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f8080 7670eb 940bd5 335f97 3daad8 6` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_372 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_377 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_colour.x_derive_colour__mutmut_378 | killed | `test_theme_derive_colour.py::test_pinned_derivations`, param `derive_colour-7f7f80 3cfde6 f1c26b 30f90e c7dd01 e` |
| tavle.theme.derive_shape.x__number__mutmut_6 | equivalent | The formatted number holds no `X`, so the strip set removes the same characters. |
| tavle.theme.derive_shape.x__number__mutmut_7 | equivalent | The formatted number holds no `X`, so the strip set removes the same characters. |
| tavle.theme.derive_shape.x__number__mutmut_8 | equivalent | A `.6f` number keeps its integer digit, so the stripped text is never empty. |
| tavle.theme.derive_shape.x_derive_shape__mutmut_35 | killed | `test_theme_derive_shape.py::test_scales_fonts_and_case` |
| tavle.theme.derive_shape.x_derive_shape__mutmut_62 | killed | `test_theme_derive_shape.py::test_scales_fonts_and_case` |
| tavle.theme.derive_shape.x_derive_shape__mutmut_69 | killed | `test_theme_derive_shape.py::test_scales_fonts_and_case` |
| tavle.theme.derive_shape.x_derive_shape__mutmut_70 | killed | `test_theme_derive_shape.py::test_scales_fonts_and_case` |
| tavle.theme.derive_shape.x_derive_shape__mutmut_99 | equivalent | Both zipped tuples are literals of length 6, so `strict` has no effect. |
| tavle.theme.derive_shape.x_derive_shape__mutmut_102 | equivalent | Both zipped tuples are literals of length 6, so `strict` has no effect. |
| tavle.theme.derive_shape.x_derive_shape__mutmut_121 | equivalent | Both zipped tuples are literals of length 6, so `strict` has no effect. |
| tavle.theme.derive_shape.x_derive_shape__mutmut_124 | killed | `test_theme_derive_shape.py::test_scales_fonts_and_case` |
| tavle.theme.derive_shape.x_derive_shape__mutmut_151 | killed | `test_theme_derive_shape.py::test_scales_fonts_and_case` |
| tavle.theme.derive_shape.x_derive_shape__mutmut_169 | killed | `test_theme_derive_shape.py::test_scales_fonts_and_case` |
| tavle.theme.layers.x__token__mutmut_11 | equivalent | `n=3` is the `get_close_matches` default. |
| tavle.theme.layers.x__token__mutmut_12 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-rad = 1-f: unknown token 'rad' with val` |
| tavle.theme.layers.x__token__mutmut_13 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-series = 1-f: unknown token 'series' wi` |
| tavle.theme.layers.x__token__mutmut_17 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-zzzzzz = 1-f: unknown token 'zzzzzz' wi` |
| tavle.theme.layers.x__token__mutmut_19 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-series = 1-f: unknown token 'series' wi` |
| tavle.theme.layers.x__token__mutmut_20 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-zzzzzz = 1-f: unknown token 'zzzzzz' wi` |
| tavle.theme.layers.x__preset__mutmut_2 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-preset = "papr"-f: preset 'papr': expec` |
| tavle.theme.layers.x__preset__mutmut_5 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-preset = "papr"-f: preset 'papr': expec` |
| tavle.theme.layers.x__preset__mutmut_6 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-preset = "papr"-f: preset 'papr': expec` |
| tavle.theme.layers.x__preset__mutmut_7 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-preset = 5-f: preset 5: expected one of` |
| tavle.theme.layers.x__preset__mutmut_15 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-preset = "papr"-f: preset 'papr': expec` |
| tavle.theme.layers.x__preset__mutmut_16 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-preset = "papr"-f: preset 'papr': expec` |
| tavle.theme.layers.x__preset__mutmut_17 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-preset = "zzz"-f: preset 'zzz': expecte` |
| tavle.theme.layers.x__preset__mutmut_19 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-preset = "parde"-f: preset 'parde': exp` |
| tavle.theme.layers.x__preset__mutmut_20 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-preset = "zzz"-f: preset 'zzz': expecte` |
| tavle.theme.layers.x_parse_toml__mutmut_10 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-preset = "papr"-f: preset 'papr': expec` |
| tavle.theme.layers.x_parse_toml__mutmut_19 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-light = 1-f: light 1: expected table` |
| tavle.theme.layers.x_parse_toml__mutmut_29 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_toml-[light]\nradius = 3-f: radius 3: expect` |
| tavle.theme.layers.x_parse_frontmatter__mutmut_1 | killed | `test_theme_layers.py::test_frontmatter_default_label_and_number` |
| tavle.theme.layers.x_parse_frontmatter__mutmut_2 | killed | `test_theme_layers.py::test_frontmatter_default_label_and_number` |
| tavle.theme.layers.x_parse_frontmatter__mutmut_9 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_frontmatter-source9-f: preset 'zzz': expecte` |
| tavle.theme.layers.x_parse_frontmatter__mutmut_29 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_frontmatter-source10-f: unknown token 'zzzzz` |
| tavle.theme.layers.x_parse_frontmatter__mutmut_33 | killed | `test_theme_layers.py::test_frontmatter_default_label_and_number` |
| tavle.theme.layers.x_parse_frontmatter__mutmut_34 | killed | `test_theme_layers.py::test_frontmatter_default_label_and_number` |
| tavle.theme.layers.x_parse_frontmatter__mutmut_35 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_frontmatter-source11-f: radius 'wide': expec` |
| tavle.theme.layers.x_parse_frontmatter__mutmut_38 | killed | `test_theme_layers.py::test_frontmatter_default_label_and_number` |
| tavle.theme.layers.x_parse_frontmatter__mutmut_43 | killed | `test_theme_layers.py::test_frontmatter_default_label_and_number` |
| tavle.theme.layers.x_parse_frontmatter__mutmut_59 | killed | `test_theme_layers.py::test_exact_errors`, param `parse_frontmatter-source10-f: unknown token 'zzzzz` |
| tavle.theme.merge.x_resolve_layers__mutmut_22 | killed | `test_theme_layers.py::test_resolved_sources_name_each_layer` |
| tavle.theme.merge.x_resolve_layers__mutmut_23 | killed | `test_theme_layers.py::test_resolved_sources_name_each_layer` |
| tavle.theme.merge.x_resolve_layers__mutmut_34 | killed | `test_theme_layers.py::test_resolved_sources_name_each_layer` |
| tavle.theme.merge.x_resolve_layers__mutmut_35 | killed | `test_theme_layers.py::test_resolved_sources_name_each_layer` |
| tavle.theme.merge.x_resolve_layers__mutmut_36 | killed | `test_theme_layers.py::test_resolved_sources_name_each_layer` |
| tavle.theme.merge.x_resolve_layers__mutmut_49 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.merge.x_resolve_layers__mutmut_53 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.merge.x_resolve_layers__mutmut_54 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.merge.x_resolve_layers__mutmut_58 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.merge.x_resolve_layers__mutmut_62 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.merge.x_resolve_layers__mutmut_63 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.merge.x_resolve_layers__mutmut_75 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.merge.x_resolve_layers__mutmut_79 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.merge.x_resolve_layers__mutmut_80 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.merge.x_resolve_layers__mutmut_83 | killed | `test_theme_layers.py::test_resolved_sources_name_each_layer` |
| tavle.theme.merge.x_resolve_layers__mutmut_84 | equivalent | Every dark name already has a source, so `setdefault` never stores its default. |
| tavle.theme.merge.x_resolve_layers__mutmut_85 | killed | `test_theme_layers.py::test_resolved_sources_name_each_layer` |
| tavle.theme.merge.x_resolve_layers__mutmut_86 | equivalent | Every dark name already has a source, so `setdefault` never stores its default. |
| tavle.theme.merge.x_resolve_layers__mutmut_89 | equivalent | Every dark name already has a source, so `setdefault` never stores its default. |
| tavle.theme.merge.x_resolve_layers__mutmut_90 | equivalent | Every dark name already has a source, so `setdefault` never stores its default. |
| tavle.theme.merge.x_resolve_layers__mutmut_94 | killed | `test_theme_layers.py::test_merged_contrast_failure_names_the_last_layer` |
| tavle.theme.merge.x_resolve_layers__mutmut_99 | killed | `test_theme_layers.py::test_merged_contrast_failure_names_the_last_layer` |
| tavle.theme.merge.x_resolve_layers__mutmut_104 | equivalent | The default label is used only with no layers, where the shipped `varde` preset cannot fail validation. |
| tavle.theme.merge.x_resolve_layers__mutmut_105 | equivalent | The default label is used only with no layers, where the shipped `varde` preset cannot fail validation. |
| tavle.theme.presets.x_load_preset__mutmut_4 | killed | `test_theme_presets_load.py::test_unknown_preset` |
| tavle.theme.presets.x_load_preset__mutmut_10 | equivalent | `files(None)` anchors at the calling module's package, which is `tavle.theme`. |
| tavle.theme.presets.x_load_preset__mutmut_16 | equivalent | The label shows only in errors from shipped preset files, which all parse. |
| tavle.theme.presets.x_load_preset__mutmut_19 | equivalent | The preset files are ASCII, which every ASCII-compatible locale decodes the same. |
| tavle.theme.presets.x_load_preset__mutmut_21 | equivalent | Codec names are case-insensitive. |
| tavle.theme.show.x__rule__mutmut_2 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x__rule__mutmut_3 | equivalent | Every catalog token has both bounds or neither. |
| tavle.theme.show.x__rule__mutmut_4 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x__rule__mutmut_5 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x__rule__mutmut_6 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x__rule__mutmut_7 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x__rule__mutmut_8 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x__rule__mutmut_9 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x__rule__mutmut_10 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x__rule__mutmut_11 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x_catalog_text__mutmut_6 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x_catalog_text__mutmut_7 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x_catalog_text__mutmut_8 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x_catalog_text__mutmut_10 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x_catalog_text__mutmut_19 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.show.x_values_text__mutmut_2 | killed | `test_theme_tokens.py::test_catalog_and_values_text` |
| tavle.theme.tokens.x_parse_colour__mutmut_8 | killed | `test_theme_tokens.py::test_parse_colour_channels` |
| tavle.theme.tokens.x_parse_colour__mutmut_11 | killed | `test_theme_tokens.py::test_parse_colour_channels` |
| tavle.theme.tokens.x_parse_colour__mutmut_12 | killed | `test_theme_tokens.py::test_parse_colour_channels` |
| tavle.theme.tokens.x_parse_colour__mutmut_13 | killed | `test_theme_tokens.py::test_parse_colour_channels` |
| tavle.theme.tokens.x_parse_colour__mutmut_17 | killed | `test_theme_tokens.py::test_parse_colour_channels` |
| tavle.theme.tokens.x_parse_colour__mutmut_20 | killed | `test_theme_tokens.py::test_parse_colour_channels` |
| tavle.theme.tokens.x_parse_colour__mutmut_21 | killed | `test_theme_tokens.py::test_parse_colour_channels` |
| tavle.theme.tokens.x_parse_colour__mutmut_22 | killed | `test_theme_tokens.py::test_parse_colour_channels` |
| tavle.theme.tokens.x_parse_colour__mutmut_23 | killed | `test_theme_tokens.py::test_parse_colour_channels` |
| tavle.theme.tokens.x_parse_colour__mutmut_24 | killed | `test_theme_tokens.py::test_parse_colour_channels` |
| tavle.theme.tokens.x_validate_value__mutmut_1 | equivalent | `None` is as falsy as the empty rule. |
| tavle.theme.tokens.x_validate_value__mutmut_8 | killed | `test_theme_tokens.py::test_value_error_messages`, param `surface-red-p: surface 'red': expected #rrggbb` |
| tavle.theme.tokens.x_validate_value__mutmut_9 | killed | `test_theme_tokens.py::test_value_error_messages`, param `surface-red-p: surface 'red': expected #rrggbb` |
| tavle.theme.tokens.x_validate_value__mutmut_18 | killed | `test_theme_tokens.py::test_value_error_messages`, param `heading-case-title-p: heading-case 'title': expect` |
| tavle.theme.tokens.x_validate_value__mutmut_23 | equivalent | Only numbers reach this branch, and every numeric catalog token has both bounds. |
| tavle.theme.tokens.x_validate_value__mutmut_24 | equivalent | Only numbers reach this branch, and every numeric catalog token has both bounds. |
| tavle.theme.tokens.x_validate_value__mutmut_34 | killed | `test_theme_tokens.py::test_steps_count_from_the_minimum` |
| tavle.theme.validate.x_validate_theme__mutmut_4 | killed | `test_theme_validate.py::test_dark_failures_print_the_whole_line` |
| tavle.theme.validate.x_validate_theme__mutmut_5 | killed | `test_theme_validate.py::test_dark_failures_print_the_whole_line` |
| tavle.theme.validate.x_validate_theme__mutmut_56 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.validate.x_validate_theme__mutmut_60 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.validate.x_validate_theme__mutmut_61 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.validate.x_validate_theme__mutmut_62 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.validate.x_validate_theme__mutmut_66 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.validate.x_validate_theme__mutmut_67 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.validate.x_validate_theme__mutmut_72 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.validate.x_validate_theme__mutmut_76 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.validate.x_validate_theme__mutmut_77 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.validate.x_validate_theme__mutmut_91 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.validate.x_validate_theme__mutmut_95 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.validate.x_validate_theme__mutmut_96 | equivalent | `cast` returns its second argument and ignores the first at run time. |
| tavle.theme.validate.x_validate_theme__mutmut_118 | equivalent | Differs only when a float contrast ratio equals the threshold exactly; ratios are sums of `**2.4` channel terms and no input hits it. |
| tavle.theme.validate.x_validate_theme__mutmut_120 | killed | `test_theme_validate.py::test_dark_failures_print_the_whole_line` |
| tavle.theme.validate.x_validate_theme__mutmut_122 | killed | `test_theme_validate.py::test_dark_failures_print_the_whole_line` |
| tavle.theme.validate.x_validate_theme__mutmut_124 | killed | `test_theme_validate.py::test_dark_failures_print_the_whole_line` |
| tavle.theme.validate.x_validate_theme__mutmut_126 | killed | `test_theme_validate.py::test_dark_failures_print_the_whole_line` |
| tavle.theme.validate.x_validate_theme__mutmut_128 | killed | `test_theme_validate.py::test_dark_failures_print_the_whole_line` |
| tavle.theme.validate.x_validate_theme__mutmut_129 | killed | `test_theme_validate.py::test_dark_failures_print_the_whole_line` |
| tavle.theme.validate.x_validate_theme__mutmut_146 | equivalent | Differs only when a float contrast ratio equals the threshold exactly; ratios are sums of `**2.4` channel terms and no input hits it. |
| tavle.theme.validate.x_validate_theme__mutmut_162 | killed | `test_theme_validate.py::test_status_hue_distance`, param `overrides2-warning and danger-20.0` |
| tavle.theme.validate.x_validate_theme__mutmut_181 | killed | `test_theme_validate.py::test_status_hue_distance`, param `overrides1-success and warning-20.0` |
| tavle.theme.validate.x_validate_theme__mutmut_208 | killed | `test_theme_validate.py::test_status_hue_distance`, param `overrides0-success and warning-4.5` |
| tavle.theme.validate.x_validate_theme__mutmut_209 | killed | `test_theme_validate.py::test_status_hue_distance`, param `overrides0-success and warning-4.5` |
| tavle.theme.validate.x_validate_theme__mutmut_212 | killed | `test_theme_validate.py::test_status_hue_distance`, param `overrides0-success and warning-4.5` |
| tavle.theme.validate.x_validate_theme__mutmut_213 | killed | `test_theme_validate.py::test_status_hue_distance`, param `overrides0-success and warning-4.5` |
| tavle.theme.validate.x_validate_theme__mutmut_214 | killed | `test_theme_validate.py::test_status_hue_distance`, param `overrides1-success and warning-20.0` |
| tavle.theme.validate.x_validate_theme__mutmut_218 | killed | `test_theme_validate.py::test_status_hue_distance`, param `overrides4-success and warning-15.0` |
| tavle.theme.validate.x_validate_theme__mutmut_221 | killed | `test_theme_validate.py::test_status_hue_distance`, param `overrides5-danger and info-0.0` |
| tavle.theme.validate.x_validate_theme__mutmut_223 | killed | `test_theme_validate.py::test_status_hue_distance`, param `overrides3-success and warning-None` |
| tavle.theme.validate.x_validate_theme__mutmut_224 | killed | `test_theme_validate.py::test_status_hue_distance`, param `overrides3-success and warning-None` |
| tavle.theme.validate.x_validate_theme__mutmut_228 | killed | `test_theme_validate.py::test_dark_failures_print_the_whole_line` |
