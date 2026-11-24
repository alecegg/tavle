"""Derive shared presentation declarations from validated theme tokens."""

from varde.ui.theme.tokens import FONT_STACKS

FIXED_TOKENS = frozenset(
    {
        "--vd-font-mono",
        "--vd-measure",
        "--vd-leading-body",
        "--vd-leading-heading",
        "--vd-flow-block",
        "--vd-flow-after-heading",
        "--vd-radius-full",
        "--vd-shadow-0",
        "--vd-shadow-1",
        "--vd-shadow-2",
        "--vd-shadow-3",
        "--vd-label-size",
        "--vd-label-weight",
        "--vd-label-tracking",
        "--vd-code-header",
        "--vd-code-size",
        "--vd-toc-width",
        "--vd-toc-gap",
        "--vd-body-leading",
        "--vd-density-pad",
        "--vd-density-font",
        "--vd-density-radius",
        "--vd-density-stroke",
        "--vd-dur-fast",
        "--vd-dur",
        "--vd-dur-flash",
        "--vd-control-height",
        "--vd-mark",
        "--vd-overlay",
    }
)


def _number(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") or "0"


def derive_shape(tokens: dict[str, str | int | float]) -> dict[str, str]:
    """Return CSS declarations for the validated shared tokens."""
    body = str(tokens["font-body"])
    heading = str(tokens["font-heading"])
    type_scale = float(tokens["type-scale"])
    heading_scale = float(tokens["heading-scale"])
    space_scale = float(tokens["space-scale"])
    radius = float(tokens["radius"])
    tracking = float(tokens["heading-tracking"])
    result = {
        "--vd-font-body": FONT_STACKS[body],
        "--vd-font-heading": FONT_STACKS[body if heading == "body" else heading],
        "--vd-heading-weight": str(tokens["heading-weight"]),
        "--vd-title-weight": str(int(tokens["heading-weight"]) + 50),
        "--vd-heading-tracking": f"{_number(tracking)}em",
        "--vd-title-tracking": f"{_number(tracking - 0.01)}em",
        "--vd-heading-case": "uppercase"
        if tokens["heading-case"] == "upper"
        else "none",
        "--vd-heading-color": f"var(--vd-{tokens['heading-color']})",
        "--vd-heading-mark-size": "0.5em"
        if tokens["heading-marker"] == "square"
        else "0",
        "--vd-flow-before-heading": f"var(--vd-space-{tokens['section-gap']})",
        "--vd-doc-width": f"{tokens['page-width']}rem",
    }
    for name, value in zip(
        ("xs", "sm", "md", "lg", "xl", "2xl"),
        (0.75, 0.875, 1, 1.125, 1.25, 1.5),
        strict=True,
    ):
        result[f"--vd-text-{name}"] = f"{_number(value * type_scale)}rem"
    for name, values in {
        "title-size": (1.75, 1.3, 1.6, 2.25),
        "heading-1": (1.375, 1.1, 1.2, 1.5),
        "heading-2": (1.25, 1.05, 0.9, 1.375),
        "heading-3": (1.125, 1, 0.5, 1.25),
    }.items():
        a, b, c, d = (_number(value * heading_scale) for value in values)
        result[f"--vd-{name}"] = f"clamp({a}rem, {b}rem + {c}vw, {d}rem)"
    for index, value in enumerate((0.25, 0.5, 0.75, 1, 1.25, 1.5, 2, 2.5, 3), 1):
        result[f"--vd-space-{index}"] = f"{_number(value * space_scale)}rem"
    for name, factor in (
        ("radius-s", 0.5),
        ("radius-m", 0.75),
        ("radius-l", 1),
        ("code-radius", 1.5),
    ):
        result[f"--vd-{name}"] = f"{_number(radius * factor)}px"
    return result
