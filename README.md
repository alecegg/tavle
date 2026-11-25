# Tavle

Tavle is a UI component library for standalone pages and app surfaces. Its Python half parses statements, validates component specs, prepares props, derives themes and builds standalone HTML. Its JavaScript half provides Mithril views and interaction enhancers, with shared CSS and theme tokens.

## Standalone use

Run `uv run tavle` in this checkout on a Markdown page. Each verb takes the page path (`doc`):

1. `export`: write one self-contained HTML file. Example: `tavle export page.md --out page.html`
2. `render`: print the page HTML fragment to stdout. Example: `tavle render page.md > fragment.html`
3. `serve`: serve the page on a loopback port with live updates; it prints the URL. Example: `tavle serve page.md`
4. `check`: print the page errors and warnings; exit 1 on errors. Example: `tavle check page.md --json`
5. `comments`: list the comments recorded for the page. Example: `tavle comments page.md --json`

## Orientation

- `src/tavle/lines`: statement grammar, parsing, identifiers and references.
- `src/tavle/blocks`: component specifications and prop validation.
- `src/tavle/blocks_render`: prepared props, layout and drawing for components.
- `src/tavle/theme`: theme tokens, presets, derivation and CSS.
- `src/tavle/static`: Mithril views, interaction scripts, styles and vendored Mithril.
- `src/tavle/page`: Markdown page rendering, includes, page checks, page themes and page chrome.
- `src/tavle/comments`: the comments store, validation and file watching for a page.
- `src/tavle/serve`: the loopback page server and the export of served pages.
- `src/tavle/listings.py`: pure listings and formatting for the page commands.
- `src/tavle/cli.py`: the `tavle` command: argument parsing and the five verbs.

## Checks

Run `just test` (CI job `test`) for lint, Python tests without `matrix_full` cells, and JavaScript tests. Run `just test-fast` for the same without `slow` tests; it is the pre-push check. Run `just test-matrix` (CI job `matrix`) for the widget-matrix cells outside the default subset: fixture x width, scheme and mode pairs run only there, not in `test` or pre-push. `just lint` checks Ruff, Pyright, Mollify and Fallow; `just hooks` installs the Git hooks: pre-commit runs `just lint` and pre-push runs `just test-fast`. Mollify and Ruff use checked-in baselines for existing findings.

Run `just mutate --only 'tavle.theme.merge.*'` to run mutmut over `src/tavle` in a throwaway copy under `$TMPDIR`; add `--fresh` to discard the cached results, and see `scripts/mutate.py` for the other options.

Layers are checked by `uv run lint-imports`; its contracts are owned by `[tool.importlinter]` in `pyproject.toml`.

## Rename

To rename the library, update the Python distribution and module name in `pyproject.toml`, the name in `package.json`, and move the source directory with `git mv src/tavle src/<new-name>`. Use `rg -l 'tavle' tests src` to find test imports and `files("tavle")` calls, then update them. Run `uv lock` and update the npm lockfile. Update varde's bridge module, dependency and source lines in `pyproject.toml`, and `uv.lock`. Catalog names are owned by `catalog/names.py` when that module exists.
