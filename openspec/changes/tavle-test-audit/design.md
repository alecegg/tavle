# Design

## Context

Owner rules for this change: never keep failing or skipped tests to defer fixing; no suppressions, ceilings or baseline edits; all Python and JS tooling lives in the tavle repository; every static check is a gate somewhere; scratch goes under `TMPDIR=/var/tmp/tmp-alec` (`/tmp` is RAM).

Existing pieces this change builds on:

- `scripts/mutate.py` (295 lines, README "Checks") runs mutmut `3.8.1` over `src/tavle` in a throwaway copy under `$TMPDIR/mutate-tavle`, with its own venv. `just mutate *args` calls it. It has `--workers`, `--fresh`, `--tag`, `--only GLOB`. It has no score gate and runs the whole `tests` directory per mutant (including browser tests).
- `matrix_full` marker already exists. `tests/page/widget_matrix/cells.py` `Cell.in_subset` hand-picks the default cells; `test_matrix.py` marks the rest `matrix_full`. Nothing excludes them: `just test` runs `uv run --locked pytest -q` with no `-n` and no `-m`.
- `tests/page/widget_matrix/pending.py` holds an empty `PENDING` dict that turns families into `xfail`. Two conditional skips exist (`tests/page/test_static_js_syntax.py:18` node missing, `tests/page/test_pages_server.py:305` uv missing).
- Consumers of these surfaces: pre-push hook `.githooks/pre-push` (`just test`, becomes `just test-fast`), `.github/workflows/tests.yml` (`just test`), README "Checks", AGENTS.md "Checks", `tests/page/widget_matrix/{cells,driver,test_matrix,test_selftest}.py` (import the subset and axis names). varde consumes only `tavle/__init__.py` names, so no varde surface changes. Other open tavle changes (`ui-catalogs`, `ui-agent-feedback`, `plan-board`, `table-phone-cards`, `ui-app-renderer`) add tests and source; none owns `justfile`, `cells.py`, `scripts/mutate.py` or CI files. Their new tests join the audit areas they land in.

## Baseline (measured 2026-11-25 on HEAD `de214d7`, 4 CPUs, 7 GB RAM, `TMPDIR=/var/tmp/tmp-alec`)

Counts (`pytest --collect-only`, `-m` filters):

| Set | Tests |
|---|---|
| pytest total | 6,524 in 120 files (including the matrix) |
| widget matrix cells (`test_matrix.py::test_cell`) | 3,432 (54 fixtures, 34 families, 5 widths, 2 schemes, 8 modes) |
| of which `matrix_full` | 2,906 |
| of which default subset | 526 (394 page loads; full matrix 2,808 page loads) |
| matrix self-tests (`test_selftest.py`) | 19 |
| all other pytest tests | 3,073 |
| `slow` marker | 3,736 (3,432 cells plus 304 other browser or integration tests) |
| `not slow` | 2,788 |
| `not matrix_full` | 3,618 |
| vitest (10 files, `tests/components`) | 341 |

Wall time (not measured serially; see the last row):

| Run | Result |
|---|---|
| `pytest -m 'not matrix_full' -n 3` | 3,617 passed, 1 failed, 263 s wall (pytest only; vitest and lint are extra); 724 s summed test time, 478 s (66%) in matrix subset cells, 246 s elsewhere |
| `pytest -m matrix_full -n 3` | 2,905 passed, 1 failed, 953 s wall (15 min 53 s) |
| `npx vitest run` | 341 passed, 20.3 s wall (14.9 s test time; jsdom created 10 times, 19.7 s) |
| current `just test` (`pytest` serial, no `-n`) | not run; about 3,360 s (56 min) estimated as 724 s plus 2,906 cells at 0.91 s (478 s / 526) |
| pre-push measured (`just test-fast`, after task 1.5 on `d0b5bf8`) | lint, 2,785 pytest and 341 vitest passed, 36 s wall |

Slowest non-matrix files by summed time: `test_theme_browser.py` 29.4 s (17 tests), `test_rich_diagram.py` 16.9 s (30), `test_table_phone_cards.py` 13.7 s (7), `test_wheel_standalone.py` 12.2 s (1), `test_rich_chart.py` 10.4 s (41). Largest files by count: `test_components_contract.py` 736, `test_tokens_shared.py` 116, `test_actions.py` 91, `test_blocks_inputs.py` 86, `test_extract_inputs.py` 80.

Axis pair coverage of the hand-picked subset (covered of valid pairs): width x scheme 4 of 10, width x mode 9 of 26, scheme x mode 9 of 16, fixture x mode 232 of 432, family x mode 168 of 272, family x width 68 of 170.

Red baseline found while measuring:

