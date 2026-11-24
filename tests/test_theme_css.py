"""Theme CSS scopes and injection boundary."""

from pathlib import Path

import pytest
from varde.pages.theme.resolve import resolve_theme

from tavle.theme.css import style_element, theme_css


def test_scopes_and_declarations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VARDE_CONFIG_DIR", str(tmp_path / "config"))
    theme = resolve_theme(tmp_path / "page.md")
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


def test_rejects_injection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VARDE_CONFIG_DIR", str(tmp_path / "config"))
    theme = resolve_theme(tmp_path / "page.md")
    for bad in ("red; color: blue", "</style><script>"):
        theme.shared["--vd-injected"] = bad
        with pytest.raises(ValueError):
            theme_css(theme)
    with pytest.raises(ValueError):
        style_element("</STYLE>")
