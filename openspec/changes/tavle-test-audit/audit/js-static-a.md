# JS baseline, static enhancers (first half)

Not mutation-tested yet; lead decision 2026-11-26, task 3.4/3.5 notes.

- Files: 8 (annotated.js to er.js).
- Stryker instrumented 1140 mutants (`/var/tmp/tmp-alec/t3x-js-static-a.log`), and the initial run passed 341 vitest tests.
- No vitest test reaches these files. Only the Python Playwright tests run them (class 3 under A2), and Stryker cannot run those.
- With `vitest.related: false` every mutant reran all 341 tests at about 10 s each. On a one-file probe (`annotated.js`, 81 mutants) every tested mutant survived. The full run would take 1.6 h at concurrency 2 to report what the reach check shows: score 0.
- Score: 0 by construction (no killing test exists). Total 1140, killed 0. Survived, NoCoverage and timeout were not measured per mutant.
- Re-measure after the vitest tasks that 5.25 plans land (task 5.26).

## Reach evidence

- `src/tavle/static/annotated.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/blocks.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/chart.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/code.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/containers.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/diagram.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/dom.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
- `src/tavle/static/er.js`: no vitest test imports it, directly or through `static/components/*` (checked with `rg` over `tests/` and `src/tavle/static/components/`).
