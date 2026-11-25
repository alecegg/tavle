"""Widget verification matrix (slow tier; needs Playwright Chromium).

Run: `uv run pytest tests/pages/widget_matrix -m slow -k <family>`, e.g.
`-k choice`, `-k chrome` or `-k "slider and stress"`. Cell ids read
`<family>-<fixture>-w<width>-<scheme>-<mode>`, so a failing id names its width,
scheme and mode. Axes: widths 320 375 768 1024 1440; light and dark; modes
default, reduced-motion, zoom200 (device scale 2), coarse (touch), forced-colors,
print, nojs (JavaScript disabled) and rtl (`dir=rtl` on the page).

Each page load is audited once for every family in its fixture (`audit.py` collects,
`checks.py` decides). Full-page PNGs go to a temp dir, or to `$VARDE_WIDGET_SHOTS`
when set (one file per fixture, mode, scheme and width). Fixtures live in
`tests/pages/fixtures/widgets/`: `normal.md`, `stress.md`, and `rich-<kind>.md`
plus `rich-<kind>-stress.md` added by the rich-block tasks (picked up by glob).
Pending families (`pending.py`) are `xfail(raises=AssertionError)` until the
widget task removes the line.
A page whose `ui` fences render as code raises `NotRendered` (never xfailed).
Chromium runs single-process (sandbox-safe), so each page load gets its own browser.
"""

from __future__ import annotations

import pytest

from .cells import Cell, all_cells
from .driver import Matrix
from .pending import PENDING

pytestmark = pytest.mark.slow


def _scope(cell: Cell) -> list[pytest.MarkDecorator]:
    return [] if cell.in_subset else [pytest.mark.matrix_full]


def _param(cell: Cell) -> object:
    reason = PENDING.get(cell.family)
    if not reason:
        return pytest.param(cell, id=cell.id, marks=_scope(cell))
    # AssertionError only: audit findings are expected while a family is
    # pending; a page that is not rendered (NotRendered) is a hard failure.
    # Not strict: some modes find nothing for a family before its redesign.
    xfail = pytest.mark.xfail(reason=reason, raises=AssertionError)
    return pytest.param(cell, id=cell.id, marks=[*_scope(cell), xfail])


@pytest.mark.parametrize("cell", [_param(c) for c in all_cells()])
def test_cell(cell: Cell, matrix: Matrix) -> None:
    problems = matrix.problems(cell)
    assert not problems, "\n".join(problems)
