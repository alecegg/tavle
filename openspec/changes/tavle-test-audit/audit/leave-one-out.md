# Leave-one-out timing

Baseline: `t26`, with the existing theme mutation results. Commands:

- `just mutate --without tests/test_theme_layers.py --baseline t26`: 183 affected mutants, approximately 239 seconds (1.31 seconds per mutant).
- `just mutate --without tests/test_theme_tokens.py --baseline t26`: 43 affected mutants, approximately 74 seconds (1.72 seconds per mutant).

Times are elapsed log creation-to-last-write timestamps. Both runs printed `lost kills`, but the detached timing wrappers did not append their `rc` lines, so exit status and exact wall time were not captured.

Projecting the larger observed run across six files gives approximately 1,434 seconds (24 minutes). This exceeds 15 minutes; the lead must decide the fallback. Actual time depends on coverage overlap and per-mutant cost.

Lead decision: the projection does not fit one 15-minute job, so area jobs group test files by affected count (at most about 700 per job) and split a larger file with `--only` module globs; design D6 records the rule.
