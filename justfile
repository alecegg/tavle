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
    uv run --locked pytest -q
    npx vitest run

hooks:
    .githooks/install

mutate *args:
    python3 scripts/mutate.py {{args}}
