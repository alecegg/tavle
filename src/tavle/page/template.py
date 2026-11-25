"""Host-owned HTML shell shared by the served page and the static export."""

from __future__ import annotations

import html
import re
from functools import cache
from importlib.resources import files
from importlib.resources.abc import Traversable

from ..shell import UI_STATIC, css_files, join_css

# Load order for the known scripts (`recap.js` hosts `window.varde` and
# `inputs_ordered.js` uses it, so they come last in that order); any other
# `static/*.js` follows alphabetically.
_SCRIPT_ORDER = (
    "app.js",
    "blocks.js",
    "inputs_fields.js",
    "inputs_widgets.js",
    "inputs_runtime.js",
    "recap.js",
    "inputs_ordered.js",
)
_MODULE_SYNTAX = re.compile(r"^(import|export)\s", re.MULTILINE)


_HOST_STATIC = files("tavle.page").joinpath("static")


def static_file(name: str) -> Traversable:
    """A served `/static/<name>` file: tavle's own page scripts, else the library's."""
    host = _HOST_STATIC.joinpath(name)
    return host if host.is_file() else UI_STATIC.joinpath(name)


def page_css(skip: tuple[str, ...] = ()) -> str:
    """The page stylesheet: library and page-chrome CSS in one name order."""
    host = (
        e for e in _HOST_STATIC.joinpath("css").iterdir() if e.name.endswith(".css")
    )
    return join_css([*css_files(), *host], skip)


@cache
def _is_es_module(name: str) -> bool:
    """A `static/*.js` with `import` or `export` lines is loaded by another script."""
    text = static_file(name).read_text(encoding="utf-8")
    return _MODULE_SYNTAX.search(text) is not None


def static_scripts() -> tuple[str, ...]:
    """Script file names served under `/static/`, in page load order."""
    found = sorted(
        entry.name
        for folder in (_HOST_STATIC, UI_STATIC)
        for entry in folder.iterdir()
        if entry.name.endswith(".js")
    )
    known = [name for name in _SCRIPT_ORDER if name in found]
    return (*known, *(name for name in found if name not in known))


BUNDLE_SCRIPT = "components.js"  # built by the UI bundle, not a file


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
        head = title_tag + f"<style>{page_css()}</style>"
    else:
        head = _served_head(token, title_tag)
    body_attrs = _api_body_attrs(api_base) if api_base else ""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"{head}</head><body{body_attrs}>{main}</body></html>"
    )
