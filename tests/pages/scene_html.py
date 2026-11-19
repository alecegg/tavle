"""Markup of the SVG shapes a block's props carry, so geometry tests can match text.

The browser builds these shapes (`static/components/shared.js` `scene`); this is the
same tree as a string, for assertions about what the server drew.
"""

from __future__ import annotations

import html
from typing import Any


def shapes_html(shapes: list[Any]) -> str:
    out = []
    for tag, attrs, content in shapes:
        attributes = "".join(f' {k}="{html.escape(v)}"' for k, v in attrs.items())
        if content is None:
            inner = ""
        elif isinstance(content, str):
            inner = html.escape(content)
        else:
            inner = shapes_html(content)
        out.append(f"<{tag}{attributes}>{inner}</{tag}>")
    return "".join(out)


def svg_html(props: dict[str, Any], cls: str = "") -> str:
    """The `<svg>` the component builds around `props["shapes"]`."""
    title, desc = html.escape(props["title"]), html.escape(props["desc"])
    css = f' class="{cls}"' if cls else ""
    return (
        f'<svg{css} viewBox="{props["box"]}" role="img" aria-label="{title}">'
        f"<title>{title}</title><desc>{desc}</desc>{shapes_html(props['shapes'])}</svg>"
    )
