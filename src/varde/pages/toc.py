"""Table of contents nav for a rendered page: pure, no I/O."""

from __future__ import annotations

import html
from collections.abc import Iterable
from dataclasses import dataclass

MIN_ENTRIES = 2
LEVELS = (2, 3)


@dataclass(frozen=True)
class TocEntry:
    level: int
    text: str
    target: str  # the id the link points at


def toc_entries(headings: Iterable[tuple[int, str, str]]) -> tuple[TocEntry, ...]:
    """Keep h2 and h3 from (level, text, target id) triples; h1 is the title."""
    return tuple(
        TocEntry(level, " ".join(text.split()), target)
        for level, text, target in headings
        if level in LEVELS
    )


def _item(entry: TocEntry) -> str:
    link = f'<a href="#{html.escape(entry.target)}">{html.escape(entry.text)}</a>'
    return f'<li class="toc-l{entry.level}">{link}</li>'


def toc_html(entries: tuple[TocEntry, ...]) -> str:
    """The nav, or "" below two entries. Level only indents; the list is flat."""
    if len(entries) < MIN_ENTRIES:
        return ""
    items = "".join(_item(entry) for entry in entries)
    return (
        '<nav class="doc-toc" aria-label="Contents"><details>'
        f"<summary>Contents ({len(entries)})</summary><ol>{items}</ol>"
        "</details></nav>"
    )
