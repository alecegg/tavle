import hashlib

import pytest

from tavle.contrast import contrast_ratio
from tavle.theme.derive_colour import derive_colour, derive_dark

# Some derive_colour mutants loop forever; fail fast so they count as killed.
pytestmark = pytest.mark.timeout(2, method="signal")

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


ORDER = [
    "surface",
    "card",
    "text",
    "accent",
    "accent-alt",
    "info",
    "success",
    "warning",
    "danger",
    "decision",
]


# Inputs picked so that each one reaches a derivation branch the palette above
# does not: mid-grey surfaces on both sides of the dark threshold, a near-black
# surface and a saturated one. The digest pins the whole result.
@pytest.mark.parametrize(
    ("function", "colours", "strengths", "digest"),
    [
        (
            derive_dark,
            "7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48875 34a20f 0b0d04 c36ed8 0e71e0",
            (0.08,),
            "d6ed9f131585ea2a",
        ),
        (
            derive_dark,
            "1e9840 6c189c 24279e 9851d5 814204 136feb 5713c1 66b132 69dd63 fc35c7",
            (0.12,),
            "c73ec5fc98487e72",
        ),
        (
            derive_colour,
            "7f7f80 3cfde6 f1c26b 30f90e c7dd01 e48875 34a20f 0b0d04 c36ed8 0e71e0",
            (0.08, 0.16),
            "ea15eef508ef95e5",
        ),
        (
            derive_colour,
            "7f8080 7670eb 940bd5 335f97 3daad8 619b91 ffc911 f57cce d458bb bf2ce0",
            (0.12, 0.2),
            "9b174f361413f9fa",
        ),
        (
            derive_colour,
            "151515 161616 d9d9d9 a745ad db6d88 31c2b0 f87821 142b44 56556d 89aa82",
            (0.3, 0.16),
            "3466a3f11e134ebb",
        ),
    ],
)
def test_pinned_derivations(function, colours, strengths, digest):
    tokens = {
        name: "#" + value for name, value in zip(ORDER, colours.split(), strict=True)
    }
    result = repr(function(tokens, *strengths))
    assert hashlib.sha256(result.encode()).hexdigest()[:16] == digest


def test_series_override_and_interactive_border_step():
    colours = dict.fromkeys(ORDER, "#000000")
    colours.update({"surface": "#ffffff", "card": "#ffffff", "series-1": "#010203"})
    palette = derive_colour(colours, 0.08, 0.155)
    assert palette["--vd-series-1"] == (1, 2, 3, 1)
    assert palette["--vd-border-interactive"] == (0, 0, 0, 0.42)
    # Text equal to the surface never reaches contrast 3, so the step stops at 1.
    flat = derive_colour(dict.fromkeys(ORDER, "#808080"), 0.08, 0.16)
    assert flat["--vd-border-interactive"] == (128, 128, 128, 1)
