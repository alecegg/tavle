"""Public theme token facts and value validation."""

import re
from dataclasses import dataclass
from typing import Literal

Kind = Literal["colour", "enum", "number", "integer"]
Scope = Literal["scheme", "shared"]


@dataclass(frozen=True)
class Token:
    name: str
    kind: Kind
    scope: Scope
    description: str
    minimum: float | None = None
    maximum: float | None = None
    step: int | None = None
    choices: tuple[str, ...] = ()


FONT_STACKS = {
    "sans": 'system-ui, -apple-system, "Segoe UI", sans-serif',
    "humanist": '"Gill Sans", "Trebuchet MS", sans-serif',
    "serif": 'Georgia, "Times New Roman", serif',
    "rounded": '"Arial Rounded MT Bold", "Trebuchet MS", sans-serif',
    "mono": '"SFMono-Regular", Consolas, monospace',
}

TOKENS = (
    *(
        Token(name, "colour", "scheme", description)
        for name, description in (
            ("surface", "Page background"),
            ("card", "Block surface"),
            ("text", "Body ink"),
            ("accent", "Primary accent"),
            ("accent-alt", "Secondary accent"),
            ("success", "Success tone"),
            ("warning", "Warning tone"),
            ("danger", "Danger tone"),
            ("info", "Information tone"),
            ("decision", "Decision tone"),
            *((f"series-{i}", f"Chart series {i}") for i in range(1, 6)),
        )
    ),
    Token("font-body", "enum", "shared", "Body font", choices=tuple(FONT_STACKS)),
    Token(
        "font-heading", "enum", "shared", "Heading font", choices=(*FONT_STACKS, "body")
    ),
    Token("type-scale", "number", "shared", "Body type scale", 0.90, 1.15),
    Token("heading-scale", "number", "shared", "Heading type scale", 0.85, 1.35),
    Token("heading-weight", "integer", "shared", "Heading weight", 500, 800, 50),
    Token(
        "heading-tracking", "number", "shared", "Heading tracking in em", -0.03, 0.08
    ),
    Token("heading-case", "enum", "shared", "Heading case", choices=("none", "upper")),
    Token(
        "heading-color", "enum", "shared", "Heading colour", choices=("text", "accent")
    ),
    Token(
        "heading-marker", "enum", "shared", "Heading marker", choices=("square", "none")
    ),
    Token("radius", "integer", "shared", "Corner radius in pixels", 0, 16),
    Token("space-scale", "number", "shared", "Spacing scale", 0.85, 1.20),
    Token("section-gap", "integer", "shared", "Heading spacing step", 4, 9),
    Token("page-width", "integer", "shared", "Page width in rem", 44, 80),
    Token("tint-strength", "number", "shared", "Tint opacity", 0.04, 0.20),
    Token("border-strength", "number", "shared", "Border opacity", 0.10, 0.35),
)
TOKEN_BY_NAME = {token.name: token for token in TOKENS}


class ThemeError(ValueError):
    """A theme layer contains an invalid value."""


def parse_colour(value: object) -> tuple[int, int, int]:
    """Parse a strict six-digit hexadecimal colour."""
    if not isinstance(value, str) or re.fullmatch(r"#[0-9a-fA-F]{6}", value) is None:
        raise ValueError("expected #rrggbb")
    return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]


def validate_value(token: Token, value: object, layer: str) -> None:
    """Reject a value outside the token's declared type or range."""
    rule = ""
    if token.kind == "colour":
        try:
            parse_colour(value)
        except ValueError:
            rule = "expected #rrggbb"
    elif token.kind == "enum":
        if not isinstance(value, str) or value not in token.choices:
            rule = f"expected one of {', '.join(token.choices)}"
    else:
        valid_type = isinstance(value, int if token.kind == "integer" else (int, float))
        if isinstance(value, bool) or not valid_type:
            rule = f"expected {token.kind}"
        elif (
            isinstance(value, (int, float))
            and token.minimum is not None
            and token.maximum is not None
        ):
            if not token.minimum <= value <= token.maximum:
                rule = f"expected {token.minimum} to {token.maximum}"
            elif token.step is not None and (value - token.minimum) % token.step:
                rule = f"expected steps of {token.step} from {token.minimum}"
    if rule:
        raise ThemeError(f"{layer}: {token.name} {value!r}: {rule}")
