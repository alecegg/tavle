"""The shared component cases cover every registered component and run as expected."""

from __future__ import annotations

import pytest
from cases_loader import Case, load_cases

from varde.pages.blocks import COMPONENT_SPECS
from varde.pages.blocks.check import check_props

CASES = load_cases()


def test_every_component_has_a_valid_and_an_invalid_case() -> None:
    valid = {c.component for c in CASES if c.valid}
    invalid = {c.component for c in CASES if not c.valid}
    assert set(COMPONENT_SPECS) - valid == set()
    assert set(COMPONENT_SPECS) - invalid == set()


def test_every_case_names_a_registered_component() -> None:
    assert {c.component for c in CASES} - set(COMPONENT_SPECS) == set()


def test_case_names_are_unique() -> None:
    names = [c.name for c in CASES]
    assert len(names) == len(set(names))


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_case_runs_through_check_props(case: Case) -> None:
    errors = check_props(case.component, case.props, 1)
    found = {(e.rule, e.path) for e in errors}
    if case.valid:
        assert errors == [], [e.text() for e in errors]
        return
    matched = [e for e in errors if e.rule == case.rule and case.path in ("", e.path)]
    assert matched, f"expected {case.rule} {case.path!r}; got {sorted(found)}"
