import pytest

from tavle.theme.layers import Layer, parse_frontmatter, parse_toml
from tavle.theme.merge import resolve_layers
from tavle.theme.tokens import TOKENS, ThemeError

# Some derive_colour mutants loop forever; fail fast so they count as killed.
pytestmark = pytest.mark.timeout(2, method="signal")


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


PRESETS = "expected one of varde, paper, harbor, signal"


@pytest.mark.parametrize(
    ("parse", "source", "message"),
    [
        (
            parse_toml,
            "series = 1",
            (
                "f: unknown token 'series' with value 1; "
                "nearest: series-5, series-4, series-3"
            ),
        ),
        (parse_toml, "zzzzzz = 1", "f: unknown token 'zzzzzz' with value 1"),
        (
            parse_toml,
            "rad = 1",
            "f: unknown token 'rad' with value 1; nearest: radius, card, surface",
        ),
        (
            parse_toml,
            'preset = "papr"',
            f"f: preset 'papr': {PRESETS}; nearest: paper",
        ),
        (parse_toml, 'preset = "zzz"', f"f: preset 'zzz': {PRESETS}"),
        (
            parse_toml,
            'preset = "parde"',
            f"f: preset 'parde': {PRESETS}; nearest: varde, paper",
        ),
        (parse_toml, "preset = 5", f"f: preset 5: {PRESETS}"),
        (parse_toml, "light = 1", "f: light 1: expected table"),
        (
            parse_toml,
            "[light]\nradius = 3",
            "f: radius 3: expected shared position",
        ),
        (parse_frontmatter, {"theme": "zzz"}, f"f: preset 'zzz': {PRESETS}"),
        (
            parse_frontmatter,
            {"theme.zzzzzz": "1"},
            "f: unknown token 'zzzzzz' with value '1'",
        ),
        (
            parse_frontmatter,
            {"theme.radius": "wide"},
            "f: radius 'wide': expected integer",
        ),
        (
            parse_frontmatter,
            {"theme.dark.radius": "3"},
            "f: radius 3: expected shared position",
        ),
    ],
)
def test_exact_errors(parse, source, message):
    with pytest.raises(ThemeError) as error:
        parse(source, "f")
    assert str(error.value) == message


def test_frontmatter_default_label_and_number():
    assert parse_frontmatter({"theme.type-scale": "1.1"}).shared == {"type-scale": 1.1}
    with pytest.raises(ThemeError, match="^front matter: preset"):
        parse_frontmatter({"theme": "zzz"})


def test_resolved_sources_name_each_layer():
    names = {token.name for token in TOKENS if token.scope == "scheme"}
    default = resolve_layers([])
    assert default.sources["light"]["accent"] == "preset varde"
    assert set(default.sources["dark"]) == names
    layered = resolve_layers([(Layer(preset="paper", shared={"radius": 3}), "page")])
    assert layered.sources["light"]["accent"] == "preset paper"
    assert layered.sources["shared"]["radius"] == "page"
    assert set(layered.sources["dark"]) == names


def test_merged_contrast_failure_names_the_last_layer():
    layers = [(Layer(), "file"), (Layer(light={"accent": "#aaaaaa"}), "page")]
    with pytest.raises(ThemeError, match="^page: "):
        resolve_layers(layers)
