"""Built-in presets are complete, valid and visually distinct."""

import hashlib
from typing import cast

import pytest

from tavle.theme.css import theme_css
from tavle.theme.layers import Layer
from tavle.theme.merge import resolve_layers
from tavle.theme.presets import PRESET_NAMES, load_preset
from tavle.theme.tokens import TOKENS
from tavle.theme.validate import validate_theme

# Some derive_colour mutants loop forever; fail fast so they count as killed.
pytestmark = pytest.mark.timeout(2, method="signal")


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


@pytest.mark.parametrize(
    ("name", "digest"),
    [
        ("varde", "289addaa5d14720d"),
        ("paper", "53fdb5a20c06918c"),
        ("harbor", "2ad0a1e707d91ef9"),
        ("signal", "0542df377b98f802"),
    ],
)
def test_preset_css_is_pinned(name: str, digest: str) -> None:
    css = theme_css(resolve_layers([(Layer(preset=name), "page")]))
    assert hashlib.sha256(css.encode()).hexdigest()[:16] == digest
