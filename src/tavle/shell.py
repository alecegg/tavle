"""Standalone page shell and shared component assets."""

import html
from collections.abc import Iterable
from importlib.resources import files
from importlib.resources.abc import Traversable

HOST_ATTR = "data-mithril"
_INPUT_TAGS = tuple(
    (f"<{tag} ", f"<{tag} disabled ")
    for tag in ("button", "textarea", "input", "select")
)


TOKENS_CSS = (  # mollify: ignore[hardcoded-secret] a CSS file name, not a credential
    "00-tokens.css"  # the design tokens; a host page that owns its own skips it
)


UI_STATIC = files("tavle").joinpath("static")
VENDOR_ASSETS = frozenset({"mithril.js"})


def vendor_asset(name: str) -> bytes:
    """Bytes of a vendored script; any name off the allowlist raises ValueError."""
    if name not in VENDOR_ASSETS:
        raise ValueError(f"unknown vendor asset: {name!r}")
    return UI_STATIC.joinpath("vendor", name).read_bytes()


def token_css() -> str:
    """The design-token stylesheet alone, for a host that loads blocks CSS itself."""
    return UI_STATIC.joinpath("css", TOKENS_CSS).read_text(encoding="utf-8")


def css_files() -> list[Traversable]:
    """The library's stylesheets: tokens, base, inputs and blocks."""
    return [e for e in UI_STATIC.joinpath("css").iterdir() if e.name.endswith(".css")]


def join_css(entries: Iterable[Traversable], skip: tuple[str, ...] = ()) -> str:
    """Concatenate stylesheets in file-name order, minus `skip`.

    A host merges its own files with `css_files()` here so the number prefixes
    keep one cascade order across both packages.
    """
    kept = sorted((e for e in entries if e.name not in skip), key=lambda e: e.name)
    return "\n".join(entry.read_text(encoding="utf-8") for entry in kept)


def static_css(skip: tuple[str, ...] = ()) -> str:
    """The library stylesheet: `css_files()` joined in name order, minus `skip`."""
    return join_css(css_files(), skip)


def make_read_only(body: str) -> str:
    """Disable input widgets. Agent text is escaped, so these tags are host-made.

    A client-side block host is marked `data-readonly`; mounting disables its controls.
    """
    for tag, disabled in _INPUT_TAGS:
        body = body.replace(tag, disabled)
    return body.replace(f"<div {HOST_ATTR}=", f"<div data-readonly {HOST_ATTR}=")


def standalone_shell(title: str, main: str, css: str) -> str:
    """Build a self-contained page without scripts, with `css` inline."""
    title_tag = f"<title>{html.escape(title)}</title>"
    head = title_tag + f"<style>{css}</style>"
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"{head}</head><body>{main}</body></html>"
    )
