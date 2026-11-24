"""Built-in presets remain complete and match the default CSS palette."""

import re
from importlib.resources import files

import pytest

from varde.ui.theme.presets import PRESET_NAMES, load_preset
from varde.ui.theme.tokens import TOKENS, ThemeError


def test_varde_complete() -> None:
    layer = load_preset("varde")
    assert set(layer.shared) == {t.name for t in TOKENS if t.scope == "shared"}
    for scheme in (layer.light, layer.dark):
        assert set(scheme) == {t.name for t in TOKENS if t.scope == "scheme"}


def test_unknown_preset() -> None:
    with pytest.raises(ThemeError) as exc:
        load_preset("missing")
    assert all(name in str(exc.value) for name in PRESET_NAMES)


def test_palette_matches_css() -> None:
    css = files("varde.pages").joinpath("static/css/00-tokens.css").read_text()
    light, dark = css.split("@media (prefers-color-scheme: dark)", 1)
    layer = load_preset("varde")
    mapping = {
        "surface": "surface",
        "card": "surface-elevated",
        "text": "ink",
        "accent": "accent",
        "accent-alt": "accent-2",
        "success": "success",
        "warning": "warning",
        "danger": "danger",
        "info": "info",
    }
    for block, palette in ((light, layer.light), (dark, layer.dark)):
        for token, css_name in mapping.items():
            match = re.search(
                rf"--vd-{css_name}:\s*(#[0-9a-f]{{6}}|rgb\((\d+), (\d+), (\d+)\))",
                block,
            )
            assert match
            value = (
                match.group(1)
                if match.group(1).startswith("#")
                else "#" + "".join(f"{int(n):02x}" for n in match.group(2, 3, 4))
            )
            assert palette[token] == value
