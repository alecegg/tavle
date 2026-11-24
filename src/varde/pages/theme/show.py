"""Theme reports as plain data, with one text form for each report shape."""

from typing import TypedDict

from varde.pages.theme.resolve import ResolvedTheme
from varde.ui.theme.presets import PRESET_NAMES, load_preset
from varde.ui.theme.tokens import TOKENS, Token

type Values = dict[str, dict[str, object]]


class Catalog(TypedDict):
    presets: list[str]
    tokens: dict[str, dict[str, str]]


def _rule(token: Token) -> str:
    if token.choices:
        return "|".join(token.choices)
    if token.minimum is None or token.maximum is None:
        return "#rrggbb"
    step = f" step {token.step}" if token.step else ""
    return f"{token.minimum:g}..{token.maximum:g}{step}"


def theme_catalog() -> Catalog:
    """Preset names and the public token catalog."""
    return {
        "presets": list(PRESET_NAMES),
        "tokens": {t.name: {"type": t.kind, "range": _rule(t)} for t in TOKENS},
    }


def catalog_text(catalog: Catalog) -> str:
    """One line for the presets, then one line per token."""
    tokens = catalog["tokens"]
    lines = ["Presets: " + ", ".join(catalog["presets"])]
    lines.extend(
        f"{name}: {item['type']} {item['range']}" for name, item in tokens.items()
    )
    return "\n".join(lines)


def preset_values(name: str) -> Values:
    """The public values of a named preset, by scope."""
    preset = load_preset(name)
    return {
        scope: dict(getattr(preset, scope)) for scope in ("shared", "light", "dark")
    }


def resolved_values(theme: ResolvedTheme) -> Values:
    """Each resolved public value with the layer it came from, by scope."""
    return {
        scope: {
            key: {"value": value, "source": theme.sources[scope][key]}
            for key, value in items.items()
        }
        for scope, items in theme.tokens.items()
    }


def _value_line(scope: str, key: str, item: object) -> str:
    if isinstance(item, dict):
        return f"{scope}.{key}: {item['value']} ({item['source']})"
    return f"{scope}.{key}: {item}"


def values_text(values: Values) -> str:
    """One `scope.token: value` line per token, with its source when known."""
    return "\n".join(
        _value_line(scope, key, item)
        for scope, items in values.items()
        for key, item in items.items()
    )
