# JS components baseline, first half

Files: first 18 of `src/tavle/static/components/*.js` in alphabetical order (`annotated-code.js` to `form.js`). Run detached: `/var/tmp/tmp-alec/t3x-js-comp-a.log`, rc=0, wall 1626 s.

- Mutation tool: Stryker 10.1.1, Vitest runner, `just mutate-js --disableBail`, default `stryker.config.json` (`vitest.related: true`).
- Counts: total 1310, killed 1287, survived 19, NoCoverage 2, timeout 2, runtime errors 0.
- Score: 98.24 % (Killed / (Killed + Survived + NoCoverage + Timeout + RuntimeError) = 1287 / 1310).

## Non-killed mutants

- `src/tavle/static/components/annotated-code.js:78` StringLiteral (Survived)
- `src/tavle/static/components/callout.js:13` Regex (Survived)
- `src/tavle/static/components/callout.js:13` MethodExpression (Survived)
- `src/tavle/static/components/diff.js:91` StringLiteral (NoCoverage)
- `src/tavle/static/components/diff.js:12` ConditionalExpression (Survived)
- `src/tavle/static/components/diff.js:12` LogicalOperator (Survived)
- `src/tavle/static/components/diff.js:12` ConditionalExpression (Survived)
- `src/tavle/static/components/diff.js:12` ConditionalExpression (Survived)
- `src/tavle/static/components/diff.js:42` EqualityOperator (Timeout)
- `src/tavle/static/components/diff.js:42` AssignmentOperator (Timeout)
- `src/tavle/static/components/diff.js:91` ConditionalExpression (Survived)
- `src/tavle/static/components/diff.js:91` LogicalOperator (Survived)
- `src/tavle/static/components/diff.js:113` StringLiteral (Survived)
- `src/tavle/static/components/diff.js:5` ArrayDeclaration (Survived)
- `src/tavle/static/components/diff.js:5` StringLiteral (Survived)
- `src/tavle/static/components/endpoint.js:23` ConditionalExpression (Survived)
- `src/tavle/static/components/file-tree.js:24` ConditionalExpression (Survived)
- `src/tavle/static/components/file-tree.js:24` ConditionalExpression (Survived)
- `src/tavle/static/components/file-tree.js:24` EqualityOperator (Survived)
- `src/tavle/static/components/flow.js:20` StringLiteral (NoCoverage)
- `src/tavle/static/components/flow.js:20` ConditionalExpression (Survived)
- `src/tavle/static/components/form.js:8` ConditionalExpression (Survived)
- `src/tavle/static/components/form.js:8` EqualityOperator (Survived)

## Killing tests per source file

| File | Total | Killed | Survived | NoCoverage | Timeout | Killed by |
|---|---|---|---|---|---|---|
| `src/tavle/static/components/annotated-code.js` | 96 | 95 | 1 | 0 | 0 | `tests/components/code_diff.test.js` |
| `src/tavle/static/components/callout.js` | 41 | 39 | 2 | 0 | 0 | `tests/components/callout.test.js`, `tests/components/containers.test.js` |
| `src/tavle/static/components/change-summary.js` | 22 | 22 | 0 | 0 | 0 | `tests/components/code_diff.test.js` |
| `src/tavle/static/components/chart.js` | 120 | 120 | 0 | 0 | 0 | `tests/components/charts_diagrams.test.js` |
| `src/tavle/static/components/checklist.js` | 75 | 75 | 0 | 0 | 0 | `tests/components/blocks_text.test.js` |
| `src/tavle/static/components/choice.js` | 48 | 48 | 0 | 0 | 0 | `tests/components/inputs.test.js`, `tests/components/inputs_markup.test.js` |
| `src/tavle/static/components/code.js` | 83 | 83 | 0 | 0 | 0 | `tests/components/code_diff.test.js` |
| `src/tavle/static/components/columns.js` | 2 | 2 | 0 | 0 | 0 | `tests/components/containers.test.js` |
| `src/tavle/static/components/comment.js` | 25 | 25 | 0 | 0 | 0 | `tests/components/inputs.test.js`, `tests/components/inputs_markup.test.js` |
| `src/tavle/static/components/data-model.js` | 84 | 84 | 0 | 0 | 0 | `tests/components/backend.test.js` |
| `src/tavle/static/components/decision.js` | 90 | 90 | 0 | 0 | 0 | `tests/components/blocks_text.test.js`, `tests/components/mount.test.js` |
| `src/tavle/static/components/deps.js` | 59 | 59 | 0 | 0 | 0 | `tests/components/code_diff.test.js` |
| `src/tavle/static/components/diagram.js` | 43 | 43 | 0 | 0 | 0 | `tests/components/charts_diagrams.test.js` |
| `src/tavle/static/components/diff.js` | 245 | 233 | 9 | 1 | 2 | `tests/components/code_diff.test.js` |
| `src/tavle/static/components/endpoint.js` | 47 | 46 | 1 | 0 | 0 | `tests/components/backend.test.js` |
| `src/tavle/static/components/file-tree.js` | 90 | 87 | 3 | 0 | 0 | `tests/components/code_diff.test.js` |
| `src/tavle/static/components/flow.js` | 42 | 40 | 1 | 1 | 0 | `tests/components/charts_diagrams.test.js` |
| `src/tavle/static/components/form.js` | 98 | 96 | 2 | 0 | 0 | `tests/components/inputs.test.js`, `tests/components/inputs_markup.test.js` |
