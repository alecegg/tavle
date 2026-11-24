"""Contrast math: exact channel values, error text, clamps and the failure margin."""

import pytest

from varde.ui.contrast import (
    FAIL_MARGIN,
    composite,
    fails_threshold,
    parse_rgba,
    relative_luminance,
)


def test_unsupported_colour_error_quotes_the_text() -> None:
    with pytest.raises(ValueError, match="^unsupported colour: 'hsl\\(0\\)'$"):
        parse_rgba("hsl(0)")


@pytest.mark.parametrize(
    ("text", "alpha"),
    [("rgba(1, 2, 3, 5)", 1.0), ("rgba(1, 2, 3, -2)", 0.0), ("rgba(1 2 3 / 50%)", 0.5)],
)
def test_alpha_is_clamped_to_the_unit_range(text: str, alpha: float) -> None:
    assert parse_rgba(text)[3] == alpha


def test_composite_of_nothing_is_transparent_black() -> None:
    assert composite((9, 8, 7, 0.0), (6, 5, 4, 0.0)) == (0.0, 0.0, 0.0, 0.0)


def test_composite_blends_each_channel_by_alpha() -> None:
    result = composite((255, 0, 0, 0.5), (0, 0, 200, 0.5))
    assert result == pytest.approx((170.0, 0.0, 66.6666667, 0.75))


def test_composite_keeps_channel_order() -> None:
    result = composite((10, 20, 30, 1.0), (200, 100, 50, 1.0))
    assert result == (10.0, 20.0, 30.0, 1.0)


def test_luminance_of_black_white_and_dark_channels() -> None:
    assert relative_luminance((0, 0, 0, 1)) == 0
    assert relative_luminance((255, 255, 255, 1)) == pytest.approx(1.0)
    assert relative_luminance((5, 5, 5, 1)) == pytest.approx(5 / 255 / 12.92)
    assert relative_luminance((255, 0, 0, 1)) == pytest.approx(0.2126)
    assert relative_luminance((0, 255, 0, 1)) == pytest.approx(0.7152)
    assert relative_luminance((0, 0, 255, 1)) == pytest.approx(0.0722)


def test_a_ratio_exactly_at_the_margin_does_not_fail() -> None:
    assert fails_threshold(4.5 - FAIL_MARGIN, 4.5) is False
    assert fails_threshold(4.5 - FAIL_MARGIN - 0.001, 4.5) is True
