# Test suite

## ADDED Requirements

### Requirement: Fast default suite and fast pre-push

`just test` (CI job `test`) SHALL run lint, the Python tests with `-m 'not matrix_full'` in parallel (`-n 3`), and vitest. `just test-fast` SHALL run lint, the Python tests with `-m 'not slow and not matrix_full'` (`-n 3`) and vitest, and the pre-push hook SHALL run it. The full widget matrix SHALL run only through `just test-matrix` and as its own CI job named `matrix`.

#### Scenario: Default run skips the full matrix

- **WHEN** `uv run --locked pytest --collect-only -q -p no:cacheprovider -m 'not matrix_full' | tail -1` runs
- **THEN** it reports fewer tests than `uv run --locked pytest --collect-only -q -p no:cacheprovider | tail -1`, and `just --dry-run test-matrix 2>&1 | rg -c "m matrix_full"` prints 1

#### Scenario: Full matrix is its own merge gate

- **WHEN** `rg -n "^  (test|matrix):|just test$|just test-matrix$" .github/workflows/tests.yml` runs
- **THEN** it prints job `test` with `just test` and a separate job `matrix` with `just test-matrix`

#### Scenario: Pre-push is fast

- **WHEN** `rg -n "just test-fast" .githooks/pre-push` runs and `/usr/bin/time -f %e just test-fast` runs on the 4-CPU development machine
- **THEN** the hook line is printed and the wall time is below 300 seconds

### Requirement: Browser tests are marked slow

Every `test_*.py` file that imports `playwright` SHALL carry a module-level `slow` mark, and any skip, skipif or xfail in Python or JavaScript tests SHALL fail the default suite.

#### Scenario: An unmarked browser file fails

- **WHEN** `uv run --locked pytest tests/test_suite_rules.py -q -p no:cacheprovider` runs
- **THEN** it passes, and its planted unmarked Playwright file, planted `pytest.skip` and planted `it.skip` each make the corresponding rule report a violation

#### Scenario: Fast selection launches no browser

- **WHEN** `uv run --locked pytest --collect-only -q -p no:cacheprovider -m "not slow" tests/page/test_table_phone_cards.py tests/page/test_plan_board.py | tail -1` runs
- **THEN** it reports 0 tests collected

### Requirement: Pairwise default matrix

The default matrix subset (the cells not marked `matrix_full`) SHALL cover every valid pair of values of any two of the axes family, width, scheme and mode, and every fixture at least once. It SHALL use fewer page loads than the 394 of the hand-picked subset it replaces.

#### Scenario: Subset covers all axis pairs

- **WHEN** `uv run --locked pytest tests/page/widget_matrix/test_selftest.py -q -p no:cacheprovider -k pairwise` runs
- **THEN** it passes, including a case that drops the only selected page key covering one pair and expects the coverage helper to report that pair

#### Scenario: Subset is cheaper than before

- **WHEN** `uv run --locked python -c "from tests.page.widget_matrix.cells import all_cells; print(len({c.page_key for c in all_cells() if c.in_subset}))"` runs from `/home/alec/source/tavle`
- **THEN** it prints a number below 394

### Requirement: Mutation testing in both languages

Python mutation testing SHALL use mutmut 3.8.1 through `just mutate` (`scripts/mutate.py`), and JavaScript mutation testing SHALL use Stryker 10.1.1 with `@stryker-mutator/vitest-runner` 10.1.1 through `just mutate-js`. Both SHALL run under a memory cap and a timeout, keep scratch under `/var/tmp/tmp-alec`, write no tracked file, and delete their scratch when the task ends. Python mutants run only tests not marked `slow` or `matrix_full`.

#### Scenario: Python mutation run reports a score

- **WHEN** `just mutate --tag spec --only 'tavle.theme.merge.*'` runs and then `just mutate --tag spec --clean`
- **THEN** the first prints killed, survived, no_tests, timeout and total counts and the score, `git status --short` shows no change, and `ls /var/tmp/tmp-alec | rg -c mutate-tavle-spec` prints 0

#### Scenario: JavaScript mutation run reports a score

- **WHEN** `just mutate-js --mutate src/tavle/static/dom.js` runs
- **THEN** it prints a mutation score, `git status --short` shows no tracked change, and `ls /var/tmp/tmp-alec | rg -c stryker-tavle` prints 0

### Requirement: Mutation-score floors

Each language SHALL have a floor in `scripts/mutation-floors.json` that is at least 1. The Python score SHALL be `killed / (total - skipped)` and the JavaScript score `Killed / (Killed + Survived + NoCoverage + Timeout + RuntimeError)`, so a survivor that becomes a timeout never raises either. `scripts/mutation_gate.py` SHALL fail when a floor is lower than at the merge base.

#### Scenario: Floors are set and never lowered

- **WHEN** `uv run --locked pytest tests/test_mutation_floors.py tests/test_mutation_gate.py -q -p no:cacheprovider` runs
- **THEN** it passes, including a floor of 0 failing, a floor lower than the base floor failing, a JS timeout not raising the score, and a Python timeout not raising the score

### Requirement: New tests must kill

Every test file added in a pull request that imports a mutated module SHALL be the sole killer of at least one mutant of those modules, and the gate SHALL run in CI job `mutation` on pull requests (changed modules) and weekly (all modules).

#### Scenario: A duplicate new test fails the gate

- **WHEN** `uv run --locked pytest tests/test_mutation_gate.py -q -p no:cacheprovider -k new_test` runs
- **THEN** it passes, including a planted added test with no unique kill failing and a planted added test with a unique kill passing

#### Scenario: Gate is wired in CI

- **WHEN** `rg -n "just mutation-gate|schedule:|pull_request|timeout-minutes" .github/workflows/mutation.yml` runs and `rg -c "min-score" .github/workflows/mutation.yml` runs
- **THEN** the first prints the gate command, the schedule, the pull request trigger and the timeouts, and the second prints 0

### Requirement: Standing test-quality rules

The default suite SHALL fail on a test with no assertion that can fail, an `assert x == x`, an identical duplicate test body within a file, a repeated parametrize row, or a test that reads `src/tavle/**/*.py` text.

#### Scenario: Planted tautologies fail

- **WHEN** `uv run --locked pytest tests/test_test_quality.py -q -p no:cacheprovider` runs
- **THEN** it passes, and each rule reports a planted violation in `tmp_path` and no hit on the real tests

### Requirement: Evidence-based test deletion

A test SHALL be deleted or merged during the audit only when `openspec/changes/tavle-test-audit/audit/<area>.md` records it with a mutation or static finding. After an area's audit its mutation score SHALL not be lower than before, every non-killed mutant SHALL be recorded as killed by a new test, equivalent, or slow-only with the slow test that kills it, and no test is skipped, xfailed or kept failing.

#### Scenario: Every removed test is recorded

- **WHEN** `uv run --locked pytest tests/test_check_audit_removals.py -q -p no:cacheprovider` runs, and each audit task runs `uv run --locked python scripts/check_audit_removals.py <base> <area>`
- **THEN** the tests pass, including a removed async test, an indented method and a JS `it(` title each reported when unrecorded, and each audit command exits 0
