"""Merge theme layers over the default preset into a validated `ResolvedTheme`."""

from typing import cast

from .derive_colour import derive_colour, derive_dark
from .derive_shape import derive_shape
from .layers import Layer
from .presets import load_preset
from .resolved import ResolvedTheme
from .validate import validate_theme


def resolve_layers(layers: list[tuple[Layer, str]]) -> ResolvedTheme:
    """Merge labelled layers, lowest first, over the default preset."""
    base = load_preset("varde")
    values: dict[str, dict[str, object]] = {
        scope: dict(getattr(base, scope)) for scope in ("shared", "light", "dark")
    }
    sources = {
        scope: dict.fromkeys(items, "preset varde") for scope, items in values.items()
    }
    for layer, label in layers:
        if layer.preset:
            base = load_preset(layer.preset)
            values = {scope: dict(getattr(base, scope)) for scope in values}
            sources = {
                scope: dict.fromkeys(items, f"preset {layer.preset}")
                for scope, items in values.items()
            }
        for scope in values:
            items = getattr(layer, scope)
            values[scope].update(items)
            sources[scope].update(dict.fromkeys(items, label))
    shared = cast("dict[str, str | int | float]", values["shared"])
    light = cast("dict[str, str]", values["light"])
    dark = derive_dark(light, float(shared["tint-strength"]))
    dark.update(cast("dict[str, str]", values["dark"]))
    for name in dark:
        sources["dark"].setdefault(name, "derived")
    validate_theme(light, dark, shared, layers[-1][1] if layers else "preset varde")
    tint, border = float(shared["tint-strength"]), float(shared["border-strength"])
    tokens = {"shared": shared, "light": dict(light), "dark": dict(dark)}
    return ResolvedTheme(
        tokens,
        sources,
        derive_colour(light, tint, border),
        derive_colour(dark, tint, border),
        derive_shape(shared),
        bool(layers),
    )
