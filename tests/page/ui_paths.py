"""Paths into the UI library for page tests that check its files.

`UI_FIXTURES` are the component goldens the library's JS tests share; the tests
that read them move into the library with `pages-extract`.
"""

from pathlib import Path

from varde.ui import UI_STATIC

UI_ROOT = Path(str(UI_STATIC)).parent
UI_STATIC_DIR = Path(str(UI_STATIC))
UI_FIXTURES = UI_ROOT.parents[1] / "tests/components/fixtures"
