"""The page library package has its three subpackages and an orientation README."""

import importlib
from pathlib import Path

import tavle

PAGELIB = Path(tavle.__file__).parent
SUBPACKAGES = ("page", "comments", "serve")


def test_subpackages_import() -> None:
    for name in SUBPACKAGES:
        assert importlib.import_module(f"tavle.{name}").__doc__


def test_readme_orientation_names_the_owner() -> None:
    text = (PAGELIB / "README.md").read_text(encoding="utf-8")
    assert "## Orientation" in text
    assert "tavle owns the component vocabulary" in text
