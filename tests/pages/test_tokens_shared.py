"""The token file serves the dashboard too: explicit and OS dark values must agree."""

from __future__ import annotations

import colorsys
import re
from importlib.resources import files
from pathlib import Path

import pytest

TOKENS = files("varde.ui").joinpath("static", "css", "00-tokens.css")
CSS = Path(str(TOKENS)).read_text()


def _body(selector_start: str) -> str:
    """Body of the first block whose header starts with `selector_start`."""
    start = CSS.index(selector_start)
    open_at = CSS.index("{", start)
    depth = 0
    for i in range(open_at, len(CSS)):
        depth += CSS[i] == "{"
        depth -= CSS[i] == "}"
        if depth == 0:
            return CSS[open_at + 1 : i]
    raise AssertionError("unclosed block")


def _declarations(body: str) -> dict[str, str]:
    return dict(re.findall(r"(--vd-[\w-]+)\s*:\s*([^;]+);", body))


def test_explicit_dark_theme_matches_the_os_dark_theme() -> None:
    os_dark = _declarations(_body("@media (prefers-color-scheme: dark)"))
    explicit = _declarations(_body(':root[data-theme="dark"]'))
    assert os_dark and os_dark == explicit


def test_os_dark_theme_skips_a_page_forced_light() -> None:
    media = _body("@media (prefers-color-scheme: dark)")
    assert ':root:not([data-theme="light"])' in media
    assert "color-scheme: light" in _body(':root[data-theme="light"]')


def test_flow_tokens_are_declared_once_for_both_schemes() -> None:
    """Spacing is scheme-independent: the dark blocks must not redeclare it."""
    for block in (
        _body("@media (prefers-color-scheme: dark)"),
        _body(':root[data-theme="dark"]'),
    ):
        assert "--vd-flow-" not in block
    assert CSS.count("--vd-flow-block:") == 1


# --- palette and surfaces: parse the token values, no browser ---

Rgb = tuple[float, float, float]
SCHEMES = ("light", "dark")
SURFACES = ("--vd-surface", "--vd-surface-elevated", "--vd-surface-sunk")
# body copy 4.5:1; large text and UI parts 3:1
TEXT_TOKENS = (
    "--vd-text",
    "--vd-text-secondary",
    "--vd-accent",
    "--vd-accent-2",
    "--vd-success",
    "--vd-warning",
    "--vd-danger",
)
TONES = ("info", "decision", "risk", "warning", "success")


def _scheme(scheme: str) -> dict[str, str]:
    tokens = _declarations(_body(":root, :host"))
    if scheme == "dark":
        tokens |= _declarations(_body(':root[data-theme="dark"]'))
    return tokens


def _resolve(value: str, tokens: dict[str, str]) -> str:
    """Substitute var(--x) references until none are left."""
    while match := re.search(r"var\((--vd-[\w-]+)\)", value):
        value = value.replace(match.group(0), tokens[match.group(1)])
    return value


def _hsl_to_rgb(h: float, s: float, light: float) -> Rgb:
    r, g, b = colorsys.hls_to_rgb(h / 360, light / 100, s / 100)
    return (r * 255, g * 255, b * 255)


def _parse(value: str, below: Rgb | None = None) -> Rgb:
    """An opaque colour; an alpha colour is mixed over `below`."""
    value = value.strip()
    alpha = 1.0
    if value.startswith("#"):
        rgb = tuple(float(int(value[i : i + 2], 16)) for i in (1, 3, 5))
    elif match := re.fullmatch(
        r"rgba?\(([\d.]+), ([\d.]+), ([\d.]+)(?:, ([\d.]+))?\)", value
    ):
        *rgb_parts, a = match.groups()
        rgb = tuple(float(v) for v in rgb_parts)
        alpha = float(a) if a else 1.0
    elif match := re.fullmatch(
        r"hsl\(([\d.]+) ([\d.]+)% ([\d.]+)%(?: / ([\d.]+))?\)", value
    ):
        h, s, light, a = match.groups()
        rgb = _hsl_to_rgb(float(h), float(s), float(light))
        alpha = float(a) if a else 1.0
    else:
        raise AssertionError(f"unparsed colour {value!r}")
    if alpha < 1.0:
        assert below is not None, f"{value} has alpha and no surface under it"
        rgb = tuple(
            c * alpha + b * (1 - alpha) for c, b in zip(rgb, below, strict=True)
        )
    return (rgb[0], rgb[1], rgb[2])


