set shell := ["bash", "-cu"]

test:
    #!/usr/bin/env bash
    status=0
    uv run pytest -q || status=1
    npx vitest run || status=1
    uv run pyright || status=1
    uv run ruff check || status=1
    uv run ruff format --check || status=1
    exit "$status"