1. `tests/page/test_export_standalone.py::test_export_fixture_matches_python_export` fails on HEAD alone: `tests/components/fixtures/export-callout.html` still carries the old `recap.js` comment (`varde learn docs recap --json` output); `src/tavle/static/components/recap.js:1` was reworded.
2. `test_matrix.py::test_cell[rich-containers-rich-containers-w375-light-default]` failed once under `-n 3` load ("focus-scroll: div#blk-diff1 > button.menu-btn was not scrolled into view") and passed alone. The focus snapshot (`audit.py:333`, `inView`) is sampled before the scroll settles.

3. Playwright files not marked `slow`: `tests/page/test_table_phone_cards.py` and `tests/page/test_plan_board.py` have no marker, and `test_cli.py`, `test_plan_board_progress.py` and `test_plan_board_sections.py` mark only some tests, so `-m 'not slow'` still launches Chromium (task 0.4).

All three are fixed first (tasks 0.1, 0.2, 0.4): mutation testing needs a green baseline, and the owner rule forbids carrying them.

## Decisions

### D1. Fast default, fast pre-push, full matrix as its own gate

Three recipes:

- `just test` (CI job `test`) = lint, `pytest -q -n 3 -m 'not matrix_full'`, vitest.
- `just test-fast` (pre-push hook) = lint, `pytest -q -n 3 -m 'not slow and not matrix_full'`, vitest. Target: under 300 s wall, measured in task 1.5 and recorded in Baseline ("pre-push measured"). Browser tests and the matrix run in CI as merge gates, not on push.
- `just test-matrix` (CI job `matrix`) = `pytest -q -n 3 -m matrix_full`.

`-n 3` everywhere: it is what was measured on a 4-CPU, 7 GB machine with single-process Chromium per page load, and GitHub's ubuntu runner has 4 vCPUs. Branch protection must list `test`, `matrix` and `mutation` as required checks (the owner's GitHub setting).

Alternatives: `-n auto` (rejected: 4 workers plus a browser each is near the 7 GB limit); keep pre-push at `just test` (rejected: lint 1 min plus 263 s plus vitest is near a likely push timeout, and the browser tests duplicate the CI gate).

### D2. Pairwise default matrix

A page load audits every family in its fixture, so cost follows page loads, not cells. Measured with a greedy cover over the 2,808 valid page keys: all pairs of (family, width, scheme, mode) plus each fixture once need 255 loads (hand-picked subset: 394 loads covering 774 of 1,372 pairs; pairs including fixture need 489 loads). Decision: replace `Cell.in_subset`'s hand-picked rule with a deterministic greedy pairwise cover of family, width, scheme and mode, plus every fixture at least once. A cell is in the default subset when its page key was selected, so all families of a selected load ride along. Expected default load cut: 394 to about 255.

Tradeoff (review L6): fixture x width, scheme and mode pairs (today 232 of 432 fixture x mode) run only in `matrix`, not on pre-push or in job `test`. The merge gate `matrix` still runs them all.

Alternatives: keep the hand-picked rule (rejected: leaves 44% of pairs uncovered and is not reproducible when axes change); full pairwise with fixture (rejected: 489 loads is 24% more than today).

### D3. Which tests mutation testing can judge

Mutation testing changes source and asks whether any test fails. It judges only tests that execute the mutated language:

| Class | Examples | Judge |
|---|---|---|
| Python logic (fast, `not slow`) | `test_lines_*`, `test_theme_*`, `test_pages_*`, `test_extract_*`, `test_blocks_*` | mutmut over `src/tavle/**/*.py` |
| JS unit (vitest, jsdom) | `tests/components/*.test.js` | Stryker over `src/tavle/static/**/*.js` |
| Asset text and browser (CSS or JS read as text, Playwright, matrix) | `test_tokens_shared.py`, `test_design_tokens.py`, `test_widget_*_design.py`, `widget_matrix` | neither tool |

A1 (accepted): mutation runs use `-m 'not slow and not matrix_full'`, so a mutant costs seconds and never launches Chromium. This holds only because task 0.4 marks every Playwright file `slow` and `tests/test_suite_rules.py` fails when one is not. A2 (accepted): class 3 tests are audited by the static criteria (C2 to C5), the standing rules in `tests/test_test_quality.py` and, for browser tests, by overlap with the matrix; they are not mutation-judged. Task 2.1 records the class of every test file in `audit/inventory.md`.

Mutants no fast test kills (`slow-only`): each is run with `just mutate --slow` (task 2.3), and the slow test that kills it is recorded in the area's audit file as the evidence. They stay in the score as survivors (design D8), so the floor does not hide them.

### D4. Python tool: mutmut 3.8.1 (keep)

