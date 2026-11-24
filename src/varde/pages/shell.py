"""Standalone page shell and shared component assets."""

import html
from importlib.resources import files

HOST_ATTR = "data-mithril"
_INPUT_TAGS = tuple(
    (f"<{tag} ", f"<{tag} disabled ")
    for tag in ("button", "textarea", "input", "select")
)


TOKENS_CSS = (  # mollify: ignore[hardcoded-secret] a CSS file name, not a credential
    "00-tokens.css"  # the design tokens; a host page that owns its own skips it
)


def static_css(skip: tuple[str, ...] = ()) -> str:
    """Page stylesheet: `static/css/*.css` concatenated in name order, minus `skip`."""
    parts = sorted(
        (
            entry
            for entry in files("varde.pages").joinpath("static", "css").iterdir()
            if entry.name.endswith(".css") and entry.name not in skip
        ),
        key=lambda entry: entry.name,
    )
    return "\n".join(entry.read_text(encoding="utf-8") for entry in parts)


def make_read_only(body: str) -> str:
    """Disable input widgets. Agent text is escaped, so these tags are host-made.

    A client-side block host is marked `data-readonly`; mounting disables its controls.
    """
    for tag, disabled in _INPUT_TAGS:
        body = body.replace(tag, disabled)
    return body.replace(f"<div {HOST_ATTR}=", f"<div data-readonly {HOST_ATTR}=")


def standalone_shell(title: str, main: str) -> str:
    """Build a self-contained page without scripts."""
    title_tag = f"<title>{html.escape(title)}</title>"
    head = title_tag + f"<style>{static_css()}</style>"
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"{head}</head><body>{main}</body></html>"
    )
