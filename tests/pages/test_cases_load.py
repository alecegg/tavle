"""The shared component cases cover every registered component.

`test_components_contract.py` runs each case through the check and renderer.
"""

from __future__ import annotations

from cases_loader import load_cases

from varde.pages.blocks import COMPONENT_SPECS

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
