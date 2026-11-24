"""Design tokens and the stylesheet layout: contrast, literals, delivery."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

import pytest

from varde.pages.shell import static_css
from varde.pages.template import page_shell

CSS_DIR = Path(str(files("varde.pages").joinpath("static", "css")))
PART_NAMES = (
    "00-tokens", "01-base", "10-chrome", "20-choice", "21-form", "22-comment",
    "23-decision", "24-ranking", "25-slider", "30-menu", "31-toc", "40-table",
    "41-chart",    "42-diagram", "43-flow", "44-wireframe", "45-code", "46-callout",
    "47-change", "48-annotated", "50-blocks", "52-diff", "53-filetree",
    "54-checklist", "55-containers", "56-matrix", "57-sequence", "58-screen-flow",
    "58-stats",
    "59-timeline", "60-state", "61-risk", "62-er", "63-image", "64-change-summary",
    "65-header",
)  # fmt: skip
COLOUR_LITERAL = re.compile(
    r"#[0-9a-fA-F]{3,8}\b|\b(?:rgb|rgba|hsl|hsla|hwb|lab|lch|oklab|oklch|color-mix)\(",
    re.IGNORECASE,
)

# (foreground token, background tokens, minimum ratio): 4.5 text, 3 non-text.
TEXT, NON_TEXT = 4.5, 3.0
SURFACES = ("--vd-surface", "--vd-surface-sunk", "--vd-surface-elevated")
HUES = ("--vd-accent", "--vd-info", "--vd-success", "--vd-warning", "--vd-danger")
NON_TEXT_TOKENS = ("--vd-border-interactive", "--vd-focus-ring", "--vd-border-selected")
PAIRS = (
    *((fg, bg, TEXT) for fg in ("--vd-text", "--vd-text-secondary") for bg in SURFACES),
    *(
        (fg, bg, TEXT)
        for fg in HUES
        for bg in SURFACES
    ),
    ("--vd-on-accent", "--vd-accent", TEXT),
    ("--vd-text", "--vd-mark", TEXT),
    ("--vd-text", "--vd-selected", TEXT),
    ("--vd-text", "--vd-hover", TEXT),
    ("--vd-info", "--vd-info-subtle", TEXT),
    ("--vd-success", "--vd-success-subtle", TEXT),
    ("--vd-warning", "--vd-warning-subtle", TEXT),
    ("--vd-danger", "--vd-danger-subtle", TEXT),
    ("--vd-text", "--vd-success-subtle", TEXT),
    ("--vd-text", "--vd-danger-subtle", TEXT),
    *((tok, bg, NON_TEXT) for tok in NON_TEXT_TOKENS for bg in SURFACES),
    *(
        (f"--vd-series-{n}", bg, NON_TEXT)
        for n in range(1, 6)
        for bg in ("--vd-surface", "--vd-surface-elevated")
    ),
)  # fmt: skip


def _block(text: str, start: int) -> tuple[str, int]:
    """Body of the `{...}` opening at or after `start`, and the index after it."""
    open_at = text.index("{", start)
    depth, i = 0, open_at
    while True:
        depth += text[i] == "{"
        depth -= text[i] == "}"
        i += 1
        if depth == 0:
            return text[open_at + 1 : i - 1], i


def _declarations(body: str) -> dict[str, str]:
    return dict(re.findall(r"(--vd-[\w-]+)\s*:\s*([^;]+);", body))


def _tokens(scheme: str) -> dict[str, str]:
    raw = (CSS_DIR / "00-tokens.css").read_text()
    css = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    root, _ = _block(css, css.index(":root"))
    tokens = _declarations(root)
    if scheme == "dark":
        media = css.index("@media (prefers-color-scheme: dark)")
        dark_body, _ = _block(css, media)
        inner, _ = _block(dark_body, dark_body.index(":root"))
        tokens |= _declarations(inner)
    return tokens


def _resolve(value: str, tokens: dict[str, str]) -> str:
    value = value.strip()
    match = re.fullmatch(r"var\((--[\w-]+)\)", value)
    return _resolve(tokens[match.group(1)], tokens) if match else value


def _rgba(value: str) -> tuple[float, float, float, float]:
    if value.startswith("#"):
        digits = value.lstrip("#")
        r, g, b = (int(digits[i : i + 2], 16) for i in (0, 2, 4))
        return r, g, b, 1.0
    nums = [float(n) for n in re.findall(r"[\d.]+", value)]
    return nums[0], nums[1], nums[2], nums[3] if len(nums) > 3 else 1.0


def _over(top: tuple, below: tuple) -> tuple[float, float, float, float]:
    alpha = top[3]
    return (
        *(top[i] * alpha + below[i] * (1 - alpha) for i in range(3)),
        1.0,
    )


def _luminance(rgb: tuple) -> float:
    def channel(v: float) -> float:
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _ratio(fg: str, bg: str, tokens: dict[str, str], page: tuple) -> float:
    back = _over(_rgba(_resolve(tokens[bg], tokens)), page)
    front = _over(_rgba(_resolve(tokens[fg], tokens)), back)
    hi, lo = sorted((_luminance(front), _luminance(back)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_token_pairs_meet_contrast(scheme: str) -> None:
    tokens = _tokens(scheme)
    page = _rgba(_resolve(tokens["--vd-surface"], tokens))
    failures = []
    for fg, bg, minimum in PAIRS:
        ratio = _ratio(fg, bg, tokens, page)
        if ratio < minimum:
            failures.append(f"{scheme} {fg} on {bg}: {ratio:.2f} < {minimum}")
    assert not failures, "\n".join(failures)


def test_token_table_covers_the_design_language() -> None:
    tokens = _tokens("light")
    required = (
        "--vd-surface", "--vd-surface-sunk", "--vd-surface-elevated", "--vd-text",
        "--vd-text-secondary", "--vd-accent", "--vd-info", "--vd-success",
        "--vd-warning", "--vd-danger", "--vd-border", "--vd-border-interactive",
        "--vd-border-selected", "--vd-hover", "--vd-pressed", "--vd-focus-ring",
        "--vd-selected", "--vd-disabled-text", "--vd-error", "--vd-readonly",
        "--vd-shadow-0", "--vd-shadow-3", "--vd-dur-fast", "--vd-dur",
        "--vd-radius-s", "--vd-radius-m", "--vd-radius-l", "--vd-radius-full",
        "--vd-text-xs", "--vd-text-2xl", "--vd-space-1", "--vd-space-9",
    )  # fmt: skip
    assert [name for name in required if name not in tokens] == []
    css = (CSS_DIR / "00-tokens.css").read_text()
    for query in (
        "prefers-color-scheme: dark", "prefers-reduced-motion: reduce",
        "forced-colors: active", "pointer: coarse", "color-scheme: light dark",
    ):  # fmt: skip
        assert query in css


FLOW_TOKENS = ("--vd-flow-block", "--vd-flow-before-heading", "--vd-flow-after-heading")


def _space_step(name: str) -> int:
    """Index on the `--vd-space-N` scale that flow token `name` points at."""
    tokens = _tokens("light")
    match = re.fullmatch(r"var\(--vd-space-(\d+)\)", tokens[name].strip())
    assert match, f"{name} must be a --vd-space-N step, got {tokens[name]!r}"
    return int(match.group(1))


def test_flow_tokens_use_the_space_scale() -> None:
    for name in FLOW_TOKENS:
        assert _space_step(name) >= 1


def test_flow_leaves_more_room_before_a_heading_than_after_it() -> None:
    assert _space_step("--vd-flow-before-heading") > _space_step(
        "--vd-flow-after-heading"
    )
    assert _space_step("--vd-flow-before-heading") > _space_step("--vd-flow-block")


def test_base_applies_the_flow_tokens_to_the_page_blocks() -> None:
    base = (CSS_DIR / "01-base.css").read_text()
    for name in FLOW_TOKENS:
        assert f"margin-block-start: var({name})" in base
    assert "main > .block + .block.heading" in base
    assert "main > .block.heading + .block" in base
    assert "main > .block > [data-mithril] > * { margin-block: 0; }" in base


def test_part_files_exist_and_load_in_order() -> None:
    names = sorted(p.stem for p in CSS_DIR.glob("*.css"))
    assert names == list(PART_NAMES)
    shipped = static_css()
    positions = [
        shipped.index((CSS_DIR / f"{name}.css").read_text().splitlines()[0])
        for name in PART_NAMES
    ]
    assert positions == sorted(positions)


def test_no_colour_literal_outside_the_tokens_file() -> None:
    offenders = []
    for part in sorted(CSS_DIR.glob("*.css")):
        if part.name == "00-tokens.css":
            continue
        text = re.sub(r"/\*.*?\*/", "", part.read_text(), flags=re.DOTALL)
        offenders += [
            f"{part.name}: {m.group(0)}" for m in COLOUR_LITERAL.finditer(text)
        ]
    assert offenders == []


def test_hover_rules_sit_inside_the_hover_media_query() -> None:
    for part in sorted(CSS_DIR.glob("*.css")):
        text = part.read_text()
        while "@media (hover: hover)" in text:
            start = text.index("@media (hover: hover)")
            _, end = _block(text, start)
            text = text[:start] + text[end:]
        assert ":hover" not in text, part.name


def test_no_import_inline_style_or_foreign_url() -> None:
    for part in sorted(CSS_DIR.glob("*.css")):
        text = part.read_text()
        assert not re.search(r"@import|expression\(|style=", text), part.name
        assert not re.search(r"url\(\s*[\"']?(?:https?:)?//", text), part.name


def test_served_css_equals_the_concatenation() -> None:
    parts = [p.read_text() for p in sorted(CSS_DIR.glob("*.css"))]
    assert static_css() == "\n".join(parts)
    assert "@import" not in static_css()
    assert "url(" not in static_css()


def test_export_inlines_the_same_css() -> None:
    out = page_shell("t", "<main></main>", None)
    assert f"<style>{static_css()}</style>" in out


def test_served_route_returns_the_concatenation() -> None:
    from varde.pages.serve import static_body

    assert static_body("app.css") == static_css().encode("utf-8")


def test_heading_tokens_keep_default_values_and_drive_chrome() -> None:
    expected = {
        "heading-weight": "700",
        "title-weight": "750",
        "heading-tracking": "-0.01em",
        "title-tracking": "-0.02em",
        "heading-case": "none",
        "heading-color": "var(--vd-text)",
        "heading-mark-size": "0.5em",
    }
    tokens = _tokens("light")
    chrome = (CSS_DIR / "10-chrome.css").read_text()
    for name, value in expected.items():
        assert tokens[f"--vd-{name}"] == value
        assert f"var(--vd-{name})" in chrome
