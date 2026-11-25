# Proposal

## Why

The owner asked: "The amount of tavle tests seems kind of insane are we auditing those for tautological tests and using a mutation testing setup to remove duplicates or useless tests".

Measured baseline (design.md, Baseline): 6,524 pytest tests plus 341 vitest tests. 3,432 of the pytest tests are cells of one browser matrix, and `just test` runs all of them serially (`uv run pytest -q`, no `-n`, no marker filter). Nothing audits the other 3,092 tests for tautology or duplication. A mutmut wrapper (`scripts/mutate.py`) exists but no full run, score or gate exists, and JavaScript has no mutation tool.

## What Changes

- Repair the one red baseline test first (a stale export fixture).
- Mark every Playwright test file `slow`, with a rule that keeps it so.
- `just test` (CI) runs `-m 'not matrix_full'` with `-n 3`; a new `just test-fast` (`-m 'not slow and not matrix_full'`, target under 5 minutes) is the pre-push hook. The full widget matrix becomes `just test-matrix` and its own CI job. The default matrix subset becomes a pairwise cover of four matrix axes.
- Mutation testing in both languages: mutmut 3.8.1 for Python (already wrapped in `scripts/mutate.py`; gains a fast test selection, a score gate and a changed-modules mode) and Stryker 10.1.1 with its Vitest runner for JavaScript (new).
- One audit pass over every test area: a test is deleted or merged only with mutation-report evidence, and each decision is recorded in `audit/<area>.md` in this change.
- A mutation-score gate per language: floors in `scripts/mutation-floors.json`, set from the measured post-audit score, with the gate failing when a floor is lower than at the merge base; timeouts never raise the score. It also requires each new test file to be the sole killer of at least one mutant. It runs as a CI job on pull requests (changed modules) and weekly (full), under memory caps and timeouts.
- Standing static rules in the default suite (no skip or xfail, no unmarked browser file, no assertion-free or self-comparing test, no duplicate bodies).

## Out of scope

- Browser (`slow`) tests are not run per mutant; they are audited by a coverage criterion (design.md D4).
- Auditing varde's tests. Follow-up change, named `varde-test-audit`: apply this change's criteria, `scripts/mutate.py` pattern and gate to varde after this one is archived.
- Lint tooling changes (fallow, mollify, pyright, ruff, lint-imports stay as they are); no suppressions, ceilings or baseline edits anywhere.

## Capabilities

### New Capabilities

- `test-suite`: how the default and full suites split, how mutation testing and its gate work, and the rules for deleting a test.

## Impact

Files touched: `justfile`, `.githooks/pre-push`, `.github/workflows/tests.yml`, new `.github/workflows/mutation.yml`, `scripts/mutate.py`, new `scripts/capped.sh`, `scripts/mutation_gate.py`, `scripts/check_audit_removals.py`, `scripts/mutation-floors.json`, `package.json`, `package-lock.json`, new `stryker.config.json`, `.gitignore`, `tests/page/widget_matrix/cells.py` and its self-test, new `tests/test_suite_rules.py`, `tests/test_test_quality.py`, `tests/test_mutation_gate.py`, `tests/test_mutation_floors.py`, `tests/test_mutate_script.py`, `README.md`, `AGENTS.md`, `pyproject.toml` (marker text), and the test files the audit deletes or merges. Consumers: the pre-push hook, CI, varde's follow-up. Branch protection naming the new `matrix` and `mutation` CI jobs as required checks is a GitHub setting the owner applies.