Verified: PyPI `mutmut` 3.8.1 (uploaded 2026-10-28, `requires-python >=3.10`, classifiers list 3.10 to 3.15); `mutmut export-cicd-stats` writes `mutants/mutmut-cicd-stats.json` with `killed`, `survived`, `total`, `no_tests`, `skipped`, `suspicious`, `timeout`, `segfault` (mutmut 3.8.1 `__main__.py`). Alternative checked: `cosmic-ray` 8.9.0 on PyPI (separate session database and per-run configuration; no reason to replace a working wrapper). Found in task 2.4: that file totals every generated mutant, so with `--only` the wrapper counts the matched `mutmut results` instead. Decision: keep mutmut and `scripts/mutate.py`; extend it (tasks 2.2 to 2.6). The version pin lives in `MUTMUT_VERSION`, the `[tool.mutmut]` config in the wrapper (written into the throwaway copy), scratch in `$TMPDIR/mutate-tavle*`.

Resource bounds (review M2): every run goes through `scripts/capped.sh`: `systemd-run --user --scope -p MemoryMax=4G -p MemorySwapMax=0` (verified to work without root on this machine) plus `timeout 20m`, overridable with `MUTATION_MEM` and `MUTATION_MINUTES`; a timed-out run resumes from mutmut's cached results. Where `systemd-run --user` is unavailable (CI) the script uses `timeout` alone. `--workers 2`. Each task deletes its scratch with `--clean`. Chromium tasks and `[mut]` tasks never overlap (tasks.md conventions).

### D5. JavaScript tool: Stryker 10.1.1 with the Vitest runner

Verified on npm: `@stryker-mutator/core` 10.1.1 (latest, modified 2026-10-23, engines node >=22) and `@stryker-mutator/vitest-runner` 10.1.1 (peer `vitest >=2.0.0`, `@stryker-mutator/core 10.1.1`; the repo has vitest 5.0.5, node 24 locally, node 22 in CI). Documented options used (Stryker docs `configuration.md`, `vitest-runner.md`): `testRunner: "vitest"`, `vitest.configFile`, `vitest.related`, `concurrency`, `tempDirName`, `disableBail`, `reporters`, `jsonReporter.fileName`, `mutate`. Alternative: none for vitest of equal standing. Decision: pin both packages exactly (as `fallow` and `vitest` are), config in `stryker.config.json`, sandbox `/var/tmp/tmp-alec/stryker-tavle` passed as `--tempDirName` (docs call it a directory name; task 3.2 verifies an absolute path works and otherwise symlinks `.stryker-tmp` there), reports to gitignored `reports/`, `concurrency: 2`, capped like mutmut.

Risk R1: the vitest config uses `projects` with a custom `root` and an alias for `@ui/static`; task 3.3 proves `related` works through the alias and proves the comma-joined `--mutate` form the gate uses. If it does not work, the task records the error and stops for the lead.

### D6. Audit criteria

A test is a deletion or merge candidate when any holds:

- C1 No unique kill: removing it changes no mutant status. Python: the mode chosen in task 2.6, `--without <test>` leave-one-out reruns, or per-mutant kill sets from mutmut's covering-test map when reruns do not fit 20 minutes per area. JavaScript: Stryker `--disableBail` with the json reporter records every killing test per mutant (`killedBy`).
- C2 Asserts its own fixture: the expected value is built from the input by the same expression the code uses, or the test asserts a literal it just set.
- C3 Restates the implementation: the assertion copies the source (a regex over source text, a constant copied from the module, `assert f(x) == f(x)`).
- C4 No assertion that can fail: no `assert`, `assert True`, a name compared to itself.
- C5 Duplicate: another test has the same call and the same asserted fact, or a parametrize repeats a row.

C1 comes from mutation data. C2 to C5 come from the one-time scan (task 4.1) and reading, and each decision cites its evidence in `audit/<area>.md`. A test that fails C1 but guards a recorded regression or a published contract stays, with a one-line reason in the audit file.

### D7. Process per area

Per area: run the mutation tool on the area's source, list non-killed mutants, apply C1 to C5 to the area's tests, delete or merge, rerun the area's tests and mutation tool. Gate for the area: tests pass, score not lower than before, every removed test named in `audit/<area>.md` (checked by `scripts/check_audit_removals.py`, task 4.3). Every non-killed mutant ends as one of: killed by a new fast test; `equivalent` with the argument; `slow-only` with the slow test id (D3). Neither a skip, an xfail, a `do_not_mutate` pattern, nor a score exclusion is used. Areas are the 5.x tasks, each at most 6 test files.

### D8. Mutation-score gate

