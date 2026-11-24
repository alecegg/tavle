import pytest

from varde.ui.theme.tokens import (
    FONT_STACKS,
    TOKENS,
    ThemeError,
    parse_colour,
    validate_value,
)


def test_catalog():
    assert len(TOKENS) == len({token.name for token in TOKENS}) == 30
    assert all(
        stack.endswith(("sans-serif", "serif", "monospace"))
        for stack in FONT_STACKS.values()
    )


@pytest.mark.parametrize(
    "name,good,bad",
    [
        ("surface", "#abcdef", "#abc"),
        ("font-body", "sans", "unknown"),
        ("type-scale", 1.0, 2.0),
        ("radius", 4, 4.5),
        ("heading-weight", 550, 525),
    ],
)
def test_values(name, good, bad):
    token = next(token for token in TOKENS if token.name == name)
    validate_value(token, good, "page")
    with pytest.raises(ThemeError, match="page"):
        validate_value(token, bad, "page")


@pytest.mark.parametrize("value", ["#ffffff;", "#ffffff}", "url(#ffffff)"])
def test_colour_rejects_css(value):
    with pytest.raises(ValueError):
        parse_colour(value)
