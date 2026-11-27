"""Contrast math: exact channel values and error text."""

import pytest

from tavle.contrast import composite, parse_rgba, relative_luminance


@pytest.mark.parametrize("text", ["#fff", "hsl(0)"])
def test_unsupported_colour_error_quotes_the_text(text: str) -> None:
    with pytest.raises(ValueError) as error:
        parse_rgba(text)
    assert str(error.value) == f"unsupported colour: {text!r}"


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
    # The sRGB cutoff itself (0.04045 * 255) is still on the linear segment.
    cutoff = relative_luminance((10.31475, 10.31475, 10.31475, 1))
    assert cutoff == pytest.approx(0.04045 / 12.92, rel=0, abs=1e-10)
