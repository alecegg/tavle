"""Theme CSS scopes and injection boundary."""

import pytest

from tavle import resolve_layers
from tavle.theme.css import style_element, theme_css
from tavle.theme.resolved import ResolvedTheme

# Some derive_colour mutants loop forever; fail fast so they count as killed.
pytestmark = pytest.mark.timeout(2, method="signal")


def test_scopes_and_declarations() -> None:
    theme = resolve_layers([])
    css = theme_css(theme)
    light, rest = css.split("@media (prefers-color-scheme: dark) {\n")
    os_dark, explicit = rest.split(
        ':root[data-theme="dark"], :host([data-theme="dark"]) {\n'
    )
    os_declarations = os_dark.split("{\n", 1)[1].rsplit("\n  }\n}", 1)[0]
    assert os_declarations == explicit.rsplit("\n}", 1)[0]
    assert light.count("--vd-font-body:") == 1
    assert all(
        line.strip().startswith("--vd-")
        for line in css.splitlines()
        if ": " in line and line.strip().endswith(";")
    )
    assert style_element(css) == f"<style data-vd-theme>{css}</style>"


def test_rejects_injection() -> None:
    theme = resolve_layers([])
    for bad in ("red; color: blue", "</style><script>"):
        theme.shared["--vd-injected"] = bad
        with pytest.raises(ValueError):
            theme_css(theme)
    with pytest.raises(ValueError, match="^Invalid style content$"):
        style_element("</STYLE>")


def _theme(light: dict) -> ResolvedTheme:
    return ResolvedTheme({}, {}, light, {"--vd-a": (0, 0, 0, 0.5)}, {}, False)


def test_exact_output() -> None:
    theme = _theme({"--vd-a": (100, 10.5, 0, 1)})
    theme.shared["--vd-b"] = "1rem"
    light = "  --vd-a: rgba(100, 10.5, 0, 1);\n  --vd-b: 1rem;"
    dark = "  --vd-a: rgba(0, 0, 0, 0.5);"
    assert theme_css(theme) == (
        f":root, :host {{\n{light}\n}}\n"
        "@media (prefers-color-scheme: dark) {\n"
        '  :root:not([data-theme="light"]), :host(:not([data-theme="light"])) {\n'
        f"{dark}\n  }}\n}}\n"
        f':root[data-theme="dark"], :host([data-theme="dark"]) {{\n{dark}\n}}\n'
    )


@pytest.mark.parametrize(
    ("light", "message"),
    [
        ({"--vd-a": (1, 2, 3)}, "^Invalid theme colour$"),
        ({"--vd-a": "red"}, "^Invalid theme value: 'red'$"),
        ({"a": "1rem"}, "^Invalid theme name: 'a'$"),
    ],
)
def test_error_messages(light: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        theme_css(_theme(light))
