"""Keep theme declarations in step with the shared token stylesheet."""

import re
from pathlib import Path

import pytest

from tavle import UI_STATIC as UI_STATIC_DIR
from tavle import doc_theme
from tavle.theme.css import theme_css
from tavle.theme.derive_shape import FIXED_TOKENS
from tavle.theme.presets import PRESET_NAMES, load_preset

TOKEN_FILE = UI_STATIC_DIR / "css/00-tokens.css"
DECLARATION = re.compile(r"(--vd-[\w-]+)\s*:")


def _resolve_theme(doc, frontmatter=None):
    text = (
        "---\n"
        + "\n".join(f"{k}: {v}" for k, v in (frontmatter or {}).items())
        + "\n---\n"
    )
    return doc_theme(doc, text)


def test_token_coverage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VARDE_CONFIG_DIR", str(tmp_path / "config"))
    theme = _resolve_theme(tmp_path / "page.md")
    derived = set(theme.light) | set(theme.dark) | set(theme.shared)
    tokens = set(DECLARATION.findall(TOKEN_FILE.read_text(encoding="utf-8")))
    assert derived.isdisjoint(FIXED_TOKENS)
    assert tokens == derived | FIXED_TOKENS


@pytest.mark.parametrize("name", PRESET_NAMES)
def test_preset_emits_only_known_tokens(
    name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VARDE_CONFIG_DIR", str(tmp_path / "config"))
    assert load_preset(name)
    theme = _resolve_theme(tmp_path / "page.md", {"theme": name})
    tokens = set(DECLARATION.findall(TOKEN_FILE.read_text(encoding="utf-8")))
    emitted = set(DECLARATION.findall(theme_css(theme)))
    assert emitted
    assert emitted <= tokens
