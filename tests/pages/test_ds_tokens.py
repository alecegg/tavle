"""Agent-Native visual bar: tone contrast, hairline elevation, density, doc layout."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

import pytest

CSS_DIR = Path(str(files("varde.pages").joinpath("static", "css")))
UI_CSS_DIR = Path(__file__).resolve().parents[2] / "src/varde/ui/static/css"
CSS_FILES = sorted(
    [*CSS_DIR.glob("*.css"), *UI_CSS_DIR.glob("*.css")], key=lambda p: p.name
)
TONES = ("info", "decision", "risk", "warning", "success")
TRIPLE = re.compile(r"(\d+) (\d+)% (\d+)%")
# classes the part files styled before the restyle; each must keep a rule
CLASSES = """
accept-btn actions align-center align-right arrow back block changed chart
choice-body choice-detail choice-error choice-grid choice-group choice-label
choice-note choice-option choice-options choice-question choice-send choice-state
choice-text comment-announce comment-count comment-error comment-field
comment-note comment-send comment-state comment-text composer danger
decision-approve decision-buttons decision-comment decision-deny decision-diff
decision-error decision-evidence decision-glyph decision-item decision-label
decision-note decision-question decision-send decision-state decision-status
decision-text decision-text-line decision-verdict dep-graph destructive diagram
doc-header doc-name done dragging edge error flow form-body form-checkbox
form-error form-field form-grid form-hint form-label form-remaining form-row
form-send form-state form-title ghost graph-empty graph-note meta missing node
orphans over-after over-before primary ranking-buttons ranking-grip ranking-hint
ranking-line ranking-list ranking-live ranking-move ranking-row ranking-text recap
recap-drift recap-error recap-file recap-state reply resolved scroll slider-end
slider-ends slider-error slider-group slider-input slider-label slider-send
slider-state slider-ticks slider-track slider-value status suggestion
task text thread vb vb-area vb-auth vb-auth-none vb-axis vb-badge vb-bar vb-bar-fill
vb-bar-num vb-bar-svg vb-bar-track vb-card vb-center vb-chart vb-col vb-controls
vb-ctl vb-data vb-data-grid vb-data-scroll vb-dense vb-dot vb-end vb-error vb-filter
vb-filter-status vb-filterbar vb-flow vb-flowbar vb-foot vb-grid vb-group-head
vb-badge-key vb-hash vb-hit vb-key vb-key-mark vb-last vb-legend vb-line
vb-method vb-na vb-name
vb-next vb-note vb-note-label vb-num vb-off vb-on vb-open vb-pct vb-plot
vb-r1 vb-r2 vb-r3 vb-r4 vb-r5 vb-readout vb-region vb-rel vb-relations vb-s0 vb-s1
vb-s2 vb-s3 vb-s4 vb-s5 vb-scroll vb-scrollhint vb-series-toggle vb-slice
vb-slice-key vb-sort vb-sortpick vb-sortselect vb-spark vb-state vb-status
vb-status-bad vb-status-neutral vb-status-ok vb-status-warn vb-step vb-sym vb-tab
vb-table vb-table-stack vb-table-sticky vb-tabs vb-tick vb-tip vb-tip-box
vb-tip-text vb-title vb-wire vd-cap vd-chev vd-dashed vd-detail
vd-dim vd-dotted vd-edge vd-elabel vd-elabel-bg vd-frame vd-g1 vd-g2 vd-g3
vd-group-head vd-group-label vd-head vd-head-hit vd-hot vd-label vd-line vd-near
vd-node vd-sel vd-shape vd-super vd-svg vd-view vf-down vf-up vw-bar vw-bezel vw-box
vw-compare vw-detail vw-dot vw-fig vw-frames vw-hatch vw-hot vw-kind vw-note
vw-note-on vw-notes vw-pin vw-region vw-region-label vw-screen vw-sel vw-svg vw-view
wireframe
""".split()  # noqa: SIM905


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


def test_neutral_ramp_is_ten_forty_five_ninety_ninety_five() -> None:
    light = _scheme_tokens("light")
    assert light["--vd-neutral-text"] == "hsl(0 0% 10%)"
    assert light["--vd-neutral-muted"] == "hsl(0 0% 45%)"
    assert light["--vd-line"] == "hsl(0 0% 90%)"
    assert light["--vd-fill"] == "hsl(0 0% 95%)"


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


def test_every_pre_existing_class_still_has_a_rule() -> None:
    css = "\n".join(_css(p.stem) for p in CSS_FILES)
    selectors = re.sub(r"\{[^{}]*\}", ";", css)
    missing = [
        c for c in CLASSES if not re.search(rf"\.{re.escape(c)}(?![\w-])", selectors)
    ]
    assert missing == []


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


def test_page_is_a_container_with_a_60rem_column_and_1_75_body() -> None:
    base, tokens = _css("01-base"), _css("00-tokens")
    assert "container: vd-doc / inline-size" in base
    assert "--vd-doc-width: 60rem" in tokens and "--vd-toc-width: 11rem" in tokens
    assert "--vd-body-leading: 1.75" in tokens
    assert "var(--vd-body-leading)" in base


def test_toc_is_a_collapsed_block_by_default_and_a_rail_from_64rem() -> None:
    base = _css("01-base")
    assert not re.search(r"\.doc-toc\s*\{[^}]*display:\s*none", base)
    start = base.index("@container vd-doc (min-width: 64rem)")
    inside, _ = _body(base, start)
    assert "display: block" in inside and "position: sticky" in inside
    assert "var(--vd-toc-width)" in inside


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


def test_headings_use_their_font_token_and_are_bolder_than_body() -> None:
    chrome = _css("10-chrome")
    heading = re.search(r"\nh1, h2, h3, h4, h5, h6 \{([^}]*)\}", "\n" + chrome)
    assert heading
    assert "font-family: var(--vd-font-heading)" in heading.group(1)
    assert "font-weight: var(--vd-heading-weight)" in heading.group(1)
    assert _root_tokens()["--vd-heading-weight"] == "700"
    assert _families(_root_tokens()["--vd-font-heading"]) == ["var(--vd-font-body)"]
    assert re.search(r"\.doc-name \{[^}]*font-family: var\(--vd-font-heading\)", chrome)


def test_prose_blocks_are_limited_to_the_reading_measure() -> None:
    measure = _root_tokens()["--vd-measure"]
    assert 70 <= int(re.fullmatch(r"(\d+)ch", measure).group(1)) <= 80  # type: ignore[union-attr]
    assert re.search(
        r"main > \.block > :is\(p, ul, ol, blockquote\) \{"
        r"[^}]*max-inline-size: var\(--vd-measure\)",
        _css("10-chrome"),
    )
