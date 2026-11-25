# Tavle

Tavle owns the component vocabulary for standalone pages and app surfaces. Python source is in `src/tavle`, JavaScript and CSS in `src/tavle/static`, and tests in `tests`. See the README Orientation for each area. OpenSpec changes live in `openspec/changes`.

- `src/tavle/page`, `src/tavle/comments`, `src/tavle/serve`: Markdown page rendering, the comments log and the page server; each has its own README Orientation.
- `src/tavle/listings.py` and `src/tavle/cli.py`: the `tavle` command (`export`, `render`, `serve`, `check`, `comments`) and its listings.
- Bridge consumer: varde's `src/varde/ui.py` (in the varde repository) imports public names from `tavle/__init__.py`; keep those names exported when changing them.

## Checks

Run `just test` (CI job `test`) for lint, pytest without `matrix_full` cells, and vitest; `just test-fast` (pre-push) also skips `slow` tests; `just test-matrix` (CI job `matrix`) runs the widget-matrix cells outside the default subset, and fixture x width, scheme and mode pairs run only there. Run `openspec validate --all --strict` for OpenSpec changes. `vitest list --json` takes an output path: pass a scratch path (`--json=<scratch>`), never a test file. The library has no runtime dependencies and makes no model API calls.

<!-- flow:begin -->
## Flow skills

- Settle unsettled scope with `flow-plan`. Apply tasks with `openspec-apply-change` and archive them with `openspec-archive-change`.
- Build one bounded task with `flow-build`. Lead several tasks with `flow-orchestrate`; its `references/step-agent-routes.md` owns how agents start and their caps.
- Small-change exception: you may change a few lines with no design choice directly, following `flow-build`. The change is still reviewed.
- Code written outside a skill route follows `references/code-design.md` in the installed `flow-build` skill directory.
- Subagents spawn only what their brief or card allows, and report once, in their final reply.
- If you were launched with a bounded task, follow that brief instead.
<!-- flow:end -->
