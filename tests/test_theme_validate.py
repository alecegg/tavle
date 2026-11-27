"""Theme contrast validation."""

from typing import cast

import pytest

from tavle.theme.derive_colour import derive_dark
from tavle.theme.presets import load_preset
from tavle.theme.tokens import ThemeError
from tavle.theme.validate import validate_theme

# Some derive_colour mutants loop forever; fail fast so they count as killed.
pytestmark = pytest.mark.timeout(2, method="signal")


def test_preset_and_derived_dark_pass():
    preset = load_preset("varde")
    light = cast("dict[str, str]", preset.light)
    dark = cast("dict[str, str]", preset.dark)
    validate_theme(light, dark, preset.shared, "preset")
    tint = cast("float", preset.shared["tint-strength"])
    validate_theme(light, derive_dark(light, tint), preset.shared, "preset")


def test_failures_are_reported_together():
    preset = load_preset("varde")
    preset.light["accent"] = "#aaaaaa"
    preset.light["success"] = preset.light["warning"]
    with pytest.raises(ThemeError) as error:
        validate_theme(
            cast("dict[str, str]", preset.light),
            cast("dict[str, str]", preset.dark),
            preset.shared,
            "page",
        )
    message = str(error.value)
    assert "page: [light] accent #aaaaaa on card is 2.3:1, needs 4.5:1" in message
    assert "success and warning hues differ" in message
    assert len(message.splitlines()) > 2


def test_unreachable_dark_tone_tint_names_text_token():
    preset = load_preset("varde")
    preset.dark["surface"] = "#ffffff"
    with pytest.raises(
        ThemeError, match="tone-warning-text.*tone-warning-tint layers over card"
    ):
        validate_theme(
            cast("dict[str, str]", preset.light),
            cast("dict[str, str]", preset.dark),
            preset.shared,
            "page",
        )


def test_dark_failures_print_the_whole_line():
    preset = load_preset("varde")
    preset.dark["surface"] = "#ffffff"
    with pytest.raises(ThemeError) as error:
        validate_theme(
            cast("dict[str, str]", preset.light),
            cast("dict[str, str]", preset.dark),
            preset.shared,
            "page",
        )
    lines = str(error.value).split("\n")
    assert all(line.startswith("page: [dark] ") for line in lines)
    assert all(line.endswith(":1") for line in lines)
    assert lines[0] == (
        "page: [dark] tone-info-text #000000 on two tone-info-tint layers "
        "over card is 1.8:1, needs 4.5:1"
    )


# Status hue pairs at the edges of the rule: either side of the red wrap, just
# under and exactly at 20 degrees, and a colour exactly at the 0.15 saturation floor.
@pytest.mark.parametrize(
    ("overrides", "pair", "degrees"),
    [
        ({"success": "#c80000", "warning": "#c8000f"}, "success and warning", "4.5"),
        ({"success": "#ff0000", "warning": "#ff5500"}, "success and warning", "20.0"),
        ({"success": "#ff0000", "warning": "#ff5500"}, "warning and danger", "20.0"),
        ({"success": "#ab0000", "warning": "#ab3900"}, "success and warning", None),
        ({"success": "#171111", "warning": "#c03000"}, "success and warning", "15.0"),
        ({"info": "#171111", "danger": "#c00000"}, "danger and info", "0.0"),
    ],
)
def test_status_hue_distance(overrides, pair, degrees):
    preset = load_preset("varde")
    preset.light.update(overrides)
    try:
        validate_theme(
            cast("dict[str, str]", preset.light),
            cast("dict[str, str]", preset.dark),
            preset.shared,
            "page",
        )
        message = ""
    except ThemeError as error:
        message = str(error)
    found = [line for line in message.split("\n") if f"{pair} hues differ" in line]
    expected = (
        f"page: [light] {pair} hues differ by {degrees} degrees, need 20.0 degrees"
    )
    assert found == ([] if degrees is None else [expected])