def _luminance(rgb: Rgb) -> float:
    def channel(v: float) -> float:
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    return (
        0.2126 * channel(rgb[0]) + 0.7152 * channel(rgb[1]) + 0.0722 * channel(rgb[2])
    )


def _contrast(a: Rgb, b: Rgb) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _color(scheme: str, name: str, below: Rgb | None = None) -> Rgb:
    tokens = _scheme(scheme)
    return _parse(_resolve(tokens[name], tokens), below)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_page_card_and_sunk_surfaces_are_visibly_distinct(scheme: str) -> None:
    page, card, sunk = (_color(scheme, name) for name in SURFACES)
    for one, other, label in (
        (page, card, "page/card"),
        (page, sunk, "page/sunk"),
        (card, sunk, "card/sunk"),
    ):
        assert _contrast(one, other) >= 1.05, f"{scheme} {label} are too close"


@pytest.mark.parametrize("scheme", SCHEMES)
@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("text", TEXT_TOKENS)
def test_text_tokens_meet_aa_on_every_surface(
    scheme: str, surface: str, text: str
) -> None:
    ground = _color(scheme, surface)
    assert _contrast(_color(scheme, text, ground), ground) >= 4.5


@pytest.mark.parametrize("scheme", SCHEMES)
@pytest.mark.parametrize("surface", SURFACES)
def test_interactive_borders_and_on_accent_text_meet_ui_contrast(
    scheme: str, surface: str
) -> None:
    ground = _color(scheme, surface)
    assert _contrast(_color(scheme, "--vd-border-interactive", ground), ground) >= 3.0
    accent = _color(scheme, "--vd-accent")
    assert _contrast(_color(scheme, "--vd-on-accent"), accent) >= 4.5


@pytest.mark.parametrize("scheme", SCHEMES)
@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("tone", TONES)
def test_tone_text_meets_aa_on_its_tint_over_every_surface(
    scheme: str, surface: str, tone: str
) -> None:
    tokens = _scheme(scheme)
    ground = _color(scheme, surface)
    tint = _parse(_resolve(tokens[f"--vd-tone-{tone}-tint"], tokens), ground)
    assert _contrast(_color(scheme, f"--vd-tone-{tone}-text"), tint) >= 4.5


@pytest.mark.parametrize("scheme", SCHEMES)
@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("tone", TONES)
def test_tone_edge_meets_ui_contrast_on_every_surface(
    scheme: str, surface: str, tone: str
) -> None:
    """The tone triple (`h s% l%`) draws badges and edges, so it needs 3:1."""
    edge = _parse(f"hsl({_scheme(scheme)[f'--vd-tone-{tone}']})")
    assert _contrast(edge, _color(scheme, surface)) >= 3.0


@pytest.mark.parametrize("scheme", SCHEMES)
def test_neutral_family_has_a_hue_and_the_accents_are_two_hues(scheme: str) -> None:
    for surface in SURFACES:
        r, g, b = _color(scheme, surface)
        assert max(r, g, b) - min(r, g, b) >= 3, f"{surface} is flat grey"
    hues = {
        round(
            colorsys.rgb_to_hls(
                *(c / 255 for c in _color(scheme, name, _color(scheme, "--vd-surface")))
            )[0]
            * 360,
            -1,
        )
        for name in ("--vd-accent", "--vd-accent-2")
    }
    assert len(hues) == 2


def test_heading_tokens_are_shared_across_schemes() -> None:
    names = (
        "heading-weight",
        "title-weight",
        "heading-tracking",
        "title-tracking",
        "heading-case",
        "heading-color",
        "heading-mark-size",
    )
    light = _declarations(_body(":root, :host"))
    for name in names:
        token = f"--vd-{name}"
        assert token in light
        assert CSS.count(f"{token}:") == 1
        for selector in (
            "@media (prefers-color-scheme: dark)",
            ':root[data-theme="dark"]',
        ):
            assert token not in _declarations(_body(selector))
