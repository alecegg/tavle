"""Built-in presets are complete, valid and visually distinct."""

from typing import cast

import pytest

from varde.ui.theme.presets import PRESET_NAMES, load_preset
from varde.ui.theme.tokens import TOKENS
from varde.ui.theme.validate import validate_theme


@pytest.mark.parametrize("name", PRESET_NAMES)
def test_preset_is_complete_and_valid(name: str) -> None:
    preset = load_preset(name)
    assert set(preset.shared) == {t.name for t in TOKENS if t.scope == "shared"}
    colours = {t.name for t in TOKENS if t.scope == "scheme"}
    assert set(preset.light) == colours
    assert set(preset.dark) == colours
    validate_theme(
        cast("dict[str, str]", preset.light),
        cast("dict[str, str]", preset.dark),
        preset.shared,
        name,
    )


def test_presets_have_distinct_identities() -> None:
    presets = [load_preset(name) for name in PRESET_NAMES]
    for values in (
        [p.light["accent"] for p in presets],
        [p.shared["font-heading"] for p in presets],
        [p.shared["radius"] for p in presets],
    ):
        assert len(set(values)) == len(PRESET_NAMES)
