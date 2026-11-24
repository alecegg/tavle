from pathlib import Path

import pytest

from varde.pages.theme.page import page_theme, require_theme
from varde.pages.theme.tokens import ThemeError


def test_no_theme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VARDE_CONFIG_DIR", str(tmp_path / "config"))
    result = page_theme(tmp_path / "page.md", "# Page")
    assert result.style == ""
    assert result.error == ""


def test_harbor_theme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VARDE_CONFIG_DIR", str(tmp_path / "config"))
    result = page_theme(tmp_path / "page.md", "---\ntheme: harbor\n---\n# Page")
    assert result.style.startswith("<style data-vd-theme>")
    assert "--vd-accent: rgba(0, 107, 115, 1);" in result.style
    assert result.error == ""


def test_invalid_theme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VARDE_CONFIG_DIR", str(tmp_path / "config"))
    text = "---\ntheme: <invalid>\n---\n# Page"
    result = page_theme(tmp_path / "page.md", text)
    assert result.style == ""
    assert '<p class="vd-theme-error" role="alert">' in result.error
    assert "&lt;invalid&gt;" in result.error
    with pytest.raises(ThemeError):
        require_theme(tmp_path / "page.md", text)
