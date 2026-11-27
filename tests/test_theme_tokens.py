import pytest

from tavle.theme.show import catalog_text, theme_catalog, values_text
from tavle.theme.tokens import (
    FONT_STACKS,
    TOKENS,
    ThemeError,
    Token,
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


def test_parse_colour_channels():
    assert parse_colour("#123456") == (18, 52, 86)
    assert parse_colour("#ABCDEF") == (171, 205, 239)
    with pytest.raises(ValueError, match="^expected #rrggbb$"):
        parse_colour("red")


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("surface", "red", "p: surface 'red': expected #rrggbb"),
        (
            "heading-case",
            "title",
            "p: heading-case 'title': expected one of none, upper",
        ),
    ],
)
def test_value_error_messages(name, value, message):
    token = next(item for item in TOKENS if item.name == name)
    with pytest.raises(ThemeError) as error:
        validate_value(token, value, "p")
    assert str(error.value) == message


def test_steps_count_from_the_minimum():
    token = Token("n", "integer", "shared", "", minimum=1, maximum=11, step=5)
    validate_value(token, 6, "p")
    with pytest.raises(ThemeError, match="^p: n 5: expected steps of 5 from 1$"):
        validate_value(token, 5, "p")


def test_catalog_and_values_text():
    lines = catalog_text(theme_catalog()).split("\n")
    assert len(lines) == len(TOKENS) + 1
    assert lines[0] == "Presets: varde, paper, harbor, signal"
    assert {
        "surface: colour #rrggbb",
        "heading-case: enum none|upper",
        "type-scale: number 0.9..1.15",
        "heading-weight: integer 500..800 step 50",
    } <= set(lines)
    values: dict[str, dict[str, object]] = {"shared": {"radius": 8, "page-width": 60}}
    assert values_text(values) == "shared.radius: 8\nshared.page-width: 60"
