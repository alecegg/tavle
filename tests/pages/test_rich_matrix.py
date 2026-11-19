"""matrix: table conversion, marker, totals, faults, escaping, registration."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any

import pytest

from varde.pages.blocks import check, check_props, type_text
from varde.pages.blocks_render.registry import COMPONENTS
from varde.pages.render import render_page

FIXTURES = Path(__file__).parent / "fixtures" / "widgets"


def sample(**extra: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "options": [{"id": "a", "label": "Alpha"}, {"id": "b", "label": "Beta"}],
        "criteria": [{"id": "x", "label": "Cost"}, {"id": "y", "label": "Speed"}],
        "cells": [["yes", "no"], ["partial", "yes"]],
    }
    return {**data, **extra}


def rules_of(data: dict[str, Any]) -> list[str]:
    return [e.rule for e in check_props("matrix", data, 1)]


def test_cell_count_fault_names_the_row() -> None:
    bad = sample(cells=[["yes", "no"], ["yes"]])
    found = [e.message for e in check_props("matrix", bad, 1)]
    assert any("cells[2] ('Speed') has 1 cells, expected 2" in m for m in found)
    assert "cells-rows" in rules_of(sample(cells=[["yes", "no"]]))


def test_one_scale_per_matrix() -> None:
    assert "scale" in rules_of(sample(cells=[["yes", "high"], ["no", "low"]]))
    assert rules_of(sample(cells=[["high", "text"], ["low", "free text"]])) == []


def test_props_are_validated() -> None:
    assert rules_of(sample()) == []
    assert rules_of(sample(covers=["x"])) == []
    assert "missing-key" in rules_of({})
    assert "recommended" in rules_of(sample(recommended="nope"))
    assert "duplicate" in rules_of(sample(options=[{"id": "a", "label": "A"}] * 2))
    assert "duplicate" in rules_of(
        sample(options=[{"id": "a", "label": "Criterion"}, {"id": "b", "label": "B"}])
    )
    bad = sample()
    bad["criteria"][0]["weight"] = 6
    assert "type" in rules_of(bad)
    bad["criteria"][0]["weight"] = True
    assert "type" in rules_of(bad)
    assert "limit" in rules_of(
        sample(options=[{"id": f"o{i}", "label": f"O{i}"} for i in range(13)])
    )
    assert "unknown-key" in rules_of(sample(extra=1))


def test_registered_help_and_fixtures() -> None:
    assert "matrix" in COMPONENTS
    text = files("varde.pages").joinpath("help", "blocks.txt").read_text()
    assert type_text("matrix") in text
    for name in ("rich-matrix", "rich-matrix-stress"):
        doc = (FIXTURES / f"{name}.md").read_text()
        assert check(doc) == []
        body = render_page(doc, "t.md").body
        assert "vb-error" not in body and "<img" not in body
        assert "<script>alert" not in body and "style=" not in body
        assert 'data-mithril="matrix"' in body


def test_stress_page_has_the_edge_cases() -> None:
    body = render_page((FIXTURES / "rich-matrix-stress.md").read_text(), "t.md").body
    assert "Twelve options" in body


@pytest.mark.parametrize("name", ["rich-matrix", "rich-matrix-stress"])
def test_fixture_family_exists(name: str) -> None:
    assert (FIXTURES / f"{name}.md").exists()
