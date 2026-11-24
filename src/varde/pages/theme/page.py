"""Resolve themes for rendered pages and builds."""

from dataclasses import dataclass
from hashlib import sha256
from html import escape
from pathlib import Path

from varde.pages.render import split_frontmatter, strip_comments
from varde.pages.theme.resolve import ResolvedTheme, resolve_theme
from varde.ui import ThemeError, style_element, theme_css


@dataclass(frozen=True)
class PageTheme:
    style: str
    error: str


def doc_theme(doc: Path, text: str) -> ResolvedTheme:
    """Resolve the theme for a page from its layers and front matter."""
    frontmatter, _ = split_frontmatter(strip_comments(text.splitlines()))
    return resolve_theme(doc, frontmatter)


def require_theme(doc: Path, text: str) -> str:
    """Return the theme style, raising on invalid input."""
    theme = doc_theme(doc, text)
    return style_element(theme_css(theme)) if theme.active else ""


def page_theme(doc: Path, text: str) -> PageTheme:
    """Return a theme style or a visible error for a served page."""
    try:
        theme = doc_theme(doc, text)
        if not theme.active:
            return PageTheme("", "")
        digest = sha256(theme_css(theme).encode()).hexdigest()[:12]
        return PageTheme(
            f'<link rel="stylesheet" data-vd-theme href="/theme.css?v={digest}">', ""
        )
    except ThemeError as exc:
        return PageTheme(
            "", f'<p class="vd-theme-error" role="alert">{escape(str(exc))}</p>'
        )
