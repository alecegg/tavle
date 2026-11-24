"""Built-in theme preset resources."""

from __future__ import annotations

from importlib.resources import files
from typing import TYPE_CHECKING

from varde.pages.theme.tokens import ThemeError

if TYPE_CHECKING:
    from varde.pages.theme.layers import Layer

PRESET_NAMES = ("varde", "paper", "harbor", "signal")


def load_preset(name: str) -> Layer:
    """Load and validate a named built-in preset."""
    if name not in PRESET_NAMES:
        raise ThemeError(
            f"unknown preset {name!r}; expected one of {', '.join(PRESET_NAMES)}"
        )
    from varde.pages.theme.layers import parse_toml

    resource = files("varde.pages.theme").joinpath("presets", f"{name}.toml")
    return parse_toml(resource.read_text(encoding="utf-8"), f"preset {name}")
