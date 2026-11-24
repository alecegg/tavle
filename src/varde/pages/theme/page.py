"""Resolve themes for rendered pages and builds."""

from dataclasses import dataclass
from html import escape
from pathlib import Path

from varde.pages.render import split_frontmatter, strip_comments
from varde.pages.theme.css import style_element, theme_css
from varde.pages.theme.resolve import resolve_theme
from varde.pages.theme.tokens import ThemeError


@dataclass(frozen=True)
class PageTheme:
    style: str
    error: str


def require_theme(doc: Path, text: str) -> str:
    """Return the theme style, raising on invalid input."""
    frontmatter, _ = split_frontmatter(strip_comments(text.splitlines()))
    theme = resolve_theme(doc, frontmatter)
    return style_element(theme_css(theme)) if theme.active else ""


def page_theme(doc: Path, text: str) -> PageTheme:
    """Return a theme style or a visible error for a served page."""
    try:
        return PageTheme(require_theme(doc, text), "")
    except ThemeError as exc:
        return PageTheme(
            "", f'<p class="vd-theme-error" role="alert">{escape(str(exc))}</p>'
        )