- Score: Python `killed / (total - skipped)`; `no_tests`, `survived`, `timeout`, `suspicious` and `segfault` all stay in the denominator and none counts as killed, so a survivor that becomes a timeout cannot raise the score. `skipped` must be 0 (exclusions are forbidden). JavaScript `Killed / (Killed + Survived + NoCoverage + Timeout + RuntimeError)` computed from the json report by the gate (Stryker's own `thresholds.break` counts a timeout as killed, so it is not used). Slow-only mutants count as survivors.
- Floors live in one file, `scripts/mutation-floors.json` (`{"python": N, "js": N}`). They are set by tasks 6.2 and 6.3 from the measured post-audit score, rounded down to a whole percent, at least 1.
- Never lowered, mechanically: `scripts/mutation_gate.py` reads the floors at the merge base (`git show BASE:scripts/mutation-floors.json`) and fails when either working floor is lower or missing. `tests/test_mutation_floors.py` fails when a floor is below 1. The CI workflow passes no `--min-score`, and `mutate.py --min-score` can only raise a run's floor.
- New-test gate (anti-tautology): runs in the PR run; what it judges is in D12 (task 6.5).
- Where it runs: `.github/workflows/mutation.yml`, job `mutation`. On `pull_request` it runs `just mutation-gate origin/<base>`: only changed modules are mutated, and the global floor applies to that subset. A weak module that a PR touches must therefore be brought up by tests; there is no exemption. A weekly `schedule` (and `workflow_dispatch`) runs `--all`. Job limits: `timeout-minutes: 60` for PRs and 350 for the weekly run; if the full-run wall time recorded in Result exceeds 300 minutes the weekly run splits into a matrix over areas (task 6.7), staying under GitHub's 6 hour cap. A changed `__init__.py` maps to its own module only, not the package.
- Not in `just test` or the pre-push hook: a run takes minutes to hours (measured in tasks 2.7 to 2.11 and 3.4 to 3.7).

### D9. Skips and xfail

The owner rule says no skipped or failing tests are kept. Task 0.3 deletes the empty `PENDING` mechanism (dead code) and turns the two conditional skips into hard requirements (node and uv are already required by `just test`). Task 0.4 adds `tests/test_suite_rules.py`, which fails the default suite on any skip, skipif or xfail in Python or JS tests, and on an unmarked Playwright file; so the rule is a gate in `just test`, `just test-fast` and CI.

### D10. Deletion evidence

Audit deletions are checked by `scripts/check_audit_removals.py` (task 4.3). After this change, a deletion's standing evidence is the PR mutation gate: removing a test cannot lower the changed-module score below the floor (D8).

### D11. Follow-up

Apply the same to varde as a separate change named `varde-test-audit`: copy the criteria (D6), this change's `scripts/mutate.py`, `scripts/capped.sh`, `scripts/mutation_gate.py` and floors rule, and measure varde's baseline first. It starts after this change is archived and is not planned further here.

### D12. Test growth stays under control

Owner request (2026-11-25): an audit is only worth doing if rules keep the count down afterwards. Measured: 6,540 collected tests from 1,141 test functions; one function (`test_matrix.py::test_cell`, a 54 x 34 x 5 x 2 x 8 cross product) is 3,432 of them; 23 other functions have more than 20 parametrize cases. Three standing rules, all merge gates:

- Each added test is judged, not each added file. The new-test gate (task 6.5) diffs collected node ids between `BASE` and the working tree (`pytest --collect-only -q`, vitest `list --json`) and requires each added node that imports a mutated module to be the sole killer of at least one mutant. A parametrized function's added cases are added nodes, so a new row that kills nothing new fails. Nodes that import no mutated module are listed as not judged and fall to the next two rules.
- No cross-product parametrization (task 6.1, rule C6). A test function with two or more stacked `parametrize` decorators, or a `parametrize` whose cases come from `itertools.product`, fails the default suite. Combinations come from a pairwise cover instead; the only cover today is `tests/page/widget_matrix/cells.py`, and a case set built by calling it passes.
- A recorded count (task 6.10). `tests/test-counts.json` holds the collected count per selection (fast, slow, total, vitest). A CI step in job `test` fails when the collected counts differ from the file, so every pull request that adds or removes tests shows the change in its diff, including browser and asset-text tests that mutation cannot judge.

Alternatives: a cap on cases per parametrize (rejected: data-driven contract tests over every component spec are legitimate, and the per-node kill gate already rejects rows that add nothing); a count ceiling that never rises (rejected: forbids legitimate new tests; the recorded count makes growth visible and the kill gate judges it).

## Assumptions

All confirmed by the lead:

- A1: `slow` browser tests are left out of per-mutant runs; see D3.
- A2: asset-text and browser tests are audited by static criteria, not by mutation; see D3.
- A3: `-n 3` for every parallel run.
- A4 (to be checked by task 3.1): `@stryker-mutator/*` do not trigger `fallow dead-code` unused-dependency findings; if they do the task stops for the lead, with no ignore-list edit.

## Open questions

None.
