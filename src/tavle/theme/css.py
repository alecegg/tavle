"""Emit validated theme declarations for document and shadow-root scopes."""

import math
import re

from ..theme.resolved import ResolvedTheme
from ..theme.tokens import FONT_STACKS

_NUMBER = r"-?(?:\d+(?:\.\d+)?|\.\d+)"
_VALUE = re.compile(
    rf"(?:{_NUMBER}(?:rem|px|em)?|{_NUMBER} {_NUMBER}% {_NUMBER}%|"
    rf"(?:rgb|rgba)\({_NUMBER}, {_NUMBER}, {_NUMBER}(?:, {_NUMBER})?\)|"
    rf"clamp\({_NUMBER}rem, {_NUMBER}rem \+ {_NUMBER}vw, {_NUMBER}rem\)|"
    r"var\(--vd-[a-z0-9-]+\)|none|uppercase)"
)
_NAME = re.compile(r"--vd-[a-z0-9-]+")


def _value(value: tuple[float, float, float, float] | str) -> str:
    if isinstance(value, tuple):
        if len(value) != 4 or not all(math.isfinite(x) for x in value):
            raise ValueError("Invalid theme colour")
        value = (
            "rgba("
            + ", ".join(f"{x:.6f}".rstrip("0").rstrip(".") or "0" for x in value)
            + ")"
        )
    if value not in FONT_STACKS.values() and not _VALUE.fullmatch(value):
        raise ValueError(f"Invalid theme value: {value!r}")
    return value


def _declarations(values: dict[str, tuple[float, float, float, float] | str]) -> str:
    lines = []
    for name, value in values.items():
        if not _NAME.fullmatch(name):
            raise ValueError(f"Invalid theme name: {name!r}")
        lines.append(f"  {name}: {_value(value)};")
    return "\n".join(lines)


def theme_css(theme: ResolvedTheme) -> str:
    """Render the light and two matching dark scopes."""
    light = _declarations({**theme.light, **theme.shared})
    dark = _declarations(theme.dark)
    return (
        f":root, :host {{\n{light}\n}}\n"
        f"@media (prefers-color-scheme: dark) {{\n"
        '  :root:not([data-theme="light"]), :host(:not([data-theme="light"])) {\n'
        f"{dark}\n  }}\n}}\n"
        f':root[data-theme="dark"], :host([data-theme="dark"]) {{\n{dark}\n}}\n'
    )


def style_element(css: str) -> str:
    """Wrap emitted CSS in its page style element."""
    if "</style" in css.lower():
        raise ValueError("Invalid style content")
    return f"<style data-vd-theme>{css}</style>"
