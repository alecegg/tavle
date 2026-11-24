from varde.base.contrast import contrast_ratio
from varde.pages.theme.derive_colour import derive_colour, derive_dark

TOKENS = {
    "surface": "#f0f0f0",
    "card": "#ffffff",
    "text": "#101010",
    "accent": "#100020",
    "accent-alt": "#006060",
    "info": "#000080",
    "success": "#006000",
    "warning": "#805000",
    "danger": "#800000",
    "decision": "#600080",
}


def test_palette_and_ink_steps():
    palette = derive_colour(TOKENS, 0.12, 0.2)
    assert palette["--vd-text"] == (16, 16, 16, 1)
    assert palette["--vd-ink-36"] == (16, 16, 16, 0.36)
    assert palette["--vd-accent-subtle"] == (16, 0, 32, 0.12)
    assert palette["--vd-tone-info"] == "240.000 100.000% 25.098%"


def test_dark_accent_contrast():
    palette = derive_colour(derive_dark(TOKENS, 0.12), 0.12, 0.2)
    accent = palette["--vd-accent"]
    assert isinstance(accent, tuple)
    for name in ("surface", "surface-sunk", "surface-elevated"):
        surface = palette["--vd-" + name]
        assert isinstance(surface, tuple)
        assert contrast_ratio(accent, surface) >= 4.5
