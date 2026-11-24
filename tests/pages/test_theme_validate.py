"""Theme contrast validation."""

from typing import cast

import pytest

from varde.pages.theme.derive_colour import derive_dark
from varde.pages.theme.presets import load_preset
from varde.pages.theme.tokens import ThemeError
from varde.pages.theme.validate import validate_theme


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
