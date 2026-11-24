import pytest

from varde.pages.theme.layers import parse_frontmatter, parse_toml
from varde.pages.theme.tokens import ThemeError


def test_toml_layer():
    layer = parse_toml(
        'preset = "harbor"\nradius = 10\n[light]\naccent = "#123456"\n'
        '[dark]\naccent = "#abcdef"',
        "file",
    )
    assert (layer.preset, layer.shared, layer.light, layer.dark) == (
        "harbor",
        {"radius": 10},
        {"accent": "#123456"},
        {"accent": "#abcdef"},
    )


def test_frontmatter():
    layer = parse_frontmatter(
        {
            "title": "test",
            "theme": "paper",
            "theme.radius": "10",
            "theme.accent": "#123456",
            "theme.dark.accent": "#abcdef",
        }
    )
    assert layer.preset == "paper"
    assert layer.shared == {"radius": 10}
    assert layer.light == {"accent": "#123456"}
    assert layer.dark == {"accent": "#abcdef"}


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("acccent = 1", "accent"),
        ('radius = "wide"', "integer"),
        ("radius = 99", "radius"),
        ('accent = "#123456"', "scheme position"),
        ("[light", "malformed TOML"),
    ],
)
def test_invalid(text, message):
    with pytest.raises(ThemeError, match=message) as error:
        parse_toml(text, "my file")
    assert "my file" in str(error.value)
