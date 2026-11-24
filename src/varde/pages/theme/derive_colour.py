"""Derive page colours from a scheme's public colour tokens."""

from __future__ import annotations

import colorsys
from collections.abc import Mapping

from varde.base.contrast import RGBA, contrast_ratio


def _rgba(value: str, alpha: float = 1) -> RGBA:
    return (
        float(int(value[1:3], 16)),
        float(int(value[3:5], 16)),
        float(int(value[5:7], 16)),
        alpha,
    )


def _hls(value: str) -> tuple[float, float, float]:
    r, g, b, _ = _rgba(value)
    return colorsys.rgb_to_hls(r / 255, g / 255, b / 255)


def _hex(h: float, lightness: float, saturation: float) -> str:
    rgb = colorsys.hls_to_rgb(h, lightness, saturation)
    return "#" + "".join(f"{round(channel * 255):02x}" for channel in rgb)


def _over(colour: RGBA, alpha: float, base: RGBA) -> RGBA:
    """`colour` at `alpha` laid over the opaque `base`."""
    mixed = (
        round(c * alpha + b * (1 - alpha))
        for c, b in zip(colour[:3], base[:3], strict=True)
    )
    return (*mixed, 1)  # type: ignore[return-value]


def derive_dark(
    light_tokens: Mapping[str, str], tint_strength: float
) -> dict[str, str]:
    """Keep hue and lift colours to contrast on dark surfaces and on their own tint."""
    result: dict[str, str] = {}
    for name in ("surface", "card", "text"):
        h, _, s = _hls(light_tokens[name])
        result[name] = _hex(
            h, {"surface": 0.10, "card": 0.15, "text": 0.92}[name], min(s, 0.8)
        )
    h, lightness, s = _hls(result["surface"])
    surfaces = [
        _rgba(result["surface"]),
        _rgba(result["card"]),
        _rgba(_hex(h, max(0, lightness - 0.04), s)),
    ]
    for name, value in light_tokens.items():
        if name in result:
            continue
        h, _, s = _hls(value)
        candidate = _hex(h, 1, min(s, 0.8))
        for step in range(70, 101, 2):
            candidate = _hex(h, step / 100, min(s, 0.8))
            colour = _rgba(candidate)
            tint = _over(colour, tint_strength, surfaces[1])
            if all(contrast_ratio(colour, back) >= 4.5 for back in (*surfaces, tint)):
                break
        result[name] = candidate
    return result


def derive_colour(
    tokens: Mapping[str, str], tint_strength: float, border_strength: float
) -> dict[str, RGBA | str]:
    """Return literal colour declarations, with tone triples represented as CSS text."""
    result: dict[str, RGBA | str] = {}

    def put(name: str, colour: RGBA) -> None:
        result["--vd-" + name] = colour

    text = _rgba(tokens["text"])
    surface = _rgba(tokens["surface"])
    dark = sum(surface[:3]) < 382.5
    put("ink", text)
    put("text", text)
    for step in (4, 8, 16, 36, 50, 60, 70, 80):
        put(f"ink-{step}", (*text[:3], step / 100))
    put("text-secondary", (*text[:3], 0.7))
    put("surface", surface)
    put("surface-elevated", _rgba(tokens["card"]))
    h, lightness, s = _hls(tokens["surface"])
    sunk = _rgba(_hex(h, max(0, lightness - (0.04 if dark else 0.03)), s))
    put("surface-sunk", sunk)
    for name, alpha in (
        ("neutral-text", 1),
        ("neutral-muted", 0.7),
        ("line", border_strength),
        ("border", border_strength),
        ("fill", 0.05),
        ("hover", 0.08),
        ("pressed", 0.16),
        ("disabled-text", 0.36),
        ("disabled-surface", 0.04),
    ):
        put(name, (*text[:3], alpha))
    put("readonly", sunk)
    alpha = border_strength
    while alpha < 1 and any(
        contrast_ratio((*text[:3], alpha), bg) < 3
        for bg in (surface, _rgba(tokens["card"]), sunk)
    ):
        alpha = min(1, round(alpha + 0.01, 2))
    put("border-interactive", (*text[:3], alpha))
    for name, source in (
        ("accent", "accent"),
        ("accent-2", "accent-alt"),
        ("info", "info"),
        ("success", "success"),
        ("warning", "warning"),
        ("danger", "danger"),
        ("error", "danger"),
    ):
        colour = _rgba(tokens[source])
        put(name, colour)
        if name != "error":
            put(name + "-subtle", (*colour[:3], tint_strength))
    accent = _rgba(tokens["accent"])
    white: RGBA = (255, 255, 255, 1)
    black: RGBA = (0, 0, 0, 1)
    put("on-accent", max((white, black), key=lambda c: contrast_ratio(c, accent)))
    for name in ("border-selected", "focus-ring"):
        put(name, accent)
    put("selected", (*accent[:3], tint_strength))
    for index, default in enumerate(
        ("success", "warning", "decision", "accent-alt", "danger"), 1
    ):
        colour = _rgba(tokens.get(f"series-{index}", tokens[default]))
        put(f"series-{index}", colour)
        put(f"series-{index}-fill", (*colour[:3], tint_strength))
    for tone, source in (
        ("info", "info"),
        ("decision", "decision"),
        ("risk", "danger"),
        ("warning", "warning"),
        ("success", "success"),
    ):
        colour = _rgba(tokens[source])
        h, lightness, s = _hls(tokens[source])
        result[f"--vd-tone-{tone}"] = (
            f"{h * 360:.3f} {s * 100:.3f}% {lightness * 100:.3f}%"
        )
        for suffix, alpha in (
            ("edge", 1),
            ("tint", tint_strength),
            ("tint-2", tint_strength / 4),
            ("text", 1),
        ):
            put(f"tone-{tone}-{suffix}", (*colour[:3], alpha))
    return result
