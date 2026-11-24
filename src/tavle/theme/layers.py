"""Parse and validate theme layers at their input boundaries."""

import contextlib
import difflib
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field

from ..theme.presets import PRESET_NAMES
from ..theme.tokens import TOKEN_BY_NAME, ThemeError, validate_value


@dataclass
class Layer:
    preset: str | None = None
    shared: dict[str, object] = field(default_factory=dict)
    light: dict[str, object] = field(default_factory=dict)
    dark: dict[str, object] = field(default_factory=dict)


def _token(name: str, value: object, scope: str, label: str) -> None:
    token = TOKEN_BY_NAME.get(name)
    if token is None:
        suggestions = difflib.get_close_matches(name, TOKEN_BY_NAME, n=3, cutoff=0.4)
        hint = f"; nearest: {', '.join(suggestions)}" if suggestions else ""
        raise ThemeError(f"{label}: unknown token {name!r} with value {value!r}{hint}")
    if token.scope != scope:
        raise ThemeError(f"{label}: {name} {value!r}: expected {token.scope} position")
    validate_value(token, value, label)


def _preset(value: object, label: str) -> str:
    names = PRESET_NAMES
    if not isinstance(value, str) or value not in names:
        matches = (
            difflib.get_close_matches(value, names) if isinstance(value, str) else []
        )
        raise ThemeError(
            f"{label}: preset {value!r}: expected one of {', '.join(names)}"
            + (f"; nearest: {', '.join(matches)}" if matches else "")
        )
    return value


def parse_toml(text: str, label: str) -> Layer:
    """Parse a TOML theme layer, identifying errors with its source label."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ThemeError(f"{label}: malformed TOML: {exc}") from exc
    layer = Layer()
    for name, value in data.items():
        if name == "preset":
            layer.preset = _preset(value, label)
        elif name in ("light", "dark"):
            if not isinstance(value, dict):
                raise ThemeError(f"{label}: {name} {value!r}: expected table")
            target = layer.light if name == "light" else layer.dark
            for key, item in value.items():
                _token(key, item, "scheme", label)
                target[key] = item
        else:
            _token(name, value, "shared", label)
            layer.shared[name] = value
    return layer


def parse_frontmatter(fields: Mapping[str, str], label: str = "front matter") -> Layer:
    """Parse flat page front matter, ignoring fields outside the theme namespace."""
    layer = Layer()
    for key, raw in fields.items():
        if key == "theme":
            layer.preset = _preset(raw, label)
            continue
        if not key.startswith("theme."):
            continue
        name = key[6:]
        dark = name.startswith("dark.")
        if dark:
            name = name[5:]
        token = TOKEN_BY_NAME.get(name)
        value: object = raw
        if token and token.kind in ("integer", "number"):
            with contextlib.suppress(ValueError):
                value = int(raw) if token.kind == "integer" else float(raw)
        scope = "scheme" if dark or (token and token.scope == "scheme") else "shared"
        _token(name, value, scope, label)
        target = (
            layer.dark if dark else layer.light if scope == "scheme" else layer.shared
        )
        target[name] = value
    return layer
