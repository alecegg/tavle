"""Contrast math: thresholds, compositing, and parity with reference ratios."""

import pytest

from tavle.contrast import (
    composite,
    contrast_ratio,
    fails_threshold,
    is_large_text,
    parse_rgba,
    required_ratio,
)

# Ratios from the repo browser-test helper (runner/tests/test_web_browser.py
# contrast_ratio) for these pairs; fixed here because design may not read runner.
PAIRS = [
    ("rgb(0, 0, 0)", "rgb(255, 255, 255)", 21.0),
    ("rgb(170, 170, 170)", "rgb(255, 255, 255)", 2.3231230535045992),
    ("rgb(36, 87, 197)", "rgb(255, 255, 255)", 6.472421857201706),
    ("rgb(89, 89, 89)", "rgb(238, 238, 255)", 6.107204193944122),
    ("rgb(255, 255, 255)", "rgb(36, 87, 197)", 6.472421857201706),
]


@pytest.mark.parametrize(("foreground", "background", "expected"), PAIRS)
def test_ratio_matches_reference_values(
    foreground: str, background: str, expected: float
) -> None:
    ours = contrast_ratio(parse_rgba(foreground), parse_rgba(background))
    assert ours == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("rgb(1, 2, 3)", (1, 2, 3, 1.0)),
        ("rgba(1, 2, 3, 0.5)", (1, 2, 3, 0.5)),
        ("rgb(1 2 3 / 50%)", (1, 2, 3, 0.5)),
        ("rgba(1, 2, 3, 5)", (1, 2, 3, 1.0)),
        ("rgba(1, 2, 3, -2)", (1, 2, 3, 0.0)),
    ],
)
def test_parse_rgba(text: str, expected: tuple[float, ...]) -> None:
    assert parse_rgba(text) == expected


def test_translucent_foreground_is_composited() -> None:
    half_black = parse_rgba("rgba(0, 0, 0, 0.5)")
    white = parse_rgba("rgb(255, 255, 255)")
    assert composite(half_black, white)[:3] == pytest.approx((127.5, 127.5, 127.5))
    assert contrast_ratio(half_black, white) < 21.0


@pytest.mark.parametrize(
    ("px", "weight", "large", "required"),
    [
        (16, 400, False, 4.5),
        (24, 400, True, 3.0),
        (18, 700, True, 3.0),
        (18, 400, False, 4.5),
    ],
)
def test_large_text_threshold(
    px: int, weight: int, large: bool, required: float
) -> None:
    assert is_large_text(px, weight) is large
    assert required_ratio(px, weight) == required


def test_fail_margin_is_0_05() -> None:
    assert fails_threshold(4.45, 4.5) is False
    assert fails_threshold(4.449, 4.5) is True
