"""Shared theme token derivation."""

import re
from pathlib import Path

from varde.ui.theme.derive_shape import FIXED_TOKENS, derive_shape


def test_shared_defaults_and_coverage() -> None:
    tokens: dict[str, str | int | float] = {
        "font-body": "sans",
        "font-heading": "body",
        "type-scale": 1,
        "heading-scale": 1,
        "heading-weight": 700,
        "heading-tracking": -0.01,
        "heading-case": "none",
        "heading-color": "text",
        "heading-marker": "square",
        "radius": 8,
        "space-scale": 1,
        "section-gap": 8,
        "page-width": 60,
    }
    result = derive_shape(tokens)
    css = Path("src/varde/pages/static/css/00-tokens.css").read_text()
    for name, value in result.items():
        if name.startswith("--vd-font-"):
            continue
        assert f"{name}: {value};" in css
    assert not FIXED_TOKENS & result.keys()
    assert set(re.findall(r"(--vd-[\w-]+)\s*:", css)) >= FIXED_TOKENS
    tokens.update({"radius": 0, "heading-marker": "none"})
    result = derive_shape(tokens)
    assert all(
        result[name] == "0px"
        for name in (
            "--vd-radius-s",
            "--vd-radius-m",
            "--vd-radius-l",
            "--vd-code-radius",
        )
    )
    assert result["--vd-heading-mark-size"] == "0"
