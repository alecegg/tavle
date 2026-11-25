set shell := ["bash", "-cu"]

lint:
    uv run --locked lint-imports
    uv run --locked ruff check
    uv run --locked ruff format --check
    scripts/check-ruff-baseline.sh
    uv run --locked pyright --warnings
    scripts/check-mollify.sh
    npx fallow dead-code --fail-on-issues
    npx fallow health --fail-on-issues
    npx fallow architecture --fail-on-issues

test:
    just lint
    uv run --locked pytest -q -n 3 -m 'not matrix_full'
    npx vitest run

test-fast:
    just lint
    uv run --locked pytest -q -n 3 -m 'not slow and not matrix_full'
    npx vitest run

test-matrix:
    uv run --locked pytest -q -n 3 -m matrix_full

hooks:
    .githooks/install

mutate *args:
    scripts/capped.sh "${MUTATION_MEM:-4G}" "${MUTATION_MINUTES:-20}" uv run --locked python scripts/mutate.py {{args}}
