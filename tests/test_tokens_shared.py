"""The token file serves the dashboard too: explicit and OS dark values must agree."""

from __future__ import annotations

import colorsys
import re
from importlib.resources import files
from pathlib import Path

import pytest

TOKENS = files("tavle").joinpath("static", "css", "00-tokens.css")
CSS = Path(str(TOKENS)).read_text()
CHROME = Path(str(files("tavle.page").joinpath("static", "css", "10-chrome.css")))


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
def test_tone_text_meets_aa_on_its_tint_over_every_surface(scheme: str) -> None:
    tokens = _scheme(scheme)
    failures = []
    for surface in SURFACES:
        ground = _color(scheme, surface)
        for tone in TONES:
            tint = _parse(_resolve(tokens[f"--vd-tone-{tone}-tint"], tokens), ground)
            ratio = _contrast(_color(scheme, f"--vd-tone-{tone}-text"), tint)
            if ratio < 4.5:
                failures.append(f"{tone} on {surface}: {ratio:.2f}")
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_tone_edge_meets_ui_contrast_on_every_surface(scheme: str) -> None:
    """The tone triple (`h s% l%`) draws badges and edges, so it needs 3:1."""
    failures = []
    for tone in TONES:
        edge = _parse(f"hsl({_scheme(scheme)[f'--vd-tone-{tone}']})")
        for surface in SURFACES:
            ratio = _contrast(edge, _color(scheme, surface))
            if ratio < 3.0:
                failures.append(f"{tone} on {surface}: {ratio:.2f}")
    assert not failures, "\n".join(failures)


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


def test_heading_tokens_are_shared_across_schemes_and_drive_chrome() -> None:
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
        assert f"var({token})" in CHROME.read_text()
        assert CSS.count(f"{token}:") == 1
        for selector in (
            "@media (prefers-color-scheme: dark)",
            ':root[data-theme="dark"]',
        ):
            assert token not in _declarations(_body(selector))
