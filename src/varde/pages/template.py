"""Host-owned HTML shell shared by the served page and the static export."""

from __future__ import annotations

import html
import re
from functools import cache
from importlib.resources import files

from varde.ui.shell import static_css

# Load order for the known scripts (`recap.js` hosts `window.varde` and
# `inputs_ordered.js` uses it, so they come last in that order); any other
# `static/*.js` follows alphabetically.
_SCRIPT_ORDER = (
    "app.js",
    "blocks.js",
    "recap.js",
    "inputs_ordered.js",
)
_MODULE_SYNTAX = re.compile(r"^(import|export)\s", re.MULTILINE)


@cache
def _is_es_module(name: str) -> bool:
    """A `static/*.js` with `import` or `export` lines is loaded by another script."""
    path = files("varde.pages").joinpath("static", name)
    return _MODULE_SYNTAX.search(path.read_text(encoding="utf-8")) is not None


def static_scripts() -> tuple[str, ...]:
    """Script file names shipped in `static/`, in page load order."""
    found = sorted(
        entry.name
        for entry in files("varde.pages").joinpath("static").iterdir()
        if entry.name.endswith(".js")
    )
    known = [name for name in _SCRIPT_ORDER if name in found]
    return (*known, *(name for name in found if name not in known))


BUNDLE_SCRIPT = "components.js"  # built by `varde.ui.components`, not a file


def page_scripts() -> tuple[str, ...]:
    """Scripts that get a tag: the component bundle, then `static_scripts` that
    are not ES modules (those are imported, not tagged)."""
    classic = (name for name in static_scripts() if not _is_es_module(name))
    return (BUNDLE_SCRIPT, *classic)


def _served_head(token: str | None, title_tag: str) -> str:
    scripts = "".join(
        f'<script src="/static/{n}" defer></script>' for n in page_scripts()
    )
    token_meta = ""
    if token is not None:
        token_meta = f'<meta name="varde-token" content="{html.escape(token)}">'
    return (
        f"{token_meta}"
        f'{title_tag}<link rel="stylesheet" href="/static/app.css">{scripts}'
    )


def _api_body_attrs(api_base: str) -> str:
    """Body attributes the page scripts read when serve hosts the page."""
    page_url = "/pages/" + api_base.removeprefix("/api/pages/")
    return (
        f' data-api-base="{html.escape(api_base)}"'
        f' data-page-url="{html.escape(page_url)}"'
    )


def page_shell(title: str, main: str, token: str | None, api_base: str = "") -> str:
    """Served page when `token` is set; else self-contained with no script.

    A non-empty `api_base` (`/api/pages/<relpath>`) makes the served page post
    to that base without a token and refresh from `/pages/<relpath>`.
    """
    title_tag = f"<title>{html.escape(title)}</title>"
    if api_base:
        head = _served_head(None, title_tag)
    elif token is None:
        head = title_tag + f"<style>{static_css()}</style>"
    else:
        head = _served_head(token, title_tag)
    body_attrs = _api_body_attrs(api_base) if api_base else ""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"{head}</head><body{body_attrs}>{main}</body></html>"
    )
