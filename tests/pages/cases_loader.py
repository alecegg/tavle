"""Shared component cases: valid props from the widget matrix, invalid ones from JSON.

`load_cases()` returns every case as a plain record. Valid cases are the `ui`
statements of the widget matrix fixtures (`tests/pages/fixtures/widgets`), so
their props live only there. `tests/pages/cases/<component>.json` adds what the
matrix lacks: `valid` (props for a component no fixture draws) and `invalid`
(props with the fault code `check_props` must report).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from varde.pages.fences import ui_statements
from varde.ui.blocks_render.registry import PAGE_STATEMENTS

CASES = Path(__file__).parent / "cases"
MATRIX = Path(__file__).parent / "fixtures" / "widgets"
# Matrix statements that hold a deliberate rejection (`name` is `<fixture>:<id>`);
# the image invalid cases cover the same rules.
MATRIX_REJECTED = frozenset(
    {"rich-image-stress:s5", "rich-image-stress:s6"},
)


@dataclass(frozen=True)
class Case:
    name: str
    component: str
    props: dict[str, object]
    rule: str = ""  # the expected `BlockError.rule`; empty for a valid case
    path: str = ""  # the expected `BlockError.path`; empty when any path matches

    @property
    def valid(self) -> bool:
        return not self.rule


def _matrix_cases() -> list[Case]:
    cases = []
    for fixture in sorted(MATRIX.glob("*.md")):
        for _, statement in ui_statements(fixture.read_text(encoding="utf-8")):
            name = f"{fixture.stem}:{statement.id}"
            # Page statements (`include`) are not components; test_include covers them.
            page_only = statement.component in PAGE_STATEMENTS
            if name not in MATRIX_REJECTED and not page_only:
                cases.append(Case(name, statement.component, statement.props))
    return cases


def _file_cases(path: Path) -> list[Case]:
    data = json.loads(path.read_text(encoding="utf-8"))
    component = path.stem
    valid = [
        Case(f"{component}:{c['name']}", component, c["props"])
        for c in data.get("valid", [])
    ]
    invalid = [
        Case(
            f"{component}:{c['name']}",
            component,
            c["props"],
            c["rule"],
            c.get("path", ""),
        )
        for c in data.get("invalid", [])
    ]
    return valid + invalid


def load_cases() -> list[Case]:
    """Every case: matrix-derived valid ones first, then the case files' cases."""
    cases = _matrix_cases()
    for path in sorted(CASES.glob("*.json")):
        cases += _file_cases(path)
    return cases
