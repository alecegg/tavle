# Tavle

Tavle is a UI component library for standalone pages and app surfaces. Its Python half parses statements, validates component specs, prepares props, derives themes and builds standalone HTML. Its JavaScript half provides Mithril views and interaction enhancers, with shared CSS and theme tokens.

## Orientation

- `src/tavle/lines`: statement grammar, parsing, identifiers and references.
- `src/tavle/blocks`: component specifications and prop validation.
- `src/tavle/blocks_render`: prepared props, layout and drawing for components.
- `src/tavle/theme`: theme tokens, presets, derivation and CSS.
- `src/tavle/static`: Mithril views, interaction scripts, styles and vendored Mithril.

## Checks

Run `just test` for lint, Python tests and JavaScript tests. `just lint` checks Ruff, Pyright, Mollify and Fallow; `just hooks` installs the Git hooks. Mollify and Ruff use checked-in baselines for existing findings.

Run `just mutate --only 'tavle.theme.merge.*'` to run mutmut over `src/tavle` in a throwaway copy under `$TMPDIR`; add `--fresh` to discard the cached results, and see `scripts/mutate.py` for the other options.

Varde's import-linter checks its own package layers, which Tavle does not have. Its shell, skill, reference, license, PEX and deployment checks cover Varde-specific assets or executables.

## Rename

To rename the library, update the Python distribution and module name in `pyproject.toml`, the name in `package.json`, and move the source directory with `git mv src/tavle src/<new-name>`. Use `rg -l 'tavle' tests src` to find test imports and `files("tavle")` calls, then update them. Run `uv lock` and update the npm lockfile. Update varde's bridge module, dependency and source lines in `pyproject.toml`, and `uv.lock`. Catalog names are owned by `catalog/names.py` when that module exists.
