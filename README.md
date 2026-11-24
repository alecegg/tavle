## Rename

To rename the library, update the Python distribution and module name in `pyproject.toml`, the name in `package.json`, and move the source directory with `git mv src/tavle src/<new-name>`. Use `rg -l 'tavle' tests src` to find test imports and `files("tavle")` calls, then update them. Run `uv lock` and update the npm lockfile. Update varde's bridge module, dependency and source lines in `pyproject.toml`, and `uv.lock`. Catalog names are owned by `catalog/names.py` when that module exists.
