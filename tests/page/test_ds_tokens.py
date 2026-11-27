"""Agent-Native visual bar: tone contrast, hairline elevation, density, doc layout."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

import pytest
from ui_paths import UI_STATIC_DIR

CSS_DIR = Path(str(files("tavle.page").joinpath("static", "css")))
UI_CSS_DIR = UI_STATIC_DIR / "css"
CSS_FILES = sorted(
    [*CSS_DIR.glob("*.css"), *UI_CSS_DIR.glob("*.css")], key=lambda p: p.name
)
TONES = ("info", "decision", "risk", "warning", "success")
TRIPLE = re.compile(r"(\d+) (\d+)% (\d+)%")


def _css(name: str) -> str:
    return re.sub(
        r"/\*.*?\*/",
        "",
        (next(p for p in CSS_FILES if p.stem == name)).read_text(),
        flags=re.DOTALL,
    )


def _body(css: str, start: int) -> tuple[str, int]:
    open_at = css.index("{", start)
    depth, i = 0, open_at
    while True:
        depth += css[i] == "{"
        depth -= css[i] == "}"
        i += 1
        if depth == 0:
            return css[open_at + 1 : i - 1], i


def _decls(body: str) -> dict[str, str]:
    return {k: v.strip() for k, v in re.findall(r"(--vd-[\w-]+)\s*:\s*([^;]+);", body)}


def _scheme_tokens(scheme: str) -> dict[str, str]:
    css = _css("00-tokens")
    root, _ = _body(css, css.index(":root"))
    tokens = _decls(root)
    if scheme == "dark":
        media = css.index("@media (prefers-color-scheme: dark)")
        dark, _ = _body(css, media)
        inner, _ = _body(dark, dark.index(":root"))
        tokens |= _decls(inner)
    return tokens


def test_dark_triples_are_ten_lightness_points_above_light() -> None:
    light, dark = _scheme_tokens("light"), _scheme_tokens("dark")
    for tone in TONES:
        lh, ls, ll = map(int, TRIPLE.fullmatch(light[f"--vd-tone-{tone}"]).groups())  # type: ignore[union-attr]
        dh, ds, dl = map(int, TRIPLE.fullmatch(dark[f"--vd-tone-{tone}"]).groups())  # type: ignore[union-attr]
        assert (dh, ds, dl) == (lh, ls, ll + 10)


def test_forced_colors_maps_every_tone_to_system_colours() -> None:
    css = _css("00-tokens")
    body, _ = _body(css, css.index("@media (forced-colors: active)"))
    forced = _decls(body)
    for tone in TONES:
        assert forced[f"--vd-tone-{tone}-edge"] == "CanvasText"
        assert forced[f"--vd-tone-{tone}-text"] == "CanvasText"


def test_no_blurred_box_shadow_anywhere() -> None:
    for scheme in ("light", "dark"):
        for name, value in _scheme_tokens(scheme).items():
            if name.startswith("--vd-shadow"):
                assert value == "none", name
    for part in CSS_FILES:
        for value in re.findall(r"box-shadow\s*:\s*([^;}]+)", _css(part.stem)):
            spread_only = re.fullmatch(
                r"0 -?\d+px 0 0 [^,]+|0 0 0 \d+px [^,]+|none|var\(--vd-shadow-\d\)",
                value.strip(),
            )
            assert spread_only, f"{part.name}: {value}"


@pytest.mark.parametrize("preset", ["compact", "roomy"])
def test_density_attribute_switches_the_vars(preset: str) -> None:
    css = _css("00-tokens")
    default = _decls(_body(css, css.index(":root"))[0])
    body, _ = _body(css, css.index(f'[data-density="{preset}"]'))
    switched = _decls(body)
    names = {n for n in default if n.startswith("--vd-density-")}
    assert names == {f"--vd-density-{k}" for k in ("pad", "font", "radius", "stroke")}
    assert set(switched) == names
    assert switched != {n: default[n] for n in names}


def _root_tokens() -> dict[str, str]:
    css = _css("00-tokens")
    return _decls(_body(css, css.index(":root"))[0])


def _families(stack: str) -> list[str]:
    return [f.strip().strip("\"'") for f in stack.split(",")]


def test_body_stack_is_proportional_system_fonts_that_never_fall_back_to_mono() -> None:
    families = _families(_root_tokens()["--vd-font-body"])
    assert families[-1] == "sans-serif"
    assert "system-ui" in families and "Arial" in families
    assert not {"monospace", "ui-monospace", "Liberation Mono"} & set(families)
    # a host whose system-ui alias is monospace must still reach a named sans family
    assert families.index("Arial") < families.index("system-ui")
    assert "@font-face" not in _css("00-tokens") + _css("01-base") + _css("10-chrome")


def test_mono_stack_is_monospace_and_used_for_code() -> None:
    assert _families(_root_tokens()["--vd-font-mono"])[-1] == "monospace"
    assert re.search(
        r"code,\s*pre\s*\{[^}]*font-family:\s*var\(--vd-font-mono\)", _css("01-base")
    )


def test_prose_blocks_are_limited_to_the_reading_measure() -> None:
    measure = _root_tokens()["--vd-measure"]
    assert 70 <= int(re.fullmatch(r"(\d+)ch", measure).group(1)) <= 80  # type: ignore[union-attr]
    assert re.search(
        r"main > \.block > :is\(p, ul, ol, blockquote\) \{"
        r"[^}]*max-inline-size: var\(--vd-measure\)",
        _css("10-chrome"),
    )
