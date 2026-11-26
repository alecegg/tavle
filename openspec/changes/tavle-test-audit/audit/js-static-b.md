# JS baseline, static enhancers (second half)

Not mutation-tested yet; lead decision 2026-11-26, task 3.4/3.5 notes.

- Files: 13 (flow.js to wireframe.js).
- Stryker instrumented 2433 mutants (`/var/tmp/tmp-alec/t3x-js-static-b.log`), and the initial run passed 341 vitest tests.
- No vitest test reaches these files. Only the Python Playwright tests run them (class 3 under A2), and Stryker cannot run those.
- With `vitest.related: false` every mutant reran all 341 tests at about 10 s each. On a one-file probe (`annotated.js`, 81 mutants) every tested mutant survived. The full run would take 3.4 h at concurrency 2 to report what the reach check shows: score 0.
- Score: 0 by construction (no killing test exists). Total 2433, killed 0. Survived, NoCoverage and timeout were not measured per mutant.
- Re-measure after the vitest tasks that 5.25 plans land (task 5.26).

## Reach evidence

- `src/tavle/static/flow.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/image.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/inputs_fields.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/inputs_ordered.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/inputs_runtime.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/inputs_widgets.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/screen_flow.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/sequence.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/table.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/tabs.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/view_keys.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/viewport.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/wireframe.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
