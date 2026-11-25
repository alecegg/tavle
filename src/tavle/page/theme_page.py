"""Resolve themes for rendered pages and builds."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from hashlib import sha256
from html import escape
from pathlib import Path

from ..theme.css import style_element, theme_css
from ..theme.layers import Layer, parse_frontmatter
from ..theme.merge import resolve_layers
from ..theme.resolved import ResolvedTheme
from ..theme.tokens import ThemeError
from .render import split_frontmatter, strip_comments

ThemeLayers = Callable[[Path], Sequence[tuple[Layer, str]]]


def no_layers(doc: Path) -> Sequence[tuple[Layer, str]]:
    """Supply no external theme layers."""
    return ()


@dataclass(frozen=True)
class PageTheme:
    style: str
    error: str


def doc_theme(
    doc: Path, text: str, theme_layers: ThemeLayers = no_layers
) -> ResolvedTheme:
    """Resolve the theme for a page from its layers and front matter."""
    frontmatter, _ = split_frontmatter(strip_comments(text.splitlines()))
    layers = list(theme_layers(doc))
    page = parse_frontmatter(frontmatter)
    if page.preset or page.shared or page.light or page.dark:
        layers.append((page, "front matter"))
    return resolve_layers(layers)


def require_theme(doc: Path, text: str, theme_layers: ThemeLayers = no_layers) -> str:
    """Return the theme style, raising on invalid input."""
    theme = doc_theme(doc, text, theme_layers)
    return style_element(theme_css(theme)) if theme.active else ""


def page_theme(
    doc: Path, text: str, theme_layers: ThemeLayers = no_layers
) -> PageTheme:
    """Return a theme style or a visible error for a served page."""
    try:
        theme = doc_theme(doc, text, theme_layers)
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
