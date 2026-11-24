"""Resolved theme values."""

from dataclasses import dataclass

from ..contrast import RGBA


@dataclass
class ResolvedTheme:
    tokens: dict[str, dict[str, str | int | float]]
    sources: dict[str, dict[str, str]]
    light: dict[str, RGBA | str]
    dark: dict[str, RGBA | str]
    shared: dict[str, str]
    active: bool
