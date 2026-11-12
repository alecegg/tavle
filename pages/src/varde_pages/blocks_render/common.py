"""Escaping and card helpers shared by the block renderers. Pure functions."""

import html
import re
from typing import Any


def esc(value: object) -> str:
    return html.escape(str(value))


_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}(?!\d)")


def dated_html(text: object) -> str:
    """Escaped text with each ISO date held on one line (no break at its hyphens)."""
    return _ISO_DATE.sub(r'<span class="vd-date">\g<0></span>', esc(text))


def as_list(value: object) -> list[Any]:
    """Validated blocks hold lists where the schema says so; anything else is empty."""
    return value if isinstance(value, list) else []


def as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def badge(text: object, kind: str = "") -> str:
    cls = f"vb-badge {kind}".strip()
    return f'<span class="{cls}">{esc(text)}</span>'


def card(title_html: str, body_html: str, kind: str = "") -> str:
    cls = f"vb-card {kind}".strip()
    head = f'<h4 class="vb-title">{title_html}</h4>' if title_html else ""
    return f'<section class="{cls}">{head}{body_html}</section>'


def count_noun(count: int, one: str, many: str) -> str:
    """`1 entity`, `2 entities`."""
    return f"{count} {one if count == 1 else many}"
